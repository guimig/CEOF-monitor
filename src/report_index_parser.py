import unicodedata
from urllib.parse import urljoin
from src.utils import get_soup, extract_date


def _normalize(text: str) -> str:
    return (
        "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
        .lower()
        .strip()
    )


def parse_index(base_url: str):
    soup = get_soup(base_url)
    reports = []

    # Encontrar a seção "Últimas atualizações" de forma robusta (ignora acentos/maiúsculas).
    header = None
    for node in soup.find_all(string=True):
        norm = _normalize(node)
        if "ultimas" in norm and "atualizacoes" in norm:
            header = node
            break

    section = None
    if header:
        for ancestor in getattr(header, "parents", []):
            if ancestor.name in ("div", "section", "main", "body"):
                section = ancestor
                break

    # Se não achou via heading, tenta id/class contendo "atualiz"
    if not section:
        section = soup.find(id=lambda x: x and "atualiz" in x.lower()) or soup.find(
            class_=lambda x: x and "atualiz" in x.lower()
        )

    if not section:
        raise RuntimeError("Sessao 'Ultimas atualizacoes' nao encontrada no indice.")

    seen_urls = set()
    for node in section.find_all(string=True):
        dt = extract_date(node)
        if not dt:
            continue

        a = node.find_previous("a")
        if not a or not a.has_attr("href"):
            continue

        url = urljoin(base_url, a["href"])
        if url in seen_urls:
            continue
        seen_urls.add(url)

        reports.append(
            {
                "title": a.get_text(strip=True),
                "url": url,
                "date": dt,
            }
        )

    return reports
