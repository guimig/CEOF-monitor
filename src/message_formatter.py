def format_message(reports, stale, indicators, base_url):
    # Mensagem em texto simples para evitar problemas de parse/emoji no Telegram
    lines = []
    lines.append("CEOF - Monitoramento Automatico")
    lines.append(f"Base: {base_url}")
    lines.append("")

    lines.append("Relatorios desatualizados (>2 dias):")
    if not stale:
        lines.append("- Nenhum; todos atualizados.")
    else:
        for r in stale:
            lines.append(f"- {r['title']} - {r['date']} ({r['age']} dias)")

    lines.append("")
    lines.append("Indicadores extraidos:")
    if not indicators:
        lines.append("- Nenhum indicador encontrado.")
    else:
        for title, info in indicators.items():
            vals = ", ".join(
                f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                for v in info["values"]
            )
            lines.append(f"- {title}")
            lines.append(f"  Linha: {info['raw']}")
            lines.append(f"  Valores: {vals}")

    return "\n".join(lines)
