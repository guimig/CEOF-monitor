def _clean_title(title: str) -> str:
    # Remove o sufixo depois do primeiro hífen (ex.: "Nome - Versão" -> "Nome")
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


def format_message(reports, stale, summary, base_url, today_str, time_str, weekday):
    lines = []
    lines.append("📊 CEOF - Monitoramento Automático")
    lines.append(f"🌐 Base: {base_url}")
    lines.append(f"🕒 Hoje é {today_str} {time_str} ({weekday})")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

    # Status de atualização
    if stale:
        lines.append("⚠️  Relatórios desatualizados (>1 dia)")
        for r in stale:
            title = _clean_title(r["title"])
            lines.append(f"  - {title}: {r['date']} ({r['age']} dias)")
    else:
        lines.append("✅ Relatórios atualizados (fechamento do dia anterior)")
    lines.append("")

    # Indicadores principais
    lines.append("📈 Principais indicadores")
    lines.append("────────────────────────")

    if summary and any(v is not None for v in summary.values()):
        if summary.get("credito_disponivel") is not None:
            delta = summary.get("credito_disponivel_delta")
            pct = summary.get("credito_disponivel_pct")
            lines.append(
                f"  • Crédito disponível: {_fmt_currency(summary['credito_disponivel'])}"
                f"{_fmt_delta(delta)}{_fmt_pct(pct)}"
            )
            if summary.get("credito_invest") is not None or summary.get("credito_odc") is not None:
                inv = summary.get("credito_invest")
                odc = summary.get("credito_odc")
                parts = []
                if inv is not None:
                    parts.append(f"Invest: {_fmt_currency(inv)}")
                if odc is not None:
                    parts.append(f"ODC: {_fmt_currency(odc)}")
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
                lines.append(
                    f"      - A liquidar: {_fmt_currency(summary['a_liquidar'])}"
                    f"{_fmt_delta(summary.get('a_liquidar_delta'))}"
                    f"{_fmt_pct(summary.get('a_liquidar_pct'))}"
                )
            if summary.get("liquidados_a_pagar") is not None:
                lines.append(
                    f"      - Liquidados a pagar: {_fmt_currency(summary['liquidados_a_pagar'])}"
                    f"{_fmt_delta(summary.get('liquidados_a_pagar_delta'))}"
                    f"{_fmt_pct(summary.get('liquidados_a_pagar_pct'))}"
                )
            if summary.get("pagos") is not None:
                lines.append(
                    f"      - Pagos: {_fmt_currency(summary['pagos'])}"
                    f"{_fmt_delta(summary.get('pagos_delta'))}"
                    f"{_fmt_pct(summary.get('pagos_pct'))}"
                )
            if summary.get("pct_pago_sobre_liq") is not None:
                lines.append(
                    f"      - % pagos s/ (liq a pagar + pagos): {summary['pct_pago_sobre_liq']*100:.1f}%"
                )
        lines.append("")
        if summary.get("rap_pagos") is not None or summary.get("rap_a_pagar") is not None:
            lines.append("  • Restos a pagar")
            if summary.get("rap_pagos") is not None:
                lines.append(
                    f"      - Pagos: {_fmt_currency(summary['rap_pagos'])}"
                    f"{_fmt_delta(summary.get('rap_pagos_delta'))}"
                    f"{_fmt_pct(summary.get('rap_pagos_pct'))}"
                )
            if summary.get("rap_a_pagar") is not None:
                lines.append(
                    f"      - A pagar: {_fmt_currency(summary['rap_a_pagar'])}"
                    f"{_fmt_delta(summary.get('rap_a_pagar_delta'))}"
                    f"{_fmt_pct(summary.get('rap_a_pagar_pct'))}"
                )
            if summary.get("pct_rap_pago") is not None:
                lines.append(f"      - % pagos do total: {summary['pct_rap_pago']*100:.1f}%")
        
        lines.append("")
        if summary.get("gru_arrecadado") is not None:
            linha_gru = f"  • GRU arrecadado: {_fmt_currency(summary['gru_arrecadado'])}"
            if summary.get("gru_arrecadado_delta") is not None:
                linha_gru += _fmt_delta(summary.get("gru_arrecadado_delta"))
            if summary.get("gru_arrecadado_pct") is not None:
                linha_gru += _fmt_pct(summary.get("gru_arrecadado_pct"))
            if summary.get("gru_media_30d") is not None:
                media = summary["gru_media_30d"]
                delta_vs_media = summary["gru_arrecadado"] - media
                pct_vs_media = (delta_vs_media / media * 100) if media else 0
                linha_gru += f" ({pct_vs_media:+.1f}% vs. média 30d)"
            else:
                linha_gru += " (sem histórico 30d)"
            lines.append(linha_gru)
        
        lines.append("")
        # Percentuais adicionais
        if summary.get("pct_empenhado_prov") is not None or summary.get("pct_liquidado_empenhado") is not None or summary.get("pct_pago_liquidado") is not None:
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
    # Tendências
    if summary.get("trends"):
        lines.append("")
        lines.append("📊 Tendências (dia vs. anterior / vs. média 7d)")
        lines.append("────────────────────────")
        for tr in summary["trends"]:
            lines.append(f"  • {tr}")
    
    lines.append("")
    # Maiores variações do dia
    if summary.get("movers"):
        lines.append("")
        lines.append("🚩 Maiores variações do dia")
        lines.append("────────────────────────")
        for mv in summary["movers"]:
            lines.append(f"  • {mv}")

    #lines.append("")
    # Top 5 listas
    #if summary.get("top5_a_liquidar") or summary.get("top5_rap_a_pagar"):
    #    lines.append("")
    #    lines.append("📌 Maiores saldos a liquidar")
    #    lines.append("────────────────────────")
    #    if summary.get("top5_a_liquidar"):
    #        lines.append("  • Exercício atual:")
    #        for item in summary["top5_a_liquidar"]:
    #            lines.append(f"      - {item}")
    #    if summary.get("top5_rap_a_pagar"):
    #        lines.append("  • Restos a pagar:")
    #        for item in summary["top5_rap_a_pagar"]:
    #            lines.append(f"      - {item}")

    return "\n".join(lines)
