import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def parse_br_number(text: str):
    if not text:
        return None

    text = text.strip()
    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = text.replace(".", "").replace(",", ".")
    try:
        value = float(text)
    except ValueError:
        return None

    return -value if negative else value


def get_soup(url: str) -> BeautifulSoup:
    try:
        # timeout: (connect, read)
        resp = requests.get(url, timeout=(5, 20))
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Erro ao buscar URL {url}: {exc}") from None

    return BeautifulSoup(resp.text, "html.parser")


def extract_date(text: str):
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%d/%m/%Y").date()
