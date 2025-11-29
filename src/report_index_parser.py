import unicodedata
from urllib.parse import urljoin
from src.utils import get_soup, extract_date


def _normalize(text: str) -> str:
    return (
        "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
        .lower()
        .strip()
    )


def _find_latest_section(soup):
    # Procura heading com "ultimas" e "atualizacoes" ignorando acento/maiúsculas
    for node in soup.find_all(string=True):
        norm = _normalize(node)
        if "ultimas" in norm and "atualizacoes" in norm:
            # sobe para um contêiner que tenha links
            for ancestor in getattr(node, "parents", []):
                if ancestor.name in ("div", "section", "main", "body"):
                    if ancestor.find("a"):
                        return ancestor
            # fallback para próximo bloco após o heading
            next_block = getattr(node.parent, "find_next", lambda *_: None)("div")
            if next_block and next_block.find("a"):
                return next_block
            return node.parent
    # fallback: tenta por id/class contendo "atualiz"
    section = soup.find(id=lambda x: x and "atualiz" in x.lower()) or soup.find(
        class_=lambda x: x and "atualiz" in x.lower()
    )
    return section


def parse_index(base_url: str):
    soup = get_soup(base_url)
    section = _find_latest_section(soup)

    if not section:
        raise RuntimeError("Sessao 'Ultimas atualizacoes' nao encontrada no indice.")

    seen = set()
    reports = []

    for a in section.find_all("a"):
        if not a.has_attr("href"):
            continue

        url = urljoin(base_url, a["href"])
        if url in seen:
            continue
        seen.add(url)

        # Extrai data do próprio link ou do texto ao redor (li/div pai)
        text_blob = " ".join(
            filter(None, [a.get_text(" ", strip=True), getattr(a.parent, "get_text", lambda *args, **kwargs: "")(" ", strip=True)])
        )
        dt = extract_date(text_blob)
        if not dt:
            # tenta no irmão seguinte (ex.: <span>Data do relatório: 01/01/2024</span>)
            sib_text = ""
            if a.next_sibling:
                sib_text = str(a.next_sibling)
            dt = extract_date(sib_text)

        if not dt:
            # sem data, ignora para evitar falsos positivos
            continue

        reports.append(
            {
                "title": a.get_text(strip=True),
                "url": url,
                "date": dt,
            }
        )

    return reports
