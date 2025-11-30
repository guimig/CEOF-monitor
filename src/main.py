from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import unicodedata
from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.report_total_extractor import extract_last_total
from src.extra_parsers import (
    creditos_por_grupo,
    provisionamentos_por_grupo,
    top5_empenhos_a_liquidar,
    top5_rap_a_pagar,
)
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
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime.now(tz)
    today = now.date()
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

    # Descobrir URLs específicos a partir dos relatórios
    def find_url(title_substr):
        for r in reports:
            if title_substr.lower() in _norm(r["title"]):
                return r["url"]
        return None

    cred_url = find_url("crédito disponível")
    prov_url = find_url("provisionamentos")
    saldos_url = find_url("saldos de empenhos do exercício - conta contábil")
    rap_url = find_url("restos a pagar (rap)")

    # Créditos disponíveis por grupo (investimentos vs ODC)
    if cred_url:
        try:
            cred_groups = creditos_por_grupo(cred_url)
            summary["credito_invest"] = cred_groups["investimentos"]
            summary["credito_odc"] = cred_groups["odc"]
        except Exception as exc:
            print(f"[warn] Falha ao calcular credito por grupo: {exc}")

    # Provisionamentos por grupo (investimentos vs ODC)
    if prov_url:
        try:
            prov = provisionamentos_por_grupo(prov_url)
            summary["prov_invest"] = prov["investimentos"]
            summary["prov_odc"] = prov["odc"]
            summary["prov_total"] = prov["total"]
        except Exception as exc:
            print(f"[warn] Falha ao calcular provisionamentos: {exc}")

    # Provisionado total direto do indicador (se existir)
    prov_total_ind = _pick_value(
        indicators,
        lambda t: "provisionamentos" in t,
        lambda c: "saldo" in c,
    )
    if prov_total_ind is not None:
        summary["prov_total"] = prov_total_ind

    # Totais de empenhado/liquidado/pago (mensal) para percentuais
    summary["empenhado_total"] = _pick_value(
        indicators,
        lambda t: "despesas empenhadas, liquidadas e pagas - m" in t,
        lambda c: "empenhadas" in c,
    )
    summary["liquidado_total"] = _pick_value(
        indicators,
        lambda t: "despesas empenhadas, liquidadas e pagas - m" in t,
        lambda c: "liquidadas" in c,
    )
    summary["pago_total"] = _pick_value(
        indicators,
        lambda t: "despesas empenhadas, liquidadas e pagas - m" in t,
        lambda c: "pagas" in c,
    )
    if summary.get("prov_total") is not None and summary.get("empenhado_total") is not None:
        summary["pct_empenhado_prov"] = (
            summary["empenhado_total"] / summary["prov_total"] if summary["prov_total"] else None
        )
    if summary.get("empenhado_total") is not None and summary.get("liquidado_total") is not None:
        summary["pct_liquidado_empenhado"] = (
            summary["liquidado_total"] / summary["empenhado_total"] if summary["empenhado_total"] else None
        )
    if summary.get("liquidado_total") is not None and summary.get("pago_total") is not None:
        summary["pct_pago_liquidado"] = (
            summary["pago_total"] / summary["liquidado_total"] if summary["liquidado_total"] else None
        )
    # Carregar histórico
    history_path = Path(".cache/history.json")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    else:
        history = []

    # Registrar valores de hoje no histórico
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

    # Remove entrada do mesmo dia e adiciona a nova
    history = [h for h in history if h.get("date") != record["date"]]
    history.append(record)
    # Mantém só os últimos 90 registros
    history = history[-90:]
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # Funções auxiliares para deltas e médias
    def last_value(key):
        for h in reversed(history[:-1]):  # ignora hoje
            if key in h:
                return h[key]
        return None

    def moving_avg(key, days=30):
        vals = []
        for h in reversed(history):
            if key in h:
                vals.append(h[key])
            if len(vals) >= days:
                break
        if not vals:
            return None
        return sum(vals) / len(vals)

    # Deltas vs dia anterior
    for key in record:
        if key == "date":
            continue
        prev = last_value(key)
        cur = record[key]
        if prev is not None:
            summary[f"{key}_delta"] = cur - prev
            summary[f"{key}_pct"] = (cur - prev) / prev if prev else None

    # Médias 30d
    summary["gru_media_30d"] = moving_avg("gru_arrecadado", days=30)

    # Tendências e maiores variações (último dia vs. anterior / médias)
    trends = []
    movers = []
    keys_trend = [
        ("a_liquidar", "A liquidar"),
        ("liquidados_a_pagar", "Liquidados a pagar"),
        ("pagos", "Pagos"),
        ("rap_a_pagar", "RAP a pagar"),
        ("rap_pagos", "RAP pagos"),
        ("gru_arrecadado", "GRU arrecadado"),
    ]
    for key, label in keys_trend:
        cur = record.get(key)
        prev = last_value(key)
        avg7 = moving_avg(key, days=7)
        if cur is None or prev is None or avg7 is None:
            continue
        delta_pct = (cur - prev) / prev if prev else None
        trend_line = f"{label}: {delta_pct*100:+.1f}% vs. dia anterior; {((cur-avg7)/avg7*100):+.1f}% vs. média 7d"
        trends.append(trend_line)
        movers.append((abs(cur - prev), f"{label}: {cur - prev:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")))

    trends = trends[:6]
    movers = sorted(movers, key=lambda x: x[0], reverse=True)[:3]

    summary["trends"] = trends
    summary["movers"] = [m[1] for m in movers]

    # Top 5 maiores empenhos a liquidar (exercício) e RAP a pagar
    if saldos_url:
        try:
            summary["top5_a_liquidar"] = top5_por_coluna(saldos_url, "a liquidar")
        except Exception as exc:
            print(f"[warn] Falha ao calcular top5 a liquidar: {exc}")
    if rap_url:
        try:
            summary["top5_rap_a_pagar"] = top5_por_coluna(rap_url, "a pagar")
        except Exception as exc:
            print(f"[warn] Falha ao calcular top5 rap a pagar: {exc}")

    # Mensagem final
    weekday = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][today.weekday()]
    today_str = today.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")
    summary["gru_media_30d"] = None  # placeholder até termos histórico

    msg = format_message(reports, stale, summary, base_url, today_str, time_str, weekday)

    # Envio em blocos para respeitar limite do Telegram (~4096 chars)
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
