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
    except:return 0

def _progress(value,goal,extra=""):
    p=_pct(value,goal)
    return f'<div class="conc-progress"><i style="width:{p:.1f}%"></i></div><b class="conc-progress-pct">{p:.0f}%</b>{extra}'

def _metric_card(label,value,projection=None,progress=None,accent="",cls=""):
    sub=f'<span>Projeção: <b>{html.escape(str(projection))}</b></span>' if projection is not None else ''
    bar=_progress(*progress) if progress else ''
    return f'<div class="conc-kpi {cls} {accent}"><small>{html.escape(label)}</small><strong>{html.escape(str(value))}</strong>{sub}{bar}</div>'

def row_metrics(row,view):
    if view=="VISÃO GERAL":
        return [("QIAs",integer(row["qias"])),("PROJEÇÃO QIAs",integer(row["qias_projection"])),("TROCAS",integer(row["changes"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("MENSAL PROJETADA",money(row["projected_award"]))]
    m=[("QIAs",integer(row["qias"])),("TROCAS",integer(row["changes"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("CAIXA",money(row["cash"]))]
    if view=="DIÁRIO":m += [("QIAs NA SEMANA",integer(row.get("week_qias",0))),("QIAs NO MÊS",integer(row.get("month_qias",0)))]
    else:m += [("PROJEÇÃO QIAs",integer(row["qias_projection"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("PRÊMIO CONQUISTADO",money(row.get("closed_award",0))),("PRÊMIO PROJETADO",money(row["award"])),("FAIXA ATUAL",str(row["tier"])+"ª" if row["tier"] else "—"),("FAIXA PROJETADA",str(row["projected_tier"])+"ª" if row["projected_tier"] else "—")]
    return m

def ranking_html(rows,view):
    out=[]
    for pos,row in enumerate(rows,1):
        _,color,ink=PALETTE[row["color"]]
        if view=="VISÃO GERAL":
            qgoal=row.get("qias_goal",0); cgoal=row.get("changes_goal",0)
            credit_proj=integer(_project_value(row,"credit","changes")); neo_proj=integer(_project_value(row,"neo","changes"))
            qproj=integer(row["qias_projection"])
            head=(f'<div class="conc-hero"><div class="conc-rank-badge">{pos}º</div><div class="conc-name">{html.escape(row["name"])}</div>'
                  f'<div class="conc-goal-label">Meta individual: <b>{integer(qgoal)} QIAs</b></div><div class="conc-goalbar">{_progress(row["qias"],qgoal)}</div>'
                  f'<div class="conc-goal-value">{integer(row["qias"])} / {integer(qgoal)} ({_pct(row["qias"],qgoal):.0f}%)</div></div>')
            cards=[
                _metric_card("QIAs",integer(row["qias"]),qproj,(row["qias"],qgoal),cls="qias"),
                _metric_card("Trocas Crédito",integer(row["credit"]),credit_proj,(row["credit"],cgoal),cls="credit"),
                _metric_card("Trocas Neoenergia",integer(row["neo"]),neo_proj,(row["neo"],cgoal),cls="neo"),
                _metric_card("Ticket Médio Geral",money(row["ticket"]),cls="ticket"),
            ]
            regimes=[]
            for label,accent in (("NR","nr"),("1 a 3","r13"),("4 a 6","r46")):
                key="1 A 3" if label=="1 a 3" else "4 A 6" if label=="4 a 6" else label
                regimes.append(f'<div class="conc-reg-mini {accent}"><small>{label}</small><strong>{integer(row[key])}</strong><span>Proj.: {integer(_project_value(row,key,"qias"))}</span><em>TM: <b>{money(row.get("regime_tickets",{}).get(key,0))}</b></em></div>')
            cards.append('<div class="conc-kpi regimes"><small>QIAs por régua</small><div class="conc-reg-grid">'+''.join(regimes)+'</div></div>')
            weekly=row.get("weekly_award",0); weekly_proj=row.get("weekly_projection",weekly)
            cards.append(_metric_card("Prêmio Semanal",money(weekly),money(weekly_proj),(weekly,weekly_proj or 1),accent="award",cls="weekly"))
            cards.append(_metric_card("Premiação Mensal",money(row.get("projected_award",0)),"(projetado)",accent="monthly",cls="monthly"))
            body=head+'<div class="conc-kpi-grid">'+''.join(cards)+'</div>'
        else:
            body=f'<div class="conc-simple-head"><b>{pos}º · {html.escape(row["name"])}</b></div><div class="conc-indicators">'+''.join(f'<span><strong>{html.escape(v)}</strong><small>{html.escape(l)}</small></span>' for l,v in row_metrics(row,view))+'</div>'
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
.conc-rank-row{border-radius:16px;background:var(--tone);color:var(--ink);padding:10px 12px 12px;margin:10px 0;box-shadow:0 5px 14px #0f172a20;overflow:hidden}.conc-hero{display:grid;grid-template-columns:auto minmax(260px,1fr) auto minmax(250px,520px) auto;align-items:center;gap:12px;margin-bottom:9px}.conc-rank-badge{width:42px;height:42px;border-radius:50%;background:#0004;display:grid;place-items:center;font-size:1.25rem;font-weight:950}.conc-name{font-size:1.55rem;font-weight:950;letter-spacing:.01em}.conc-goal-label{font-size:.68rem;white-space:nowrap}.conc-goalbar{min-width:0}.conc-goalbar .conc-progress{margin:0}.conc-goalbar .conc-progress-pct{display:none}.conc-goal-value{font-size:.83rem;font-weight:900;white-space:nowrap}
.conc-kpi-grid{display:grid;grid-template-columns:1.05fr 1.05fr 1.05fr 1fr 1.75fr 1.15fr 1.15fr;gap:6px}.conc-kpi{background:#fffffff0;color:#0f2b63;border:1px solid #ffffffcc;border-radius:10px;padding:8px 10px;min-width:0;min-height:105px;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box}.conc-kpi small{font-size:.62rem!important;font-weight:900;color:#102c64!important;line-height:1.15}.conc-kpi>strong{font-size:1.72rem!important;line-height:1.02;margin:8px 0 3px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.conc-kpi>span{font-size:.67rem}.conc-kpi>span b{font-size:.74rem}.conc-progress{height:9px;background:#cfe4f8;border-radius:999px;overflow:hidden;margin-top:auto}.conc-progress i{display:block;height:100%;border-radius:999px;background:#0ea5e9}.conc-progress-pct{font-size:.62rem!important;margin-top:2px;text-align:right}.conc-kpi.ticket>strong{font-size:1.7rem!important;color:#174bd6}.conc-kpi.award>strong{color:#067647}.conc-kpi.monthly>strong{color:#4c1d95}.conc-kpi.monthly{text-align:center}.conc-kpi.monthly>span{margin-top:4px}.conc-kpi.regimes{padding:7px}.conc-reg-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:5px}.conc-reg-mini{border-radius:7px;padding:6px 4px;text-align:center;display:flex;flex-direction:column;gap:2px}.conc-reg-mini.nr{background:#fee2e2;color:#991b1b}.conc-reg-mini.r13{background:#dbeafe;color:#1d4ed8}.conc-reg-mini.r46{background:#dcfce7;color:#166534}.conc-reg-mini small{color:inherit!important;font-size:.55rem!important}.conc-reg-mini strong{font-size:1rem!important}.conc-reg-mini span,.conc-reg-mini em{font-size:.52rem!important;font-style:normal}.conc-warning{font-size:.52rem;margin-top:2px}.conc-simple-head{font-size:.85rem;font-weight:900;margin-bottom:6px}.conc-indicators{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px}.conc-indicators span{text-align:center;border-left:1px solid currentColor;padding:4px}.conc-indicators strong{display:block;font-size:.86rem}.conc-indicators small{font-size:.52rem}.conc-regimes{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0}.conc-regimes>div{background:#fff;border:1px solid #e2e8f0;border-radius:9px;padding:6px 9px}.conc-regimes small,.conc-regimes span,.conc-regimes em{font-size:.62rem}.st-key-conc_refresh button{background:transparent!important;color:#64748b!important;border:0!important;min-height:26px!important;padding:0 5px!important}
@media(max-width:1100px){.conc-hero{grid-template-columns:auto 1fr auto}.conc-goal-label{grid-column:1/2}.conc-goalbar{grid-column:2/3}.conc-goal-value{grid-column:3/4}.conc-kpi-grid{grid-template-columns:repeat(4,1fr)}.conc-kpi.regimes{grid-column:span 2}}
@media(max-width:700px){.conc-summary.exec-compact-grid{grid-template-columns:1fr!important}.conc-hero{grid-template-columns:auto 1fr auto;gap:7px}.conc-rank-badge{width:36px;height:36px;font-size:1rem}.conc-name{font-size:1.05rem}.conc-goal-label{font-size:.55rem}.conc-goal-value{font-size:.62rem}.conc-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.conc-kpi{min-height:90px;padding:7px}.conc-kpi>strong{font-size:1.35rem!important}.conc-kpi.regimes{grid-column:1/-1}.conc-kpi.weekly,.conc-kpi.monthly{grid-column:span 1}.conc-indicators{grid-template-columns:repeat(2,1fr)}}
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

def _draw_daily_ordinal(draw,x,y,position,ink):draw.text((x,y),f"{position}º",font=_daily_font(24,True),fill=ink,anchor="mm")
def _draw_daily_status_icon(draw,x,y,label):
    colors={"Azul":"#2563EB","Verde":"#16A34A","Amarelo":"#EAB308","Laranja":"#EA580C","Vermelho":"#DC2626"};draw.ellipse((x-12,y-12,x+12,y+12),fill=colors.get(label,"#64748B"))

def ranking_png(rows,view,period,totals,goals,synced_at):
    from PIL import Image,ImageDraw
    team_height=180; row_height=430 if view=="VISÃO GERAL" else 360
    image=Image.new("RGB",(1080,225+team_height+max(1,len(rows))*(row_height+14)),"white");draw=ImageDraw.Draw(image)
    draw.text((24,22),"PAINEL DE RESULTADOS · CONCILIAÇÃO",font=_daily_font(34,True),fill="#0F172A");draw.text((24,68),period,font=_daily_font(24),fill="#475569")
    team=[("QIAs",integer(totals["qias"])),("TROCAS",integer(totals["changes"]))]
    for key,label in (("qias","QIAs"),("changes","TROCAS")):
        goal=goals.get(key,0);team.append((f"% META {label}",percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    for j,(label,value) in enumerate(team):
        x,y=38+(j%4)*254,112+(j//4)*65;draw.text((x,y),_fit_image_text(draw,value,_daily_font(27,True),240),font=_daily_font(27,True),fill="#0F172A");draw.text((x,y+33),label,font=_daily_font(16),fill="#64748B")
    for i,row in enumerate(rows):
        y=167+team_height+i*(row_height+14);_,color,ink=PALETTE[row.get("color",daily_color(row["qias"]))];draw.rounded_rectangle((16,y,1064,y+row_height),radius=24,fill=color)
        _draw_daily_ordinal(draw,48,y+34,i+1,ink);draw.text((82,y+15),_fit_image_text(draw,row["name"],_daily_font(31,True),620),font=_daily_font(31,True),fill=ink)
        if view=="VISÃO GERAL":
            qgoal=row.get("qias_goal",0);draw.text((720,y+20),f'Meta: {integer(qgoal)} QIAs · {integer(row["qias"])} / {integer(qgoal)} ({_pct(row["qias"],qgoal):.0f}%)',font=_daily_font(17,True),fill=ink)
            items=[("QIAs",integer(row["qias"]),integer(row["qias_projection"])),("TROCAS CRÉDITO",integer(row["credit"]),integer(_project_value(row,"credit","changes"))),("TROCAS NEO",integer(row["neo"]),integer(_project_value(row,"neo","changes"))),("TICKET MÉDIO",money(row["ticket"]),None),("NR",integer(row["NR"]),integer(_project_value(row,"NR","qias"))),("1 A 3",integer(row["1 A 3"]),integer(_project_value(row,"1 A 3","qias"))),("4 A 6",integer(row["4 A 6"]),integer(_project_value(row,"4 A 6","qias"))),("PRÊMIO SEMANAL",money(row.get("weekly_award",0)),money(row.get("weekly_projection",row.get("weekly_award",0)))),("PREMIAÇÃO MENSAL",money(row.get("projected_award",0)),None)]
            for j,(label,val,proj) in enumerate(items):
                col,line=j%3,j//3;x,top=38+col*336,y+70+line*112;draw.rounded_rectangle((x,top,x+322,top+98),radius=12,fill="#FFFFFFE8" if False else None,outline=ink,width=1);draw.text((x+10,top+8),label,font=_daily_font(14,True),fill=ink);draw.text((x+10,top+30),_fit_image_text(draw,val,_daily_font(26,True),300),font=_daily_font(26,True),fill=ink)
                if proj is not None:draw.text((x+10,top+65),"Projeção: "+str(proj),font=_daily_font(14),fill=ink)
        else:
            for j,(label,value) in enumerate(row_metrics(row,view)):
                x,top=38+(j%4)*254,y+64+(j//4)*82;draw.text((x,top),_fit_image_text(draw,value,_daily_font(27,True),232),font=_daily_font(27,True),fill=ink);draw.text((x,top+40),label,font=_daily_font(15),fill=ink)
    if not rows:draw.text((40,205+team_height),"Nenhum conciliador habilitado.",font=_daily_font(28),fill="#475569")
    footer=f"Atualizado em {synced_at:%d/%m/%Y %H:%M}";draw.text((26,image.height-34),footer,font=_daily_font(20),fill="#475569");output=io.BytesIO();image.save(output,"PNG");return output.getvalue()
