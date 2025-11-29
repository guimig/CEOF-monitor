import re
from src.utils import get_soup, parse_br_number


def extract_last_total(url: str):
    soup = get_soup(url)
    full_text = soup.get_text("\n")

    # Remove trecho final com "Relatorio gerado em ..."
    cutoff = full_text.find("Relatorio gerado")
    if cutoff != -1:
        full_text = full_text[:cutoff]

    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

    total_lines = [ln for ln in lines if ln.startswith("Total")]
    if not total_lines:
        return None

    line = total_lines[-1]
    nums = re.findall(r"[\\(\\)\\d\\.\\,]+", line)
    values = [parse_br_number(n) for n in nums if parse_br_number(n) is not None]

    return {
        "raw": line,
        "values": values,
    }
