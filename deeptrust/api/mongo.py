# api/mongo.py
from pymongo import MongoClient, ASCENDING
import os

MONGO_URI = "mongodb+srv://nishaddsutar42203_db_user:j4IwCoKI05NwMzwn@cluster0.zmeaadd.mongodb.net/?deeptrust=Cluster0"
MONGO_DB_NAME = "deeptrust"

client = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=5000
)

db = client[MONGO_DB_NAME]

media_docs = db["media_docs"]
claims = db["claims"]
verifications = db["verifications"]
snippets = db["snippets"]
watchlist = db["watchlist"]
audit_log = db["audit_log"]
sources = db["sources"]

# Create indexes if missing (idempotent)
media_docs.create_index([("media_id", ASCENDING)], unique=True)
media_docs.create_index([("sha256", ASCENDING)])
media_docs.create_index([("phash", ASCENDING)])
media_docs.create_index([("file_type", ASCENDING)])  # important
media_docs.create_index([("status", ASCENDING)])
claims.create_index([("claim_hash", ASCENDING)], unique=True)
claims.create_index([("expires_at", ASCENDING)])
verifications.create_index([("media_id", ASCENDING)])
snippets.create_index([("published_at", ASCENDING)])
