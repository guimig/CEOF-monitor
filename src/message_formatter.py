def _clean_title(title: str) -> str:
    # Remove o sufixo depois do primeiro hífen (ex.: "Nome - Versão" -> "Nome")
    parts = title.split(" - ", 1)
    return parts[0].strip() if parts else title.strip()


def format_message(reports, stale, indicators, base_url):
    # Texto com acentos e pequenos ícones para legibilidade; sem Markdown.
    lines = []
    lines.append("📊 CEOF - Monitoramento Automático")
    lines.append(f"🌐 Base: {base_url}")
    lines.append("")

    lines.append("⚠️  Relatórios desatualizados (>2 dias)")
    if not stale:
        lines.append("   - Nenhum; todos atualizados.")
    else:
        for r in stale:
            title = _clean_title(r["title"])
            lines.append(f"   - {title} ({r['date']}, {r['age']} dias)")
    lines.append("")

    lines.append("📈 Indicadores extraídos (linha de total)")
    if not indicators:
        lines.append("   - Nenhum 'Total' encontrado nos relatórios analisados.")
    else:
        for title, info in indicators.items():
            title = _clean_title(title)
            vals = ", ".join(
                f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                for v in info["values"]
            )
            lines.append(f"   - {title}")
            lines.append(f"     Linha: {info['raw']}")
            lines.append(f"     Valores: {vals}")
            lines.append("")  # separador visual

    return "\n".join(lines)
