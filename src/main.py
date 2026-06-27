import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.report_total_extractor import extract_last_total, extract_last_total_from_json
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
        metadata = report.get("metadata") or {}
        if "status" in metadata and "limite_dias" in metadata:
            if metadata.get("limite_dias") is None:
                continue
            age = int(metadata.get("idade_dias", (today - report["date"]).days))
            allowed_age = int(metadata["limite_dias"])
            if metadata.get("status") == "desatualizado" or age > allowed_age:
                stale.append({**report, "age": age, "allowed_age": allowed_age})
            continue

        allowed_age = _allowed_age_days(report, today, cfg)
        if allowed_age is None:
            continue

        age = (today - report["date"]).days
        if age > allowed_age:
            stale.append({**report, "age": age, "allowed_age": allowed_age})
    return stale


def _pick_value(indicators, title_pred, col_pred):
    for title, info in indicators.items():
        title_norm = _norm(title)
        if not title_pred(title_norm):
            continue
        vals = info.get("values") or []
        for item in reversed(vals):
            if isinstance(item, dict):
                col_norm = _norm(item.get("col", ""))
                if col_pred(col_norm):
                    return item.get("value")
            else:
                if col_pred(""):
                    return item
    return None


def _extract_indicators(reports):
    indicators = {}
    for report in reports:
        print(f"[info] Extraindo indicador de {report['url']}", flush=True)
        try:
            total = None
            if report.get("json_url"):
                try:
                    total = extract_last_total_from_json(report["json_url"])
                except Exception as exc:
                    print(f"[warn] Falha ao extrair JSON de {report['json_url']}: {exc}", flush=True)
            if not total:
                total = extract_last_total(report["url"])
            if total and total.get("values"):
                indicators[report["title"]] = total
                print(f"[info] Indicador extraido: {report['title']} -> {total['values']}", flush=True)
            else:
                print(f"[warn] Nenhum 'Total' util encontrado em {report['url']}", flush=True)
        except Exception as exc:
            print(f"[error] Falha ao extrair total de {report['url']}: {exc}", flush=True)
    return indicators


def _build_summary(indicators, today):
    summary = {
        "credito_disponivel": _pick_value(
            indicators,
            lambda title: "credito disponivel" in title,
            lambda col: True,
        ),
        "a_liquidar": _pick_value(
            indicators,
            lambda title: "saldos de empenhos do exercicio" in title and "conta contabil" in title,
            lambda col: "a liquidar" in col,
        ),
        "liquidados_a_pagar": _pick_value(
            indicators,
            lambda title: "saldos de empenhos do exercicio" in title and "conta contabil" in title,
            lambda col: "liquidados a pagar" in col,
        ),
        "pagos": _pick_value(
            indicators,
            lambda title: "saldos de empenhos do exercicio" in title and "conta contabil" in title,
            lambda col: "pagos" in col,
        ),
        "rap_pagos": _pick_value(
            indicators,
            lambda title: "restos a pagar" in title and "rap" in title,
            lambda col: "restos a pagar pagos" in col,
        ),
        "rap_a_pagar": _pick_value(
            indicators,
            lambda title: "restos a pagar" in title and "rap" in title,
            lambda col: "restos a pagar a pagar" in col,
        ),
        "gru_arrecadado": _pick_value(
            indicators,
            lambda title: "recolhimento" in title and "gru" in title,
            lambda col: "arrecad" in col or "liquida" in col,
        ),
    }

    if summary.get("liquidados_a_pagar") is not None and summary.get("pagos") is not None:
        base_liq = summary["liquidados_a_pagar"] + summary["pagos"]
        if base_liq:
            summary["pct_pago_sobre_liq"] = summary["pagos"] / base_liq

    if summary.get("rap_a_pagar") is not None and summary.get("rap_pagos") is not None:
        base_rap = summary["rap_a_pagar"] + summary["rap_pagos"]
        if base_rap:
            summary["pct_rap_pago"] = summary["rap_pagos"] / base_rap

    history_path = Path(".cache/history.json")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    else:
        history = []

    record = {"date": today.isoformat()}
    for key in [
        "credito_disponivel",
        "a_liquidar",
        "liquidados_a_pagar",
        "pagos",
        "rap_pagos",
        "rap_a_pagar",
        "gru_arrecadado",
    ]:
        if summary.get(key) is not None:
            record[key] = summary[key]

    history = [item for item in history if item.get("date") != record["date"]]
    history.append(record)
    history = history[-90:]
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    def last_value(key):
        for item in reversed(history[:-1]):
            if key in item:
                return item[key]
        return None

    def moving_avg(key, days=30):
        values = []
        for item in reversed(history):
            if key in item:
                values.append(item[key])
            if len(values) >= days:
                break
        if not values:
            return None
        return sum(values) / len(values)

    for key in record:
        if key == "date":
            continue
        previous = last_value(key)
        current = record[key]
        if previous is not None:
            summary[f"{key}_delta"] = current - previous
            summary[f"{key}_pct"] = (current - previous) / previous if previous else None

    summary["gru_media_30d"] = moving_avg("gru_arrecadado", days=30)
    return summary


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

    indicators = _extract_indicators(reports)
    summary = _build_summary(indicators, today)

    weekday = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][today.weekday()]
    today_str = today.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")

    msg = format_message(
        reports=reports,
        stale=stale,
        summary=summary,
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
