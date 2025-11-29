import re
from src.utils import get_soup, parse_br_number


def extract_last_total(url: str):
    soup = get_soup(url)
    full_text = soup.get_text("\n")

    # Remove trecho final com "Relatorio gerado em ..." (sem acento)
    cutoff = full_text.find("Relatorio gerado")
    if cutoff != -1:
        full_text = full_text[:cutoff]

    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

    # Procura linhas de total (ignora acentos/nbsp). Preferir "total final"/"total geral", senão última.
    total_lines = []
    preferred_lines = []
    for ln in lines:
        clean = ln.replace("\xa0", " ").strip()  # remove nbsp
        low = clean.lower()
        if low.startswith("total"):
            total_lines.append(clean)
            if "total final" in low or "total geral" in low:
                preferred_lines.append(clean)

    if not total_lines:
        return None

    line = preferred_lines[-1] if preferred_lines else total_lines[-1]
    nums = re.findall(r"[\(\)\d\.\,]+", line)
    values = [parse_br_number(n) for n in nums if parse_br_number(n) is not None]

    if not values:
        return None

    return {
        "raw": line,
        "values": values,
    }
