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


def _font(size, bold=False):
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


def ranking_png(rows, view, period, totals, goals, synced_at):
    """Export PNG faithful to the approved 1024x1536 mobile reference."""
    from PIL import Image, ImageDraw, ImageFilter

    W = 1024
    n = max(1, len(rows))
    fixed = 806
    row_h = 88
    row_gap = 9
    H = max(1536, fixed + n * (row_h + row_gap))

    bg = "#F4F8FC"
    navy = "#17345F"
    muted = "#5E7190"
    line = "#D9E4EE"
    white = "#FFFFFF"
    green1, green2 = (4, 123, 70), (0, 84, 52)

    image = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(image)

    def font(sz, bold=False):
        return _font(sz, bold)

    def fit(text, fnt, max_width):
        text = str(text)
        if draw.textlength(text, font=fnt) <= max_width:
            return text
        while text and draw.textlength(text + "…", font=fnt) > max_width:
            text = text[:-1]
        return text + "…"

    def text(x, y, value, size=18, color=navy, bold=False, anchor=None, max_width=None):
        fnt = font(size, bold)
        value = fit(value, fnt, max_width) if max_width else str(value)
        draw.text((x, y), value, font=fnt, fill=color, anchor=anchor)

    def shadow_box(x, y, w, h, fill=white, radius=14, outline=None, shadow=True):
        if shadow:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.rounded_rectangle((x + 2, y + 4, x + w + 2, y + h + 4), radius=radius, fill=(24, 57, 96, 24))
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

    def gradient_header(height=266):
        for yy in range(height):
            t = yy / max(1, height - 1)
            r = int(green1[0] * (1 - t) + green2[0] * t)
            g = int(green1[1] * (1 - t) + green2[1] * t)
            b = int(green1[2] * (1 - t) + green2[2] * t)
            draw.line((0, yy, W, yy), fill=(r, g, b))

    def face(cx, cy, status, scale=1.0):
        r = 23 * scale
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#FFD84D")
        ink = "#12233D"
        if status == "blue":
            draw.rounded_rectangle((cx-r*0.78, cy-r*0.35, cx-r*0.06, cy+r*0.02), radius=4, fill=ink)
            draw.rounded_rectangle((cx+r*0.06, cy-r*0.35, cx+r*0.78, cy+r*0.02), radius=4, fill=ink)
            draw.line((cx-r*0.06, cy-r*0.18, cx+r*0.06, cy-r*0.18), fill=ink, width=max(2,int(3*scale)))
            draw.arc((cx-r*0.48, cy-r*0.05, cx+r*0.48, cy+r*0.65), start=10, end=170, fill=ink, width=max(2,int(3*scale)))
        else:
            eye_r = max(2, int(2.5*scale))
            draw.ellipse((cx-r*0.38-eye_r, cy-r*0.22-eye_r, cx-r*0.38+eye_r, cy-r*0.22+eye_r), fill=ink)
            draw.ellipse((cx+r*0.38-eye_r, cy-r*0.22-eye_r, cx+r*0.38+eye_r, cy-r*0.22+eye_r), fill=ink)
            if status == "green":
                draw.arc((cx-r*0.45, cy-r*0.02, cx+r*0.45, cy+r*0.58), start=10, end=170, fill=ink, width=max(2,int(3*scale)))
            elif status == "yellow":
                draw.line((cx-r*0.28, cy+r*0.27, cx+r*0.28, cy+r*0.27), fill=ink, width=max(2,int(3*scale)))
            else:
                draw.arc((cx-r*0.45, cy+r*0.18, cx+r*0.45, cy+r*0.70), start=190, end=350, fill=ink, width=max(2,int(3*scale)))

    gradient_header()
    text(42, 24, "CARTÃO DE TODOS · AFOGADOS", 25, "#B9E7C9", True)
    title = {
        "VISÃO GERAL": "RANKING DE CONCILIAÇÃO - GERAL",
        "DIÁRIO": "RANKING DE CONCILIAÇÃO - HOJE",
        "SEMANAL": "RANKING DE CONCILIAÇÃO - SEMANA",
    }.get(view, "RANKING DE CONCILIAÇÃO")
    subtitle = {
        "VISÃO GERAL": "RESULTADOS DO MÊS · " + str(period),
        "DIÁRIO": "RESULTADOS DO DIA · " + str(period),
        "SEMANAL": "RESULTADOS DA SEMANA · " + str(period),
    }.get(view, str(period))
    text(42, 61, title, 38, white, True, max_width=760)
    text(42, 112, subtitle, 21, "#D8F0E3", True)
    text(W-45, 26, synced_at.strftime("%d/%m/%Y"), 25, white, True, "ra")
    text(W-45, 60, "Atualizado em " + synced_at.strftime("%d/%m/%Y %H:%M"), 12, "#D8F0E3", False, "ra")

    if view == "VISÃO GERAL":
        kpis = [
            ("QIAs DO MÊS", _integer(totals.get("qias", 0)), "#0A6B47"),
            ("TROCAS TOTAL", _integer(totals.get("changes", 0)), "#174BD6"),
            ("TROCAS CRÉDITO", _integer(totals.get("credit", 0)), "#7E22CE"),
            ("TROCAS NEOENERGIA", _integer(totals.get("neo", 0)), "#C2410C"),
            ("TICKET MÉDIO", _money(totals.get("ticket", 0)), navy),
            ("CONCILIADORES ATIVOS", _integer(len(rows)), navy),
        ]
    elif view == "DIÁRIO":
        kpis = [
            ("QIAs HOJE", _integer(totals.get("qias", 0)), "#0A6B47"),
            ("TROCAS TOTAL", _integer(totals.get("changes", 0)), "#174BD6"),
            ("TROCAS CRÉDITO", _integer(totals.get("credit", 0)), "#7E22CE"),
            ("TROCAS NEOENERGIA", _integer(totals.get("neo", 0)), "#C2410C"),
            ("TICKET MÉDIO", _money(totals.get("ticket", 0)), navy),
            ("CONCILIADORES ATIVOS", _integer(len(rows)), navy),
        ]
    else:
        kpis = [
            ("QIAs DA SEMANA", _integer(totals.get("qias", 0)), "#0A6B47"),
            ("TROCAS TOTAL", _integer(totals.get("changes", 0)), "#174BD6"),
            ("TROCAS CRÉDITO", _integer(totals.get("credit", 0)), "#7E22CE"),
            ("TROCAS NEOENERGIA", _integer(totals.get("neo", 0)), "#C2410C"),
            ("TICKET MÉDIO", _money(totals.get("ticket", 0)), navy),
            ("CONCILIADORES ATIVOS", _integer(len(rows)), navy),
        ]
    left = 26
    gap = 8
    kw = (W - 52 - gap*5) / 6
    ky = 151
    for i, (lab, val, col) in enumerate(kpis):
        x = left + i*(kw+gap)
        shadow_box(x, ky, kw, 104, white, 12, None, True)
        text(x+kw/2, ky+21, lab, 11, muted, True, "ma", kw-10)
        text(x+kw/2, ky+57, val, 26, col, True, "ma", kw-10)

    sy = 279
    summary_h = 134
    left_w = 500
    shadow_box(26, sy, left_w, summary_h, white, 14, line, True)
    text(42, sy+16, "QIAs POR RÉGUA (MÊS)" if view=="VISÃO GERAL" else ("QIAs POR RÉGUA (HOJE)" if view=="DIÁRIO" else "QIAs POR RÉGUA (SEMANA)"), 15, navy, True)
    specs = (("NR","NR","#FDE2E2","#B91C1C"),("1 a 3","1 A 3","#DDEBFC","#174BD6"),("4 a 6","4 A 6","#DDF8E7","#166534"))
    mw = 145
    for j, (lab, key, bgc, fg) in enumerate(specs):
        mx = 42 + j*(mw+8)
        draw.rounded_rectangle((mx, sy+45, mx+mw, sy+116), radius=8, fill=bgc)
        text(mx+mw/2, sy+58, lab, 14, fg, True, "ma")
        text(mx+mw/2, sy+84, _integer(totals.get(key, 0)), 24, fg, True, "ma")

    right_x = 539
    right_w = 459
    gap2 = 8
    aw = (right_w-gap2)/2
    shadow_box(right_x, sy, aw, summary_h, white, 14, line, True)
    shadow_box(right_x+aw+gap2, sy, aw, summary_h, white, 14, line, True)
    if view == "VISÃO GERAL":
        weekly_real = sum(float(r.get("weekly_award", 0) or 0) for r in rows)
        weekly_proj = sum(float(r.get("weekly_projection", r.get("weekly_award", 0)) or 0) for r in rows)
        monthly_real = sum(float(r.get("monthly_award", 0) or 0) for r in rows)
        monthly_proj = sum(float(r.get("projected_award", 0) or 0) for r in rows)
        l1, v1, s1 = "PREMIAÇÃO SEMANAL", _money(weekly_real), "Projetado: " + _money(weekly_proj)
        l2, v2, s2 = "PREMIAÇÃO MENSAL", _money(monthly_real), "Projetado: " + _money(monthly_proj)
    elif view == "DIÁRIO":
        l1, v1, s1 = "REFERÊNCIA DIÁRIA", "30 QIAs", "por conciliador"
        l2, v2, s2 = "QIAs DA EQUIPE", _integer(totals.get("qias", 0)), "no dia"
    else:
        won = sum(float(r.get("earned_award", 0) or 0) for r in rows)
        projected = sum(float(r.get("award", 0) or 0) for r in rows)
        l1, v1, s1 = "PRÊMIO CONQUISTADO", _money(won), "na semana"
        l2, v2, s2 = "PRÊMIO PROJETADO", _money(projected), "projeção atual"
    for x, lab, val, sub in ((right_x,l1,v1,s1),(right_x+aw+gap2,l2,v2,s2)):
        text(x+aw/2, sy+22, lab, 14, muted, True, "ma", aw-14)
        text(x+aw/2, sy+58, val, 25, navy, True, "ma", aw-14)
        text(x+aw/2, sy+93, sub, 14, muted, False, "ma", aw-14)

    hy = 430
    header_h = 45
    draw.rounded_rectangle((16, hy, W-16, hy+header_h), radius=8, fill="#E9F0F6")
    if view == "SEMANAL":
        headers = [("POS.",50),("CONCILIADOR",200),("STATUS",62),("QIAs",110),("TROCAS",110),("CONQUISTADO",130),("PROJETADO",130),("PRÓXIMO",130)]
    else:
        headers = [("POS.",50),("CONCILIADOR",200),("STATUS",62),("QIAs",83),("TROCAS",80),("CRÉDITO",80),("NEO",70),("TICKET\nMÉDIO",100),("NR",75),("1 a 3",75),("4 a 6",75)]
    usable = W-32
    scale = usable/sum(w for _,w in headers)
    xx = 16
    for lab,w0 in headers:
        w = w0*scale
        parts = lab.split("\n")
        if len(parts)==1:
            text(xx+w/2,hy+15,parts[0],13,muted,True,"ma",w-4)
        else:
            text(xx+w/2,hy+8,parts[0],12,muted,True,"ma",w-4)
            text(xx+w/2,hy+23,parts[1],12,muted,True,"ma",w-4)
        xx += w

    y = hy + 53
    for pos,row in enumerate(rows,1):
        tone = {"blue":"#0B9AD7","green":"#10B555","yellow":"#FFBE0B","orange":"#F59E0B","red":"#E11D25"}.get(row.get("color"),"#E11D25")
        ink = "#FFFFFF" if row.get("color") not in ("yellow",) else "#172033"
        draw.rounded_rectangle((16,y,W-16,y+row_h),radius=14,fill=tone)
        xx = 16
        w = headers[0][1]*scale
        text(xx+w/2,y+28,f"{pos}º",22,ink,True,"ma"); xx+=w
        w = headers[1][1]*scale
        text(xx+8,y+18,row.get("name",""),17,ink,True,max_width=w-16)
        if view=="VISÃO GERAL": sub=f"Meta: {_integer(row.get('qias_goal',0))} QIAs"
        elif view=="DIÁRIO": sub=f"{_integer(row.get('month_qias',0))} no mês"
        else: sub=f"Proj. QIAs {_integer(row.get('qias_projection',0))}"
        text(xx+8,y+48,sub,12,ink,False,max_width=w-16); xx+=w
        w = headers[2][1]*scale
        face(xx+w/2,y+44,row.get("color","red"),0.8); xx+=w

        if view == "SEMANAL":
            cells = [
                ("QIAs", _integer(row.get("qias",0)), "Proj. "+_integer(row.get("qias_projection",0)), white, navy),
                ("TROCAS", _integer(row.get("changes",0)), "Proj. "+_integer(row.get("changes_projection",0)), white, navy),
                ("CONQUISTADO", _money(row.get("earned_award",0)), "", white, "#067647"),
                ("PROJETADO", _money(row.get("award",0)), "", white, "#4C1D95"),
                ("PRÓXIMO", _money(row.get("next_award",0)) if row.get("next_award",0) else "Máximo", "", "#FFF7ED", "#9A3412"),
            ]
        else:
            qsub = "Proj. "+_integer(row.get("qias_projection",0)) if view=="VISÃO GERAL" else f"{_pct(row.get('qias',0),30):.0f}% ref."
            cells = [
                ("QIAs", _integer(row.get("qias",0)), qsub, white, navy),
                ("TROCAS", _integer(row.get("changes",0)), ("Proj. "+_integer(row.get("changes_projection",0))) if view=="VISÃO GERAL" else "", white, navy),
                ("CRÉDITO", _integer(row.get("credit",0)), ("Proj. "+_integer(_project_value(row,"credit","changes"))) if view=="VISÃO GERAL" else "", white, navy),
                ("NEO", _integer(row.get("neo",0)), ("Proj. "+_integer(_project_value(row,"neo","changes"))) if view=="VISÃO GERAL" else "", white, navy),
                ("TICKET", _money(row.get("ticket",0)), "", white, "#1467D2"),
                ("NR", _integer(row.get("NR",0)), "TM "+_money(row.get("regime_tickets",{}).get("NR",0)), "#FDE2E2", "#B91C1C"),
                ("1 a 3", _integer(row.get("1 A 3",0)), "TM "+_money(row.get("regime_tickets",{}).get("1 A 3",0)), "#DDEBFC", "#174BD6"),
                ("4 a 6", _integer(row.get("4 A 6",0)), "TM "+_money(row.get("regime_tickets",{}).get("4 A 6",0)), "#DDF8E7", "#166534"),
            ]
        for idx,cell in enumerate(cells, start=3):
            lab,val,sub,bgc,fg = cell
            w = headers[idx][1]*scale
            draw.rounded_rectangle((xx+3,y+9,xx+w-3,y+row_h-9),radius=9,fill=bgc)
            text(xx+w/2,y+21,val,16,fg,True,"ma",w-10)
            if sub:
                text(xx+w/2,y+50,sub,10,fg if idx>=8 else muted,False,"ma",w-10)
            xx += w
        y += row_h + row_gap

    gy = y + 18
    half = (W-52-14)/2
    for x in (26,26+half+14):
        shadow_box(x,gy,half,128,white,14,line,True)
    qgoal = goals.get("qias",0)
    cgoal = goals.get("changes",0)
    text(90,gy+20,"META DA EQUIPE (MÊS)",14,muted,True)
    text(90,gy+48,(_integer(qgoal)+" QIAs") if qgoal else "Não definida",22,navy,True)
    text(26+half-16,gy+20,"REALIZADO",14,muted,True,"ra")
    text(26+half-16,gy+48,_integer(totals.get("qias",0)),21,navy,True,"ra")
    text(26+half-16,gy+73,f"({_pct(totals.get('qias',0),qgoal):.0f}%)" if qgoal else "",16,muted,False,"ra")
    progress(45,gy+96,half-38,totals.get("qias",0),qgoal)
    x2=26+half+14
    text(x2+64,gy+20,"TROCAS (MÊS)",14,muted,True)
    text(x2+64,gy+48,_integer(cgoal) if cgoal else "Não definida",22,navy,True)
    text(x2+half-16,gy+20,"REALIZADO",14,muted,True,"ra")
    text(x2+half-16,gy+48,_integer(totals.get("changes",0)),21,navy,True,"ra")
    text(x2+half-16,gy+73,f"({_pct(totals.get('changes',0),cgoal):.0f}%)" if cgoal else "",16,muted,False,"ra")
    progress(x2+19,gy+96,half-38,totals.get("changes",0),cgoal)

    fy = gy+160
    draw.line((26,fy,W-26,fy),fill=line,width=1)
    text(26,fy+20,"CARTÃO DE TODOS · AFOGADOS",14,muted,True)
    text(26,fy+43,"PAINEL DE RESULTADOS · CONCILIAÇÃO",13,muted,False)
    text(W-26,fy+28,"Resultados geram oportunidades.",14,muted,False,"ra")

    content_bottom = fy+72
    image = image.crop((0,0,W,max(1536, content_bottom)))
    output = io.BytesIO()
    image.save(output,"PNG",optimize=True)
    return output.getvalue()
