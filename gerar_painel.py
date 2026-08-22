#!/usr/bin/env python3
"""Gera o Painel Comercial Afogados a partir de CSV e JSON.

O programa usa somente a biblioteca padrão e grava um XLSX (OOXML) novo; nenhum
arquivo binário é editado. Use ``--dados`` para apontar para a exportação real.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
DEFAULT_OUTPUT = ROOT / "output" / "Painel_Comercial_Afogados.xlsx"
COLORS = {"dark":"16324F","blue":"19A7CE","cyan":"DDF6FC","green":"2EAD67","yellow":"F4C542","red":"E55353","white":"FFFFFF","light":"F4F7FA"}


def column(number: int) -> str:
    out = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        out = chr(65 + remainder) + out
    return out


class Sheet:
    def __init__(self, name, widths=None, freeze="A2", autofilter=None, hidden=False):
        self.name, self.rows, self.merges = name, [], []
        self.widths, self.freeze, self.autofilter = widths or {}, freeze, autofilter
        self.validations, self.conditionals, self.performance_conditionals, self.hidden = [], [], [], hidden

    def add(self, values, styles=None, height=None): self.rows.append((values, styles or {}, height))
    def merge(self, ref): self.merges.append(ref)
    def validate_list(self, ref, formula): self.validations.append((ref, formula))
    def color_scale(self, ref): self.conditionals.append(ref)
    def performance_scale(self, ref, first_row, projection_col="H", target_col="AG"):
        """Colore vendedor/projeção pela proporção entre projeção e meta."""
        self.performance_conditionals.append((ref, first_row, projection_col, target_col))

    def xml(self):
        row_xml = []
        for r, (values, styles, height) in enumerate(self.rows, 1):
            cells = []
            for c, value in enumerate(values, 1):
                if value is None: continue
                ref, style = f"{column(c)}{r}", styles.get(c, 0)
                attr = f' s="{style}"' if style else ""
                if isinstance(value, str) and value.startswith("="):
                    body = f"<f>{escape(value[1:])}</f><v>0</v>"
                elif isinstance(value, (int, float)):
                    body = f"<v>{value}</v>"
                else:
                    attr += ' t="inlineStr"'; body = f'<is><t xml:space="preserve">{escape(str(value))}</t></is>'
                cells.append(f'<c r="{ref}"{attr}>{body}</c>')
            h = f' ht="{height}" customHeight="1"' if height else ""
            row_xml.append(f'<row r="{r}"{h}>{"".join(cells)}</row>')
        cols = "".join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in self.widths.items())
        pane = ""
        if self.freeze:
            letters = ''.join(x for x in self.freeze if x.isalpha()); nums = ''.join(x for x in self.freeze if x.isdigit())
            xs, ys = max(0, sum((ord(ch)-64)*26**i for i,ch in enumerate(letters[::-1]))-1), max(0,int(nums)-1)
            pane = f'<pane xSplit="{xs}" ySplit="{ys}" topLeftCell="{self.freeze}" activePane="bottomRight" state="frozen"/>'
        merges = f'<mergeCells count="{len(self.merges)}">'+''.join(f'<mergeCell ref="{x}"/>' for x in self.merges)+'</mergeCells>' if self.merges else ""
        flt = f'<autoFilter ref="{self.autofilter}"/>' if self.autofilter else ""
        dvs = ""
        if self.validations:
            dvs=f'<dataValidations count="{len(self.validations)}">'+''.join(f'<dataValidation type="list" allowBlank="0" showErrorMessage="1" sqref="{r}"><formula1>{escape(f)}</formula1></dataValidation>' for r,f in self.validations)+'</dataValidations>'
        cfs=''.join(f'<conditionalFormatting sqref="{r}"><cfRule type="colorScale" priority="1"><colorScale><cfvo type="min"/><cfvo type="percentile" val="50"/><cfvo type="max"/><color rgb="FFE55353"/><color rgb="FFF4C542"/><color rgb="FF2EAD67"/></colorScale></cfRule></conditionalFormatting>' for r in self.conditionals)
        for ref, first, projection, target in self.performance_conditionals:
            rules = [
                (0, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=1.5*${target}{first})'),
                (1, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=${target}{first},${projection}{first}&lt;1.5*${target}{first})'),
                (2, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=0.7*${target}{first},${projection}{first}&lt;${target}{first})'),
                (3, f'AND(${target}{first}&gt;0,${projection}{first}&lt;0.7*${target}{first})'),
            ]
            cfs += f'<conditionalFormatting sqref="{ref}">'+''.join(f'<cfRule type="expression" dxfId="{dxf}" priority="{10+dxf}"><formula>{formula}</formula></cfRule>' for dxf,formula in rules)+'</conditionalFormatting>'
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0">{pane}</sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"/><cols>{cols}</cols><sheetData>{''.join(row_xml)}</sheetData>{merges}{flt}{cfs}{dvs}</worksheet>'''


def normalize_seller_name(value):
    import unicodedata, re
    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

def parse_date(value): return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def load_inputs(csv_path, config_path):
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        reader=csv.DictReader(handle); rows=list(reader)
    required={"data_venda","vendedor","setor","categoria","neoenergia","adimplencia_m2","status","id_venda"}
    missing=required-set(reader.fieldnames or [])
    if missing: raise ValueError("Colunas ausentes no CSV: "+", ".join(sorted(missing)))
    seen=set(); clean=[]
    for row in rows:
        if row["id_venda"] in seen or row["status"].strip().lower() not in config["status_validos"]: continue
        row["data_venda"]=parse_date(row["data_venda"]); seen.add(row["id_venda"]); clean.append(row)
    return clean, config


def workdays(year, month, saturday=True, sunday=False, start=None, end=None, absences=None):
    d=date(year,month,1); days=[]
    start = parse_flexible_date(start) or d
    end = parse_flexible_date(end) or date(year, month, 28) + timedelta(days=4)
    end -= timedelta(days=end.day)
    excluded = {x for value in (absences or []) if (x := parse_flexible_date(value))}
    while d.month==month:
        scheduled = d.weekday()<5 or (saturday and d.weekday()==5) or (sunday and d.weekday()==6)
        if scheduled and start<=d<=end and d not in excluded: days.append(d)
        d += timedelta(days=1)
    return days


def parse_flexible_date(value):
    if not value: return None
    if isinstance(value, date): return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try: return datetime.strptime(str(value), fmt).date()
        except ValueError: pass
    return None


def month_weeks(year, month):
    """Retorna blocos segunda-domingo que intersectam a competência."""
    first=date(year,month,1); last=(date(year,month,28)+timedelta(days=4)); last-=timedelta(days=last.day)
    cursor=first-timedelta(days=first.weekday()); weeks=[]
    while cursor<=last:
        weeks.append((max(first,cursor),min(last,cursor+timedelta(days=6)))); cursor+=timedelta(days=7)
    return weeks


def tier_value(qty, tiers):
    eligible=[float(t["valor_por_venda"]) for t in tiers if qty>=int(t["vendas"])]
    return eligible[-1] if eligible else 0


def weekly_prize(qty, awards):
    eligible=[float(x["premio"]) for x in awards if qty>=int(x["vendas"])]
    return eligible[-1] if eligible else 0


def summarize(rows, cfg):
    year,month=cfg["ano"],cfg["mes"]; calendar_days=workdays(year,month,True,True); weeks_ranges=month_weeks(year,month)
    last_month=calendar_days[-1]; cutoff=min(date(year,month,min(cfg["dia_referencia"],last_month.day)),last_month)
    by=defaultdict(list)
    for row in rows:
        if row["data_venda"].year==year and row["data_venda"].month==month and row["data_venda"]<=cutoff:
            # A contagem é feita pela identidade normalizada do vendedor. Isso evita
            # perder vendas quando o sistema exporta, por exemplo, DANIELE..., Daniele...
            # ou o mesmo nome com variações de acento/espaçamento.
            key=normalize_seller_name(row.get("vendedor",""))
            if key:by[key].append(row)
    total=sum(len(x) for x in by.values()); official="maior_ou_igual_1000" if total>=cfg["limite_cenario_maior"] else "abaixo_1000"
    result=[]
    for seller in cfg["vendedores"]:
        name=seller["vendedor"]; sales=by[normalize_seller_name(name)]; qty=len(sales); selling_days={x["data_venda"] for x in sales}
        category=seller.get("categoria","Vendedor"); franchise=seller.get("pertence_franquia",True); active=seller.get("ativo",True)
        local_seller=active and franchise and category.lower() not in ("website","adm","freelance","canal nacional")
        scheduled=workdays(year,month,seller.get("trabalha_sabado",cfg.get("calendario",{}).get("trabalha_sabado",True)),seller.get("trabalha_domingo",False),seller.get("data_inicio"),seller.get("data_desligamento"),seller.get("folgas",[]))
        elapsed=[d for d in scheduled if d<=cutoff]; days_worked=len(elapsed); avg=qty/days_worked if days_worked else 0; projection=round(avg*len(scheduled)) if days_worked else 0; minimum=35 if seller["experiencia"] else 40
        weeks=[sum(a<=x["data_venda"]<=b for x in sales) for a,b in weeks_ranges]
        prizes=[weekly_prize(x,cfg["premiacao_semanal"]) if local_seller else 0 for x in weeks]
        neo=sum(x["neoenergia"].strip().lower() in ("sim","1","true","neoenergia celpe") for x in sales); neo_pct=neo/qty if qty else 0
        ruler=cfg["reguas_comissao"][official]; rate=tier_value(qty,ruler) if local_seller and qty>=minimum else 0; base=qty*rate
        adim=all(x["adimplencia_m2"].strip().replace(",",".") in ("1","1.0","100%") for x in sales) if sales else False
        bonus_neo=base*cfg["bonus_neoenergia"]["percentual_bonus"] if neo_pct>=cfg["bonus_neoenergia"]["percentual_minimo"] else 0
        bonus_adim=base*cfg["bonus_adimplencia"]["percentual_bonus"] if adim else 0
        zero_days=[d for d in elapsed if d not in selling_days] if local_seller else []
        current_sequence=0
        for d in reversed(elapsed):
            if d in selling_days: break
            current_sequence+=1
        longest=run=0
        for d in elapsed:
            run=run+1 if d not in selling_days else 0; longest=max(longest,run)
        current_week=next(((a,b) for a,b in weeks_ranges if a<=cutoff<=b),weeks_ranges[-1])
        zeros_week=sum(current_week[0]<=d<=current_week[1] for d in zero_days)
        next_tier=next((int(x["vendas"]) for x in ruler if int(x["vendas"])>qty),None); next_gain=0
        if next_tier: next_gain=next_tier*tier_value(next_tier,ruler)-base
        daily={d.day:sum(x["data_venda"]==d for x in sales) for d in calendar_days}
        result.append({"vendedor":name,"setor":seller.get("setor","NÃO INFORMADO"),"categoria":category,"ativo":active,"pertence_franquia":franchise,"elegivel_individual":local_seller,"experiencia":"Sim" if seller["experiencia"] else "Não","vendas":qty,"dias":days_worked,"dias_previstos":len(scheduled),"media":avg,"projecao":projection,"meta_individual":int(seller["meta_individual"]),"zeros":len(zero_days),"zeros_semana":zeros_week,"sequencia_zeros":current_sequence,"maior_sequencia_zeros":longest,"neo":neo,"neo_pct":neo_pct,"neo_elegivel":local_seller and neo_pct>=cfg["bonus_neoenergia"]["percentual_minimo"],"adim_elegivel":local_seller and adim,"semanas":weeks,"premios":prizes,"premio_total":sum(prizes),"minimo":minimum,"taxa":rate,"base":base,"bonus_neo":bonus_neo if local_seller else 0,"bonus_adim":bonus_adim if local_seller else 0,"total":base+(bonus_neo if local_seller else 0)+(bonus_adim if local_seller else 0)+sum(prizes),"proxima":next_tier or "Faixa máxima","faltam_proxima":max(0,(next_tier or qty)-qty) if local_seller else 0,"ganho_proxima":next_gain if local_seller else 0,"proxima_taxa":tier_value(next_tier,ruler) if next_tier and local_seller else rate,"proxima_comissao":next_tier*tier_value(next_tier,ruler) if next_tier and local_seller else base,"diario":daily,"dias_agendados":{d.day for d in scheduled},"dias_decorridos":{d.day for d in elapsed}})
    enterprise_projection=sum(x["projecao"] for x in result); projected_scenario="maior_ou_igual_1000" if enterprise_projection>=cfg["limite_cenario_maior"] else "abaixo_1000"
    for item in result:
        projected_ruler=cfg["reguas_comissao"][projected_scenario]; projected_rate=tier_value(item["projecao"],projected_ruler) if item["elegivel_individual"] and item["projecao"]>=item["minimo"] else 0
        projected_base=item["projecao"]*projected_rate
        projected_neo=projected_base*cfg["bonus_neoenergia"]["percentual_bonus"] if item["neo_elegivel"] else 0
        projected_adim=projected_base*cfg["bonus_adimplencia"]["percentual_bonus"] if item["elegivel_individual"] else 0
        item.update({"cenario_projetado":projected_scenario,"taxa_proj":projected_rate,"base_proj":projected_base,"comissao_proj":projected_base,"bonus_neo_proj":projected_neo,"bonus_adim_proj":projected_adim,"total_variavel_proj":projected_base+projected_neo+projected_adim+item["premio_total"]})
    return result, calendar_days, [d for d in calendar_days if d<=cutoff], official


def title(sh, text, subtitle, end):
    sh.add([text],{1:7},30); sh.merge(f"A1:{end}1"); sh.add([subtitle],{1:8},22); sh.merge(f"A2:{end}2")


def header(sh, values, row=None): sh.add(values,{i:1 for i in range(1,len(values)+1)},22)


def build_sheets(rows,cfg,summary,all_days,elapsed,official):
    report_summary=sorted([x for x in summary if x.get("elegivel_individual",True)],key=lambda x:(x["vendas"],x["projecao"]),reverse=True); sheets=[]; n=len(report_summary)+4; week_count=max((len(x["semanas"]) for x in report_summary),default=5)
    dash=Sheet("DASHBOARD",{1:27,2:18,3:3,4:28,5:18,6:18},freeze=None)
    title(dash,"PAINEL COMERCIAL • AFOGADOS",f"Competência {cfg['mes']:02d}/{cfg['ano']}  |  Atualizado até dia {cfg['dia_referencia']}","F")
    dash.add([]); dash.add(["VISÃO GERAL"],{1:9}); dash.merge("A4:F4")
    total=sum(x["vendas"] for x in summary); proj=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary)
    website=sum(x["vendas"] for x in summary if x["categoria"].lower()=="website"); adm=sum(x["vendas"] for x in summary if x["categoria"].lower()=="adm"); free=sum(x["vendas"] for x in summary if x["categoria"].lower()=="freelance")
    kpis=[("VENDAS TOTAIS",total,11),("META DO MÊS",cfg["meta_empresa"],12),("% DA META",total/cfg["meta_empresa"],13),("PROJEÇÃO",proj,12),("FALTAM",max(0,cfg["meta_empresa"]-total),14),("VENDAS NEO",neo,11),("% NEO",neo/total if total else 0,13),("DIAS ZERADOS",sum(x["zeros"] for x in summary),14),("WEBSITE",website,11),("ADM",adm,11),("FREELANCE",free,11),("PREMIAÇÃO EQUIPE",sum(x["total"] for x in summary),15),("PREMIAÇÃO PROJETADA",sum(x["comissao_proj"] for x in summary),15),("TOTAL VAR. PROJETADO",sum(x["total_variavel_proj"] for x in summary),15),("SEMANAIS ACUMULADOS",sum(x["premio_total"] for x in summary),15)]
    for i in range(0,len(kpis),2):
        a=kpis[i]; b=kpis[i+1] if i+1<len(kpis) else ("","",10); dash.add([a[0],a[1],None,b[0],b[1]],{1:10,2:a[2],4:10,5:b[2]},24)
    first_seller=report_summary[0]["vendedor"] if report_summary else "Sem vendedor ativo"; dash.add([]); dash.add(["VISÃO INDIVIDUAL",None,None,"SELECIONE O VENDEDOR",first_seller],{1:9,4:10,5:12},24); dash.merge(f"A{len(dash.rows)}:B{len(dash.rows)}"); selector=f"E{len(dash.rows)}"
    if report_summary: dash.validate_list(selector, '"' + ','.join(x['vendedor'] for x in report_summary) + '"')
    tail=12+2*week_count
    metrics=[("Total de vendas",5), ("Média diária",7),("Projeção mensal",8),("Dias zerados",9),("Vendas Neoenergia",10),("% Neoenergia",11),*[(f"Semana {i+1}",12+i) for i in range(week_count)],*[(f"Prêmio S{i+1}",12+week_count+i) for i in range(week_count)],("Prêmio acumulado",tail),("Premiação base",tail+3),("Bônus Neoenergia",tail+4),("Bônus adimplência",tail+5),("Premiação total",tail+6),("Premiação projetada",tail+7),("Próxima faixa",tail+8),("Faltam próxima faixa",tail+9),("Ganho adicional",tail+10)]
    for i,(label,colnum) in enumerate(metrics):
        if i%2==0: dash.add([label,f'=IFERROR(VLOOKUP($E$13,\'RELATORIO GERAL\'!$A$4:$AF${n},{colnum},FALSE),0)',None],{1:10,2:15 if i>=17 else 11},20)
        else:
            r=len(dash.rows); dash.rows[-1][0].extend([label,f'=IFERROR(VLOOKUP($E$13,\'RELATORIO GERAL\'!$A$4:$AF${n},{colnum},FALSE),0)']); dash.rows[-1][1].update({4:10,5:15 if i>=17 else 11})
    sheets.append(dash)

    general_end=column(tail+11)
    general=Sheet("RELATORIO GERAL",{1:24,2:13,3:13,**{i:14 for i in range(4,tail+12)}},freeze="A5",autofilter=f"A4:{general_end}{n}")
    title(general,"RELATÓRIO GERAL","Produção, projeção e remuneração por vendedor",general_end)
    general.add([]); headers=["Vendedor","Setor","Categoria","Experiência","Vendas","Dias trabalhados","Média/dia","Projeção","Dias zerados","Neo","% Neo",*[f"S{i}" for i in range(1,week_count+1)],*[f"Prêmio S{i}" for i in range(1,week_count+1)],"Semanais","Mínimo","R$/venda","Premiação base","Bônus Neo","Bônus adimpl.","Total acumulado","Premiação projetada","Próxima faixa","Faltam próxima","Ganho adicional","Meta individual"]
    header(general,headers)
    for x in report_summary: general.add([x["vendedor"],x["setor"],x["categoria"],x["experiencia"],x["vendas"],x["dias"],x["media"],x["projecao"],x["zeros"],x["neo"],x["neo_pct"],*x["semanas"],*x["premios"],x["premio_total"],x["minimo"],x["taxa"],x["base"],x["bonus_neo"],x["bonus_adim"],x["total"],x["comissao_proj"],x["proxima"],x["faltam_proxima"],x["ganho_proxima"],x["meta_individual"]],{7:3,11:4,**{i:5 for i in range(17,23)},25:5,26:5,27:5,28:5,29:5,32:5})
    general.color_scale(f"E5:E{n}"); general.performance_scale(f"A5:A{n} H5:H{n}",5,target_col=general_end); sheets.append(general)

    weekly_end=column(2*week_count+7); weekly=Sheet("SEMANAL",{1:24,**{i:15 for i in range(2,2*week_count+8)}},freeze="A5",autofilter=f"A4:{weekly_end}{n}"); title(weekly,"ACOMPANHAMENTO SEMANAL","Semanas automáticas de segunda-feira a domingo",weekly_end); weekly.add([]); header(weekly,["Vendedor",*[f"Vendas S{i}" for i in range(1,week_count+1)],*[f"Prêmio S{i}" for i in range(1,week_count+1)],"Total semanais","Melhor semana","Pior semana","Média semanal","Semana atual","Evolução"])
    current=min(week_count,((date(cfg["ano"],cfg["mes"],cfg["dia_referencia"])-date(cfg["ano"],cfg["mes"],1)).days+date(cfg["ano"],cfg["mes"],1).weekday())//7+1)
    for x in report_summary: weekly.add([x["vendedor"],*x["semanas"],*x["premios"],x["premio_total"],max(x["semanas"]),min(x["semanas"]),sum(x["semanas"])/week_count,current,x["semanas"][current-1]-x["semanas"][max(0,current-2)]],{i:5 for i in range(2+week_count,3+2*week_count)})
    weekly.color_scale(f"B5:{column(week_count+1)}{n}"); sheets.append(weekly)

    comm=Sheet("COMISSOES",{1:24,**{i:18 for i in range(2,17)}},freeze="A5",autofilter=f"A4:P{n}"); title(comm,"COMISSÕES E REMUNERAÇÃO",f"Cenário oficial: {'empresa >= 1.000' if official=='maior_ou_igual_1000' else 'empresa < 1.000'}","P"); comm.add([]); header(comm,["Vendedor","Vendas","Mínimo","R$/venda","Base atual","Bônus Neo atual","Bônus adimpl. atual","Semanais acumulados","Total atual","Premiação projetada","Bônus Neo proj.","Bônus adimpl. proj.","Total variável projetado","Próxima faixa","Faltam","Ganho adicional"])
    for x in report_summary: comm.add([x["vendedor"],x["vendas"],x["minimo"],x["taxa"],x["base"],x["bonus_neo"],x["bonus_adim"],x["premio_total"],x["total"],x["comissao_proj"],x["bonus_neo_proj"],x["bonus_adim_proj"],x["total_variavel_proj"],x["proxima"],x["faltam_proxima"],x["ganho_proxima"]],{i:5 for i in range(4,14)}|{16:5})
    comm.color_scale(f"I5:I{n}"); sheets.append(comm)

    conf=Sheet("CONFIGURACOES",{1:30,2:22,3:52},freeze="A5"); title(conf,"CONFIGURAÇÕES","Valores carregados de config.json; altere o JSON e gere novamente","C"); conf.add([]); header(conf,["Parâmetro","Valor","Observação"])
    vals=[("Mês",cfg["mes"],"Competência"),("Ano",cfg["ano"],"Competência"),("Dia de referência",cfg["dia_referencia"],"Data de corte"),("Meta empresa",cfg["meta_empresa"],"Meta mensal"),("Limite cenário",cfg["limite_cenario_maior"],"Régua oficial automática"),("Neo mínimo",cfg["bonus_neoenergia"]["percentual_minimo"],"Participação"),("Bônus Neo",cfg["bonus_neoenergia"]["percentual_bonus"],"Sobre premiação base"),("Bônus adimplência",cfg["bonus_adimplencia"]["percentual_bonus"],"Quando M2 = 100%")]
    for v in vals: conf.add(v,{2:4 if isinstance(v[1],float) else 3})
    conf.add([]); header(conf,["Faixa semanal","Prêmio",""]); [conf.add([x["vendas"],x["premio"],""]) for x in cfg["premiacao_semanal"]]; sheets.append(conf)

    cad=Sheet("CADASTRO VENDEDORES",{1:26,2:18,3:18,4:15,5:16},freeze="A5",autofilter=f"A4:E{len(cfg['vendedores'])+4}"); title(cad,"CADASTRO DE VENDEDORES","Cadastro mestre carregado de config.json","E"); cad.add([]); header(cad,["Vendedor","Setor","Categoria","Em experiência?","Meta individual"])
    for x in cfg["vendedores"]: cad.add([x["vendedor"],x["setor"],x["categoria"],"Sim" if x["experiencia"] else "Não",x["meta_individual"]])
    sheets.append(cad)

    base=Sheet("BASE IMPORTADA",{1:15,2:25,3:15,4:18,5:15,6:18,7:15,8:18},freeze="A5",autofilter=f"A4:H{len(rows)+4}"); title(base,"BASE IMPORTADA","Dados válidos lidos do CSV; IDs duplicados e status inválidos são descartados","H"); base.add([]); header(base,["Data da venda","Vendedor","Setor","Categoria","Neoenergia","Adimplência M2","Status","ID venda"])
    for x in rows: base.add([x["data_venda"].isoformat(),x["vendedor"],x["setor"],x["categoria"],x["neoenergia"],x["adimplencia_m2"],x["status"],x["id_venda"]])
    sheets.append(base); return sheets


def write_xlsx(path,sheets):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    types=['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>','<Default Extension="xml" ContentType="application/xml"/>','<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>','<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']+[f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1)]
    wb=''.join(f'<sheet name="{escape(s.name)}" sheetId="{i}" r:id="rId{i}"/>' for i,s in enumerate(sheets,1)); rel=''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    fonts='<fonts count="3"><font><sz val="10"/><name val="Aptos"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Aptos"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="18"/><name val="Aptos Display"/></font></fonts>'; fills='<fills count="7"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'+''.join(f'<fill><patternFill patternType="solid"><fgColor rgb="FF{COLORS[x]}"/></patternFill></fill>' for x in ("dark","blue","green","yellow","red"))+'</fills>'
    xfs=['<xf numFmtId="0" fontId="0" fillId="0" borderId="1"/>','<xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFill="1" applyFont="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>','<xf numFmtId="0" fontId="0" fillId="0" borderId="1"/>','<xf numFmtId="2" fontId="0" fillId="0" borderId="1" applyNumberFormat="1"/>','<xf numFmtId="10" fontId="0" fillId="0" borderId="1" applyNumberFormat="1"/>','<xf numFmtId="164" fontId="0" fillId="0" borderId="1" applyNumberFormat="1"/>','<xf numFmtId="14" fontId="0" fillId="0" borderId="1"/>','<xf numFmtId="0" fontId="2" fillId="2" borderId="1" applyFill="1" applyFont="1"/>','<xf numFmtId="0" fontId="1" fillId="3" borderId="1" applyFill="1" applyFont="1"/>','<xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFill="1" applyFont="1"/>','<xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFill="1" applyFont="1"/>','<xf numFmtId="0" fontId="1" fillId="4" borderId="1" applyFill="1"/>','<xf numFmtId="0" fontId="1" fillId="5" borderId="1" applyFill="1"/>','<xf numFmtId="10" fontId="1" fillId="4" borderId="1" applyFill="1"><alignment horizontal="center"/></xf>','<xf numFmtId="0" fontId="1" fillId="6" borderId="1" applyFill="1"/>','<xf numFmtId="164" fontId="1" fillId="4" borderId="1" applyFill="1"/>']
    dxfs='<dxfs count="4"><dxf><font><b/><color rgb="FFFFFFFF"/></font><fill><patternFill patternType="solid"><fgColor rgb="FF19A7CE"/></patternFill></fill></dxf><dxf><font><b/><color rgb="FFFFFFFF"/></font><fill><patternFill patternType="solid"><fgColor rgb="FF2EAD67"/></patternFill></fill></dxf><dxf><font><b/><color rgb="FF16324F"/></font><fill><patternFill patternType="solid"><fgColor rgb="FFF4C542"/></patternFill></fill></dxf><dxf><font><b/><color rgb="FFFFFFFF"/></font><fill><patternFill patternType="solid"><fgColor rgb="FFE55353"/></patternFill></fill></dxf></dxfs>'
    styles=f'<?xml version="1.0"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="1"><numFmt numFmtId="164" formatCode="R$ #,##0.00"/></numFmts>{fonts}{fills}<borders count="2"><border/><border><left style="thin"><color rgb="FFD7DEE5"/></left><right style="thin"><color rgb="FFD7DEE5"/></right><top style="thin"><color rgb="FFD7DEE5"/></top><bottom style="thin"><color rgb="FFD7DEE5"/></bottom></border></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="{len(xfs)}">{"".join(xfs)}</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0"/></cellStyles>{dxfs}</styleSheet>'
    with ZipFile(path,"w",ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",f'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{"".join(types)}</Types>'); z.writestr("_rels/.rels",'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'); z.writestr("xl/workbook.xml",f'<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><calcPr fullCalcOnLoad="1" forceFullCalc="1"/><sheets>{wb}</sheets></workbook>'); z.writestr("xl/_rels/workbook.xml.rels",f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rel}</Relationships>'); z.writestr("xl/styles.xml",styles)
        for i,s in enumerate(sheets,1): z.writestr(f"xl/worksheets/sheet{i}.xml",s.xml())
    return path


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--dados",default=ROOT/"dados_exemplo.csv",type=Path); p.add_argument("--config",default=ROOT/"config.json",type=Path); p.add_argument("--output",default=DEFAULT_OUTPUT,type=Path); args=p.parse_args(argv)
    rows,cfg=load_inputs(args.dados,args.config); summary,all_days,elapsed,official=summarize(rows,cfg); path=write_xlsx(args.output,build_sheets(rows,cfg,summary,all_days,elapsed,official)); print(f"Painel gerado: {path} ({len(rows)} vendas válidas)")


if __name__=="__main__": main()
