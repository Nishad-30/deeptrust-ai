# api/views.py
import uuid
import mimetypes
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.shortcuts import get_object_or_404

from .mongo import media_docs
from .minio_client import minio_client, BUCKET
from .models import VerificationJob
from django_q.tasks import async_task
from .qtasks import orchestrate_job


# /api/verify/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_media(request):
    user = request.user
    uploaded_file = request.FILES.get("file")
    text_input = request.data.get("text_input", "").strip()
    claim_text = request.data.get("claim_text", "").strip()

    if not uploaded_file and not text_input:
        return Response({"error": "Please upload a file or enter text."}, status=400)

    media_id = f"m-{uuid.uuid4()}"
    job_id = f"job-{uuid.uuid4()}"

    minio_path = None
    file_type = None
    sha256 = None
    phash = None

    # If uploaded file: save to local (dev) or MinIO; determine file type
    if uploaded_file:
        # determine type from filename
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if mime_type:
            if mime_type.startswith("image"):
                file_type = "image"
            elif mime_type.startswith("video"):
                file_type = "video"
            elif mime_type.startswith("audio"):
                file_type = "audio"
        # save locally (development) or to MinIO
        if os.getenv("DEVELOPMENT_MODE", "True") == "True":
            local_path = os.path.join(settings.MEDIA_ROOT, f"{media_id}_{uploaded_file.name}")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            minio_path = f"local://{local_path}"
        else:
            minio_path = f"uploads/{media_id}/{uploaded_file.name}"
            # minio_client.put_object expects a stream - for file upload use uploaded_file.file or uploaded_file.read
            minio_client.put_object(BUCKET, minio_path, uploaded_file, length=uploaded_file.size)

    # If only text input, mark file_type as text
    if not file_type and text_input:
        file_type = "text"

    # Insert media doc in Mongo (include file_type)
    media_doc = {
        "media_id": media_id,
        "user_id": str(user.id),
        "minio_path": minio_path,
        "text_input": text_input,
        "claim_text": claim_text,
        "file_type": file_type,
        "status": "uploaded",
    }
    media_docs.insert_one(media_doc)

    # Create SQL job
    VerificationJob.objects.create(
        job_id=job_id,
        user=user,
        media_id=media_id,
        status="processing",
        result_ready=False
    )

    # Kick off orchestration (Celery)
    async_task("api.qtasks.orchestrate_job", job_id, media_id)

    return Response({"message": "Verification started.", "job_id": job_id, "media_id": media_id}, status=200)


# /api/status/<job_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_status(request, job_id):
    try:
        job = VerificationJob.objects.get(job_id=job_id, user=request.user)
    except VerificationJob.DoesNotExist:
        return Response({"error": "Invalid job_id"}, status=404)

    media_doc = media_docs.find_one({"media_id": job.media_id}) or {}
    status = media_doc.get("status", job.status or "processing")

    # compute progress heuristically
    keys = ["frames_extracted", "transcript", "authenticity_score", "claim_extracted", "truthscore"]
    completed = sum(1 for k in keys if media_doc.get(k))
    progress = int((completed / max(len(keys), 1)) * 100)
    if status == "completed":
        progress = 100

    return Response({
        "job_id": job.job_id,
        "media_id": job.media_id,
        "status": status,
        "progress": progress
    })


# /api/report/<job_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_report(request, job_id):
    try:
        job = VerificationJob.objects.get(job_id=job_id, user=request.user)
    except VerificationJob.DoesNotExist:
        return Response({"error": "Invalid job_id"}, status=404)

    media_doc = media_docs.find_one({"media_id": job.media_id}) or {}
    claim = media_doc.get("claim") or {}
    verification = media_doc.get("verification") or {}

    result = {
        "job_id": job.job_id,
        "media_id": job.media_id,
        "status": media_doc.get("status"),
        "authenticity_score": media_doc.get("authenticity_score"),
        "transcript": media_doc.get("transcript"),
        "text_ai_score": media_doc.get("text_ai_score"),
        "truthscore": media_doc.get("truthscore"),
        "claim": {
            "normalized_text": claim.get("normalized_text"),
            "latest_verdict": claim.get("latest_verdict"),
        } if claim else None,
        "evidence": verification.get("evidence", []),
    }
    return Response(result)
