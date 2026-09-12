"""Destaque do próximo prêmio na visão semanal da Conciliação."""
import html

import conciliacao_visual_screen as base


def _next_award_card(row):
    next_award = row.get("next_award", 0)
    if not next_award:
        return (
            '<div class="conc-kpi next-award next-award-highlight next-award-max">'
            '<small>PRÓXIMO PRÊMIO</small>'
            '<strong>MÁXIMO</strong>'
            '<div class="next-award-max-text">Faixa máxima atingida</div>'
            '</div>'
        )

    remain_q = int(row.get("qias_remaining", 0) or 0)
    remain_c = int(row.get("changes_remaining", 0) or 0)
    return (
        '<div class="conc-kpi next-award next-award-highlight">'
        '<small>PRÓXIMO PRÊMIO</small>'
        f'<strong>{html.escape(base.money(next_award))}</strong>'
        '<div class="next-award-missing">'
        '<div><span>FALTAM</span>'
        f'<b>{base.integer(remain_q)}</b><em>QIAs</em></div>'
        '<div><span>FALTAM</span>'
        f'<b>{base.integer(remain_c)}</b><em>TROCAS</em></div>'
        '</div>'
        '</div>'
    )


def _weekly_ranking_html(rows):
    out = []
    for pos, row in enumerate(rows, 1):
        _, color, ink = base.PALETTE[row["color"]]
        qgoal = row.get("weekly_qias_goal", 0)
        head = base._hero(pos, row, "Meta inicial da semana", qgoal)
        cards = [
            base._metric_card("QIAs", base.integer(row["qias"]), base.integer(row["qias_projection"]), (row["qias"], qgoal), cls="qias"),
            base._metric_card("Trocas", base.integer(row["changes"]), base.integer(row["changes_projection"]), (row["changes"], row.get("weekly_changes_goal", 0)), cls="changes"),
            base._metric_card("Prêmio conquistado", base.money(row.get("earned_award", 0)), accent="award", cls="weekly"),
            base._metric_card("Prêmio projetado", base.money(row.get("award", 0)), accent="monthly", cls="monthly"),
            _next_award_card(row),
        ]
        body = head + '<div class="conc-kpi-grid conc-weekly-grid">' + ''.join(cards) + '</div>'
        warning = ' · Caixa e ticket parciais' if row.get("cash_invalid") else ''
        out.append(
            f'<article class="conc-rank-row" style="--tone:{color};--ink:{ink}">'
            f'{body}<div class="conc-warning">{warning}</div></article>'
        )
    return '<div class="conc-ranking" translate="no">' + ''.join(out) + '</div>'


def ranking_html(rows, view):
    if view != "SEMANAL":
        return base.ranking_html(rows, view)
    return _weekly_ranking_html(rows)


STYLE = base.STYLE + """<style>
.conc-kpi.next-award-highlight{background:#fff7ed!important;border:2px solid #fb923c!important;box-shadow:0 4px 12px #9a341226!important;padding:9px 10px!important}
.conc-kpi.next-award-highlight>small{font-size:.66rem!important;color:#9a3412!important;letter-spacing:.03em}
.conc-kpi.next-award-highlight>strong{font-size:1.5rem!important;color:#9a3412!important;margin:5px 0 7px!important}
.next-award-missing{display:grid;grid-template-columns:1fr 1fr;gap:6px;width:100%}
.next-award-missing>div{background:#ffffff;border:1px solid #fed7aa;border-radius:8px;padding:5px 6px;text-align:center;display:grid;grid-template-columns:auto auto;align-items:end;justify-content:center;column-gap:4px}
.next-award-missing span{grid-column:1/-1;font-size:.49rem;font-weight:900;color:#9a3412;letter-spacing:.06em;line-height:1}
.next-award-missing b{font-size:1.4rem;line-height:1;color:#c2410c}
.next-award-missing em{font-size:.58rem;font-style:normal;font-weight:900;color:#7c2d12;padding-bottom:2px}
.next-award-max-text{font-size:.68rem;font-weight:900;color:#9a3412;margin-top:4px}
@media(max-width:700px){.conc-kpi.next-award-highlight{grid-column:1/-1!important}.next-award-missing b{font-size:1.55rem}}
</style>"""
