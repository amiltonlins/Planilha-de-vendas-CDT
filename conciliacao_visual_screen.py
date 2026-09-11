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
    if view=="DIÁRIO": return [("QIAs HOJE",integer(row["qias"])),("TROCAS HOJE",integer(row["changes"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("QIAs NA SEMANA",integer(row.get("week_qias",0))),("QIAs NO MÊS",integer(row.get("month_qias",0)))]
    if view=="SEMANAL": return [("QIAs",integer(row["qias"])),("PROJEÇÃO QIAs",integer(row["qias_projection"])),("TROCAS",integer(row["changes"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("PRÊMIO CONQUISTADO",money(row.get("earned_award",0))),("PRÊMIO PROJETADO",money(row.get("award",0))),("PRÓXIMO PRÊMIO",money(row.get("next_award",0)))]
    return [("QIAs",integer(row["qias"])),("PROJEÇÃO QIAs",integer(row["qias_projection"])),("TROCAS",integer(row["changes"])),("PROJEÇÃO TROCAS",integer(row["changes_projection"])),("CRÉDITO",integer(row["credit"])),("NEOENERGIA",integer(row["neo"])),("TICKET MÉDIO",money(row["ticket"])),("MENSAL PROJETADA",money(row["projected_award"]))]

def ranking_html(rows,view):
    out=[]
    for pos,row in enumerate(rows,1):
        _,color,ink=PALETTE[row["color"]]
        if view=="VISÃO GERAL":
            qgoal=row.get("qias_goal",0); cgoal=row.get("changes_goal",0); head=_hero(pos,row,"Meta individual",qgoal)
            cards=[_metric_card("QIAs",integer(row["qias"]),integer(row["qias_projection"]),(row["qias"],qgoal),cls="qias"),_metric_card("Trocas Crédito",integer(row["credit"]),integer(_project_value(row,"credit","changes")),(row["credit"],cgoal),cls="credit"),_metric_card("Trocas Neoenergia",integer(row["neo"]),integer(_project_value(row,"neo","changes")),(row["neo"],cgoal),cls="neo"),_metric_card("Ticket Médio Geral",money(row["ticket"]),cls="ticket"),_regimes_card(row,True),_metric_card("Prêmio Semanal",money(row.get("weekly_award",0)),money(row.get("weekly_projection",row.get("weekly_award",0))),accent="award",cls="weekly"),_metric_card("Premiação Mensal",money(row.get("projected_award",0)),accent="monthly",cls="monthly",note="projetado")]
            body=head+'<div class="conc-kpi-grid">'+''.join(cards)+'</div>'
        elif view=="DIÁRIO":
            head=_hero(pos,row,"Referência diária",30); qnote=f'{integer(row.get("week_qias",0))} na semana · {integer(row.get("month_qias",0))} no mês'
            cards=[_metric_card("QIAs hoje",integer(row["qias"]),progress=(row["qias"],30),cls="qias",note=qnote),_metric_card("Trocas hoje",integer(row["changes"]),cls="changes"),_metric_card("Trocas Crédito",integer(row["credit"]),cls="credit"),_metric_card("Trocas Neoenergia",integer(row["neo"]),cls="neo"),_metric_card("Ticket Médio",money(row["ticket"]),cls="ticket"),_regimes_card(row,False)]
            body=head+'<div class="conc-kpi-grid conc-daily-grid">'+''.join(cards)+'</div>'
        else:
            qgoal=row.get("weekly_qias_goal",0); head=_hero(pos,row,"Meta inicial da semana",qgoal); remain_q=int(row.get("qias_remaining",0) or 0); remain_c=int(row.get("changes_remaining",0) or 0)
            if row.get("next_award",0): remain=f'Faltam {remain_q} QIAs e {remain_c} trocas'; next_value=money(row.get("next_award",0))
            else: remain="Faixa máxima atingida"; next_value="Máximo"
            cards=[_metric_card("QIAs",integer(row["qias"]),integer(row["qias_projection"]),(row["qias"],qgoal),cls="qias"),_metric_card("Trocas",integer(row["changes"]),integer(row["changes_projection"]),(row["changes"],row.get("weekly_changes_goal",0)),cls="changes"),_metric_card("Prêmio conquistado",money(row.get("earned_award",0)),accent="award",cls="weekly"),_metric_card("Prêmio projetado",money(row.get("award",0)),accent="monthly",cls="monthly"),_metric_card("Próximo prêmio",next_value,accent="next-award",cls="next",note=remain)]
            body=head+'<div class="conc-kpi-grid conc-weekly-grid">'+''.join(cards)+'</div>'
        warning=' · Caixa e ticket parciais' if row.get("cash_invalid") else ''; out.append(f'<article class="conc-rank-row" style="--tone:{color};--ink:{ink}">{body}<div class="conc-warning">{warning}</div></article>')
    return '<div class="conc-ranking" translate="no">'+''.join(out)+'</div>'

def summary_html(totals,summary,goals,monthly=True):
    def fields(values):return ''.join(f'<div><small>{l}</small><strong>{html.escape(v)}</strong></div>' for l,v in values)
    results=[("QIAs REALIZADOS",integer(totals["qias"])),("TROCAS REALIZADAS",integer(totals["changes"]))]
    if monthly:results += [("PROJEÇÃO QIAs",integer(sum(r["qias_projection"] for r in summary))),("PROJEÇÃO TROCAS",integer(sum(r["changes_projection"] for r in summary)))]
    goals_values=[]
    for key,label in (("qias","QIAs"),("changes","TROCAS")):
        goal=goals.get(key,0); goals_values.append((f"META {label}",integer(goal) if goal else "Não definida")); results.append((f"% META {label}",percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    values=dict(results); order=["QIAs REALIZADOS","% META QIAs"]+(["PROJEÇÃO QIAs"] if monthly else [])+["TROCAS REALIZADAS","% META TROCAS"]+(["PROJEÇÃO TROCAS"] if monthly else []); results=[(l,values[l]) for l in order]+[("TICKET MÉDIO GERAL",money(totals["ticket"]))]
    return '<div class="exec-compact-grid conc-summary" translate="no"><div class="exec-compact-card exec-performance"><div class="exec-compact-title">DESEMPENHO GERAL</div><div class="exec-performance-values conc-performance-values">'+fields(results)+'</div></div><div class="exec-compact-card"><div class="exec-compact-title">METAS MENSAIS GERAIS</div><div class="conc-summary-values">'+fields(goals_values)+'</div></div></div>'

def regimes_html(totals):
    return '<div class="conc-regimes">'+''.join(f'<div><small>{l}</small><b>{integer(totals[l])} QIAs</b><span>{percentage(Decimal(totals[l])*100/totals["qias"]) if totals["qias"] else "0%"}</span><em>Ticket Médio <b>{money(totals.get("regime_tickets",{}).get(l,0))}</b></em></div>' for l in ("NR","1 A 3","4 A 6"))+'</div>'

STYLE="""<style>
.conc-summary.exec-compact-grid{display:grid;grid-template-columns:2.4fr 1fr!important;gap:9px!important;margin:6px 0 10px!important}.conc-summary .exec-compact-card{min-height:0!important;padding:10px 12px!important;border-radius:12px!important}.conc-summary .conc-performance-values{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px 12px!important}.conc-summary .conc-performance-values>div:last-child{grid-column:1/-1}.conc-summary small{font-size:.52rem!important}.conc-summary strong{display:block;font-size:1.3rem!important;margin-top:4px}.conc-summary-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.conc-rank-row{border-radius:16px;background:var(--tone);color:var(--ink);padding:10px 12px 12px;margin:10px 0;box-shadow:0 5px 14px #0f172a20;overflow:hidden}.conc-hero{display:grid;grid-template-columns:auto minmax(220px,1fr) auto minmax(220px,520px) auto;align-items:center;gap:12px;margin-bottom:9px}.conc-rank-badge{width:42px;height:42px;border-radius:50%;background:#0004;display:grid;place-items:center;font-size:1.25rem;font-weight:950}.conc-name{font-size:1.55rem;font-weight:950;letter-spacing:.01em}.conc-goal-label{font-size:.68rem;white-space:nowrap}.conc-goalbar{min-width:0}.conc-goalbar .conc-progress{margin:0}.conc-goalbar .conc-progress-pct{display:none}.conc-goal-value{font-size:.83rem;font-weight:900;white-space:nowrap}.conc-kpi-grid{display:grid;grid-template-columns:1.05fr 1.05fr 1.05fr 1fr 1.75fr 1.15fr 1.15fr;gap:6px}.conc-daily-grid{grid-template-columns:1.15fr 1fr 1fr 1fr 1.1fr 1.9fr}.conc-weekly-grid{grid-template-columns:1.1fr 1.1fr 1.05fr 1.05fr 1.7fr}.conc-kpi{background:#fffffff0;color:#0f2b63;border:1px solid #ffffffcc;border-radius:10px;padding:8px 10px;min-width:0;min-height:105px;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box}.conc-kpi small{font-size:.62rem!important;font-weight:900;color:#102c64!important;line-height:1.15}.conc-kpi>strong{font-size:1.72rem!important;line-height:1.02;margin:8px 0 3px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.conc-kpi>span{font-size:.67rem}.conc-kpi>span b{font-size:.74rem}.conc-kpi>em{font-size:.58rem;font-style:normal;margin-top:5px;color:#52657e;line-height:1.25}.conc-progress{height:9px;background:#cfe4f8;border-radius:999px;overflow:hidden;margin-top:auto}.conc-progress i{display:block;height:100%;border-radius:999px;background:#0ea5e9}.conc-progress-pct{font-size:.62rem!important;margin-top:2px;text-align:right}.conc-kpi.ticket>strong{font-size:1.7rem!important;color:#174bd6}.conc-kpi.award>strong{color:#067647}.conc-kpi.monthly>strong{color:#4c1d95}.conc-kpi.next-award{background:#fff7ed;color:#9a3412}.conc-kpi.next-award small{color:#9a3412!important}.conc-kpi.next-award>strong{color:#9a3412}.conc-kpi.regimes{padding:7px}.conc-reg-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:5px}.conc-reg-mini{border-radius:7px;padding:6px 4px;text-align:center;display:flex;flex-direction:column;gap:2px}.conc-reg-mini.nr{background:#fee2e2;color:#991b1b}.conc-reg-mini.r13{background:#dbeafe;color:#1d4ed8}.conc-reg-mini.r46{background:#dcfce7;color:#166534}.conc-reg-mini small{color:inherit!important;font-size:.55rem!important}.conc-reg-mini strong{font-size:1rem!important}.conc-reg-mini span,.conc-reg-mini em{font-size:.52rem!important;font-style:normal}.conc-warning{font-size:.52rem;margin-top:2px}.conc-regimes{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0}.conc-regimes>div{background:#fff;border:1px solid #e2e8f0;border-radius:9px;padding:6px 9px}.conc-regimes small,.conc-regimes span,.conc-regimes em{font-size:.62rem}.st-key-conc_refresh button{background:transparent!important;color:#64748b!important;border:0!important;min-height:26px!important;padding:0 5px!important}@media(max-width:1100px){.conc-hero{grid-template-columns:auto 1fr auto}.conc-goal-label{grid-column:1/2}.conc-goalbar{grid-column:2/3}.conc-goal-value{grid-column:3/4}.conc-kpi-grid,.conc-daily-grid,.conc-weekly-grid{grid-template-columns:repeat(3,1fr)}.conc-kpi.regimes,.conc-kpi.next{grid-column:span 2}}@media(max-width:700px){.conc-summary.exec-compact-grid{grid-template-columns:1fr!important}.conc-hero{grid-template-columns:auto 1fr auto;gap:7px}.conc-rank-badge{width:36px;height:36px;font-size:1rem}.conc-name{font-size:1.05rem}.conc-goal-label{font-size:.55rem}.conc-goal-value{font-size:.62rem}.conc-kpi-grid,.conc-daily-grid,.conc-weekly-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.conc-kpi{min-height:90px;padding:7px}.conc-kpi>strong{font-size:1.35rem!important}.conc-kpi.regimes,.conc-kpi.next{grid-column:1/-1}}</style>"""

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
    """Compact portrait export inspired by the commercial ranking, optimized for a phone screen."""
    from PIL import Image,ImageDraw
    W=1080; margin=28; green="#075E3A"; bg="#F4F8FC"; navy="#17345F"; muted="#64748B"; line="#D8E3EE"; white="#FFFFFF"
    n=max(1,len(rows)); row_h=112 if view=="VISÃO GERAL" else 104; header_h=300; summary_h=190 if view=="VISÃO GERAL" else 112; goals_h=150; footer_h=70
    H=header_h+summary_h+n*(row_h+8)+goals_h+footer_h
    image=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(image)
    def f(sz,b=False): return _daily_font(sz,b)
    def txt(x,y,s,sz=18,color=navy,b=False,anchor=None,maxw=None):
        font=f(sz,b); s=str(s); s=_fit_image_text(d,s,font,maxw) if maxw else s; d.text((x,y),s,font=font,fill=color,anchor=anchor)
    def box(x,y,w,h,fill=white,r=14,outline=None): d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=outline)
    def prog(x,y,w,val,goal,fg="#0EA5E9"):
        p=_pct(val,goal); d.rounded_rectangle((x,y,x+w,y+9),radius=5,fill="#CFE4F8"); fw=max(9,w*p/100) if p else 0
        if fw:d.rounded_rectangle((x,y,x+fw,y+9),radius=5,fill=fg)
        return p
    # header
    d.rectangle((0,0,W,230),fill=green); txt(42,28,"CARTÃO DE TODOS · AFOGADOS",24,"#B9E7C9",True); title={"VISÃO GERAL":"RANKING DE CONCILIAÇÃO - GERAL","DIÁRIO":"RANKING DE CONCILIAÇÃO - HOJE","SEMANAL":"RANKING DE CONCILIAÇÃO - SEMANA"}[view]; txt(42,67,title,40,white,True,maxw=760); txt(42,119,period,20,"#D6F1E1",True); txt(W-42,34,synced_at.strftime("%d/%m/%Y"),26,white,True,"ra"); txt(W-42,72,"Atualizado às "+synced_at.strftime("%H:%M"),14,"#D6F1E1",False,"ra")
    # headline KPIs
    kpis=[]
    if view=="VISÃO GERAL": kpis=[("QIAs DO MÊS",integer(totals.get("qias",0)),"#0B6B47"),("TROCAS TOTAL",integer(totals.get("changes",0)),"#174BD6"),("TROCAS CRÉDITO",integer(totals.get("credit",0)),"#6D28D9"),("TROCAS NEOENERGIA",integer(totals.get("neo",0)),"#C2410C"),("TICKET MÉDIO",money(totals.get("ticket",0)),navy)]
    elif view=="DIÁRIO": kpis=[("QIAs HOJE",integer(totals.get("qias",0)),"#0B6B47"),("TROCAS HOJE",integer(totals.get("changes",0)),"#174BD6"),("CRÉDITO",integer(totals.get("credit",0)),"#6D28D9"),("NEOENERGIA",integer(totals.get("neo",0)),"#C2410C"),("TICKET MÉDIO",money(totals.get("ticket",0)),navy)]
    else: kpis=[("QIAs SEMANA",integer(totals.get("qias",0)),"#0B6B47"),("TROCAS SEMANA",integer(totals.get("changes",0)),"#174BD6"),("CONCILIADORES",integer(len(rows)),navy)]
    gap=10; kw=(W-2*margin-gap*(len(kpis)-1))/len(kpis); ky=152
    for i,(lab,val,col) in enumerate(kpis): x=margin+i*(kw+gap); box(x,ky,kw,88,white,12); txt(x+kw/2,ky+17,lab,13,muted,True,"ma",kw-14); txt(x+kw/2,ky+47,val,25,col,True,"ma",kw-14)
    y=255
    # summary band like generated reference
    if view=="VISÃO GERAL":
        left_w=545; box(margin,y,left_w,summary_h-18,white,14,line); txt(margin+18,y+14,"QIAs POR RÉGUA (MÊS)",16,navy,True)
        specs=(("NR","NR","#FEE2E2","#B91C1C"),("1 a 3","1 A 3","#DBEAFE","#174BD6"),("4 a 6","4 A 6","#DCFCE7","#166534")); mw=(left_w-48)/3
        for j,(lab,key,bgc,fg) in enumerate(specs): mx=margin+16+j*(mw+8); box(mx,y+45,mw,92,bgc,10); txt(mx+mw/2,y+59,lab,14,fg,True,"ma"); txt(mx+mw/2,y+88,integer(totals.get(key,0)),25,fg,True,"ma")
        ax=margin+left_w+12; aw=(W-margin-ax-10)/2; box(ax,y,aw,summary_h-18,white,14,line); box(ax+aw+10,y,aw,summary_h-18,white,14,line)
        weekly=sum(float(r.get("weekly_award",0) or 0) for r in rows); monthly=sum(float(r.get("projected_award",0) or 0) for r in rows)
        txt(ax+aw/2,y+20,"PREMIAÇÃO SEMANAL",15,muted,True,"ma"); txt(ax+aw/2,y+60,money(weekly),25,navy,True,"ma"); txt(ax+aw+10+aw/2,y+20,"PREMIAÇÃO MENSAL",15,muted,True,"ma"); txt(ax+aw+10+aw/2,y+60,money(monthly),25,navy,True,"ma")
    else:
        box(margin,y,W-2*margin,summary_h-18,white,14,line); note="Desempenho diário por conciliador" if view=="DIÁRIO" else "Resultado semanal, projeções e premiação"; txt(margin+18,y+20,note.upper(),17,navy,True)
    y+=summary_h
    # column header
    box(margin,y,W-2*margin,46,"#E8EFF6",8); y+=52
    if view=="VISÃO GERAL": headers=[("POS.",44),("CONCILIADOR",250),("QIAs",92),("TROCAS",86),("CRÉDITO",82),("NEO",72),("TICKET",108),("NR",75),("1 a 3",75),("4 a 6",75)]
    elif view=="DIÁRIO": headers=[("POS.",44),("CONCILIADOR",270),("QIAs",100),("TROCAS",100),("CRÉDITO",90),("NEO",80),("TICKET",120),("SEMANA",100)]
    else: headers=[("POS.",44),("CONCILIADOR",270),("QIAs",120),("TROCAS",120),("CONQUISTADO",150),("PROJETADO",150),("PRÓXIMO",150)]
    totalw=sum(w for _,w in headers); scale=(W-2*margin)/totalw; xx=margin
    for lab,w0 in headers: w=w0*scale; txt(xx+w/2,y-37,lab,13,muted,True,"ma",w-4); xx+=w
    # rows
    for pos,row in enumerate(rows,1):
        _,tone,ink=PALETTE[row.get("color","red")]; box(margin,y,W-2*margin,row_h,tone,14); xx=margin
        vals=[]
        if view=="VISÃO GERAL": vals=[f"{pos}º",row["name"],integer(row["qias"]),integer(row["changes"]),integer(row["credit"]),integer(row["neo"]),money(row["ticket"]),integer(row.get("NR",0)),integer(row.get("1 A 3",0)),integer(row.get("4 A 6",0))]
        elif view=="DIÁRIO": vals=[f"{pos}º",row["name"],integer(row["qias"]),integer(row["changes"]),integer(row["credit"]),integer(row["neo"]),money(row["ticket"]),integer(row.get("week_qias",0))]
        else:
            nxt=money(row.get("next_award",0)) if row.get("next_award",0) else "Máximo"; vals=[f"{pos}º",row["name"],integer(row["qias"]),integer(row["changes"]),money(row.get("earned_award",0)),money(row.get("award",0)),nxt]
        for j,((lab,w0),val) in enumerate(zip(headers,vals)):
            w=w0*scale
            if j==0: txt(xx+w/2,y+35,val,22,ink,True,"ma")
            elif j==1:
                txt(xx+10,y+22,val,19,ink,True,maxw=w-18)
                sub=(f"Meta: {integer(row.get('qias_goal',0))} QIAs" if view=="VISÃO GERAL" else (f"{integer(row.get('month_qias',0))} no mês" if view=="DIÁRIO" else f"Proj. QIAs {integer(row.get('qias_projection',0))}")); txt(xx+10,y+53,sub,13,ink,False,maxw=w-18)
            else:
                # white inset cells reproduce the generated reference
                box(xx+3,y+10,w-6,row_h-20,"#FFFFFF",10); txt(xx+w/2,y+27,val,18,navy,True,"ma",w-10)
                sub=""
                if view=="VISÃO GERAL" and lab=="QIAs": sub="Proj. "+integer(row.get("qias_projection",0))
                elif view=="VISÃO GERAL" and lab=="TROCAS": sub="Proj. "+integer(row.get("changes_projection",0))
                elif view=="DIÁRIO" and lab=="QIAs": sub=f"{_pct(row.get('qias',0),30):.0f}% da ref."
                elif view=="SEMANAL" and lab=="QIAs": sub="Proj. "+integer(row.get("qias_projection",0))
                elif view=="SEMANAL" and lab=="TROCAS": sub="Proj. "+integer(row.get("changes_projection",0))
                if sub: txt(xx+w/2,y+55,sub,11,muted,False,"ma",w-10)
            xx+=w
        y+=row_h+8
    # goals footer
    gy=y+8; half=(W-2*margin-12)/2; box(margin,gy,half,118,white,14,line); box(margin+half+12,gy,half,118,white,14,line)
    qgoal=goals.get("qias",0); cgoal=goals.get("changes",0); txt(margin+18,gy+18,"META DA EQUIPE",15,muted,True); txt(margin+18,gy+45,(integer(qgoal)+" QIAs") if qgoal else "Não definida",23,navy,True); prog(margin+18,gy+83,half-36,totals.get("qias",0),qgoal)
    x2=margin+half+12; txt(x2+18,gy+18,"TROCAS",15,muted,True); txt(x2+18,gy+45,integer(cgoal) if cgoal else "Não definida",23,navy,True); prog(x2+18,gy+83,half-36,totals.get("changes",0),cgoal)
    fy=gy+140; d.line((margin,fy,W-margin,fy),fill=line,width=1); txt(margin,fy+18,"CARTÃO DE TODOS · AFOGADOS",15,muted,True); txt(W-margin,fy+18,"PAINEL DE RESULTADOS · CONCILIAÇÃO",14,muted,False,"ra")
    out=io.BytesIO(); image.save(out,"PNG",optimize=True); return out.getvalue()
