from datetime import date
from src.config_loader import load_settings
from src.report_index_parser import parse_index
from src.report_total_extractor import extract_last_total
from src.message_formatter import format_message
from src.telegram_client import send_telegram

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
                indicators[rep["title"]] = total
                print(f"[info] Indicador extraido: {rep['title']} -> {total['values']}", flush=True)
            else:
                print(f"[warn] Nenhum 'Total' util encontrado em {rep['url']}", flush=True)
        except Exception as exc:
            print(f"[error] Falha ao extrair total de {rep['url']}: {exc}", flush=True)

    # Mensagem final
    msg = format_message(reports, stale, indicators, base_url)
    print(f"[info] Enviando mensagem para Telegram ({len(msg)} chars)", flush=True)
    resp = send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"], msg)
    print(f"[info] Telegram enviado com sucesso: status={resp.status_code} body={resp.text}", flush=True)


if __name__ == "__main__":
    main()
