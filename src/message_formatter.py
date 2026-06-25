def _clean_title(title: str) -> str:
    parts = title.split(" - ", 1)
    return parts[0].strip() if parts else title.strip()


def _fmt_currency(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_message(reports, stale, summary, base_url, portal_url, today_str, time_str, weekday):
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

    if summary:
        if (
            summary.get("a_liquidar") is not None
            or summary.get("liquidados_a_pagar") is not None
            or summary.get("pagos") is not None
        ):
            lines.append("💼 Saldos de empenhos")
            if summary.get("a_liquidar") is not None:
                lines.append(f"  - A liquidar: {_fmt_currency(summary['a_liquidar'])}")
            if summary.get("liquidados_a_pagar") is not None:
                lines.append(f"  - Liquidados a pagar: {_fmt_currency(summary['liquidados_a_pagar'])}")
            if summary.get("pagos") is not None:
                lines.append(f"  - Pagos: {_fmt_currency(summary['pagos'])}")
            lines.append("")

        if summary.get("rap_pagos") is not None or summary.get("rap_a_pagar") is not None:
            lines.append("📌 Restos a pagar")
            if summary.get("rap_pagos") is not None:
                lines.append(f"  - Pagos: {_fmt_currency(summary['rap_pagos'])}")
            if summary.get("rap_a_pagar") is not None:
                lines.append(f"  - A pagar: {_fmt_currency(summary['rap_a_pagar'])}")
            if summary.get("pct_rap_pago") is not None:
                lines.append(f"  - % pagos do total: {summary['pct_rap_pago']*100:.1f}%")
            lines.append("")

        if summary.get("gru_arrecadado") is not None:
            lines.append(f"💰 GRU arrecadado: {_fmt_currency(summary['gru_arrecadado'])}")
            lines.append("")

    lines.append(f"Relatórios monitorados: {len(reports)}")

    return "\n".join(lines)
