from urllib.parse import urljoin
from src.utils import get_soup, extract_date


def parse_index(base_url: str):
    soup = get_soup(base_url)
    reports = []

    # Restringir à seção "Últimas atualizações"
    header = soup.find(string=lambda s: s and "ultima" in s.lower() and "atualiz" in s.lower())
    section = header.find_parent("div") if header else None
    if not section:
        raise RuntimeError("Sessao 'Ultimas atualizacoes' nao encontrada no indice.")

    for node in section.find_all(string=lambda s: s and "data do relat" in s.lower()):
        dt = extract_date(node)
        if not dt:
            continue

        a = node.find_previous("a")
        if not a or not a.has_attr("href"):
            continue

        reports.append(
            {
                "title": a.get_text(strip=True),
                "url": urljoin(base_url, a["href"]),
                "date": dt,
            }
        )

    if not reports:
        return reports

    # Manter apenas as entradas com a data mais recente encontrada no índice.
    latest_date = max(r["date"] for r in reports)
    latest_only = [r for r in reports if r["date"] == latest_date]

    return latest_only
