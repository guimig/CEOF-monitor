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

123456789:AA...XYZ

4. Pegue seu `chat_id` abrindo no navegador:

https://api.telegram.org/botSEU_TOKEN/getUpdates

---

### 2. Adicione Secrets no GitHub

No repositório:

Settings → Secrets → Actions → New secret

Crie:

- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`

---

### 3. Estrutura do projeto

Clone este repositório e mantenha a estrutura:

src/ config/ .github/workflows/ requirements.txt

---

### 4. Comportamento automático

O GitHub executará o script:

- Todos os dias às 10h UTC
- Ou manualmente via "Run workflow"

Você receberá um relatório assim:

- ❗ Relatórios desatualizados  
- 📌 Totais por relatório  
- 📊 Valores extraídos  

---

### 5. Executar manualmente (opcional)

pip install -r requirements.txt python -m src.main

---

## 🧠 Observações

- O sistema é modularizado para fácil manutenção.
- O código segue boas práticas (responsabilidades separadas).
- Fácil expandir para novas métricas ou gráficos.