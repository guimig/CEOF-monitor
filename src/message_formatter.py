def format_message(reports, stale, indicators, base_url):
    lines = []
    lines.append("*📊 CEOF – Monitoramento Automático*")
    lines.append(f"_Base: {base_url}_\n")

    lines.append("*⏱ Relatórios desatualizados (>2 dias):*")
    if not stale:
        lines.append("Todos atualizados ✔️")
    else:
        for r in stale:
            lines.append(f"• *{r['title']}* — {r['date']} ({r['age']} dias)")

    lines.append("\n*📌 Indicadores extraídos:*")
    for title, info in indicators.items():
        vals = ", ".join(f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                         for v in info["values"])
        lines.append(f"\n*{title}*\n`{info['raw']}`\nValores: {vals}")

    return "\n".join(lines)