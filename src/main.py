from datetime import date
import unicodedata
from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.report_total_extractor import extract_last_total
from src.message_formatter import format_message
from src.telegram_client import send_telegram


def _norm(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    ).lower()


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


def main():
    cfg = load_settings()

    base_url = cfg["base_url"]
    max_age = cfg["max_report_age_days"]

    print(f"[info] Iniciando monitor. base_url={base_url} max_age={max_age}", flush=True)

    reports = parse_index(base_url)
    print(f"[info] Relatorios encontrados no indice: {len(reports)}", flush=True)
    if not reports:
        raise RuntimeError("Nenhum relatorio encontrado no indice; verifique base_url/HTML.")

    # Verificar desatualizados
    stale = []
    today = date.today()
    for rep in reports:
        age = (today - rep["date"]).days
        if age > max_age:
            rep["age"] = age
            stale.append(rep)
    # Remove do controle de desatualizados o relatório anual de 2024 (não precisa ser diário)
    stale = [
        r for r in stale
        if "despesas empenhadas, liquidadas e pagas - 2024" not in _norm(r["title"])
    ]
    print(f"[info] Relatorios desatualizados: {len(stale)}", flush=True)

    # Indicadores
    indicators = {}
    for rep in reports:
        print(f"[info] Extraindo indicador de {rep['url']}", flush=True)
        try:
            total = extract_last_total(rep["url"])
            if total and total.get("values"):
                indicators[rep["title"]] = total
                print(f"[info] Indicador extraido: {rep['title']} -> {total['values']}", flush=True)
            else:
                print(f"[warn] Nenhum 'Total' util encontrado em {rep['url']}", flush=True)
        except Exception as exc:
            print(f"[error] Falha ao extrair total de {rep['url']}: {exc}", flush=True)

    # Resumo dos principais indicadores (com filtros específicos por título/coluna)
    summary = {
        "credito_disponivel": _pick_value(
            indicators,
            lambda t: "credito disponivel" in t,
            lambda c: True,
        ),
        "a_liquidar": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercicio - conta contabil" in t,
            lambda c: "a liquidar" in c,
        ),
        "liquidados_a_pagar": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercicio - conta contabil" in t,
            lambda c: "liquidados a pagar" in c,
        ),
        "pagos": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercicio - conta contabil" in t,
            lambda c: "pagos" in c,
        ),
        "rap_pagos": _pick_value(
            indicators,
            lambda t: "restos a pagar (rap)" in t,
            lambda c: "pagos" in c,
        ),
        "rap_a_pagar": _pick_value(
            indicators,
            lambda t: "restos a pagar (rap)" in t,
            lambda c: "a pagar" in c,
        ),
        "gru_arrecadado": _pick_value(
            indicators,
            lambda t: "recolhimento" in t and "gru" in t,
            lambda c: "arrecad" in c or "liquida" in c,
        ),
    }
    # Derivar porcentagens básicas
    if summary.get("liquidados_a_pagar") is not None and summary.get("pagos") is not None:
        base_liq = summary["liquidados_a_pagar"] + summary["pagos"]
        if base_liq:
            summary["pct_pago_sobre_liq"] = summary["pagos"] / base_liq
    if summary.get("rap_a_pagar") is not None and summary.get("rap_pagos") is not None:
        base_rap = summary["rap_a_pagar"] + summary["rap_pagos"]
        if base_rap:
            summary["pct_rap_pago"] = summary["rap_pagos"] / base_rap

    # Mensagem final
    weekday = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][today.weekday()]
    today_str = today.strftime("%d/%m/%Y")
    msg = format_message(reports, stale, summary, base_url, today_str, weekday)
    print(f"[info] Enviando mensagem para Telegram ({len(msg)} chars)", flush=True)
    resp = send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"], msg)
    print(f"[info] Telegram enviado com sucesso: status={resp.status_code} body={resp.text}", flush=True)


if __name__ == "__main__":
    main()
