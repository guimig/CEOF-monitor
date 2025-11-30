# CEOF – Monitoramento Automático (GitHub Actions + Telegram)

Este repositório roda um monitor diário dos relatórios publicados em  
https://guimig.github.io/EmailBackupHub/ e envia um resumo para o Telegram.

Principais funções:
- Verifica a data dos relatórios (stale > 1 dia, exceto o relatório anual 2024).
- Extrai a linha de **Total** dos relatórios mais recentes.
- Calcula indicadores-chave (crédito disponível, saldos de empenhos, RAP, GRU, coberturas).
- Histórico em cache para variações e médias.
- Envia mensagem formatada (com ícones/separadores) para o Telegram.
- Divide a mensagem se ultrapassar o limite de caracteres do Telegram.

## Configuração rápida

1) **Bot e chat no Telegram**  
   - Crie um bot com o **@BotFather** (`/newbot`) e guarde o token.  
   - Descubra o `chat_id` chamando `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
     ou usando bots de utilitário como @userinfobot.

2) **Secrets no GitHub**  
   Em *Settings > Secrets > Actions*, crie:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`

3) **Configurações gerais**  
   - Arquivo: `config/settings.yaml` (base_url, max_report_age_days, etc.).  
   - Workflow: `.github/workflows/monitor.yml` (agenda diária, cache do histórico em `.cache/history.json`).

4) **Rodar local (opcional)**  
   ```bash
   pip install -r requirements.txt
   TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m src.main
   ```

## O que a mensagem mostra

- Status de atualização dos relatórios (com data/hora em America/Sao_Paulo).
- Indicadores principais: crédito disponível (invest x ODC), saldos de empenhos
  (a liquidar, liquidados a pagar, pagos), RAP (pagos e a pagar), GRU.
- Coberturas: empenhado/provisionado, liquidado/empenhado, pago/liquidado.
- Variações diárias e contra média 7d (quando há histórico).
- Se a mensagem ficar longa, ela é enviada em partes (<3800 caracteres cada).

## Observações
- Histórico é persistido em `.cache/history.json` (cacheado no workflow).
- Relatórios do exercício 2024 não entram no alerta de desatualização.
- Sem dependências além de `requests`, `beautifulsoup4`, `pyyaml`.
