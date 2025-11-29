import requests


def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    resp = requests.post(url, data=payload, timeout=(5, 20))

    # Se o Telegram devolver erro (token/chat_id/Markdown), falhamos o job para aparecer no log
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise RuntimeError(
            f"Falha ao enviar Telegram ({resp.status_code}): {resp.text}"
        ) from None

    return resp
