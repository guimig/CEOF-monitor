import re
import unicodedata
from src.utils import get_soup, parse_br_number


def _normalize(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    ).lower()


def _extract_values_from_text(text: str):
    nums = re.findall(r"[\(\)\d\.\,]+", text)
    values = [parse_br_number(n) for n in nums if parse_br_number(n) is not None]
    return values


def extract_last_total(url: str):
    soup = get_soup(url)

    candidate = None
    # Percorre linhas de tabela/div/p e pega a última linha com "total" e número.
    for row in soup.find_all(["tr", "p", "div"]):
        row_text = row.get_text(" ", strip=True).replace("\xa0", " ")
        norm = _normalize(row_text)
        if "total" not in norm:
            continue

        vals = _extract_values_from_text(row_text)
        if vals:
            candidate = {"raw": row_text, "values": vals}

    # Fallback: texto completo (se não achou nada nos nós principais)
    if not candidate:
        full_text = soup.get_text("\n").replace("\xa0", " ")
        cutoff = _normalize(full_text).find("relatorio gerado")
        if cutoff != -1:
            full_text = full_text[:cutoff]
        for ln in [ln.strip() for ln in full_text.splitlines() if ln.strip()]:
            if "total" not in _normalize(ln):
                continue
            vals = _extract_values_from_text(ln)
            if vals:
                candidate = {"raw": ln, "values": vals}

    return candidate
