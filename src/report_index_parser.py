import json
from datetime import datetime
from urllib.parse import urljoin

import requests

from src.utils import get_soup, extract_date


def _parse_json_index(base_url: str):
    index_url = urljoin(base_url, "data/index.json")
    resp = requests.get(index_url, timeout=(5, 20))
    resp.raise_for_status()
    payload = resp.json()

    reports = []
    for item in payload.get("reports") or []:
        date_str = item.get("date") or item.get("date_iso") or ""
        dt = extract_date(date_str)
        if not dt and item.get("date_iso"):
            dt = datetime.strptime(item["date_iso"], "%Y-%m-%d").date()
        if not dt:
            continue

        html_path = item.get("html_path") or ""
        json_path = item.get("json_path") or ""
        reports.append(
            {
                "title": item.get("title") or item.get("slug") or html_path,
                "slug": item.get("slug"),
                "url": urljoin(base_url, html_path),
                "json_url": urljoin(base_url, json_path) if json_path else None,
                "date": dt,
                "metadata": item.get("metadata") or {},
            }
        )

    return reports


def parse_index(base_url: str):
    try:
        reports = _parse_json_index(base_url)
        if reports:
            return reports
    except (json.JSONDecodeError, requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"[warn] Falha ao ler data/index.json; usando HTML do indice: {exc}", flush=True)

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
