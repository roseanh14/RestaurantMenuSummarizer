import requests
from bs4 import BeautifulSoup


def fetch_page_text(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MenuScraper/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    body = soup.body or soup
    text = body.get_text(separator="\n")

    return text[:15000]
