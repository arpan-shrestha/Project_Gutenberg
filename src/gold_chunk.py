import os
import argparse
from pathlib import Path
import pandas as pd

from minio_client import ensure_bucket, upload_file  

base_dir = Path(__file__).resolve().parent.parent
silver_dir = base_dir / "data" / "silver"
meta_csv = base_dir / "data" / "meta" / "books_meta.csv"
gold_dir = base_dir / "data" / "gold"

gold_dir.mkdir(parents=True, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    n = len(text)
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        yield start, end, text[start:end]
        if end == n:
            break
        start = end - overlap  


def build_gold(meta_csv: Path = meta_csv,
               silver_dir: Path = silver_dir,
               gold_dir: Path = gold_dir,
               write_chunk_files: bool = False,
               chunk_size: int = 1000,
               overlap: int = 200) -> pd.DataFrame:
    """
    Build Gold layer dataframe from Silver text files.
    """
    if not meta_csv.exists():
        raise FileNotFoundError(f"Metadata CSV not found: {meta_csv}")

    meta_df = pd.read_csv(meta_csv)
    rows = []

    for _, row in meta_df.iterrows():
        book_id = row["book_id"]
        title = row["title"]
        silver_path = Path(row["silver_path"])

        if not silver_path.is_absolute():
            silver_path = base_dir / silver_path

        if not silver_path.exists():
            print(f"[WARN] Missing silver text for {book_id}: {silver_path}")
            continue

        text = silver_path.read_text(encoding="utf-8", errors="ignore")

        chunk_idx = 0
        for start, end, chunk_txt in chunk_text(text, chunk_size=chunk_size, overlap=overlap):
            chunk_id = f"{book_id}_{chunk_idx:05d}"
            n_chars = len(chunk_txt)
            n_words = len(chunk_txt.split())

            if write_chunk_files:
                chunk_file = gold_dir / f"{chunk_id}.txt"
                chunk_file.write_text(chunk_txt, encoding="utf-8")
                chunk_path = str(chunk_file)
            else:
                chunk_path = ""  

            rows.append({
                "chunk_id": chunk_id,
                "book_id": book_id,
                "title": title,
                "chunk_index": chunk_idx,
                "char_start": start,
                "char_end": end,
                "n_chars": n_chars,
                "n_words": n_words,
                "chunk_text": chunk_txt,
                "chunk_path": chunk_path,
            })

            chunk_idx += 1

    gold_df = pd.DataFrame(rows)


    gold_parquet = gold_dir / "gold_chunks.parquet"
    gold_csv = gold_dir / "gold_chunks.csv"

    gold_df.to_parquet(gold_parquet, index=False)
    gold_df.to_csv(gold_csv, index=False)

    print(f"[gold] Wrote:\n  {gold_parquet}\n  {gold_csv}")
    print(gold_df.head())

    return gold_df


def upload_gold_to_minio(gold_dir: Path = gold_dir):
    ensure_bucket()

    for p in gold_dir.glob("gold_chunks.*"):
        content_type = "text/csv" if p.suffix == ".csv" else "application/octet-stream"
        upload_file(p, f"gold/{p.name}", content_type=content_type)

    for p in gold_dir.glob("*.txt"):
        upload_file(p, f"gold/{p.name}", content_type="text/plain")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--write-chunk-files", action="store_true",
                        help="Write individual chunk text files (optional; increases storage).")
    parser.add_argument("--no-upload", action="store_true",
                        help="Skip upload to MinIO.")
    args = parser.parse_args()

    df = build_gold(chunk_size=args.chunk_size,
                    overlap=args.overlap,
                    write_chunk_files=args.write_chunk_files)

    if not args.no_upload:
        upload_gold_to_minio()


if __name__ == "__main__":
    main()
