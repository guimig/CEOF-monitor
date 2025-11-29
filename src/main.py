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

    reports = parse_index(base_url)

    # Verificar desatualizados
    stale = []
    today = date.today()
    for rep in reports:
        age = (today - rep["date"]).days
        if age > max_age:
            rep["age"] = age
            stale.append(rep)

    # Indicadores
    indicators = {}
    for rep in reports:
        try:
            total = extract_last_total(rep["url"])
            if total:
                indicators[rep["title"]] = total
        except Exception:
            pass

    # Mensagem final
    msg = format_message(reports, stale, indicators, base_url)
    send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"], msg)


if __name__ == "__main__":
    main()