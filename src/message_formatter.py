def _clean_title(title: str) -> str:
    # Remove o sufixo depois do primeiro hífen (ex.: "Nome - Versão" -> "Nome")
    parts = title.split(" - ", 1)
    return parts[0].strip() if parts else title.strip()


def _fmt_currency(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_message(reports, stale, summary, base_url, today_str, weekday):
    lines = []
    lines.append("📊 CEOF - Monitoramento Automático")
    lines.append(f"🌐 Base: {base_url}")
    lines.append("────────────────────────────")

    # Status de atualização
    if stale:
        lines.append("⚠️  Relatórios desatualizados (>1 dia)")
        for r in stale:
            title = _clean_title(r["title"])
            lines.append(f"  - {title}: {r['date']} ({r['age']} dias)")
    else:
        lines.append(f"✅ Relatórios atualizados (fechamento do dia anterior))
    lines.append("")

    lines.append("Hoje é " + today_str + f" ({weekday})")
    lines.append("")

    # Indicadores principais
    lines.append("📈 Principais indicadores")
    lines.append("────────────────────────")

    if summary and any(v is not None for v in summary.values()):
        if summary.get("credito_disponivel") is not None:
            lines.append(f"  • Crédito disponível: {_fmt_currency(summary['credito_disponivel'])}")

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
            if summary.get("pct_pago_sobre_liq") is not None:
                lines.append(f"      - % pagos s/ (liq a pagar + pagos): {summary['pct_pago_sobre_liq']*100:.1f}%")

        if summary.get("rap_pagos") is not None or summary.get("rap_a_pagar") is not None:
            lines.append("  • Restos a pagar")
            if summary.get("rap_pagos") is not None:
                lines.append(f"      - Pagos: {_fmt_currency(summary['rap_pagos'])}")
            if summary.get("rap_a_pagar") is not None:
                lines.append(f"      - A pagar: {_fmt_currency(summary['rap_a_pagar'])}")
            if summary.get("pct_rap_pago") is not None:
                lines.append(f"      - % pagos do total: {summary['pct_rap_pago']*100:.1f}%")

        if summary.get("gru_arrecadado") is not None:
            lines.append(f"  • GRU arrecadado: {_fmt_currency(summary['gru_arrecadado'])}")
    else:
        lines.append("  • Nenhum indicador principal encontrado.")

    return "\n".join(lines)
