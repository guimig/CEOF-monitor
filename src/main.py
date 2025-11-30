from datetime import date
from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.report_total_extractor import extract_last_total
from src.message_formatter import format_message
from src.telegram_client import send_telegram


def _pick_value(indicators, title_pred, col_pred):
    for title, info in indicators.items():
        if not title_pred(title):
            continue
        vals = info.get("values") or []
        for item in reversed(vals):
            if isinstance(item, dict):
                col = item.get("col", "")
                if col_pred(col):
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
    print(f"[info] Relatorios desatualizados: {len(stale)}", flush=True)

    # Indicadores
    indicators = {}
    for rep in reports:
        print(f"[info] Extraindo indicador de {rep['url']}", flush=True)
        try:
            total = extract_last_total(rep["url"])
            if total and total.get("values"):
                title_key = rep["title"]
                indicators[title_key] = total
                print(f"[info] Indicador extraido: {rep['title']} -> {total['values']}", flush=True)
            else:
                print(f"[warn] Nenhum 'Total' util encontrado em {rep['url']}", flush=True)
        except Exception as exc:
            print(f"[error] Falha ao extrair total de {rep['url']}: {exc}", flush=True)

    # Resumo dos principais indicadores
    summary = {
        "credito_disponivel": _pick_value(
            indicators,
            lambda t: "crédito disponível" in t.lower(),
            lambda c: True,
        ),
        "empenhado": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercício" in t.lower(),
            lambda c: "empenhad" in c.lower(),
        )
        or _pick_value(
            indicators,
            lambda t: "despesas empenhadas, liquidadas e pagas" in t.lower(),
            lambda c: "empenhad" in c.lower(),
        ),
        "liquidado": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercício" in t.lower(),
            lambda c: "liquidad" in c.lower(),
        )
        or _pick_value(
            indicators,
            lambda t: "despesas empenhadas, liquidadas e pagas" in t.lower(),
            lambda c: "liquidad" in c.lower(),
        ),
        "pago": _pick_value(
            indicators,
            lambda t: "saldos de empenhos do exercício" in t.lower(),
            lambda c: "pago" in c.lower(),
        )
        or _pick_value(
            indicators,
            lambda t: "despesas empenhadas, liquidadas e pagas" in t.lower(),
            lambda c: "pago" in c.lower(),
        ),
        "rap_pagos": _pick_value(
            indicators,
            lambda t: "restos a pagar" in t.lower(),
            lambda c: "pagos" in c.lower(),
        ),
        "rap_a_pagar": _pick_value(
            indicators,
            lambda t: "restos a pagar" in t.lower(),
            lambda c: "a pagar" in c.lower(),
        ),
        "gru_arrecadado": _pick_value(
            indicators,
            lambda t: "recolhimento" in t.lower() and "gru" in t.lower(),
            lambda c: "arrecad" in c.lower(),
        ),
    }

    # Mensagem final
    msg = format_message(reports, stale, summary, base_url)
    print(f"[info] Enviando mensagem para Telegram ({len(msg)} chars)", flush=True)
    resp = send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"], msg)
    print(f"[info] Telegram enviado com sucesso: status={resp.status_code} body={resp.text}", flush=True)


if __name__ == "__main__":
    main()
