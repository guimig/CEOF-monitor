def _clean_title(title: str) -> str:
    parts = title.split(" - ", 1)
    return parts[0].strip() if parts else title.strip()


def format_message(reports, stale, base_url, portal_url, today_str, time_str, weekday):
    lines = []
    lines.append("📊 CEOF - Monitoramento Automático")
    lines.append(f"🌐 Relatórios: {base_url}")
    if portal_url:
        lines.append(f"🏛️ Portal DAP: {portal_url}")
    lines.append(f"🕒 Hoje é {today_str} {time_str} ({weekday})")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

    if stale:
        lines.append("⚠️ Relatórios desatualizados")
        for report in stale:
            title = _clean_title(report["title"])
            lines.append(
                f"  - {title}: {report['date']} "
                f"({report['age']} dias; limite {report['allowed_age']} dias)"
            )
    else:
        lines.append("✅ Relatórios dentro das regras de atualização")

    lines.append("")
    lines.append(f"Relatórios monitorados: {len(reports)}")

    return "\n".join(lines)
