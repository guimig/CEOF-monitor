from urllib.parse import urljoin
from src.utils import get_soup, extract_date


def parse_index(base_url: str):
    soup = get_soup(base_url)
    reports = []

    for node in soup.find_all(string=lambda s: s and "Data do relat" in s):
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

    return reports
