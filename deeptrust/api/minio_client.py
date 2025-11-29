import os

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "True") == "True"

# These variables are imported by other modules
BUCKET = "deeptrust-media"
minio_client = None

if DEVELOPMENT_MODE:
    print("⚠ Running in DEVELOPMENT MODE → MinIO disabled")
    
else:
    from minio import Minio
    from minio.error import S3Error

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE = os.getenv("MINIO_SECURE", "False") == "True"

    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

    # Create bucket only in real mode
    try:
        if not minio_client.bucket_exists(BUCKET):
            minio_client.make_bucket(BUCKET)
            print(f"✔ Created bucket: {BUCKET}")
    except Exception as e:
        print("❌ MinIO connection failed:", e)
