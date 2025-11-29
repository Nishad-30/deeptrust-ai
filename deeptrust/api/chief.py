# api/chief.py
import os
import json
import requests

OPENROUTER_API_KEY = "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"
CHIEF_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# -----------------------------
# Build prompt for the LLM
# -----------------------------
def generate_prompt(media_doc):
    metadata = {
        "media_id": media_doc.get("media_id"),
        "file_type": media_doc.get("file_type", ""),
        "text_input_present": bool(media_doc.get("text_input")),
        "claim_text_present": bool(media_doc.get("claim_text")),
    }

    return f"""
You are the Chief Orchestration Agent for DeepTrust AI.

Your job is to produce a JSON-only task plan for Django-Q.

MEDIA INFORMATION:
{json.dumps(metadata, indent=2)}

RULES:
1. Output ONLY JSON (no explanation).
2. JSON format: {{"plan":[{{"task":"task_name","args":{{}}}}]}}
3. Tasks available:
   - extract_frames
   - transcribe_audio
   - authenticity_image
   - authenticity_video
   - authenticity_audio
   - detect_text_ai
   - claim_extract
   - claim_normalize
   - retrieval_semantic_search
   - verification_ensemble
   - truthscore_compute
   - job_finalize
"""



# -----------------------------
# Safe LLM API Call
# -----------------------------
def call_openrouter(prompt):
    if not OPENROUTER_API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY is missing. Set it in environment variables.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": CHIEF_MODEL,
        "messages": [
            {"role": "system", "content": "You output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ]
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload)

    # Debug info for failures
    if resp.status_code != 200:
        print("\n🔥 OpenRouter API Error")
        print("Status:", resp.status_code)
        print("Response:", resp.text)
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]



# -----------------------------
# Safe JSON parsing
# -----------------------------
def safe_json_loads(raw):
    try:
        return json.loads(raw)
    except:
        # Extract JSON inside text
        try:
            cleaned = raw[raw.index("{"): raw.rindex("}") + 1]
            return json.loads(cleaned)
        except:
            return {"plan": []}



# -----------------------------
# Build final task plan
# -----------------------------
def generate_task_plan(media_doc):
    prompt = generate_prompt(media_doc)
    raw_output = call_openrouter(prompt)

    plan = safe_json_loads(raw_output)

    # Always ensure valid structure
    if "plan" not in plan:
        plan = {"plan": []}

    # Inject media_id automatically
    for step in plan["plan"]:
        step.setdefault("args", {})
        step["args"].setdefault("media_id", media_doc.get("media_id"))

    return plan
