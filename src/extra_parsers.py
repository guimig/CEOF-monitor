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
        gd = cells[0].strip()
        if "TOTAL" in gd.upper():
            continue
        val = None
        for cell in reversed(cells):
            v = parse_br_number(cell)
            if v is not None:
                val = v
                break
        if val is None:
            continue
        if gd.startswith("4"):  # Investimento
            invest += val
        elif gd.startswith("3"):  # ODC
            odc += val
    return {"investimentos": invest, "odc": odc, "total": invest + odc}


def top5_por_coluna(url, col_keyword):
    rows = _parse_rows(url)
    items = []
    # tenta encontrar índice da coluna que contém o keyword
    col_idx = None
    for row in rows:
        for idx, cell in enumerate(row):
            if col_keyword in cell.lower():
                col_idx = idx
                break
        if col_idx is not None:
            break

    for cells in rows:
        label_row = " ".join(cells).lower()
        if "total" in label_row:
            continue

        val = None
        if col_idx is not None and col_idx < len(cells):
            val = parse_br_number(cells[col_idx])
        if val is None:
            for cell in cells:
                if col_keyword in cell.lower():
                    val = parse_br_number(cell)
                    if val is not None:
                        break
        if val is None:
            continue

        memo = ""
        nd = ""
        for cell in cells:
            if "ne" in cell.lower():
                memo = cell
            if cell.isdigit() and len(cell) in (8, 9):
                nd = cell
        if not nd and len(cells) > 1:
            nd = cells[1]

        memo_short = memo[-12:] if memo else ""
        items.append((val, nd, memo_short))

    items = sorted(items, key=lambda x: x[0], reverse=True)
    top = items[:5]
    formatted = []
    for val, nd, memo in top:
        formatted.append(f"{nd}: {memo} -> R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return formatted
