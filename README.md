# CEOF – Monitoramento Automático (GitHub + Telegram)

Este projeto monitora automaticamente os relatórios do portal:

**https://guimig.github.io/EmailBackupHub/**

Ele verifica:

- Datas dos relatórios
- Relatórios desatualizados (>2 dias)
- Última linha “Total” de cada relatório
- Extrai valores numéricos
- Envia alertas para o Telegram

Tudo é executado automaticamente via **GitHub Actions**.

---

## 🚀 Como usar

### 1. Crie o bot no Telegram

1. Abra o Telegram → procure por **@BotFather**
2. `/newbot`
3. Receba seu token, algo como: