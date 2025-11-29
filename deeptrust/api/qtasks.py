# api/qtasks.py
import time
from django_q.tasks import async_task
from .mongo import media_docs
from .chief import generate_task_plan
from .models import VerificationJob


def orchestrate_job(job_id, media_id):
    """
    Orchestrates the entire verification pipeline.
    Replaces Celery's orchestrate_job.delay()
    """
    print("🎬 Django-Q: Starting Orchestration", job_id)

    job = VerificationJob.objects.get(job_id=job_id)
    media_doc = media_docs.find_one({"media_id": media_id})

    # 1) Generate task plan via LLM
    plan = generate_task_plan(media_doc)

    # 2) Run subtasks based on plan
    for step in plan["plan"]:
        step_type = step["task"]

        if step_type == "extract_frames":
            async_task("api.qtasks.extract_frames", job_id, media_id)

        elif step_type == "transcribe_audio":
            async_task("api.qtasks.transcribe_audio", job_id, media_id)

        elif step_type == "authenticity":
            async_task("api.qtasks.authenticity_check", job_id, media_id)

        elif step_type == "claim_extract":
            async_task("api.qtasks.claim_extract", job_id, media_id)

        elif step_type == "truthscore":
            async_task("api.qtasks.truthscore_compute", job_id, media_id)

    # 3) Finalize when all tasks done
    async_task("api.qtasks.job_finalize", job_id, media_id)

    return True


def extract_frames(job_id, media_id):
    print("🎞 Extracting frames...")
    time.sleep(3)
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"frames_extracted": True}}
    )


def transcribe_audio(job_id, media_id):
    print("🎤 Transcribing audio...")
    time.sleep(3)
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"transcript": "Dummy transcript"}}
    )


def authenticity_check(job_id, media_id):
    print("🔍 Authenticity check...")
    time.sleep(3)
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"authenticity_score": 0.88}}
    )


def claim_extract(job_id, media_id):
    print("📝 Extracting claim...")
    time.sleep(3)
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"claim_extracted": "Example claim"}}
    )


def truthscore_compute(job_id, media_id):
    print("📊 Truthscore compute...")
    time.sleep(3)
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"truthscore": 72}}
    )


def job_finalize(job_id, media_id):
    print("🏁 Finalizing job...")
    media_docs.update_one(
        {"media_id": media_id},
        {"$set": {"status": "completed"}}
    )
    VerificationJob.objects.filter(job_id=job_id).update(
        status="completed",
        result_ready=True
    )
