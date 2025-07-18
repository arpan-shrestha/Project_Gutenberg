# src/minio_client.py
import os
from pathlib import Path
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "gutenrag")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

def ensure_bucket(bucket: str = MINIO_BUCKET):
    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
        print(f"[minio] Created bucket: {bucket}")
    else:
        print(f"[minio] Bucket exists: {bucket}")

def upload_file(local_path: Path, key: str, bucket: str = MINIO_BUCKET, content_type: str | None = None):
    local_path = Path(local_path)
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    s3.upload_file(str(local_path), bucket, key, ExtraArgs=extra)
    print(f"[minio] Uploaded {local_path} → s3://{bucket}/{key}")

def upload_dir(local_dir: Path, prefix: str, bucket: str = MINIO_BUCKET):
    local_dir = Path(local_dir)
    for p in local_dir.glob("*"):
        if p.is_file():
            key = f"{prefix}/{p.name}"
            ctype = "text/html" if p.suffix == ".html" else "text/plain"
            upload_file(p, key, bucket=bucket, content_type=ctype)

if __name__ == "__main__":
    ensure_bucket()
    upload_dir(Path("data/raw"), "raw")
