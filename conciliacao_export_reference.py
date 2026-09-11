import io
from decimal import Decimal


def _money(value):
    return "R$ " + f"{float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _integer(value):
    return f"{float(value or 0):,.0f}".replace(",", ".")


def _pct(value, goal):
    try:
        if not goal:
            return 0.0
        return max(0.0, min(100.0, float(Decimal(str(value or 0)) * 100 / Decimal(str(goal)))))
    except Exception:
        return 0.0


def _project_value(row, key, total_key="qias"):
    total = Decimal(str(row.get(total_key, 0) or 0))
    projected = Decimal(str(row.get(total_key + "_projection", total) or 0))
    realized = Decimal(str(row.get(key, 0) or 0))
    return realized if total <= 0 else realized * projected / total


def _classification(row):
    color = str(row.get("color", "red")).lower()
    if color == "blue":
        return "Azul", "#0897D4"
    if color == "green":
        return "Verde", "#08AF56"
    if color in {"yellow", "orange"}:
        return "Amarelo", "#FDBA05"
    return "Vermelho", "#E31B23"


def ranking_png(rows, view, period, totals, goals, synced_at):
    """PNG da Conciliação usando a referência oficial 1024x1536 como template fixo."""
    from PIL import Image, ImageDraw, ImageFilter
    from app_core import _daily_font, _draw_daily_brand, _draw_daily_ordinal, _draw_daily_status_icon, _fit_image_text

    W = 1024
    base_h = 1536
    row_h = 88
    row_gap = 9
    rows_start = 484
    goals_top = 1242
    if len(rows) <= 7:
        H = base_h
        goals_y = goals_top
    else:
        extra = (len(rows) - 7) * (row_h + row_gap)
        H = base_h + extra
        goals_y = goals_top + extra

    bg = "#F4F8FC"
    navy = "#17345F"
    muted = "#5E7190"
    line = "#D9E4EE"
    white = "#FFFFFF"
    image = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=18, color=navy, bold=False, anchor=None, max_width=None):
        fnt = _daily_font(size, bold)
        value = str(value)
        if max_width:
            value = _fit_image_text(draw, value, fnt, max_width)
        draw.text((x, y), value, font=fnt, fill=color, anchor=anchor)

    def shadow_box(x, y, w, h, fill=white, radius=14, outline=None, shadow=True):
        if shadow:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.rounded_rectangle((x + 2, y + 4, x + w + 2, y + h + 4), radius=radius, fill=(24, 57, 96, 20))
            layer = layer.filter(ImageFilter.GaussianBlur(5))
            image.paste(layer, (0, 0), layer)
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline)

    def progress(x, y, w, value, goal, fg="#0799E5", height=12):
        p = _pct(value, goal)
        draw.rounded_rectangle((x, y, x + w, y + height), radius=height // 2, fill="#CDE4F8")
        if p > 0:
            fw = max(height, w * p / 100)
            draw.rounded_rectangle((x, y, x + fw, y + height), radius=height // 2, fill=fg)
        return p

    g1, g2 = (6, 129, 72), (0, 91, 53)
    for yy in range(266):
        t = yy / 265
        rgb = tuple(int(a * (1 - t) + b * t) for a, b in zip(g1, g2))
        draw.line((0, yy, W, yy), fill=rgb)

    _draw_daily_brand(draw, 42, 24)
    title = {"VISÃO GERAL":"RANKING DE CONCILIAÇÃO - GERAL","DIÁRIO":"RANKING DE CONCILIAÇÃO - HOJE","SEMANAL":"RANKING DE CONCILIAÇÃO - SEMANA"}.get(view,"RANKING DE CONCILIAÇÃO")
    subtitle = {"VISÃO GERAL":"RESULTADOS DO MÊS · ","DIÁRIO":"RESULTADOS DO DIA · ","SEMANAL":"RESULTADOS DA SEMANA · "}.get(view,"RESULTADOS · ") + str(period)
    text(42, 61, title, 38, white, True, max_width=760)
    text(42, 112, subtitle, 21, "#D8F0E3", True)
    text(W-45, 26, synced_at.strftime("%d/%m/%Y"), 25, white, True, "ra")
    text(W-45, 60, "Atualizado em " + synced_at.strftime("%d/%m/%Y %H:%M"), 12, "#D8F0E3", False, "ra")

    scope = "MÊS" if view == "VISÃO GERAL" else "HOJE" if view == "DIÁRIO" else "SEMANA"
    kpis = [
        (f"QIAs DO {scope}", _integer(totals.get("qias",0)), "#0A6B47"),
        ("TROCAS TOTAL", _integer(totals.get("changes",0)), "#174BD6"),
        ("TROCAS CRÉDITO", _integer(totals.get("credit",0)), "#7E22CE"),
        ("TROCAS NEOENERGIA", _integer(totals.get("neo",0)), "#C2410C"),
        ("TICKET MÉDIO", _money(totals.get("ticket",0)), navy),
        ("CONCILIADORES ATIVOS", _integer(len(rows)), navy),
    ]
    left, gap, ky = 26, 8, 151
    kw = (W - 52 - gap*5) / 6
    for i,(lab,val,col) in enumerate(kpis):
        x = left + i*(kw+gap)
        shadow_box(x, ky, kw, 104, white, 12)
        text(x+kw/2, ky+21, lab, 11, muted, True, "ma", kw-10)
        text(x+kw/2, ky+57, val, 26 if i != 4 else 25, col, True, "ma", kw-10)

    sy, summary_h = 279, 134
    left_w = 500
    shadow_box(26, sy, left_w, summary_h, white, 14, line)
    regime_title = "QIAs POR RÉGUA (MÊS)" if view=="VISÃO GERAL" else "QIAs POR RÉGUA (HOJE)" if view=="DIÁRIO" else "QIAs POR RÉGUA (SEMANA)"
    text(42, sy+16, regime_title, 15, navy, True)
    specs=(("NR","NR","#FDE2E2","#B91C1C"),("1 a 3","1 A 3","#DDEBFC","#174BD6"),("4 a 6","4 A 6","#DDF8E7","#166534"))
    mw=145
    for j,(lab,key,bgc,fg) in enumerate(specs):
        mx=42+j*(mw+8)
        draw.rounded_rectangle((mx,sy+45,mx+mw,sy+116),radius=8,fill=bgc)
        text(mx+mw/2,sy+58,lab,14,fg,True,"ma")
        text(mx+mw/2,sy+84,_integer(totals.get(key,0)),24,fg,True,"ma")

    right_x,right_w,gap2=539,459,8
    aw=(right_w-gap2)/2
    shadow_box(right_x,sy,aw,summary_h,white,14,line)
    shadow_box(right_x+aw+gap2,sy,aw,summary_h,white,14,line)
    draw.rounded_rectangle((right_x,sy,right_x+7,sy+summary_h),radius=4,fill="#0EA5E9")
    if view == "VISÃO GERAL":
        weekly_real=sum(float(r.get("weekly_award",0) or 0) for r in rows)
        weekly_proj=sum(float(r.get("weekly_projection",r.get("weekly_award",0)) or 0) for r in rows)
        monthly_real=sum(float(r.get("monthly_award",0) or 0) for r in rows)
        monthly_proj=sum(float(r.get("projected_award",0) or 0) for r in rows)
        blocks=((right_x,"PREMIAÇÃO SEMANAL",_money(weekly_real),"Projetado: "+_money(weekly_proj)),(right_x+aw+gap2,"PREMIAÇÃO MENSAL",_money(monthly_real),"Projetado: "+_money(monthly_proj)))
    elif view == "DIÁRIO":
        blocks=((right_x,"REFERÊNCIA DIÁRIA","30 QIAs","por conciliador"),(right_x+aw+gap2,"QIAs DA EQUIPE",_integer(totals.get("qias",0)),"no dia"))
    else:
        won=sum(float(r.get("earned_award",0) or 0) for r in rows)
        projected=sum(float(r.get("award",0) or 0) for r in rows)
        blocks=((right_x,"PRÊMIO CONQUISTADO",_money(won),"na semana"),(right_x+aw+gap2,"PRÊMIO PROJETADO",_money(projected),"projeção atual"))
    for x,lab,val,sub in blocks:
        text(x+aw/2,sy+22,lab,14,muted,True,"ma",aw-14)
        text(x+aw/2,sy+58,val,25,navy,True,"ma",aw-14)
        text(x+aw/2,sy+93,sub,14,muted,False,"ma",aw-14)

    hy=430
    draw.rounded_rectangle((16,hy,W-16,hy+45),radius=8,fill="#E9F0F6")
    headers=[("POS.",30),("CONCILIADOR",88),("STATUS",272),("QIAs",357),("TROCAS",444),("CRÉDITO",526),("NEO",620),("TICKET\nMÉDIO",687),("NR",802),("1 a 3",883),("4 a 6",961)]
    for lab,x in headers:
        if "\n" in lab:
            a,b=lab.split("\n")
            text(x,hy+12,a,14,"#536176",True,"ma")
            text(x,hy+29,b,14,"#536176",True,"ma")
        else:
            anchor="la" if lab in {"POS.","CONCILIADOR"} else "ma"
            text(x,hy+17,lab,14,"#536176",True,anchor)

    y=rows_start
    for pos,item in enumerate(rows,1):
        classification, fill = _classification(item)
        text_fill = "#071A33" if classification == "Amarelo" else "#FFFFFF"
        muted_fill = "#4B5563" if classification == "Amarelo" else "#E8EEF5"
        draw.rounded_rectangle((16,y,W-16,y+row_h),radius=15,fill=fill)
        _draw_daily_ordinal(draw, 49, y+45, pos, text_fill)
        name_font=_daily_font(18,True)
        name=_fit_image_text(draw,item.get("name",""),name_font,210)
        text(88,y+26,name,18,text_fill,True,max_width=210)
        meta = item.get("qias_goal",650) if view=="VISÃO GERAL" else item.get("weekly_qias_goal",30) if view=="SEMANAL" else 30
        meta_label = f"Meta: {_integer(meta)} QIAs" if view!="DIÁRIO" else f"{_integer(item.get('month_qias',0))} no mês"
        text(88,y+57,meta_label,14,muted_fill,False,max_width=210)
        _draw_daily_status_icon(draw, 300, y+45, classification)

        cells=[
            (339,419,"qias"),(423,500,"changes"),(504,581,"credit"),(585,660,"neo"),(665,756,"ticket"),(761,840,"NR"),(844,922,"1 A 3"),(926,1003,"4 A 6")
        ]
        for x1,x2,key in cells:
            if key=="NR": cfill="#FDE2E2"
            elif key=="1 A 3": cfill="#DDEBFC"
            elif key=="4 A 6": cfill="#DDF8E7"
            else: cfill="#FFFFFF"
            draw.rounded_rectangle((x1,y+10,x2,y+78),radius=10,fill=cfill)
            cx=(x1+x2)/2
            if key=="ticket":
                text(cx,y+28,_money(item.get("ticket",0)),16,"#0662C7",True,"ma",x2-x1-8)
            else:
                color = "#B91C1C" if key=="NR" else "#174BD6" if key=="1 A 3" else "#166534" if key=="4 A 6" else "#10224A"
                text(cx,y+22,_integer(item.get(key,0)),17,color,True,"ma")
                sub=""
                if key=="qias":
                    sub="Proj. "+_integer(item.get("qias_projection",item.get("qias",0))) if view!="DIÁRIO" else f"{_pct(item.get('qias',0),30):.0f}% da ref."
                elif key=="changes": sub="Proj. "+_integer(item.get("changes_projection",item.get("changes",0))) if view!="DIÁRIO" else ""
                elif key=="credit": sub="Proj. "+_integer(_project_value(item,"credit","changes")) if view!="DIÁRIO" else ""
                elif key=="neo": sub="Proj. "+_integer(_project_value(item,"neo","changes")) if view!="DIÁRIO" else ""
                elif key in {"NR","1 A 3","4 A 6"}:
                    tm=item.get("regime_tickets",{}).get(key,0)
                    sub="TM "+_money(tm).replace("R$ ","")
                if sub:
                    scolor="#B91C1C" if key=="NR" else "#174BD6" if key=="1 A 3" else "#166534" if key=="4 A 6" else "#52657E"
                    text(cx,y+53,sub,11,scolor,False,"ma",x2-x1-8)
        y += row_h + row_gap

    goal_w=478
    shadow_box(17,goals_y,goal_w,148,white,14,line)
    shadow_box(509,goals_y,goal_w,148,white,14,line)
    for cx, symbol in ((64,"◎"),(556,"↔")):
        draw.ellipse((cx-31,goals_y+20,cx+31,goals_y+82),fill="#0B8CE7")
        text(cx,goals_y+50,symbol,34,white,True,"mm")
    qgoal=goals.get("qias",0); cgoal=goals.get("changes",0)
    qreal=totals.get("qias",0); creal=totals.get("changes",0)
    text(108,goals_y+20,"META DA EQUIPE (MÊS)",15,muted,True)
    text(108,goals_y+55,(_integer(qgoal)+" QIAs") if qgoal else "Não definida",23,"#10224A",True)
    text(457,goals_y+20,"REALIZADO",14,muted,True,"ra")
    text(457,goals_y+50,_integer(qreal),22,"#10224A",True,"ra")
    text(457,goals_y+78,f"({_pct(qreal,qgoal):.0f}%)",18,navy,False,"ra")
    progress(35,goals_y+111,452,qreal,qgoal)

    text(600,goals_y+20,"TROCAS (MÊS)",15,muted,True)
    text(600,goals_y+55,_integer(cgoal) if cgoal else "Não definida",23,"#10224A",True)
    text(970,goals_y+20,"REALIZADO",14,muted,True,"ra")
    text(970,goals_y+50,_integer(creal),22,"#10224A",True,"ra")
    text(970,goals_y+78,f"({_pct(creal,cgoal):.0f}%)",18,navy,False,"ra")
    progress(527,goals_y+111,452,creal,cgoal)

    fy=goals_y+176
    draw.line((17,fy,1007,fy),fill="#D7E1EB",width=1)
    text(26,fy+23,"CARTÃO DE TODOS · AFOGADOS",14,"#405574",True)
    text(26,fy+45,"PAINEL DE RESULTADOS · CONCILIAÇÃO",12,"#5E7190",False)
    text(998,fy+28,"Resultados geram oportunidades.",16,"#405574",False,"ra")

    out=io.BytesIO(); image.save(out,"PNG",optimize=True); return out.getvalue()
