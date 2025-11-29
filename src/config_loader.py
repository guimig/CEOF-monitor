import yaml
import os

def load_settings(path="config/settings.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Lê token e chat_id do ambiente (GitHub Secrets)
    config["telegram"]["token"] = os.getenv(config["telegram"]["token_env"])
    config["telegram"]["chat_id"] = os.getenv(config["telegram"]["chat_id_env"])

    if not config["telegram"]["token"] or not config["telegram"]["chat_id"]:
        raise RuntimeError("Erro: TELEGRAM_TOKEN e/ou TELEGRAM_CHAT_ID não definidos.")

    return config