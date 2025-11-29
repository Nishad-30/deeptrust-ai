# api/q_subtasks.py
from .mongo import media_docs

def extract_frames(media_id):
    print("▶ extract_frames", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"frames_extracted": True}})

def transcribe_audio(media_id):
    print("▶ transcribe_audio", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"transcription": "example transcript"}})

def authenticity_image(media_id):
    print("▶ authenticity_image", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"authenticity_score": 72}})

def claim_extract(media_id):
    print("▶ claim_extract", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"claims": ["sample claim"]}})

def claim_normalize(media_id):
    print("▶ claim_normalize", media_id)
    doc = media_docs.find_one({"media_id": media_id})
    claims = doc.get("claims", [])
    normalized = [c.lower() for c in claims]
    media_docs.update_one({"media_id": media_id}, {"$set": {"normalized_claims": normalized}})

def retrieval_semantic_search(media_id):
    print("▶ retrieval_semantic_search", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"evidence": ["dummy evidence"]}})

def verification_ensemble(media_id):
    print("▶ verification_ensemble", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"verification_result": True}})

def truthscore_compute(media_id):
    print("▶ truthscore_compute", media_id)
    media_docs.update_one({"media_id": media_id}, {"$set": {"truthscore": 90}})
