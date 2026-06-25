def _clean_title(title: str) -> str:
    parts = title.split(" - ", 1)
    return parts[0].strip() if parts else title.strip()


def _fmt_currency(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_delta(delta: float) -> str:
    if delta is None:
        return ""
    sign = "+" if delta >= 0 else ""
    return f" ({sign}{delta:,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(pct: float) -> str:
    if pct is None:
        return ""
    sign = "+" if pct >= 0 else ""
    return f" ({sign}{pct*100:.1f}%)"


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

    lines.append("📈 Principais indicadores")
    lines.append("────────────────────────")

    if summary and any(value is not None for value in summary.values()):
        if summary.get("credito_disponivel") is not None:
            lines.append(
                f"  • Crédito disponível: {_fmt_currency(summary['credito_disponivel'])}"
                f"{_fmt_delta(summary.get('credito_disponivel_delta'))}"
                f"{_fmt_pct(summary.get('credito_disponivel_pct'))}"
            )
            if summary.get("credito_invest") is not None or summary.get("credito_odc") is not None:
                parts = []
                if summary.get("credito_invest") is not None:
                    parts.append(f"Invest: {_fmt_currency(summary['credito_invest'])}")
                if summary.get("credito_odc") is not None:
                    parts.append(f"ODC: {_fmt_currency(summary['credito_odc'])}")
                if parts:
                    lines.append("      - " + "; ".join(parts))

        lines.append("")
        if (
            summary.get("a_liquidar") is not None
            or summary.get("liquidados_a_pagar") is not None
            or summary.get("pagos") is not None
        ):
            lines.append("  • Saldos de empenhos")
            if summary.get("a_liquidar") is not None:
                lines.append(f"      - A liquidar: {_fmt_currency(summary['a_liquidar'])}")
            if summary.get("liquidados_a_pagar") is not None:
                lines.append(f"      - Liquidados a pagar: {_fmt_currency(summary['liquidados_a_pagar'])}")
            if summary.get("pagos") is not None:
                lines.append(f"      - Pagos: {_fmt_currency(summary['pagos'])}")

        lines.append("")
        if (
            summary.get("pct_empenhado_prov") is not None
            or summary.get("pct_liquidado_empenhado") is not None
            or summary.get("pct_pago_liquidado") is not None
        ):
            lines.append("  • Coberturas")
            if summary.get("pct_empenhado_prov") is not None:
                lines.append(f"      - Empenhado / Provisionado: {summary['pct_empenhado_prov']*100:.1f}%")
            if summary.get("pct_liquidado_empenhado") is not None:
                lines.append(f"      - Liquidado / Empenhado: {summary['pct_liquidado_empenhado']*100:.1f}%")
            if summary.get("pct_pago_liquidado") is not None:
                lines.append(f"      - Pago / Liquidado: {summary['pct_pago_liquidado']*100:.1f}%")
        else:
            lines.append("  • Nenhum indicador principal encontrado.")

        lines.append("")
        if summary.get("rap_pagos") is not None or summary.get("rap_a_pagar") is not None:
            lines.append("  • Restos a pagar")
            if summary.get("rap_pagos") is not None:
                lines.append(f"      - Pagos: {_fmt_currency(summary['rap_pagos'])}")
            if summary.get("rap_a_pagar") is not None:
                lines.append(f"      - A pagar: {_fmt_currency(summary['rap_a_pagar'])}")
            if summary.get("pct_rap_pago") is not None:
                lines.append(f"      - % pagos do total: {summary['pct_rap_pago']*100:.1f}%")

        lines.append("")
        if summary.get("gru_arrecadado") is not None:
            linha_gru = f"  • GRU arrecadado: {_fmt_currency(summary['gru_arrecadado'])}"
            if summary.get("gru_media_30d") is not None:
                media = summary["gru_media_30d"]
                delta_vs_media = summary["gru_arrecadado"] - media
                pct_vs_media = (delta_vs_media / media * 100) if media else 0
                linha_gru += f" ({pct_vs_media:+.1f}% vs. média 30d)"
            else:
                linha_gru += " (sem histórico 30d)"
            lines.append(linha_gru)
    else:
        lines.append("  • Nenhum indicador principal encontrado.")

    lines.append("")
    lines.append(f"Relatórios monitorados: {len(reports)}")

    return "\n".join(lines)
