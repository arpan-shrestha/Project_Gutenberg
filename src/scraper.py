import os
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

Books = {
    "alice_in_wonderland": "https://www.gutenberg.org/files/11/11-h/11-h.htm",
    "sherlock_holmes": "https://www.gutenberg.org/files/1661/1661-h/1661-h.htm",
    "pride_and_prejudice": "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm",
    "moby_dick": "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm",
    "dorian_gray": "https://www.gutenberg.org/files/174/174-h/174-h.htm"
}
out_dir = Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)

def book_download(title, url):
    print(f"Downloading {title}")
    response = requests.get(url)
    response.raise_for_status()
    filepath = out_dir / f"{title}.html"
    filepath.write_text(response.text, encoding="utf-8")
    print(f"saved {filepath}")

def main():
    for title, url in Books.items():
        book_download(title, url)
        time.sleep(2)

if __name__=="__main__":
    main()
    