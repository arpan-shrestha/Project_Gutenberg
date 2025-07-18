from pathlib import Path
from minio_client import ensure_bucket, upload_dir

def main():
    ensure_bucket()
    upload_dir(Path("data/bronze"), "bronze")
    upload_dir(Path("data/silver"), "silver")
    print("[upload] Bronze and Silver layers uploaded successfully.")

if __name__ == "__main__":
    main()
