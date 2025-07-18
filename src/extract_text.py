import re
import argparse
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

base_dir = Path(__file__).resolve().parent.parent
raw_dir = base_dir / "data/raw"
bronze_dir = base_dir/"data/bronze"
silver_dir = base_dir/"data/silver"
meta_dir = base_dir/"data/meta"

bronze_dir.mkdir(parents=True, exist_ok=True)
silver_dir.mkdir(parents=True, exist_ok=True)
meta_dir.mkdir(parents=True, exist_ok=True)

Books = {
    "alice_in_wonderland": "https://www.gutenberg.org/files/11/11-h/11-h.htm",
    "sherlock_holmes": "https://www.gutenberg.org/files/1661/1661-h/1661-h.htm",
    "pride_and_prejudice": "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm",
    "moby_dick": "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm",
    "dorian_gray": "https://www.gutenberg.org/files/174/174-h/174-h.htm"
}
Titles = {
    "alice_in_wonderland": "Alice's Adventures in Wonderland",
    "sherlock_holmes": "The Adventures of Sherlock Holmes",
    "pride_and_prejudice": "Pride and Prejudice",
    "moby_dick": "Moby-Dick; or, The Whale",
    "dorian_gray": "The Picture of Dorian Gray",
}

def html_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["style","script","header","footer","nav"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    return text

START_PAT = re.compile(r"^\s*\*{3}\s*start[^\\n]*project gutenberg ebook.*$", re.IGNORECASE | re.MULTILINE)
END_PAT = re.compile(r"^\s*\*{3}\s*end[^\\n]*project gutenberg ebook.*$", re.IGNORECASE | re.MULTILINE)

def strip_license(txt: str) -> str:
    start_match = START_PAT.search(txt)
    end_match = END_PAT.search(txt)
    if start_match and end_match and end_match.start() > start_match.end():
        return txt[start_match.end():end_match.start()]
    return txt

def whitespace(txt: str) -> str:
    txt = re.sub(r"\r\n?", "\n", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n\s*\n+", "\n\n", txt)
    return txt.strip()

def extract_all(raw_dir=raw_dir, bronze_dir=bronze_dir, silver_dir=silver_dir, meta_dir=meta_dir):
    records = []

    for raw_path in sorted(raw_dir.glob("*.html")):
        book_id = raw_path.stem 
        html_str = raw_path.read_text(encoding="utf-8", errors="ignore")

        bronze_text = html_to_text(html_str)

        bronze_file = bronze_dir / f"{book_id}.txt"
        bronze_file.write_text(bronze_text, encoding="utf-8")

        clean_slice = strip_license(bronze_text)
        clean_text = whitespace(clean_slice)
        silver_file = silver_dir / f"{book_id}.txt"
        silver_file.write_text(clean_text, encoding="utf-8")

        title = Titles.get(book_id, book_id)
        n_chars_raw = len(bronze_text)
        n_chars_clean = len(clean_text)
        n_words_clean = len(clean_text.split())
        records.append(
            {
                "book_id": book_id,
                "title": title,
                "raw_path": str(raw_path),
                "bronze_path": str(bronze_file),
                "silver_path": str(silver_file),
                "n_chars_raw": n_chars_raw,
                "n_chars_clean": n_chars_clean,
                "n_words_clean": n_words_clean,
            }
        )

    df = pd.DataFrame(records)
    csv_path = meta_dir / "books_meta.csv"
    parquet_path = meta_dir / "books_meta.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"Wrote metadata:\n  {csv_path}\n  {parquet_path}")
    print(df)


def main():
    extract_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main()