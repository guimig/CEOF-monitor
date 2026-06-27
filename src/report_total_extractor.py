import re
import unicodedata
import requests
from src.utils import get_soup, parse_br_number


def _normalize(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    ).lower()


def _extract_values_from_text(text: str):
    nums = re.findall(r"[\(\)\d\.\,]+", text)
    values = [parse_br_number(n) for n in nums if parse_br_number(n) is not None]
    return values


def _is_header_row(row):
    first_value = next(iter(row.values()), "")
    return "natureza despesa" in _normalize(str(first_value))


def _json_headers(rows):
    headers = {}
    header_rows = []
    for row in rows[:10]:
        if not _is_header_row(row):
            break
        header_rows.append(row)

    for row in header_rows:
        for col, value in row.items():
            text = str(value or "").strip()
            if not text:
                continue
            if parse_br_number(text) is not None:
                continue
            headers.setdefault(col, [])
            if text not in headers[col]:
                headers[col].append(text)

    return {col: " | ".join(parts) for col, parts in headers.items()}, len(header_rows)


def extract_last_total_from_json(url: str):
    resp = requests.get(url, timeout=(5, 20))
    resp.raise_for_status()
    payload = resp.json()
    rows = payload.get("rows") or []
    if not rows:
        return None

    headers, header_count = _json_headers(rows)
    totals = {}
    for row in rows[header_count:]:
        for col, value in row.items():
            val = parse_br_number(str(value or ""))
            if val is None:
                continue
            totals[col] = totals.get(col, 0.0) + val

    financial_terms = ("saldo", "valor", "arrecad", "liquid", "pago", "empenh", "restos")
    values = []
    for col, value in totals.items():
        header = headers.get(col)
        if not header:
            continue
        if not any(term in _normalize(header) for term in financial_terms):
            continue
        values.append(
            {
                "col": header,
                "value": value,
                "raw_cell": str(value),
            }
        )
    if not values:
        return None

    return {
        "raw": f"Somatorio calculado do JSON: {payload.get('title') or url}",
        "values": values,
    }


def _build_table_grid(table):
    grid = []
    rowspans = []  # quantidade de linhas restantes por coluna
    for tr in table.find_all("tr"):
        row = []
        col_idx = 0

        # Avança col_idx para pular colunas ocupadas por rowspan de linhas anteriores
        while col_idx < len(rowspans) and rowspans[col_idx] > 0:
            row.append(None)
            rowspans[col_idx] -= 1
            col_idx += 1

        for cell in tr.find_all(["td", "th"]):
            text = cell.get_text(" ", strip=True)
            colspan = int(cell.get("colspan", "1") or 1)
            rowspan = int(cell.get("rowspan", "1") or 1)

            for _ in range(colspan):
                # Garante tamanho de rowspans
                if col_idx >= len(rowspans):
                    rowspans.append(0)

                row.append(text)
                # Marca rowspan para colunas cobertas
                rowspans[col_idx] = max(rowspans[col_idx], rowspan - 1)
                col_idx += 1

            # Pular colunas ocupadas por rowspan anteriores
            while col_idx < len(rowspans) and rowspans[col_idx] > 0:
                row.append(None)
                rowspans[col_idx] -= 1
                col_idx += 1

        grid.append(row)

    return grid


def extract_last_total(url: str):
    soup = get_soup(url)

    candidate = None

    # Analisa tabelas estruturadas
    for table in soup.find_all("table"):
        grid = _build_table_grid(table)
        if not grid:
            continue

        # Header: guarda última string não numérica por coluna antes dos dados
        col_headers = [None] * max(len(r) for r in grid)
        for row in grid:
            # normaliza linhas vazias
            if all(not (cell and cell.strip()) for cell in row):
                continue

            norm_row = [_normalize(cell or "") for cell in row]
            if any(cell.startswith("total") for cell in norm_row):
                # linha de total: captura números por coluna
                values = []
                for idx, cell in enumerate(row):
                    if not cell:
                        continue
                    vals = _extract_values_from_text(cell)
                    if not vals:
                        continue
                    values.append(
                        {
                            "col": col_headers[idx] or f"Coluna {idx+1}",
                            "value": vals[-1],  # último número da célula
                            "raw_cell": cell,
                        }
                    )
                if values:
                    candidate = {
                        "raw": " ".join(c for c in row if c),
                        "values": values,
                    }
                continue

            # Atualiza headers para colunas que ainda não têm descrição
            for idx, cell in enumerate(row):
                if not cell:
                    continue
                if col_headers[idx]:
                    continue
                # ignora células só numéricas
                if _extract_values_from_text(cell):
                    continue
                col_headers[idx] = cell.strip()

    # Fallback se nada encontrado em tabelas
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
                candidate = {
                    "raw": ln,
                    "values": [{"col": "Total", "value": vals[-1], "raw_cell": ln}],
                }

    return candidate
