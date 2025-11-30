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
        label = " ".join(cells).lower()
        if not any(ch.isdigit() for ch in label) and "total" in label:
            continue
        val = None
        for cell in reversed(cells):
            v = parse_br_number(cell)
            if v is not None:
                val = v
                break
        if val is None:
            continue
        if "investiment" in label:
            invest += val
        elif "outras despesas correntes" in label:
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
    for cells in rows:
        label_row = " ".join(cells).lower()
        if "total" in label_row:
            continue
        val = None
        for idx, cell in enumerate(cells):
            if col_keyword in cell.lower():
                # procurar número nessa célula ou à direita
                v = parse_br_number(cell)
                if v is None and idx + 1 < len(cells):
                    v = parse_br_number(cells[idx + 1])
                if v is not None:
                    val = v
                    break
        if val is None:
            continue

        memo = ""
        nd = ""
        # heurística: ND costuma estar na coluna seguinte ao grupo/natureza
        for cell in cells:
            if "ne" in cell.lower():
                memo = cell[-20:] if len(cell) > 20 else cell
            if any(ch.isdigit() for ch in cell) and " " not in cell and len(cell) in (8, 9):
                nd = cell
        if not nd and len(cells) > 2:
            nd = cells[1]

        items.append((val, nd, memo))

    items = sorted(items, key=lambda x: x[0], reverse=True)
    top = items[:5]
    formatted = []
    for val, nd, memo in top:
        memo_short = memo[-12:] if memo else ""
        formatted.append(f"{nd}: {memo_short} -> R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return formatted
