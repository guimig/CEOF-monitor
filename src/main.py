import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.message_formatter import format_message
from src.telegram_client import send_telegram


def _norm(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)
    ).lower()


def _matches_any(title: str, patterns):
    title_norm = _norm(title)
    return any(_norm(pattern) in title_norm for pattern in patterns or [])


def _has_previous_year(title: str, current_year: int):
    years = [int(year) for year in re.findall(r"\b(20\d{2})\b", title or "")]
    return any(year < current_year for year in years)


def _allowed_age_days(report, today, cfg):
    rules = cfg.get("stale_rules") or {}
    title = report.get("title", "")

    if _matches_any(title, rules.get("ignore_title_patterns")):
        return None

    if rules.get("previous_years") == "ignore" and _has_previous_year(title, today.year):
        return None

    if _matches_any(title, rules.get("monthly_title_patterns")):
        return int(rules.get("monthly_max_report_age_days", 35))

    return int(cfg.get("max_report_age_days", 1))


def _find_stale_reports(reports, today, cfg):
    stale = []
    for report in reports:
        allowed_age = _allowed_age_days(report, today, cfg)
        if allowed_age is None:
            continue

        age = (today - report["date"]).days
        if age > allowed_age:
            stale.append({**report, "age": age, "allowed_age": allowed_age})
    return stale


def main():
    cfg = load_settings()
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime.now(tz)
    today = now.date()

    if today.weekday() == 6:
        print("[info] Domingo: envio de mensagem desativado.", flush=True)
        return

    base_url = cfg["base_url"]
    print(f"[info] Iniciando monitor. base_url={base_url}", flush=True)

    reports = parse_index(base_url)
    print(f"[info] Relatorios encontrados no indice: {len(reports)}", flush=True)
    if not reports:
        raise RuntimeError("Nenhum relatorio encontrado no indice; verifique base_url/HTML.")

    stale = _find_stale_reports(reports, today, cfg)
    print(f"[info] Relatorios desatualizados: {len(stale)}", flush=True)

    weekday = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][today.weekday()]
    today_str = today.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")

    msg = format_message(
        reports=reports,
        stale=stale,
        base_url=base_url,
        portal_url=cfg.get("portal_url"),
        today_str=today_str,
        time_str=time_str,
        weekday=weekday,
    )

    max_len = 3800
    parts = []
    while msg:
        parts.append(msg[:max_len])
        msg = msg[max_len:]

    for idx, part in enumerate(parts, 1):
        print(f"[info] Enviando parte {idx}/{len(parts)} ({len(part)} chars)", flush=True)
        resp = send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"], part)
        print(f"[info] Telegram enviado com sucesso: status={resp.status_code} body={resp.text}", flush=True)


if __name__ == "__main__":
    main()
