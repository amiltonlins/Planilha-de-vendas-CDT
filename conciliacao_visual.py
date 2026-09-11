"""Shared Conciliação presentation rules for screen and PNG exports."""
import html
import io
from decimal import Decimal

PALETTE={"red":("🔴","#B91C1C","#FFFFFF"),"orange":("🟠","#C2410C","#FFFFFF"),"yellow":("🟡","#FACC15","#172033"),"green":("🟢","#15803D","#FFFFFF"),"blue":("🔵","#1D4ED8","#FFFFFF")}

def money(value): return "R$ "+f"{value:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def integer(value): return f"{value:,.0f}".replace(",",".")
def percentage(value): return f"{value:.1f}".rstrip("0").rstrip(".").replace(".",",")+"%"
def daily_color(qias): return "blue" if qias>=30 else "green" if qias>=25 else "yellow" if qias>=20 else "orange" if qias>=15 else "red"
def projection_color(projected,goal):
    if goal<=0:return "red"
    p=Decimal(projected)*100/Decimal(goal)
    return "blue" if p>=101 else "green" if p>=100 else "yellow" if p>=75 else "orange" if p>=50 else "red"

def _project_value(row,key,total_key="qias"):
    total=Decimal(row.get(total_key,0) or 0); projected=Decimal(row.get(total_key+"_projection",total) or 0); realized=Decimal(row.get(key,0) or 0)
    return realized if total<=0 else realized*projected/total

def _pct(value,goal):
    try:return max(0,min(100,float(Decimal(value)*100/Decimal(goal)))) if goal else 0
    except Exception:return 0

def _progress(value,goal):
    p=_pct(value,goal)
    return f'<div class="conc-progress"><i style="width:{p:.1f}%"></i></div><b class="conc-progress-pct">{p:.0f}%</b>'

def _metric_card(label,value,projection=None,progress=None,accent="",cls="",note=None):
    sub=f'<span>Projeção: <b>{html.escape(str(projection))}</b></span>' if projection is not None else ''
    note_html=f'<em>{html.escape(str(note))}</em>' if note else ''
    bar=_progress(*progress) if progress else ''
    return f'<div class="conc-kpi {cls} {accent}"><small>{html.escape(label)}</small><strong>{html.escape(str(value))}</strong>{sub}{note_html}{bar}</div>'

def _hero(pos,row,label,goal,value=None):
    value=row.get("qias",0) if value is None else value
    return (f'<div class="conc-hero"><div class="conc-rank-badge">{pos}º</div><div class="conc-name">{html.escape(row["name"])}</div>'
            f'<div class="conc-goal-label">{html.escape(label)}: <b>{integer(goal)} QIAs</b></div><div class="conc-goalbar">{_progress(value,goal)}</div>'
            f'<div class="conc-goal-value">{integer(value)} / {integer(goal)} ({_pct(value,goal):.0f}%)</div></div>')

def _regimes_card(row, projections=False):
    items=[]
    for label,accent in (("NR","nr"),("1 a 3","r13"),("4 a 6","r46")):
        key="1 A 3" if label=="1 a 3" else "4 A 6" if label=="4 a 6" else label
        proj=f'<span>Proj.: {integer(_project_value(row,key,"qias"))}</span>' if projections else ''
        items.append(f'<div class="conc-reg-mini {accent}"><small>{label}</small><strong>{integer(row.get(key,0))}</strong>{proj}<em>TM: <b>{money(row.get("regime_tickets",{}).get(key,0))}</b></em></div>')
    return '<div class="conc-kpi regimes"><small>QIAs por régua</small><div class="conc-reg-grid">'+''.join(items)+'</div></div>'

def row_metrics(row,view):
    if view=="DIÁRIO":
        return [("QIAs HOJE",integer(row["qias"])),("TROCAS HOJE",integer(row["changes"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("QIAs NA SEMANA",integer(row.get("week_qias",0))),("QIAs NO MÊS",integer(row.get("month_qias",0)))]
    if view=="SEMANAL":
        return [("QIAs",integer(row["qias"])),("PROJEÇÃO QIAs",integer(row["qias_projection"])),("TROCAS",integer(row["changes"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("PRÊMIO CONQUISTADO",money(row.get("earned_award",0))),("PRÊMIO PROJETADO",money(row.get("award",0))),("PRÓXIMO PRÊMIO",money(row.get("next_award",0)))]
    return [("QIAs",integer(row["qias"])),("PROJEÇÃO QIAs",integer(row["qias_projection"])),("TROCAS",integer(row["changes"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("MENSAL PROJETADA",money(row["projected_award"]))]

def ranking_html(rows,view):
    out=[]
    for pos,row in enumerate(rows,1):
        _,color,ink=PALETTE[row["color"]]
        if view=="VISÃO GERAL":
            qgoal=row.get("qias_goal",0); cgoal=row.get("changes_goal",0)
            head=_hero(pos,row,"Meta individual",qgoal)
            cards=[
                _metric_card("QIAs",integer(row["qias"]),integer(row["qias_projection"]),(row["qias"],qgoal),cls="qias"),
                _metric_card("Trocas Crédito",integer(row["credit"]),integer(_project_value(row,"credit","changes")),(row["credit"],cgoal),cls="credit"),
                _metric_card("Trocas Neoenergia",integer(row["neo"]),integer(_project_value(row,"neo","changes")),(row["neo"],cgoal),cls="neo"),
                _metric_card("Ticket Médio Geral",money(row["ticket"]),cls="ticket"),
                _regimes_card(row,True),
                _metric_card("Prêmio Semanal",money(row.get("weekly_award",0)),money(row.get("weekly_projection",row.get("weekly_award",0))),accent="award",cls="weekly"),
                _metric_card("Premiação Mensal",money(row.get("projected_award",0)),accent="monthly",cls="monthly",note="projetado"),
            ]
            body=head+'<div class="conc-kpi-grid">'+''.join(cards)+'</div>'
        elif view=="DIÁRIO":
            head=_hero(pos,row,"Referência diária",30)
            qnote=f'{integer(row.get("week_qias",0))} na semana · {integer(row.get("month_qias",0))} no mês'
            cards=[
                _metric_card("QIAs hoje",integer(row["qias"]),progress=(row["qias"],30),cls="qias",note=qnote),
                _metric_card("Trocas hoje",integer(row["changes"]),cls="changes"),
                _metric_card("Trocas Crédito",integer(row["credit"]),cls="credit"),
                _metric_card("Trocas Neoenergia",integer(row["neo"]),cls="neo"),
                _metric_card("Ticket Médio",money(row["ticket"]),cls="ticket"),
                _regimes_card(row,False),
            ]
            body=head+'<div class="conc-kpi-grid conc-daily-grid">'+''.join(cards)+'</div>'
        else:
            qgoal=row.get("weekly_qias_goal",0)
            head=_hero(pos,row,"Meta inicial da semana",qgoal)
            remain_q=int(row.get("qias_remaining",0) or 0); remain_c=int(row.get("changes_remaining",0) or 0)
            if row.get("next_award",0):
                remain=f'Faltam {remain_q} QIAs e {remain_c} trocas'
                next_value=money(row.get("next_award",0))
            else:
                remain="Faixa máxima atingida"
                next_value="Máximo"
            cards=[
                _metric_card("QIAs",integer(row["qias"]),integer(row["qias_projection"]),(row["qias"],qgoal),cls="qias"),
                _metric_card("Trocas",integer(row["changes"]),integer(row["changes_projection"]),(row["changes"],row.get("weekly_changes_goal",0)),cls="changes"),
                _metric_card("Prêmio conquistado",money(row.get("earned_award",0)),accent="award",cls="weekly"),
                _metric_card("Prêmio projetado",money(row.get("award",0)),accent="monthly",cls="monthly"),
                _metric_card("Próximo prêmio",next_value,accent="next-award",cls="next",note=remain),
            ]
            body=head+'<div class="conc-kpi-grid conc-weekly-grid">'+''.join(cards)+'</div>'
        warning=' · Caixa e ticket parciais' if row.get("cash_invalid") else ''
        out.append(f'<article class="conc-rank-row" style="--tone:{color};--ink:{ink}">{body}<div class="conc-warning">{warning}</div></article>')
    return '<div class="conc-ranking" translate="no">'+''.join(out)+'</div>'

def summary_html(totals,summary,goals,monthly=True):
    def fields(values):return ''.join(f'<div><small>{l}</small><strong>{html.escape(v)}</strong></div>' for l,v in values)
    results=[("QIAs REALIZADOS",integer(totals["qias"])),("TROCAS REALIZADAS",integer(totals["changes"]))]
    if monthly:results += [("PROJEÇÃO QIAs",integer(sum(r["qias_projection"] for r in summary))),("PROJEÇÃO TROCAS",integer(sum(r["changes_projection"] for r in summary)))]
    goals_values=[]
    for key,label in (("qias","QIAs"),("changes","TROCAS")):
        goal=goals.get(key,0); goals_values.append((f"META {label}",integer(goal) if goal else "Não definida")); results.append((f"% META {label}",percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    values=dict(results); order=["QIAs REALIZADOS","% META QIAs"]+(["PROJEÇÃO QIAs"] if monthly else [])+["TROCAS REALIZADAS","% META TROCAS"]+(["PROJEÇÃO TROCAS"] if monthly else [])
    results=[(l,values[l]) for l in order]+[("TICKET MÉDIO GERAL",money(totals["ticket"]))]
    return '<div class="exec-compact-grid conc-summary" translate="no"><div class="exec-compact-card exec-performance"><div class="exec-compact-title">DESEMPENHO GERAL</div><div class="exec-performance-values conc-performance-values">'+fields(results)+'</div></div><div class="exec-compact-card"><div class="exec-compact-title">METAS MENSAIS GERAIS</div><div class="conc-summary-values">'+fields(goals_values)+'</div></div></div>'

def regimes_html(totals):
    return '<div class="conc-regimes">'+''.join(f'<div><small>{l}</small><b>{integer(totals[l])} QIAs</b><span>{percentage(Decimal(totals[l])*100/totals["qias"]) if totals["qias"] else "0%"}</span><em>Ticket Médio <b>{money(totals.get("regime_tickets",{}).get(l,0))}</b></em></div>' for l in ("NR","1 A 3","4 A 6"))+'</div>'

STYLE="""<style>
.conc-summary.exec-compact-grid{display:grid;grid-template-columns:2.4fr 1fr!important;gap:9px!important;margin:6px 0 10px!important}.conc-summary .exec-compact-card{min-height:0!important;padding:10px 12px!important;border-radius:12px!important}.conc-summary .conc-performance-values{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px 12px!important}.conc-summary .conc-performance-values>div:last-child{grid-column:1/-1}.conc-summary small{font-size:.52rem!important}.conc-summary strong{display:block;font-size:1.3rem!important;margin-top:4px}.conc-summary-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.conc-rank-row{border-radius:16px;background:var(--tone);color:var(--ink);padding:10px 12px 12px;margin:10px 0;box-shadow:0 5px 14px #0f172a20;overflow:hidden}.conc-hero{display:grid;grid-template-columns:auto minmax(220px,1fr) auto minmax(220px,520px) auto;align-items:center;gap:12px;margin-bottom:9px}.conc-rank-badge{width:42px;height:42px;border-radius:50%;background:#0004;display:grid;place-items:center;font-size:1.25rem;font-weight:950}.conc-name{font-size:1.55rem;font-weight:950;letter-spacing:.01em}.conc-goal-label{font-size:.68rem;white-space:nowrap}.conc-goalbar{min-width:0}.conc-goalbar .conc-progress{margin:0}.conc-goalbar .conc-progress-pct{display:none}.conc-goal-value{font-size:.83rem;font-weight:900;white-space:nowrap}
.conc-kpi-grid{display:grid;grid-template-columns:1.05fr 1.05fr 1.05fr 1fr 1.75fr 1.15fr 1.15fr;gap:6px}.conc-daily-grid{grid-template-columns:1.15fr 1fr 1fr 1fr 1.1fr 1.9fr}.conc-weekly-grid{grid-template-columns:1.1fr 1.1fr 1.05fr 1.05fr 1.7fr}.conc-kpi{background:#fffffff0;color:#0f2b63;border:1px solid #ffffffcc;border-radius:10px;padding:8px 10px;min-width:0;min-height:105px;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box}.conc-kpi small{font-size:.62rem!important;font-weight:900;color:#102c64!important;line-height:1.15}.conc-kpi>strong{font-size:1.72rem!important;line-height:1.02;margin:8px 0 3px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.conc-kpi>span{font-size:.67rem}.conc-kpi>span b{font-size:.74rem}.conc-kpi>em{font-size:.58rem;font-style:normal;margin-top:5px;color:#52657e;line-height:1.25}.conc-progress{height:9px;background:#cfe4f8;border-radius:999px;overflow:hidden;margin-top:auto}.conc-progress i{display:block;height:100%;border-radius:999px;background:#0ea5e9}.conc-progress-pct{font-size:.62rem!important;margin-top:2px;text-align:right}.conc-kpi.ticket>strong{font-size:1.7rem!important;color:#174bd6}.conc-kpi.award>strong{color:#067647}.conc-kpi.monthly>strong{color:#4c1d95}.conc-kpi.next-award{background:#fff7ed;color:#9a3412}.conc-kpi.next-award small{color:#9a3412!important}.conc-kpi.next-award>strong{color:#9a3412}.conc-kpi.regimes{padding:7px}.conc-reg-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:5px}.conc-reg-mini{border-radius:7px;padding:6px 4px;text-align:center;display:flex;flex-direction:column;gap:2px}.conc-reg-mini.nr{background:#fee2e2;color:#991b1b}.conc-reg-mini.r13{background:#dbeafe;color:#1d4ed8}.conc-reg-mini.r46{background:#dcfce7;color:#166534}.conc-reg-mini small{color:inherit!important;font-size:.55rem!important}.conc-reg-mini strong{font-size:1rem!important}.conc-reg-mini span,.conc-reg-mini em{font-size:.52rem!important;font-style:normal}.conc-warning{font-size:.52rem;margin-top:2px}.conc-regimes{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0}.conc-regimes>div{background:#fff;border:1px solid #e2e8f0;border-radius:9px;padding:6px 9px}.conc-regimes small,.conc-regimes span,.conc-regimes em{font-size:.62rem}.st-key-conc_refresh button{background:transparent!important;color:#64748b!important;border:0!important;min-height:26px!important;padding:0 5px!important}
@media(max-width:1100px){.conc-hero{grid-template-columns:auto 1fr auto}.conc-goal-label{grid-column:1/2}.conc-goalbar{grid-column:2/3}.conc-goal-value{grid-column:3/4}.conc-kpi-grid,.conc-daily-grid,.conc-weekly-grid{grid-template-columns:repeat(3,1fr)}.conc-kpi.regimes,.conc-kpi.next{grid-column:span 2}}
@media(max-width:700px){.conc-summary.exec-compact-grid{grid-template-columns:1fr!important}.conc-hero{grid-template-columns:auto 1fr auto;gap:7px}.conc-rank-badge{width:36px;height:36px;font-size:1rem}.conc-name{font-size:1.05rem}.conc-goal-label{font-size:.55rem}.conc-goal-value{font-size:.62rem}.conc-kpi-grid,.conc-daily-grid,.conc-weekly-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.conc-kpi{min-height:90px;padding:7px}.conc-kpi>strong{font-size:1.35rem!important}.conc-kpi.regimes,.conc-kpi.next{grid-column:1/-1}}
</style>"""

def _fit_image_text(draw,text,font,width):
    text=str(text)
    if draw.textlength(text,font=font)<=width:return text
    while text and draw.textlength(text+"…",font=font)>width:text=text[:-1]
    return text+"…"

def _daily_font(size,bold=False):
    from PIL import ImageFont
    paths=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for p in paths:
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()

def ranking_png(rows,view,period,totals,goals,synced_at):
    """Generate a phone-friendly portrait PNG matching the dashboard hierarchy."""
    from PIL import Image, ImageDraw

    width = 1080
    header_height = 150
    footer_height = 54
    row_height = 730 if view == "VISÃO GERAL" else 550 if view == "DIÁRIO" else 455
    gap = 18
    image_height = header_height + max(1, len(rows)) * (row_height + gap) + footer_height
    image = Image.new("RGB", (width, image_height), "#F8FAFC")
    draw = ImageDraw.Draw(image)

    navy = "#0F2B63"
    muted = "#64748B"
    border = "#DCE6F1"
    card_bg = "#FFFFFF"

    draw.text((34, 24), "PAINEL DE RESULTADOS · CONCILIAÇÃO", font=_daily_font(31, True), fill="#0F172A")
    draw.text((34, 68), period, font=_daily_font(21), fill=muted)
    draw.text((34, 105), "Ranking preparado para visualização no celular", font=_daily_font(14), fill=muted)

    def progress_bar(x, y, w, value, goal, fg="#0EA5E9", bg="#CFE4F8", height=12):
        p = _pct(value, goal)
        draw.rounded_rectangle((x, y, x + w, y + height), radius=height // 2, fill=bg)
        if p > 0:
            fill_w = max(height, w * p / 100)
            draw.rounded_rectangle((x, y, x + fill_w, y + height), radius=height // 2, fill=fg)
        return p

    def text_card(x, y, w, h, label, value, projection=None, note=None,
                  value_color=navy, progress=None, fill=card_bg):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline=border, width=1)
        draw.text((x + 16, y + 14), label.upper(), font=_daily_font(16, True), fill=navy)
        value_font = _daily_font(34, True)
        draw.text((x + 16, y + 46), _fit_image_text(draw, value, value_font, w - 32), font=value_font, fill=value_color)
        cursor = y + 92
        if projection is not None:
            projection_text = "Projeção: " + str(projection)
            draw.text((x + 16, cursor), _fit_image_text(draw, projection_text, _daily_font(17), w - 32), font=_daily_font(17), fill="#52657E")
            cursor += 27
        if note:
            draw.text((x + 16, cursor), _fit_image_text(draw, note, _daily_font(15), w - 32), font=_daily_font(15), fill="#52657E")
        if progress:
            progress_bar(x + 16, y + h - 26, w - 32, progress[0], progress[1])

    def hero(y, row, pos, label, goal, value=None):
        value = row.get("qias", 0) if value is None else value
        _, tone, ink = PALETTE[row.get("color", daily_color(row.get("qias", 0)))]
        draw.rounded_rectangle((18, y, width - 18, y + row_height), radius=28, fill=tone)
        draw.ellipse((38, y + 24, 94, y + 80), fill="#00000044")
        draw.text((66, y + 52), f"{pos}º", font=_daily_font(21, True), fill=ink, anchor="mm")
        draw.text((112, y + 25), _fit_image_text(draw, row["name"], _daily_font(29, True), 470), font=_daily_font(29, True), fill=ink)
        draw.text((112, y + 63), f"{label}: {integer(goal)} QIAs", font=_daily_font(16, True), fill=ink)
        bar_x = 600
        bar_w = 270
        progress_bar(bar_x, y + 38, bar_w, value, goal, fg="#FFFFFF", bg="#DCEBFA", height=14)
        draw.text((892, y + 28), f"{integer(value)} / {integer(goal)}", font=_daily_font(18, True), fill=ink)
        draw.text((892, y + 53), f"{_pct(value, goal):.0f}%", font=_daily_font(15, True), fill=ink)
        return tone, ink

    def regimes_card(x, y, w, h, row, projections):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=card_bg, outline=border, width=1)
        draw.text((x + 16, y + 14), "QIAs POR RÉGUA", font=_daily_font(16, True), fill=navy)
        mini_gap = 8
        mini_w = (w - 32 - mini_gap * 2) / 3
        mini_top = y + 48
        mini_h = h - 64
        specs = (("NR", "NR", "#FEE2E2", "#991B1B"), ("1 a 3", "1 A 3", "#DBEAFE", "#1D4ED8"), ("4 a 6", "4 A 6", "#DCFCE7", "#166534"))
        for j, (label, key, bg, fg) in enumerate(specs):
            mx = x + 16 + j * (mini_w + mini_gap)
            draw.rounded_rectangle((mx, mini_top, mx + mini_w, mini_top + mini_h), radius=12, fill=bg)
            draw.text((mx + mini_w / 2, mini_top + 12), label, font=_daily_font(14, True), fill=fg, anchor="ma")
            draw.text((mx + mini_w / 2, mini_top + 48), integer(row.get(key, 0)), font=_daily_font(30, True), fill=fg, anchor="ma")
            cursor = mini_top + 90
            if projections:
                draw.text((mx + mini_w / 2, cursor), "Proj. " + integer(_project_value(row, key, "qias")), font=_daily_font(13), fill=fg, anchor="ma")
                cursor += 25
            draw.text((mx + mini_w / 2, cursor), "TM " + money(row.get("regime_tickets", {}).get(key, 0)), font=_daily_font(12), fill=fg, anchor="ma")

    def two_cols():
        left = 36
        gap_x = 12
        card_w = (width - 72 - gap_x) / 2
        return left, card_w, gap_x

    def three_cols():
        left = 36
        gap_x = 12
        card_w = (width - 72 - gap_x * 2) / 3
        return left, card_w, gap_x

    for i, row in enumerate(rows):
        y = header_height + i * (row_height + gap)
        if view == "VISÃO GERAL":
            qgoal = row.get("qias_goal", 0)
            cgoal = row.get("changes_goal", 0)
            hero(y, row, i + 1, "Meta individual", qgoal)
            left, cw, gx = two_cols()
            top = y + 104
            h = 150
            text_card(left, top, cw, h, "QIAs", integer(row["qias"]), integer(row["qias_projection"]), progress=(row["qias"], qgoal))
            text_card(left + cw + gx, top, cw, h, "Ticket Médio Geral", money(row["ticket"]), value_color="#174BD6")
            top2 = top + h + 12
            text_card(left, top2, cw, h, "Trocas Crédito", integer(row["credit"]), integer(_project_value(row, "credit", "changes")), progress=(row["credit"], cgoal))
            text_card(left + cw + gx, top2, cw, h, "Trocas Neoenergia", integer(row["neo"]), integer(_project_value(row, "neo", "changes")), progress=(row["neo"], cgoal))
            top3 = top2 + h + 12
            regimes_card(left, top3, width - 72, 160, row, True)
            top4 = top3 + 172
            award_w = (width - 72 - gx) / 2
            text_card(left, top4, award_w, 112, "Prêmio Semanal", money(row.get("weekly_award", 0)), money(row.get("weekly_projection", row.get("weekly_award", 0))), value_color="#067647")
            text_card(left + award_w + gx, top4, award_w, 112, "Premiação Mensal", money(row.get("projected_award", 0)), note="projetado", value_color="#4C1D95")
        elif view == "DIÁRIO":
            hero(y, row, i + 1, "Referência diária", 30)
            left, cw, gx = two_cols()
            top = y + 104
            h = 132
            text_card(left, top, cw, h, "QIAs hoje", integer(row["qias"]), note=f'{integer(row.get("week_qias", 0))} na semana · {integer(row.get("month_qias", 0))} no mês', progress=(row["qias"], 30))
            text_card(left + cw + gx, top, cw, h, "Ticket Médio", money(row["ticket"]), value_color="#174BD6")
            top2 = top + h + 12
            left3, cw3, gx3 = three_cols()
            text_card(left3, top2, cw3, 118, "Trocas hoje", integer(row["changes"]))
            text_card(left3 + cw3 + gx3, top2, cw3, 118, "Crédito", integer(row["credit"]))
            text_card(left3 + 2 * (cw3 + gx3), top2, cw3, 118, "Neoenergia", integer(row["neo"]))
            regimes_card(36, top2 + 130, width - 72, 155, row, False)
        else:
            qgoal = row.get("weekly_qias_goal", 0)
            cgoal = row.get("weekly_changes_goal", 0)
            hero(y, row, i + 1, "Meta inicial da semana", qgoal)
            left, cw, gx = two_cols()
            top = y + 104
            h = 138
            text_card(left, top, cw, h, "QIAs", integer(row["qias"]), integer(row["qias_projection"]), progress=(row["qias"], qgoal))
            text_card(left + cw + gx, top, cw, h, "Trocas", integer(row["changes"]), integer(row["changes_projection"]), progress=(row["changes"], cgoal))
            top2 = top + h + 12
            left3, cw3, gx3 = three_cols()
            text_card(left3, top2, cw3, 132, "Prêmio conquistado", money(row.get("earned_award", 0)), value_color="#067647")
            text_card(left3 + cw3 + gx3, top2, cw3, 132, "Prêmio projetado", money(row.get("award", 0)), value_color="#4C1D95")
            remain_q = int(row.get("qias_remaining", 0) or 0)
            remain_c = int(row.get("changes_remaining", 0) or 0)
            if row.get("next_award", 0):
                next_value = money(row.get("next_award", 0))
                remain = f"Faltam {remain_q} QIAs e {remain_c} trocas"
            else:
                next_value = "Máximo"
                remain = "Faixa máxima atingida"
            text_card(left3 + 2 * (cw3 + gx3), top2, cw3, 132, "Próximo prêmio", next_value, note=remain, value_color="#9A3412", fill="#FFF7ED")

    if not rows:
        draw.text((40, 180), "Nenhum conciliador habilitado.", font=_daily_font(28), fill="#475569")
    draw.text((34, image.height - 36), f"Atualizado em {synced_at:%d/%m/%Y %H:%M}", font=_daily_font(17), fill=muted)
    output = io.BytesIO()
    image.save(output, "PNG", optimize=True)
    return output.getvalue()
