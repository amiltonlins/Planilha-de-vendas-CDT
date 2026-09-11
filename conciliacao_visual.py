"""Shared Conciliação presentation rules for the screen and PNG exports."""
import html
import io
from decimal import Decimal

PALETTE = {
    "red": ("🔴", "#B91C1C", "#FFFFFF"),
    "orange": ("🟠", "#C2410C", "#FFFFFF"),
    "yellow": ("🟡", "#FACC15", "#172033"),
    "green": ("🟢", "#15803D", "#FFFFFF"),
    "blue": ("🔵", "#1D4ED8", "#FFFFFF"),
}


def money(value):
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def integer(value):
    return f"{value:,.0f}".replace(",", ".")


def percentage(value):
    return f"{value:.1f}".rstrip("0").rstrip(".").replace(".", ",") + "%"


def daily_color(qias):
    return "blue" if qias >= 30 else "green" if qias >= 25 else "yellow" if qias >= 20 else "orange" if qias >= 15 else "red"


def projection_color(projected, goal):
    if goal <= 0:
        return "red"
    percent = Decimal(projected) * 100 / Decimal(goal)
    return "blue" if percent >= 101 else "green" if percent >= 100 else "yellow" if percent >= 75 else "orange" if percent >= 50 else "red"


def _project_value(row, key, total_key="qias"):
    realized_total = Decimal(row.get(total_key, 0) or 0)
    projected_total = Decimal(row.get(total_key + "_projection", realized_total) or 0)
    realized = Decimal(row.get(key, 0) or 0)
    if realized_total <= 0:
        return realized
    return realized * projected_total / realized_total


def _balloon(label, realized, projection=None, ticket=None, wide=False):
    classes = "conc-balloon conc-balloon-wide" if wide else "conc-balloon"
    secondary = ""
    if projection is not None:
        secondary += f'<span class="conc-balloon-projection">Projeção <b>{html.escape(str(projection))}</b></span>'
    if ticket is not None:
        secondary += f'<span class="conc-balloon-ticket">Ticket médio <b>{html.escape(str(ticket))}</b></span>'
    return (
        f'<div class="{classes}"><small>{html.escape(label)}</small>'
        f'<strong>{html.escape(str(realized))}</strong>{secondary}</div>'
    )


def row_metrics(row, view):
    if view == "VISÃO GERAL":
        return [
            ("QIAs", integer(row["qias"])), ("% META QIAs", percentage(Decimal(row["qias"])*100/row["qias_goal"]) if row.get("qias_goal") else "—"), ("PROJEÇÃO QIAs", integer(row["qias_projection"])),
            ("TROCAS", integer(row["changes"])), ("% META TROCAS", percentage(Decimal(row["changes"])*100/row["changes_goal"]) if row.get("changes_goal") else "—"), ("PROJEÇÃO TROCAS", integer(row["changes_projection"])),
            ("CAIXA", money(row["cash"])), ("CRÉDITO", integer(row["credit"])), ("NEOENERGIA", integer(row["neo"])),
            ("TICKET MÉDIO", money(row["ticket"])), ("% META PROJETADA", percentage(row["goal_percent"])),
            ("MENSAL ATUAL", money(row["monthly_award"])), ("SEMANAIS CONQUISTADAS", money(row["weekly_award"])),
            ("MENSAL PROJETADA", money(row["projected_award"])), ("TOTAL PROJETADO", money(row["commission_projection"])),
        ]
    metrics = [("QIAs", integer(row["qias"])), ("TROCAS", integer(row["changes"])),
               ("CRÉDITO", integer(row["credit"])), ("NEOENERGIA", integer(row["neo"])),
               ("TICKET MÉDIO", money(row["ticket"])), ("CAIXA", money(row["cash"]))]
    if view == "DIÁRIO":
        metrics += [("QIAs NA SEMANA", integer(row.get("week_qias", 0))),
                    ("QIAs NO MÊS", integer(row.get("month_qias", 0)))]
    else:
        metrics += [("PROJEÇÃO QIAs", integer(row["qias_projection"])),
                    ("PROJEÇÃO TROCAS", integer(row["changes_projection"])),
                    ("PRÊMIO CONQUISTADO", money(row.get("closed_award", 0))),
                    ("PRÊMIO PROJETADO", money(row["award"])),
                    ("FAIXA ATUAL", str(row["tier"]) + "ª" if row["tier"] else "—"),
                    ("FAIXA PROJETADA", str(row["projected_tier"]) + "ª" if row["projected_tier"] else "—")]
    return metrics


def ranking_html(rows, view):
    result = []
    for index, row in enumerate(rows, 1):
        emoji, color, ink = PALETTE[row["color"]]
        goal = f'Meta individual: {integer(row["qias_goal"])} QIAs' if "qias_goal" in row else ""
        warning = ' · Caixa e ticket parciais' if row.get("cash_invalid") else ''

        if view == "VISÃO GERAL":
            balloons = [
                _balloon("QIAs", integer(row["qias"]), integer(row["qias_projection"])),
                _balloon("Trocas Crédito", integer(row["credit"]), integer(_project_value(row, "credit", "changes"))),
                _balloon("Trocas Neoenergia", integer(row["neo"]), integer(_project_value(row, "neo", "changes"))),
                _balloon("Ticket Médio Geral", money(row["ticket"])),
            ]
            for label in ("NR", "1 A 3", "4 A 6"):
                balloons.append(_balloon(
                    label,
                    integer(row[label]),
                    integer(_project_value(row, label, "qias")),
                    money(row.get("regime_tickets", {}).get(label, 0)),
                    wide=True,
                ))
            weekly_projected = row.get("weekly_projection", row.get("weekly_award", 0))
            balloons += [
                _balloon("Prêmio Semanal", money(row.get("weekly_award", 0)), money(weekly_projected), wide=True),
                _balloon("Premiação Mensal", money(row.get("projected_award", 0)), wide=True),
            ]
            body = '<div class="conc-balloon-grid">' + ''.join(balloons) + '</div>'
        else:
            body = '<div class="conc-indicators">' + ''.join(
                f'<span><strong>{html.escape(value)}</strong><small>{html.escape(label)}</small></span>'
                for label, value in row_metrics(row, view)
            ) + '</div>'

        result.append(
            f'<article class="conc-rank-row" style="--tone:{color};--ink:{ink}">'
            f'<div class="conc-person"><b>{index}º · {html.escape(row["name"])}</b><span>{emoji}</span></div>'
            f'{body}'
            f'<div class="conc-regime">{goal}{warning}</div></article>'
        )
    return '<div class="conc-ranking" translate="no">' + ''.join(result) + '</div>'


def summary_html(totals, summary, goals, monthly=True):
    def fields(values):
        return ''.join(f'<div><small>{label}</small><strong>{html.escape(value)}</strong></div>' for label, value in values)
    results = [("QIAs REALIZADOS", integer(totals["qias"])), ("TROCAS REALIZADAS", integer(totals["changes"]))]
    if monthly:
        results += [("PROJEÇÃO QIAs", integer(sum(r["qias_projection"] for r in summary))),
                    ("PROJEÇÃO TROCAS", integer(sum(r["changes_projection"] for r in summary)))]
    goals_values = []
    for key, label in (("qias", "QIAs"), ("changes", "TROCAS")):
        goal = goals.get(key, 0)
        goals_values.append((f"META {label}", integer(goal) if goal else "Não definida"))
        results.append((f"% META {label}", percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    values = dict(results)
    order = ["QIAs REALIZADOS", "% META QIAs"]
    if monthly:
        order += ["PROJEÇÃO QIAs"]
    order += ["TROCAS REALIZADAS", "% META TROCAS"]
    if monthly:
        order += ["PROJEÇÃO TROCAS"]
    results = [(label, values[label]) for label in order] + [("TICKET MÉDIO GERAL", money(totals["ticket"]))]
    return ('<div class="exec-compact-grid conc-summary" translate="no">'
            '<div class="exec-compact-card exec-performance"><div class="exec-compact-title">DESEMPENHO GERAL</div>'
            f'<div class="exec-performance-values conc-performance-values">{fields(results)}</div></div>'
            '<div class="exec-compact-card"><div class="exec-compact-title">METAS MENSAIS GERAIS</div>'
            f'<div class="conc-summary-values">{fields(goals_values)}</div></div></div>')


def regimes_html(totals):
    return '<div class="conc-regimes">' + ''.join(
        f'<div><small>{label}</small><b>{integer(totals[label])} QIAs</b><span>'
        f'{percentage(Decimal(totals[label])*100/totals["qias"]) if totals["qias"] else "0%"}</span><em>Ticket Médio <b>{money(totals.get("regime_tickets", {}).get(label, 0))}</b></em></div>'
        for label in ("NR", "1 A 3", "4 A 6")) + '</div>'


STYLE = """<style>
.conc-summary.exec-compact-grid{display:grid;grid-template-columns:2.4fr 1fr!important;gap:9px!important;margin:6px 0 10px!important;align-items:start!important}
.conc-summary .exec-compact-card{min-height:0!important;padding:10px 12px!important;border-radius:12px!important}
.conc-summary .exec-compact-title{font-size:.58rem!important;line-height:1.1!important;margin-bottom:8px!important}
.conc-summary .conc-performance-values{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px 12px!important}
.conc-summary .conc-performance-values>div:last-child{grid-column:1/-1}
.conc-summary .conc-performance-values small{display:block;font-size:.52rem!important;line-height:1.15!important;color:#E2E8F0!important;white-space:normal!important}
.conc-summary .conc-performance-values strong{display:block;font-size:1.42rem!important;line-height:1.02!important;margin-top:4px!important;color:#fff!important}
.conc-summary-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.conc-summary-values small{display:block;font-size:.52rem!important;color:#64748b}.conc-summary-values strong{display:block;font-size:1.22rem!important;line-height:1.1!important;margin-top:4px;white-space:nowrap}
.conc-regimes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:6px 0 10px}
.conc-regimes>div{background:#fff;border:1px solid #e2e8f0;border-radius:9px;padding:6px 9px;display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.conc-regimes small{color:#64748b;font-weight:800;font-size:.62rem!important}.conc-regimes b{font-size:.78rem!important}.conc-regimes span{margin-left:auto;color:#64748b;font-size:.65rem!important}
.conc-rank-row{border-radius:14px;background:var(--tone);color:var(--ink);padding:9px 12px;margin:8px 0;box-shadow:0 2px 7px #0f172a18}
.conc-person{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:7px;font-size:.84rem!important}.conc-person b{font-size:inherit!important}
.conc-balloon-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:6px;align-items:stretch}
.conc-balloon{grid-column:span 2;min-width:0;background:color-mix(in srgb,#fff 16%,transparent);border:1px solid color-mix(in srgb,#fff 42%,transparent);border-radius:11px;padding:7px 8px;text-align:left;display:flex;flex-direction:column;justify-content:center;min-height:72px;box-sizing:border-box}
.conc-balloon-wide{grid-column:span 3}
.conc-balloon small{font-size:.52rem!important;font-weight:850;line-height:1.15!important;color:inherit!important;opacity:.88;text-transform:uppercase;letter-spacing:.02em}
.conc-balloon>strong{font-size:1.28rem!important;line-height:1.05!important;font-weight:950;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.conc-balloon-projection,.conc-balloon-ticket{display:block;font-size:.56rem!important;line-height:1.2!important;margin-top:4px;opacity:.92}
.conc-balloon-projection b,.conc-balloon-ticket b{font-size:.68rem!important;font-weight:900}
.conc-balloon-ticket{opacity:.82}
.conc-indicators{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px}.conc-indicators span{border-left:1px solid currentColor;text-align:center;padding:3px;min-width:0;display:flex;flex-direction:column;justify-content:center}.conc-indicators strong{font-size:.85rem!important;font-weight:800;line-height:1.15!important;white-space:nowrap}.conc-indicators small{font-size:.52rem!important;line-height:1.15!important;margin-top:3px;color:inherit!important}
.conc-regime{font-size:.58rem;padding-top:5px;margin-top:6px;border-top:1px solid currentColor}
.st-key-conc_refresh button{background:transparent!important;color:#64748b!important;border:0!important;min-height:26px!important;padding:0 5px!important}.st-key-conc_refresh button p{font-size:.68rem!important}
@media(max-width:900px){.conc-balloon{grid-column:span 3}.conc-balloon-wide{grid-column:span 4}}
@media(max-width:700px){
.conc-summary.exec-compact-grid{grid-template-columns:1fr!important;gap:6px!important}.conc-summary .exec-performance{grid-column:auto!important}.conc-summary .exec-compact-card{padding:8px 9px!important}.conc-summary .conc-performance-values{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:7px 12px!important}.conc-summary .conc-performance-values>div:last-child{grid-column:1/-1}.conc-summary .conc-performance-values strong{font-size:1.1rem!important}
.conc-rank-row{padding:8px;margin:6px 0}.conc-person{font-size:.76rem!important;margin-bottom:6px}.conc-balloon-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.conc-balloon,.conc-balloon-wide{grid-column:span 1;min-height:68px;padding:6px 7px}.conc-balloon>strong{font-size:1.08rem!important}.conc-balloon small{font-size:.48rem!important}.conc-balloon-projection,.conc-balloon-ticket{font-size:.51rem!important}.conc-balloon-projection b,.conc-balloon-ticket b{font-size:.62rem!important}.conc-indicators{grid-template-columns:repeat(2,minmax(0,1fr))}.conc-regimes{grid-template-columns:1fr}.conc-regime{font-size:.54rem!important}
}
@media(max-width:420px){.conc-balloon-grid{grid-template-columns:1fr 1fr}.conc-balloon,.conc-balloon-wide{grid-column:span 1}.conc-balloon:nth-child(7),.conc-balloon:nth-child(8),.conc-balloon:nth-child(9){grid-column:span 2}}
</style>"""


def _fit_image_text(draw, text, font, width):
    text = str(text)
    if draw.textlength(text, font=font) <= width:
        return text
    while text and draw.textlength(text + "…", font=font) > width:
        text = text[:-1]
    return text + "…"


def _daily_font(size, bold=False):
    from PIL import ImageFont
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _draw_daily_ordinal(draw, x, y, position, ink):
    draw.text((x, y), f"{position}º", font=_daily_font(24, True), fill=ink, anchor="mm")


def _draw_daily_status_icon(draw, x, y, label):
    colors = {"Azul": "#2563EB", "Verde": "#16A34A", "Amarelo": "#EAB308", "Laranja": "#EA580C", "Vermelho": "#DC2626"}
    draw.ellipse((x-12, y-12, x+12, y+12), fill=colors.get(label, "#64748B"))


def ranking_png(rows, view, period, totals, goals, synced_at):
    from PIL import Image, ImageDraw
    team_height = 180
    row_height = 510 if view == "VISÃO GERAL" else 360
    image = Image.new("RGB", (1080, 225 + team_height + max(1, len(rows)) * (row_height + 14)), "white")
    draw = ImageDraw.Draw(image)
    draw.text((24, 22), "PAINEL DE RESULTADOS · CONCILIAÇÃO", font=_daily_font(34, True), fill="#0F172A")
    draw.text((24, 68), period, font=_daily_font(24), fill="#475569")

    team = [("QIAs", integer(totals["qias"])), ("TROCAS", integer(totals["changes"]))]
    for key, label in (("qias", "QIAs"), ("changes", "TROCAS")):
        goal = goals.get(key, 0)
        team.append((f"% META {label}", percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    for j, (label, value) in enumerate(team):
        x, y = 38 + (j % 4) * 254, 112 + (j // 4) * 65
        draw.text((x, y), _fit_image_text(draw, value, _daily_font(27, True), 240), font=_daily_font(27, True), fill="#0F172A")
        draw.text((x, y+33), label, font=_daily_font(16), fill="#64748B")

    for i, row in enumerate(rows):
        y = 167 + team_height + i * (row_height + 14)
        _, color, ink = PALETTE[row.get("color", daily_color(row["qias"]))]
        draw.rounded_rectangle((16, y, 1064, y+row_height), radius=24, fill=color)
        name = _fit_image_text(draw, row["name"], _daily_font(31, True), 875)
        _draw_daily_ordinal(draw, 48, y+34, i+1, ink)
        draw.text((82, y+15), name, font=_daily_font(31, True), fill=ink)
        _draw_daily_status_icon(draw, 1020, y+36, {"blue":"Azul","green":"Verde","yellow":"Amarelo","orange":"Laranja","red":"Vermelho"}[row.get("color",daily_color(row["qias"]))])

        if view == "VISÃO GERAL":
            items = [
                ("QIAs", integer(row["qias"]), integer(row["qias_projection"]), None),
                ("TROCAS CRÉDITO", integer(row["credit"]), integer(_project_value(row, "credit", "changes")), None),
                ("TROCAS NEOENERGIA", integer(row["neo"]), integer(_project_value(row, "neo", "changes")), None),
                ("TICKET MÉDIO GERAL", money(row["ticket"]), None, None),
                ("NR", integer(row["NR"]), integer(_project_value(row, "NR", "qias")), money(row.get("regime_tickets", {}).get("NR", 0))),
                ("1 A 3", integer(row["1 A 3"]), integer(_project_value(row, "1 A 3", "qias")), money(row.get("regime_tickets", {}).get("1 A 3", 0))),
                ("4 A 6", integer(row["4 A 6"]), integer(_project_value(row, "4 A 6", "qias")), money(row.get("regime_tickets", {}).get("4 A 6", 0))),
                ("PRÊMIO SEMANAL", money(row.get("weekly_award", 0)), money(row.get("weekly_projection", row.get("weekly_award", 0))), None),
                ("PREMIAÇÃO MENSAL", money(row.get("projected_award", 0)), None, None),
            ]
            cols = 3
            card_w, card_h = 322, 112
            start_x, start_y = 38, y + 72
            for j, (label, realized, projection, ticket) in enumerate(items):
                col, line = j % cols, j // cols
                x, top = start_x + col * 336, start_y + line * 126
                draw.rounded_rectangle((x, top, x+card_w, top+card_h), radius=14, outline=ink, width=1)
                draw.text((x+12, top+10), label, font=_daily_font(15, True), fill=ink)
                draw.text((x+12, top+32), _fit_image_text(draw, realized, _daily_font(27, True), card_w-24), font=_daily_font(27, True), fill=ink)
                secondary_y = top + 67
                if projection is not None:
                    draw.text((x+12, secondary_y), "Projeção " + str(projection), font=_daily_font(15), fill=ink)
                    secondary_y += 20
                if ticket is not None:
                    draw.text((x+12, secondary_y), "Ticket médio " + str(ticket), font=_daily_font(14), fill=ink)
        else:
            for j, (label, value) in enumerate(row_metrics(row, view)):
                x, top = 38 + (j % 4) * 254, y + 64 + (j // 4) * 82
                if j % 4:
                    draw.line((x-12, top+2, x-12, top+59), fill=ink, width=1)
                font = _daily_font(42 if j == 0 else 36 if j == 1 else 27, True)
                fitted = _fit_image_text(draw, value, font, 232)
                draw.text((x, top), fitted, font=font, fill=ink)
                label_font = _daily_font(18)
                if draw.textlength(label, font=label_font) > 238:
                    label_font = _daily_font(15)
                draw.text((x, top+40), label, font=label_font, fill=ink)

    if not rows:
        draw.text((40, 205+team_height), "Nenhum conciliador habilitado.", font=_daily_font(28), fill="#475569")
    footer = f"Atualizado em {synced_at:%d/%m/%Y %H:%M}"
    if any(r.get("cash_invalid") for r in rows):
        footer += " · Caixa e Ticket Médio parciais"
    draw.text((26, image.height-34), footer, font=_daily_font(20), fill="#475569")
    output = io.BytesIO(); image.save(output, "PNG")
    return output.getvalue()
