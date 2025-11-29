# api/tasks.py
import time, json
from celery import shared_task, chain
from django.utils import timezone
from .mongo import media_docs, claims, verifications
from .chief import generate_task_plan

# Agent functions referenced below (placeholders)
@shared_task
def extract_frames(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"frames_extracted": True}})

@shared_task
def transcribe_audio(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"transcript": "dummy transcript", "transcript_at": timezone.now()}})

@shared_task
def authenticity_image(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"authenticity_score": 0.12}})

@shared_task
def authenticity_video(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"authenticity_score": 0.22}})

@shared_task
def authenticity_audio(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"audio_authenticity": 0.10}})

@shared_task
def detect_text_ai(args):
    media_id = args["media_id"]
    time.sleep(1)
    media_docs.update_one({"media_id": media_id}, {"$set": {"text_ai_score": 0.30}})

@shared_task
def claim_extract(args):
    media_id = args["media_id"]
    time.sleep(1)
    claim_doc = {"normalized_text":"dummy claim", "media_id":media_id, "created_at": timezone.now()}
    media_docs.update_one({"media_id": media_id}, {"$set":{"claim": claim_doc, "claim_extracted": True}})

@shared_task
def claim_normalize(args):
    media_id = args["media_id"]
    time.sleep(1)
    # update normalized claim
    media_docs.update_one({"media_id": media_id}, {"$set":{"claim.normalized_text":"normalized dummy claim"}})

@shared_task
def claim_lookup_cache(args):
    media_id = args["media_id"]
    time.sleep(0.2)
    # In real system check claim_hash in claims collection

@shared_task
def retrieval_semantic_search(args):
    media_id = args["media_id"]
    time.sleep(1)
    # Insert dummy evidence
    verifications.insert_one({"media_id": media_id, "evidence": ["dummy evidence"], "created_at": timezone.now()})

@shared_task
def verification_ensemble(args):
    media_id = args["media_id"]
    time.sleep(1)
    # set verdict in claim & verification
    media_docs.update_one({"media_id": media_id}, {"$set":{"claim.latest_verdict":"Supported"}})
    verifications.update_one({"media_id": media_id}, {"$set":{"completed": True}}, upsert=True)

@shared_task
def truthscore_compute(args):
    media_id = args["media_id"]
    time.sleep(1)
    # compute truthscore and update
    media_docs.update_one({"media_id": media_id}, {"$set":{"truthscore": 92}})

@shared_task
def job_finalize(args):
    media_id = args["media_id"]

    # mark media_doc completed
    media_docs.update_one({"media_id": media_id}, {"$set": {"status": "completed", "completed_at": timezone.now()}})

    # Update SQL VerificationJob too (import lazily to avoid circular import)
    from .models import VerificationJob
    VerificationJob.objects.filter(media_id=media_id).update(status="completed", result_ready=True, updated_at=timezone.now())

    # Optionally write final verification doc
    ver_doc = verifications.find_one({"media_id": media_id}) or {}
    media_docs.update_one({"media_id": media_id}, {"$set": {"verification": ver_doc}})


@shared_task
def orchestrate_job(job_id, media_id):
    media_doc = media_docs.find_one({"media_id": media_id})
    if not media_doc:
        print("media not found")
        return

    # produce plan
    plan = generate_task_plan(media_doc)
    steps = plan.get("plan", [])

    # ensure job_finalize is present as last step
    if not steps or steps[-1].get("task") != "job_finalize":
        steps.append({"task":"job_finalize","args":{"media_id":media_id}})

    # build chain of task signatures (using the local named task functions)
    sigs = []
    for step in steps:
        task_name = step["task"]
        args = step.get("args", {})
        # Map to our shared_task function names
        mapping = {
            "extract_frames": extract_frames.s,
            "transcribe_audio": transcribe_audio.s,
            "authenticity_image": authenticity_image.s,
            "authenticity_video": authenticity_video.s,
            "authenticity_audio": authenticity_audio.s,
            "detect_text_ai": detect_text_ai.s,
            "claim_extract": claim_extract.s,
            "claim_normalize": claim_normalize.s,
            "claim_lookup_cache": claim_lookup_cache.s,
            "retrieval_semantic_search": retrieval_semantic_search.s,
            "verification_ensemble": verification_ensemble.s,
            "truthscore_compute": truthscore_compute.s,
            "job_finalize": job_finalize.s
        }
        fn = mapping.get(task_name)
        if fn:
            sigs.append(fn(args))
        else:
            # unknown task — no-op
            print("Unknown task:", task_name)

    if sigs:
        # chain them so they run sequentially
        c = chain(*sigs)
        c.apply_async()

    # update media_doc status
    media_docs.update_one({"media_id": media_id}, {"$set": {"status": "workflow_started"}})
