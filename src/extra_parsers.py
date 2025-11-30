import re
from src.utils import get_soup, parse_br_number


def _parse_rows(url):
    soup = get_soup(url)
    rows = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    return rows


def creditos_por_grupo(url):
    rows = _parse_rows(url)
    invest = 0.0
    odc = 0.0
    for cells in rows:
        if not cells:
            continue
        label0 = cells[0].upper()
        if "TOTAL" in label0 or "GRUPO DESPESA" in label0:
            continue
        # último número da linha (Saldo)
        val = None
        for cell in reversed(cells):
            v = parse_br_number(cell)
            if v is not None:
                val = v
                break
        if val is None:
            continue
        if "INVEST" in label0:
            invest += val
        elif "OUTRAS DESPESAS CORRENTES" in label0:
            odc += val
    total = invest + odc
    return {"investimentos": invest, "odc": odc, "total": total}


def provisionamentos_por_grupo(url):
    rows = _parse_rows(url)
    invest = 0.0
    odc = 0.0
    for cells in rows:
        if not cells:
            continue
        label0 = cells[0].upper()
        if "TOTAL" in label0 or "GRUPO DESPESA" in label0:
            continue
        val = None
        for cell in reversed(cells):
            v = parse_br_number(cell)
            if v is not None:
                val = v
                break
        if val is None:
            continue
        if label0.startswith("4") or "INVEST" in label0:
            invest += val
        elif label0.startswith("3") or "OUTRAS DESPESAS CORRENTES" in label0:
            odc += val
    return {"investimentos": invest, "odc": odc, "total": invest + odc}


def _extract_ne(cell: str):
    m = re.search(r"(\d{4}NE\d+)", cell)
    if m:
        return m.group(1)
    return cell[-12:]


def top5_rap_a_pagar(url):
    rows = _parse_rows(url)
    value_idx = None
    ne_idx = None
    nd_code_idx = None
    nd_desc_idx = None

    # Detecta índices pelo cabeçalho
    for row in rows:
        upper = [c.upper() for c in row]
        if value_idx is None:
            for idx, cell in enumerate(upper):
                if "RESTOS A PAGAR A PAGAR" in cell:
                    value_idx = idx
                    break
        if ne_idx is None:
            for idx, cell in enumerate(upper):
                if cell.startswith("NE"):
                    ne_idx = idx
                    break
        if nd_code_idx is None and any("NATUREZA DESPESA DETALHADA" in cell for cell in upper):
            nd_code_idx = 1
            nd_desc_idx = 2
        if value_idx is not None and ne_idx is not None and nd_code_idx is not None:
            break

    items = []
    for cells in rows:
        if not cells or any("TOTAL" in c.upper() for c in cells):
            continue
        if value_idx is None or value_idx >= len(cells):
            continue
        val = parse_br_number(cells[value_idx])
        if val is None or val == 0:
            continue

        ne = cells[ne_idx] if ne_idx is not None and ne_idx < len(cells) else ""
        ne = _extract_ne(ne)
        nd_code = cells[nd_code_idx] if nd_code_idx is not None and nd_code_idx < len(cells) else ""
        nd_desc = cells[nd_desc_idx] if nd_desc_idx is not None and nd_desc_idx < len(cells) else ""

        label = f"{nd_code} - {nd_desc}".strip(" -")
        items.append((val, label, ne))

    items = sorted(items, key=lambda x: x[0], reverse=True)[:5]
    return [
        f"{label}: {ne} -> R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        for val, label, ne in items
    ]


def top5_empenhos_a_liquidar(url):
    rows = _parse_rows(url)
    value_idx = None
    ne_idx = None
    nd_code_idx = None
    nd_desc_idx = None

    # Detecta índices
    for row in rows:
        upper = [c.upper() for c in row]
        if value_idx is None:
            for idx, cell in enumerate(upper):
                if "A LIQUIDAR" in cell:
                    value_idx = idx
                    break
        if ne_idx is None:
            for idx, cell in enumerate(upper):
                if cell.startswith("EMPENHO") or cell.startswith("NE"):
                    ne_idx = idx
                    break
        if nd_code_idx is None and any("NATUREZA DESPESA" in cell for cell in upper):
            nd_code_idx = 1
            nd_desc_idx = 2
        if value_idx is not None and ne_idx is not None and nd_code_idx is not None:
            break

    items = []
    for cells in rows:
        if not cells or any("TOTAL" in c.upper() for c in cells):
            continue
        if value_idx is None or value_idx >= len(cells):
            continue
        val = parse_br_number(cells[value_idx])
        if val is None or val == 0:
            continue

        ne = cells[ne_idx] if ne_idx is not None and ne_idx < len(cells) else ""
        ne = _extract_ne(ne)
        nd_code = cells[nd_code_idx] if nd_code_idx is not None and nd_code_idx < len(cells) else ""
        nd_desc = cells[nd_desc_idx] if nd_desc_idx is not None and nd_desc_idx < len(cells) else ""

        label = f"{nd_code} - {nd_desc}".strip(" -")
        items.append((val, label, ne))

    items = sorted(items, key=lambda x: x[0], reverse=True)[:5]
    return [
        f"{label}: {ne} -> R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        for val, label, ne in items
    ]
