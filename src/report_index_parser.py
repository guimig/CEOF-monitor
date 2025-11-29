from urllib.parse import urljoin
from src.utils import get_soup, extract_date


def parse_index(base_url: str):
    soup = get_soup(base_url)

    # Seção "Últimas Atualizações" tem id="latestReports" com div.report-card
    section = soup.find(id="latestReports")
    if not section:
        raise RuntimeError("Sessao 'Ultimas atualizacoes' (id=latestReports) nao encontrada no indice.")

    reports = []
    for card in section.select(".report-card"):
        link = card.find("a", href=True)
        if not link:
            continue

        url = urljoin(base_url, link["href"])
        # Data preferencialmente no atributo data-date (formato dd/mm/aaaa)
        date_str = card.get("data-date") or card.get_text(" ", strip=True)
        dt = extract_date(date_str)
        if not dt:
            continue

        reports.append(
            {
                "title": link.get_text(strip=True),
                "url": url,
                "date": dt,
            }
        )

    return reports
