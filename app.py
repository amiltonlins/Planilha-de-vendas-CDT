#!/usr/bin/env python3
"""Painel Comercial Afogados — dashboard, histórico diário e gestão de vendedores."""
from __future__ import annotations
import copy, csv, hmac, html, io, json, os, re, tempfile, unicodedata, zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

from gerar_painel import ROOT, build_sheets, summarize, tier_value, write_xlsx

NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
PUBLISHED_PATH=Path(os.environ.get("PAINEL_DATA_PATH",ROOT/"data"/"dados_publicados.json"))
ALIASES={
 "data_venda":("data venda","data da venda","data","dt venda","criado em","data cadastro"),
 "vendedor":("vendedor","colaborador","consultor","nome vendedor","usuario","responsavel"),
 "setor":("setor","equipe","canal","franquia"),
 "categoria":("categoria","tipo vendedor","perfil"),
 "neoenergia":("nome","neoenergia","neoenergia celpe","produto","prospeccao","prospeccao produto","convenio","meio"),
 "adimplencia_m2":("adimplencia m2","m2","pago m2","status m2","adimplencia"),
 "status":("status","situacao","estado"),
 "id_venda":("id venda","id","codigo","numero","proposta","matricula")
}

def normalize_text(value):
    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

def detect_columns(headers):
    normalized={normalize_text(h):h for h in headers if h is not None}; result={}
    for target,aliases in ALIASES.items():
        for alias in aliases:
            if normalize_text(alias) in normalized:
                result[target]=normalized[normalize_text(alias)]; break
        if target not in result:
            for key,original in normalized.items():
                if any(len(normalize_text(a))>3 and normalize_text(a) in key for a in aliases):
                    result[target]=original; break
    if not {"data_venda","vendedor"}<=result.keys():
        raise ValueError("Não foi possível identificar as colunas de data e vendedor.")
    return result

def excel_date(value):
    if isinstance(value,(int,float)) or (str(value).replace(".","",1).isdigit() and float(value)>1000):
        return (date(1899,12,30)+timedelta(days=int(float(value)))).isoformat()
    text=str(value).strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M"):
        try:return datetime.strptime(text,fmt).date().isoformat()
        except ValueError:pass
    raise ValueError(f"Data inválida: {text}")

def rows_from_csv(data):
    text=data.decode("utf-8-sig",errors="replace")
    try:dialect=csv.Sniffer().sniff(text[:4096],delimiters=",;\t|")
    except csv.Error:dialect=csv.excel
    return list(csv.DictReader(io.StringIO(text),dialect=dialect))

def _xlsx_sheets(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(x.text or "" for x in si.iterfind(".//m:t",NS)) for si in root.findall("m:si",NS)]
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        relroot=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels={x.attrib["Id"]:x.attrib["Target"] for x in relroot}
        for sheet in workbook.findall(".//m:sheet",NS):
            target=rels[sheet.attrib[f"{{{NS['r']}}}id"]]
            path=target.lstrip("/"); path=path if path.startswith("xl/") else "xl/"+path
            root=ET.fromstring(z.read(path)); table=[]
            for row in root.findall(".//m:sheetData/m:row",NS):
                values={}
                for cell in row.findall("m:c",NS):
                    letters=re.match(r"[A-Z]+",cell.attrib["r"]).group(); idx=0
                    for ch in letters:idx=idx*26+ord(ch)-64
                    typ=cell.attrib.get("t"); value=""
                    if typ=="inlineStr":value="".join(x.text or "" for x in cell.findall(".//m:t",NS))
                    else:
                        node=cell.find("m:v",NS); value=node.text if node is not None else ""
                        if typ=="s" and value:value=shared[int(value)]
                    values[idx-1]=value
                if values:table.append([values.get(i,"") for i in range(max(values)+1)])
            yield sheet.attrib["name"],table

def rows_from_xlsx(data):
    best=None
    for _,table in _xlsx_sheets(data):
        for index,row in enumerate(table[:30]):
            try:mapping=detect_columns(row)
            except ValueError:continue
            candidate=(len(mapping),row,table[index+1:])
            if best is None or candidate[0]>best[0]:best=candidate
    if not best:raise ValueError("Nenhuma aba de vendas reconhecida no XLSX.")
    _,headers,body=best
    return [{str(headers[i]):row[i] if i<len(row) else "" for i in range(len(headers)) if str(headers[i]).strip()} for row in body if any(str(x).strip() for x in row)]

def canonicalize(raw_rows,base_config):
    if not raw_rows:raise ValueError("O relatório está vazio.")
    mapping=detect_columns(raw_rows[0].keys()); output=[]; seen=set()
    valid={normalize_text(x) for x in base_config["status_validos"]}
    for number,row in enumerate(raw_rows,1):
        try:day=excel_date(row.get(mapping["data_venda"],""))
        except ValueError:continue
        seller=str(row.get(mapping["vendedor"],"")).strip()
        if not seller:continue
        product=str(row.get(mapping.get("neoenergia",""),""))
        status=str(row.get(mapping.get("status",""),"Aprovada") or "Aprovada")
        identifier=str(row.get(mapping.get("id_venda",""),"") or f"UPLOAD-{day}-{seller}-{number}")
        if identifier in seen or normalize_text(status) not in valid:continue
        seen.add(identifier)
        output.append({
            "data_venda":datetime.strptime(day,"%Y-%m-%d").date(),
            "vendedor":seller,
            "setor":str(row.get(mapping.get("setor",""),"NÃO INFORMADO") or "NÃO INFORMADO"),
            "categoria":str(row.get(mapping.get("categoria",""),"Vendedor") or "Vendedor"),
            "neoenergia":"Sim" if "neoenergia celpe" in normalize_text(product) or normalize_text(product) in ("neoenergia","sim","1","true") else "Não",
            "adimplencia_m2":str(row.get(mapping.get("adimplencia_m2",""),"0") or "0"),
            "status":status,"id_venda":identifier})
    if not output:raise ValueError("Nenhuma venda válida após filtros de status e duplicidade.")
    return output,mapping

def merge_registry(base,current):
    cfg=copy.deepcopy(current or base)
    known={normalize_text(x["vendedor"]):x for x in cfg.get("vendedores",[])}
    for seller in base.get("vendedores",[]):
        key=normalize_text(seller["vendedor"])
        if key not in known or not known[key].get("classificado",False):known[key]=copy.deepcopy(seller)
    cfg["vendedores"]=list(known.values())
    return cfg

def prepare_config(base,rows,month,year):
    cfg=copy.deepcopy(base); cfg["mes"],cfg["ano"]=month,year
    existing={normalize_text(x["vendedor"]):x for x in cfg.get("vendedores",[])}; sellers=[]
    for name in sorted({x["vendedor"] for x in rows},key=normalize_text):
        sample=next(x for x in rows if x["vendedor"]==name); old=existing.get(normalize_text(name),{})
        inferred=next((label for label in ("Website","ADM","Freelance") if normalize_text(label) in normalize_text(name)),sample["categoria"])
        registered=bool(old); belongs=old.get("pertence_franquia",registered)
        category=old.get("categoria",inferred if registered else "Canal Nacional")
        sellers.append({"vendedor":name,"setor":old.get("setor",sample["setor"]),"categoria":category,
            "pertence_franquia":belongs,"classificado":old.get("classificado",registered),"ativo":old.get("ativo",registered),
            "experiencia":old.get("experiencia",False),"meta_individual":old.get("meta_individual",70),
            "trabalha_sabado":old.get("trabalha_sabado",True),"trabalha_domingo":old.get("trabalha_domingo",False),
            "data_inicio":old.get("data_inicio",f"{year}-01-01"),"data_desligamento":old.get("data_desligamento",""),"folgas":old.get("folgas",[])})
    cfg["vendedores"]=sellers; return cfg

def merge_daily_history(current_rows,incoming_rows):
    if not incoming_rows:return current_rows,[]
    imported_days={x["data_venda"] for x in incoming_rows}
    kept=[x for x in current_rows if x["data_venda"] not in imported_days]
    dedup={}
    for row in kept+incoming_rows:dedup[str(row["id_venda"])]=row
    merged=sorted(dedup.values(),key=lambda x:(x["data_venda"],normalize_text(x["vendedor"]),str(x["id_venda"])))
    return merged,sorted(imported_days)

def serialize_row(row):
    out=dict(row); out["data_venda"]=row["data_venda"].isoformat(); return out

def save_published(rows,cfg,source_name,history=None,updated_at=None):
    updated_at=updated_at or datetime.now(); PUBLISHED_PATH.parent.mkdir(parents=True,exist_ok=True)
    payload={"atualizado_em":updated_at.isoformat(timespec="seconds"),"arquivo":Path(source_name).name,
             "config":cfg,"historico_importacoes":history or [],"vendas":[serialize_row(row) for row in rows]}
    temporary=PUBLISHED_PATH.with_suffix(".tmp"); temporary.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8"); temporary.replace(PUBLISHED_PATH)

def load_published(base):
    if PUBLISHED_PATH.exists():
        payload=json.loads(PUBLISHED_PATH.read_text(encoding="utf-8")); rows=payload.get("vendas",[])
        for row in rows:row["data_venda"]=datetime.strptime(row["data_venda"],"%Y-%m-%d").date()
        return rows,merge_registry(base,payload.get("config",base)),payload
    raw=rows_from_csv((ROOT/"dados_exemplo.csv").read_bytes()); rows,_=canonicalize(raw,base); cfg=prepare_config(base,rows,base["mes"],base["ano"])
    return rows,cfg,{"atualizado_em":datetime.now().isoformat(timespec="seconds"),"arquivo":"dados_exemplo.csv","demonstracao":True,"historico_importacoes":[]}

def performance(media):
    media=float(media or 0)
    if media>=2.0:return "Azul","#0891B2","cyan"
    if media>=1.5:return "Verde","#16A34A","green"
    if media>=1.0:return "Amarelo","#F59E0B","yellow"
    return "Vermelho","#DC2626","red"

def money(value):return f"R$ {value:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def pct(value):return f"{value:.1%}".replace(".",",")
FIXED_DASHBOARD_USERS={
    "Amilton Lins":("amilton lins","hamilton lins"),
    "Sheyla Santos":("sheyla santos","sheila santos"),
    "Joice Larissa":("joice larissa","joyce larissa"),
    "Rafael Salgado":("rafael salgado","raphael salgado"),
}

def first_name(value):
    return str(value or "").strip().split()[0] if str(value or "").strip() else ""

def first_two_names(value):
    parts=str(value or "").strip().split()
    return " ".join(parts[:2]) if len(parts)>=2 else ""

def authorized_dashboard_users(cfg):
    identities={}
    for display,aliases in FIXED_DASHBOARD_USERS.items():
        for alias in aliases:
            identities[normalize_text(alias)]={"display":display,"full":display,"fixed":True}
    for seller in cfg.get("vendedores",[]):
        if not seller.get("ativo",False):continue
        full=str(seller.get("vendedor","")).strip()
        key=normalize_text(first_two_names(full))
        if not key:continue
        identities.setdefault(key,{"display":first_two_names(full),"full":full,"fixed":False})
    return identities

def authenticate_dashboard_name(cfg,provided_first,provided_full=""):
    candidate=(provided_full or provided_first or "").strip()
    key=normalize_text(first_two_names(candidate))
    if not key:return None,"invalid"
    selected=authorized_dashboard_users(cfg).get(key)
    return (selected["display"],"ok") if selected else (None,"invalid")

def is_mobile_client(st):
    try:
        ua=str(st.context.headers.get("User-Agent","")).lower()
    except Exception:
        return False
    return any(token in ua for token in ("iphone","ipad","ipod","android","mobile"))

def validate_xlsx_bytes(data,required_sheet=None):
    if not data:raise ValueError("Arquivo XLSX vazio.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:raise ValueError("Estrutura ZIP do XLSX inválida.")
            names=set(archive.namelist())
            for required in ("[Content_Types].xml","xl/workbook.xml","xl/_rels/workbook.xml.rels"):
                if required not in names:raise ValueError(f"Componente XLSX ausente: {required}")
            ET.fromstring(archive.read("xl/workbook.xml"))
        sheets=list(_xlsx_sheets(data))
        if not sheets:raise ValueError("O XLSX não contém planilhas legíveis.")
        if required_sheet and required_sheet not in {name for name,_ in sheets}:raise ValueError(f"A aba {required_sheet} não foi encontrada no XLSX.")
    except (zipfile.BadZipFile,ET.ParseError,KeyError,IndexError,ValueError) as exc:
        if isinstance(exc,ValueError):raise
        raise ValueError(f"XLSX inválido: {exc}") from exc
    return True

def general_report_display(team):
    display=[]
    for item in sorted(team,key=lambda z:(z["vendas"],z["projecao"]),reverse=True):
        display.append(item|{
            "media":f'{item["media"]:.2f}',
            "meta_pct":pct(item["projecao"]/item["meta_individual"] if item["meta_individual"] else 0),
            "neo_pct_fmt":pct(item["neo_pct"]),
            "base_fmt":money(item["base"]),
            "proj_fmt":money(item["comissao_proj"]),
            "neo_proj_fmt":money(item["bonus_neo_proj"]),
            "adim_proj_fmt":money(item["bonus_adim_proj"]),
            "premio_fmt":money(item["premio_total"]),
            "total_proj_fmt":money(item["total_variavel_proj"])})
    return display

def render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color):
    st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True)
    cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","PREMIAÇÃO ATUAL"),("proj_fmt","PREMIAÇÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS (SE) 100% ADIM"),("premio_fmt","SEMANAIS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]
    display=general_report_display(team)
    st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)
    try:
        with tempfile.TemporaryDirectory() as folder:
            general_path=Path(folder)/"Relatorio_Geral_Equipe_Afogados.xlsx"
            general_sheet=next(s for s in build_sheets(rows,cfg,summary,all_days,elapsed,official) if s.name=="RELATORIO GERAL")
            write_xlsx(general_path,[general_sheet])
            general_book=general_path.read_bytes()
        validate_xlsx_bytes(general_book,"RELATORIO GERAL")
        st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=False)
    except Exception as exc:
        st.error(f"Não foi possível gerar um XLSX válido do Relatório Geral: {exc}")

def manager_password(st):
    try:return str(st.secrets["GESTOR_SENHA"])
    except (KeyError,FileNotFoundError):return os.environ.get("GESTOR_SENHA","")
def card(label,value,tone="cyan",sub=""):return f'<div class="metric {tone}"><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong><small>{html.escape(sub)}</small></div>'
def cards(st,items,columns=4):
    cols=st.columns(columns)
    for i,item in enumerate(items):cols[i%columns].markdown(card(*item),unsafe_allow_html=True)
def regular(summary):return [x for x in summary if x.get("elegivel_individual",True)]
def channel_name(item):
    if not item.get("pertence_franquia",True) or normalize_text(item.get("categoria"))=="canal nacional":return "CANAL NACIONAL"
    category=normalize_text(item.get("categoria"))
    if category in {"website","adm","freelance"}:return category.upper()
    return "VENDEDORES FRANQUIA"

def table_html(records,columns,row_color=None,daily=False):
    heads="".join(f"<th>{html.escape(str(label))}</th>" for _,label in columns); body=[]
    for rec in records:
        color=row_color(rec) if row_color else "#fff"; cells=[]
        for key,_ in columns:
            value=rec.get(key,""); style=""
            if key=="vendedor" and row_color:style=f"background:{color};color:white;font-weight:900"
            if daily and isinstance(key,int):
                elapsed=rec.get("dias_decorridos",set()); scheduled=rec.get("dias_agendados",set()); diario=rec.get("diario",{})
                if key not in elapsed:style="background:#F1F5F9;color:#94A3B8"; value=""
                elif key in scheduled and diario.get(key,0)==0:style="background:#FEE2E2;color:#B91C1C;font-weight:800"; value=0
                elif diario.get(key,0)>=3:style="background:#CFFAFE;color:#155E75;font-weight:800"; value=diario.get(key,0)
                else:value=diario.get(key,0)
            cells.append(f'<td style="{style}">{html.escape(str(value))}</td>')
        body.append(f'<tr>{"".join(cells)}</tr>')
    return f'<div class="table-wrap"><table class="report"><thead><tr>{heads}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'

def executive_kpis_html(cfg,total,projection,neo,team):
    meta=cfg["meta_empresa"]
    ating=total/meta if meta else 0
    faltam=max(0,meta-total)
    neo_pct=neo/total if total else 0
    zeros=sum(x["zeros"] for x in team)
    return (
        '<div class="exec-grid">'
        f'<div class="exec-card hero"><small>VENDAS REALIZADAS</small><strong>{total}</strong><span>Resultado atual</span></div>'
        f'<div class="exec-card"><small>META DO MÊS</small><strong>{meta}</strong><span>Objetivo comercial</span></div>'
        f'<div class="exec-card projection"><small>PROJEÇÃO</small><strong>{projection}</strong><span>Fechamento estimado</span></div>'
        f'<div class="exec-card attainment"><small>% DA META</small><strong>{pct(ating)}</strong><span>Atingimento atual</span></div>'
        f'<div class="exec-card secondary"><small>FALTAM PARA META</small><strong>{faltam}</strong><span>Vendas necessárias</span></div>'
        f'<div class="exec-card secondary"><small>VENDAS NEO</small><strong>{neo}</strong><span>{pct(neo_pct)} do total</span></div>'
        f'<div class="exec-card secondary"><small>% NEO</small><strong>{pct(neo_pct)}</strong><span>Participação</span></div>'
        '</div>'
    )

def performance_summary_html(counts):
    items=[
        ("Azul",counts.get("Azul",0),"#0891B2"),
        ("Verde",counts.get("Verde",0),"#16A34A"),
        ("Amarelo",counts.get("Amarelo",0),"#F59E0B"),
        ("Vermelho",counts.get("Vermelho",0),"#DC2626"),
    ]
    chips=''.join(
        f'<div class="perf-chip" style="--chip:{color}"><span>{label}</span><strong>{value}</strong></div>'
        for label,value,color in items
    )
    return f'<div class="perf-summary">{chips}</div>'

def channel_summary_html(channels,total):
    groups=[
        (("VENDEDORES FRANQUIA",channels.get("VENDEDORES FRANQUIA",0)),("WEBSITE",channels.get("WEBSITE",0))),
        (("FREELANCE",channels.get("FREELANCE",0)),("CANAL NACIONAL",channels.get("CANAL NACIONAL",0))),
    ]
    cards=[]
    for pair in groups:
        inner=''.join(
            f'<div class="channel-mini"><span>{name}</span><strong>{value}</strong><small>{pct(value/total if total else 0)} do total</small></div>'
            for name,value in pair
        )
        cards.append(f'<div class="channel-group">{inner}</div>')
    return '<div class="channel-summary">'+''.join(cards)+'</div>'

def projection_status_visual(projected_ratio, meta_value=None, projection_value=None):
    try:
        if meta_value in (None, 0, "") or projection_value in (None, ""):
            return "🙂", "AGUARDANDO DADOS"
        ratio=float(projected_ratio)
        if ratio != ratio or ratio < 0:  # NaN ou inválido
            return "🙂", "AGUARDANDO DADOS"
    except (TypeError, ValueError, ZeroDivisionError):
        return "🙂", "AGUARDANDO DADOS"

    if ratio < 0.40:return "😭", "MUITO ABAIXO"
    if ratio < 0.60:return "😟", "ATENÇÃO"
    if ratio < 0.80:return "😐", "PRECISA ACELERAR"
    if ratio < 0.90:return "🙂", "BOM RITMO"
    if ratio < 1.00:return "😄", "QUASE LÁ!"
    if ratio < 1.20:return "😎", "META NO CAMINHO!"
    return "🤩", "VOANDO!"


def projection_status_card(emoji,message):
    return (
        '<div class="seller-kpi projection-status">'
        f'<div class="projection-status-emoji">{emoji}</div>'
        f'<div class="projection-status-message">{html.escape(str(message))}</div>'
        '</div>'
    )

def seller_kpi_card(label,value,sub,cls):
    return f'<div class="seller-kpi {cls}"><small>{html.escape(str(label))}</small><strong>{html.escape(str(value))}</strong><span>{html.escape(str(sub))}</span></div>'

def seller_kpis_html(x):
    meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
    status,_,_=performance(x["media"])
    commercial=[
        ("VENDAS",x["vendas"],"Produção","primary mobile-duplicate"),
        ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"level2 mobile-duplicate"),
        ("MÉDIA/DIA",f'{x["media"]:.2f}',f'{x["dias"]} dias',"level2"),
        ("% META",pct(meta_pct),status,"level2"),
        ("ZEROS",x["zeros"],f'Semana {x["zeros_semana"]}',"level3"),
        ("NEO",x["neo"],"Neoenergia","level3"),
        ("% NEO",pct(x["neo_pct"]),"Participação","level3"),
    ]
    awards=[
        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary mobile-duplicate"),
        ("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"Base projetada","level2"),
        ("BÔNUS NEO PROJETADO",money(x["bonus_neo_proj"]),"Projeção","level3"),
        ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"Condicional","level3"),
        ("SEMANAIS",money(x["premio_total"]),"Acumulado semanal","level3"),
        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total mobile-duplicate"),
    ]
    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)
    awards_html=''.join(seller_kpi_card(*item) for item in awards)
    mobile_primary=[
        ("VENDAS",x["vendas"],"Produção","primary"),
        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary"),
        ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"primary mobile-projection"),
        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total"),
    ]
    mobile_html=''.join(seller_kpi_card(*item) for item in mobile_primary)
    return (
        f'<div class="seller-mobile-primary">{mobile_html}</div>'
        '<div class="seller-groups">'
        '<div class="seller-group-title">DESEMPENHO COMERCIAL</div>'
        f'<div class="seller-kpi-grid">{commercial_html}</div>'
        '<div class="seller-group-title award">PREMIAÇÃO</div>'
        f'<div class="seller-kpi-grid award-grid">{awards_html}</div>'
        '</div>'
    )

def ranking_html(ranking):
    medals=("🥇","🥈","🥉")
    rows=[]
    for i,x in enumerate(ranking):
        _,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))
        rows.append(
            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'
            f'<a class="rank-click" href="?seller={html.escape(str(x["vendedor"]),quote=True)}" target="_self">'
            f'<div class="rank-name" style="background:{color}">' 
            f'<div class="rank-seller"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'
            f'<div class="rank-inside">'
            f'<span class="main-kpi"><strong>{x["vendas"]}</strong><small>VENDAS</small></span>'
            f'<span class="main-kpi"><strong>{x["projecao"]}</strong><small>PROJEÇÃO</small></span>'
            f'<span><strong>{x["media"]:.2f}</strong><small>MÉDIA/DIA</small></span>'
            f'<span><strong>{x["zeros"]}</strong><small>ZEROS</small></span>'
            f'<span><strong>{pct(meta_pct)}</strong><small>% META</small></span>'
            f'<span class="neo-highlight"><strong>{x["neo"]}</strong><small>NEO</small></span>'
            f'<span class="neo-highlight"><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'
            f'<span><strong>{money(x["base"])}</strong><small>PREMIAÇÃO ATUAL</small></span>'
            f'<span><strong>{money(x["comissao_proj"])}</strong><small>PREMIAÇÃO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_neo_proj"])}</strong><small>BÔNUS NEO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_adim_proj"])}</strong><small>BÔNUS (SE) 100% ADIM</small></span>'
            f'<span><strong>{money(x["premio_total"])}</strong><small>SEMANAIS</small></span>'
            f'<span class="total-highlight"><strong>{money(x["total_variavel_proj"])}</strong><small>TOTAL VAR. PROJ.</small></span>'
            f'<span class="rank-projection-status"><strong class="rank-status-emoji">{status_emoji}</strong><small>{html.escape(status_message)}</small></span>'
            f'</div></div></a></div>'
        )
    return '<div class="rank-card">'+''.join(rows)+'</div>' if rows else '<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>'

def daily_series(rows,cfg,data_until):
    relevant=[x for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"] and x["data_venda"]<=data_until]
    by_day={}
    for row in relevant:by_day[row["data_venda"].day]=by_day.get(row["data_venda"].day,0)+1
    last=max(1,data_until.day); cumulative=[]; ideal=[]; running=0
    for day in range(1,last+1):
        running+=by_day.get(day,0); cumulative.append(running); ideal.append(round(cfg["meta_empresa"]*day/31))
    return cumulative,ideal

CSS="""<style>
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none!important}
:root{--navy:#0F172A;--ink:#111827;--muted:#64748B;--line:#E2E8F0;--surface:#FFFFFF;--bg:#F4F7FB;--cyan:#0EA5E9;--green:#22C55E;--amber:#F59E0B;--red:#EF4444}
.stApp{background:var(--bg);color:var(--ink)}.block-container{padding:1rem 1.5rem 2.5rem;max-width:1920px}[data-testid="stSidebar"]{display:none!important}
.bi-topbar{background:linear-gradient(110deg,#0F172A,#172554);color:white;border-radius:14px;padding:18px 22px;margin:0 0 10px;box-shadow:0 8px 30px rgba(15,23,42,.12)}.bi-topbar h1{font-size:1.42rem;margin:0;font-weight:800;letter-spacing:-.02em}.bi-topbar p{margin:4px 0 0;color:#CBD5E1;font-size:.78rem}
.section{font-size:.83rem;font-weight:800;color:#334155;padding:5px 0;margin:14px 0 7px;letter-spacing:.035em;text-transform:uppercase}.metric{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 14px;min-height:92px;margin:2px 0 5px;box-shadow:0 2px 10px rgba(15,23,42,.045);overflow:hidden}.metric:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--cyan)}.metric span{display:block;font-size:.66rem;font-weight:800;color:#64748B;letter-spacing:.05em;text-transform:uppercase}.metric strong{display:block;font-size:1.65rem;line-height:1.15;color:#0F172A;margin-top:8px;font-weight:800}.metric small{display:block;font-size:.68rem;color:#94A3B8;margin-top:5px}.metric.green:before{background:var(--green)}.metric.yellow:before{background:var(--amber)}.metric.red:before{background:var(--red)}
.bi-panel{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(15,23,42,.04)}.rank-card{background:white;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(15,23,42,.04)}.rank-row{display:grid;grid-template-columns:54px 1fr;align-items:center;gap:10px;padding:9px 13px;border-bottom:1px solid #EEF2F7}.rank-row:last-child{border-bottom:0}.rank-pos{font-weight:900;text-align:center}.rank-name{display:grid;grid-template-columns:minmax(220px,.9fr) 3.6fr;align-items:start;gap:14px;min-width:0;padding:12px;border-radius:10px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-seller{display:flex;flex-direction:column;min-width:0;padding-top:4px}.rank-seller b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.94rem}.rank-seller small{font-size:.65rem;color:rgba(255,255,255,.82)}.rank-inside{display:grid;grid-template-columns:repeat(7,minmax(92px,1fr));gap:7px;align-items:stretch}.rank-inside span{display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:54px;padding:5px 7px;border-left:1px solid rgba(255,255,255,.25);text-align:center}.rank-inside strong{font-size:.92rem;line-height:1.08;font-weight:900;white-space:nowrap}.rank-inside small{font-size:.54rem;color:rgba(255,255,255,.84);margin-top:5px}.rank-inside .main-kpi strong{font-size:1.35rem}.rank-inside .neo-highlight{background:rgba(255,255,255,.14);border-radius:8px}.rank-inside .neo-highlight strong{font-size:1.5rem;text-shadow:0 1px 2px rgba(0,0,0,.18)}.rank-inside .total-highlight{background:rgba(15,23,42,.22);border-radius:8px}.rank-inside .total-highlight strong{font-size:1.05rem}
.table-wrap{overflow:auto;max-height:590px;border:1px solid var(--line);border-radius:12px;background:white}.report{border-collapse:separate;border-spacing:0;white-space:nowrap;width:100%;font-size:.72rem}.report th{position:sticky;top:0;background:#0F172A;color:white;padding:8px 9px;z-index:2;font-size:.65rem}.report td{border-right:1px solid #EEF2F7;border-bottom:1px solid #EEF2F7;padding:6px 8px;text-align:center}.report tr:hover td{background-color:#F8FAFC}.empty-bi{background:white;border:1px dashed #CBD5E1;border-radius:12px;padding:22px;text-align:center;color:#64748B}
.stButton button,.stDownloadButton button{border-radius:9px;background:#0F172A;color:white;border:0;font-weight:750;min-height:40px}.stButton button:hover,.stDownloadButton button:hover{background:#1E293B;color:white;border:0}[data-testid="stPopover"] button{border-radius:10px!important;background:#0F172A!important;color:white!important;border:1px solid #334155!important;min-width:48px!important;font-size:1.35rem!important}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}.element-container{margin-bottom:.2rem}
@media(max-width:1250px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px 1fr}.rank-name{grid-template-columns:1fr}.rank-inside{grid-template-columns:repeat(4,1fr)}.metric strong{font-size:1.35rem}}@media(max-width:720px){.bi-topbar{padding:14px}.bi-topbar h1{font-size:1.05rem}.rank-row{grid-template-columns:38px 1fr;padding:7px 4px}.rank-inside{grid-template-columns:repeat(2,1fr)}.block-container{padding:.5rem}}

.exec-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0 14px}.exec-card{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(15,23,42,.05);min-width:0}.exec-card small{display:block;font-size:.64rem;font-weight:900;letter-spacing:.055em;color:#64748B}.exec-card strong{display:block;font-size:1.8rem;line-height:1.05;margin-top:7px;color:#0F172A;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.exec-card span{display:block;font-size:.67rem;color:#94A3B8;margin-top:5px}.exec-card.hero{grid-column:span 2;background:linear-gradient(120deg,#0F172A,#172554);border-color:#172554}.exec-card.hero small,.exec-card.hero strong,.exec-card.hero span{color:white}.exec-card.hero strong{font-size:2.35rem}.exec-card.projection{border-top:4px solid #F59E0B}.exec-card.attainment{border-top:4px solid #22C55E}.exec-card.critical{border-top:4px solid #EF4444}.seller-groups{margin-top:12px}.seller-group-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;color:#475569;margin:14px 0 7px}.seller-group-title.award{margin-top:18px}.seller-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.seller-kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:12px;min-width:0}.seller-kpi small{display:block;font-size:.59rem;font-weight:900;color:#64748B;letter-spacing:.035em}.seller-kpi strong{display:block;font-size:1.2rem;color:#0F172A;margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.seller-kpi span{display:block;font-size:.63rem;color:#94A3B8;margin-top:4px}.seller-kpi.primary{background:#0F172A;border-color:#0F172A}.seller-kpi.primary small,.seller-kpi.primary strong,.seller-kpi.primary span{color:white}.seller-kpi.primary strong{font-size:1.55rem}.seller-kpi.total{background:linear-gradient(120deg,#0F172A,#172554)}
@media(max-width:900px){.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.exec-card.hero{grid-column:span 2}.exec-card.hero strong{font-size:2rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-name{grid-template-columns:1fr}.rank-inside strong{white-space:normal;overflow-wrap:anywhere}.report{font-size:.68rem}}
@media(max-width:560px){.block-container{padding:.45rem!important}.bi-topbar{border-radius:10px;padding:12px}.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.exec-card{padding:11px 10px;border-radius:11px}.exec-card.hero{grid-column:span 2}.exec-card strong{font-size:1.35rem}.exec-card.hero strong{font-size:1.9rem}.exec-card small{font-size:.56rem}.exec-card span{font-size:.58rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.seller-kpi{padding:10px 9px}.seller-kpi strong{font-size:1.05rem}.seller-kpi.primary strong{font-size:1.3rem}.rank-row{grid-template-columns:34px minmax(0,1fr)!important;padding:6px 2px!important}.rank-pos{font-size:.8rem}.rank-name{padding:9px!important;gap:8px!important}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))!important}.rank-inside span{min-width:0}.rank-inside strong{font-size:.86rem!important;white-space:normal!important;overflow-wrap:anywhere}.rank-inside .neo-highlight strong{font-size:1.05rem!important}.rank-seller b{white-space:normal!important}.metric strong{white-space:normal;overflow-wrap:anywhere}.stDownloadButton button{width:100%}}

.seller-mobile-primary{display:none}
@media(max-width:560px){.seller-mobile-primary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:12px}.seller-kpi-grid .mobile-duplicate{display:none}.seller-mobile-primary .seller-kpi{min-width:0}.seller-mobile-primary .seller-kpi strong{white-space:normal;overflow-wrap:anywhere}.seller-groups{margin-top:8px}}


.perf-summary{background:white;border:1px solid var(--line);border-radius:14px;padding:12px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;box-shadow:0 2px 10px rgba(15,23,42,.04)}.perf-chip{position:relative;border:1px solid #E2E8F0;border-radius:11px;padding:12px 14px;background:#F8FAFC;overflow:hidden}.perf-chip:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--chip)}.perf-chip span{display:block;font-size:.64rem;font-weight:900;color:#64748B;text-transform:uppercase;letter-spacing:.05em}.perf-chip strong{display:block;font-size:1.65rem;margin-top:6px;color:#0F172A}.channel-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.channel-group{background:white;border:1px solid var(--line);border-radius:14px;padding:12px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;box-shadow:0 2px 10px rgba(15,23,42,.04)}.channel-mini{border:1px solid #E2E8F0;border-radius:11px;padding:13px 14px;background:#F8FAFC;min-width:0}.channel-mini span{display:block;font-size:.64rem;font-weight:900;color:#64748B;letter-spacing:.04em}.channel-mini strong{display:block;font-size:1.75rem;line-height:1.05;margin-top:7px;color:#0F172A}.channel-mini small{display:block;font-size:.66rem;color:#94A3B8;margin-top:5px}
@media(max-width:720px){.perf-summary{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;padding:8px}.perf-chip{padding:10px 11px}.perf-chip strong{font-size:1.4rem}.channel-summary{grid-template-columns:1fr;gap:8px}.channel-group{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;padding:8px}.channel-mini{padding:10px}.channel-mini strong{font-size:1.4rem}.rank-card{border-radius:12px}.rank-row{grid-template-columns:28px minmax(0,1fr)!important;gap:4px!important;padding:5px 3px!important}.rank-pos{font-size:.72rem}.rank-name{padding:9px!important;border-radius:10px!important;gap:7px!important}.rank-seller{padding-top:0!important;margin-bottom:3px}.rank-seller b{font-size:.9rem!important;line-height:1.15}.rank-seller small{font-size:.57rem!important}.rank-inside{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:5px!important}.rank-inside span{grid-column:span 2;min-height:42px!important;padding:5px 3px!important;border-left:0!important;border:1px solid rgba(255,255,255,.18);border-radius:7px;background:rgba(255,255,255,.06)}.rank-inside .main-kpi{grid-column:span 3!important;background:rgba(15,23,42,.20)}.rank-inside .main-kpi strong{font-size:1.55rem!important}.rank-inside .main-kpi small{font-size:.58rem!important;font-weight:800}.rank-inside strong{font-size:.82rem!important;line-height:1.05!important}.rank-inside small{font-size:.49rem!important;margin-top:3px!important}.rank-inside .neo-highlight{grid-column:span 2!important}.rank-inside .total-highlight{grid-column:span 3!important}.rank-inside .total-highlight strong{font-size:.98rem!important}}


.projection-status{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:white;border:1px solid var(--line);box-shadow:none;min-height:100%}.projection-status-emoji{font-size:2.25rem;line-height:1;margin:1px 0 8px}.projection-status-message{font-size:.70rem;line-height:1.15;font-weight:900;letter-spacing:.035em;color:#475569;text-align:center;word-break:normal;overflow-wrap:break-word}
@media(max-width:560px){.projection-status{padding:9px 7px!important;min-height:82px}.projection-status-emoji{font-size:1.8rem;margin-bottom:6px}.projection-status-message{font-size:.58rem;line-height:1.12}}


.rank-inside .rank-projection-status{background:rgba(255,255,255,.12);border-radius:8px;border-left:0}.rank-inside .rank-projection-status .rank-status-emoji{font-size:1.7rem;line-height:1}.rank-inside .rank-projection-status small{font-size:.52rem;font-weight:900;line-height:1.05;text-align:center}
@media(max-width:720px){.rank-inside .rank-projection-status{grid-column:span 2!important}.rank-inside .rank-projection-status .rank-status-emoji{font-size:1.45rem!important}.rank-inside .rank-projection-status small{font-size:.46rem!important;line-height:1.05!important}}


.bi-topbar-nav{display:flex;align-items:center;justify-content:space-between;gap:24px}.bi-brand{min-width:0;flex:1}.top-nav{display:flex;align-items:center;justify-content:flex-end;gap:6px;flex-wrap:wrap}.top-nav-item{display:inline-flex;align-items:center;justify-content:center;padding:9px 12px;border-radius:9px;color:#CBD5E1!important;text-decoration:none!important;font-size:.68rem;font-weight:800;letter-spacing:.02em;white-space:nowrap;border:1px solid transparent;transition:.15s ease}.top-nav-item:hover{background:rgba(255,255,255,.09);color:white!important}.top-nav-item.active{background:white;color:#0F172A!important;border-color:rgba(255,255,255,.7);box-shadow:0 2px 8px rgba(0,0,0,.12)}
@media(max-width:980px){.bi-topbar-nav{align-items:flex-start;flex-direction:column;gap:12px}.top-nav{justify-content:flex-start;width:100%}.top-nav-item{padding:8px 10px;font-size:.62rem}}
@media(max-width:560px){.bi-topbar-nav{gap:10px}.top-nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.top-nav-item{width:100%;padding:8px 6px;font-size:.58rem}.top-nav-item:last-child{grid-column:span 2}.bi-brand p{font-size:.68rem!important}}


/* Navegação nativa: troca apenas a área da aplicação, sem abrir nova página/aba. */
[data-testid="stSegmentedControl"]{margin-top:-18px;margin-bottom:10px;background:#172554;border-radius:0 0 14px 14px;padding:0 16px 14px}
[data-testid="stSegmentedControl"] button{color:#CBD5E1!important;border-color:rgba(255,255,255,.16)!important;font-weight:800!important;font-size:.68rem!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#FFFFFF!important;color:#0F172A!important;border-color:#FFFFFF!important}
[data-testid="stSegmentedControl"] button:hover{background:rgba(255,255,255,.10)!important;color:white!important}
@media(max-width:720px){[data-testid="stSegmentedControl"]{padding:0 8px 10px;overflow-x:auto}[data-testid="stSegmentedControl"]>div{min-width:max-content}[data-testid="stSegmentedControl"] button{font-size:.58rem!important;padding-left:8px!important;padding-right:8px!important}}


.rank-click{display:block;color:inherit!important;text-decoration:none!important;min-width:0}.rank-click:hover .rank-name{filter:brightness(1.03);box-shadow:0 4px 12px rgba(15,23,42,.18);transform:translateY(-1px)}.rank-name{transition:filter .12s ease,box-shadow .12s ease,transform .12s ease}.login-shell{min-height:58vh;display:flex;align-items:center;justify-content:center;padding:32px 12px 10px}.login-card{width:min(520px,100%);background:linear-gradient(120deg,#0F172A,#172554);border-radius:18px;padding:28px 26px;color:white;box-shadow:0 14px 44px rgba(15,23,42,.18);margin-bottom:4px}.login-brand{font-weight:900;font-size:1.35rem;letter-spacing:-.02em}.login-title{font-size:1rem;font-weight:800;margin-top:24px}.login-sub{color:#CBD5E1;font-size:.78rem;margin-top:5px}
@media(max-width:560px){.login-shell{min-height:36vh;padding:18px 4px 4px}.login-card{padding:22px 18px;border-radius:14px}.login-brand{font-size:1.05rem}.rank-click{width:100%}[data-testid="stDialog"] [role="dialog"]{max-width:calc(100vw - 14px)!important;width:calc(100vw - 14px)!important;max-height:92vh!important}[data-testid="stDialog"] .seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}[data-testid="stDialog"] .seller-mobile-primary{display:grid!important}}


.seller-dialog-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:-4px 0 8px;padding:7px 10px;border-radius:9px;background:#F8FAFC;border-left:4px solid var(--seller-color);font-size:.72rem;color:#64748B}.seller-dialog-meta b{color:#334155;font-size:.7rem}
@media(max-width:560px){
[data-testid="stDialog"] [role="dialog"]{width:calc(100vw - 12px)!important;max-width:calc(100vw - 12px)!important;max-height:94dvh!important;margin:3dvh auto!important;overflow:hidden!important}
[data-testid="stDialog"] [role="dialog"]>div{max-height:94dvh!important;overflow-y:auto!important;padding:.65rem .65rem .8rem!important}
[data-testid="stDialog"] h2{font-size:1.1rem!important;line-height:1.1!important;margin:0 0 .3rem!important}
[data-testid="stDialog"] .seller-dialog-meta{margin:-2px 0 6px;padding:5px 8px;font-size:.62rem}.seller-dialog-meta b{font-size:.62rem}
[data-testid="stDialog"] .seller-mobile-primary{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important;margin:0 0 7px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi{min-height:70px!important;padding:8px!important;border-radius:10px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi strong{font-size:1.18rem!important;margin-top:4px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi small{font-size:.53rem!important;line-height:1.05!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi span{font-size:.54rem!important;margin-top:3px!important}
[data-testid="stDialog"] .seller-groups{margin-top:4px!important}
[data-testid="stDialog"] .seller-group-title{font-size:.61rem!important;margin:7px 0 4px!important;letter-spacing:.05em!important}
[data-testid="stDialog"] .seller-group-title.award{margin-top:8px!important}
[data-testid="stDialog"] .seller-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:5px!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi{min-height:52px!important;padding:6px 5px!important;border-radius:9px!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi strong{font-size:.86rem!important;margin-top:3px!important;white-space:normal!important;line-height:1.05!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi small{font-size:.47rem!important;line-height:1.05!important;letter-spacing:.015em!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi span{display:none!important}
[data-testid="stDialog"] .mobile-duplicate{display:none!important}
[data-testid="stDialog"] .stButton{display:none!important}
}

</style>"""

def render_login(st,cfg):
    st.markdown('<div class="login-shell"><div class="login-card"><div class="login-brand">PAINEL COMERCIAL — AFOGADOS</div><div class="login-title">Acesso ao painel</div><div class="login-sub">Informe seu primeiro e segundo nome para continuar.</div></div></div>',unsafe_allow_html=True)
    with st.form("dashboard_login",clear_on_submit=False):
        name=st.text_input("Primeiro e segundo nome",placeholder="Ex.: Magda Alexandra")
        submitted=st.form_submit_button("ENTRAR",use_container_width=True)
    if submitted:
        display,status=authenticate_dashboard_name(cfg,name)
        if status=="ok":
            st.session_state.dashboard_autenticado=True
            st.session_state.dashboard_usuario=display
            st.rerun()
        else:
            st.error("Usuário não autorizado. Informe o primeiro e o segundo nome cadastrados.")

def open_seller_dialog(st,x):
    @st.dialog(x["vendedor"],width="large")
    def _dialog():
        status,c,_=performance(x["media"])
        st.markdown(f'<div class="seller-dialog-meta" style="--seller-color:{c}"><span>{html.escape(x["setor"])}</span><b>Performance {status}</b></div>',unsafe_allow_html=True)
        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)
        if st.button("FECHAR",key="close_seller_dialog",use_container_width=True):
            st.session_state.pop("seller_detail",None)
            st.rerun()
    _dialog()

def render_management(st,base,current_rows,current_cfg,metadata):
    st.markdown('<div class="section">GESTÃO · ACESSO RESTRITO</div>',unsafe_allow_html=True)
    if not st.session_state.get("gestor_autenticado"):
        password=manager_password(st)
        if not password:st.error("A senha do gestor não foi configurada. Defina GESTOR_SENHA nos Secrets do Streamlit."); return
        supplied=st.text_input("Senha do gestor",type="password")
        if st.button("ENTRAR NA GESTÃO"):
            if hmac.compare_digest(supplied,password):st.session_state.gestor_autenticado=True; st.rerun()
            else:st.error("Senha inválida.")
        return

    st.info("HISTÓRICO DIÁRIO ATIVO: envie somente o relatório do dia anterior. Se uma data já existir, ela será substituída; os demais dias permanecerão acumulados.")
    uploaded=st.file_uploader("IMPORTAR RELATÓRIO DIÁRIO",type=["xlsx","csv"],key="gestao_upload")
    rows=current_rows; cfg=merge_registry(base,current_cfg); source=metadata.get("arquivo","base atual")
    history=list(metadata.get("historico_importacoes",[])); imported_days=[]
    if uploaded:
        try:
            raw=rows_from_xlsx(uploaded.getvalue()) if uploaded.name.lower().endswith(".xlsx") else rows_from_csv(uploaded.getvalue())
            incoming,_=canonicalize(raw,base)
            if metadata.get("demonstracao"):rows=[]
            rows,imported_days=merge_daily_history(rows,incoming)
            ref=max(imported_days); month_rows=[x for x in rows if x["data_venda"].year==ref.year and x["data_venda"].month==ref.month]
            cfg=prepare_config(merge_registry(base,current_cfg),month_rows,ref.month,ref.year)
            cfg["dia_referencia"]=max(x["data_venda"].day for x in month_rows); source=uploaded.name
        except Exception as exc:st.error(f"O relatório não pôde ser validado: {exc}"); return
    month_rows=[x for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]]
    dates=[x["data_venda"] for x in month_rows] or [date(cfg["ano"],cfg["mes"],1)]
    unknown=sum(not x.get("classificado",True) for x in cfg["vendedores"]); local=sum(x.get("pertence_franquia",False) for x in cfg["vendedores"])
    cards(st,[("PERÍODO",f"{min(dates):%d/%m/%Y} a {max(dates):%d/%m/%Y}","cyan","Histórico acumulado"),("VENDAS ACUMULADAS",len(month_rows),"green","Competência atual"),("VENDEDORES",len(cfg["vendedores"]),"cyan",f"{local} locais"),("NÃO CLASSIFICADOS",unknown,"yellow","Revisar abaixo")])
    if uploaded and imported_days:st.success("Datas detectadas no novo arquivo: "+", ".join(d.strftime("%d/%m/%Y") for d in imported_days))
    if unknown:st.warning(f"{unknown} vendedores aguardam classificação. Eles ficam em CANAL NACIONAL até você ativá-los como franquia.")

    with st.form("gestao_config"):
        st.markdown("#### METAS E BÔNUS"); a,b,c=st.columns(3)
        cfg["meta_empresa"]=int(a.number_input("Meta mensal",1,value=int(cfg["meta_empresa"])))
        cfg["limite_cenario_maior"]=int(b.number_input("Limite do cenário maior",1,value=int(cfg["limite_cenario_maior"])))
        cfg["dia_referencia"]=int(c.number_input("Dados até o dia",1,31,value=min(int(cfg["dia_referencia"]),31)))
        a,b,c=st.columns(3)
        cfg["bonus_neoenergia"]["percentual_minimo"]=a.number_input("Neo mínimo (%)",0.,100.,value=float(cfg["bonus_neoenergia"]["percentual_minimo"]*100))/100
        cfg["bonus_neoenergia"]["percentual_bonus"]=b.number_input("Bônus Neo (%)",0.,100.,value=float(cfg["bonus_neoenergia"]["percentual_bonus"]*100))/100
        cfg["bonus_adimplencia"]["percentual_bonus"]=c.number_input("Bônus M2 (%)",0.,100.,value=float(cfg["bonus_adimplencia"]["percentual_bonus"]*100))/100
        st.markdown("#### PREMIAÇÕES SEMANAIS"); cols=st.columns(len(cfg["premiacao_semanal"]))
        for i,item in enumerate(cfg["premiacao_semanal"]):
            item["vendas"]=int(cols[i].number_input(f"Faixa {i+1}",1,value=int(item["vendas"]),key=f"gfq{i}")); item["premio"]=cols[i].number_input("Prêmio R$",0.,value=float(item["premio"]),key=f"gfp{i}")
        st.markdown("#### VENDEDORES · ATIVAR / DESATIVAR / CLASSIFICAR")
        for i,s in enumerate(cfg["vendedores"]):
            marker="⚠️ " if not s.get("classificado",True) else ""
            with st.expander(marker+s["vendedor"]):
                a,b,c,d=st.columns(4); s["setor"]=a.text_input("Setor",s.get("setor",""),key=f"gset{i}"); s["pertence_franquia"]=b.checkbox("Pertence à franquia",s.get("pertence_franquia",False),key=f"gfr{i}"); s["ativo"]=c.checkbox("Ativo no dashboard",s.get("ativo",False),key=f"gat{i}"); s["experiencia"]=d.checkbox("Em experiência",s.get("experiencia",False),key=f"gex{i}")
                a,b,c=st.columns(3); s["meta_individual"]=int(a.number_input("Meta individual",1,value=int(s.get("meta_individual",70)),key=f"gme{i}")); s["trabalha_sabado"]=b.checkbox("Trabalha sábado",s.get("trabalha_sabado",True),key=f"gsa{i}"); s["trabalha_domingo"]=c.checkbox("Trabalha domingo",s.get("trabalha_domingo",False),key=f"gdo{i}"); s["classificado"]=s["pertence_franquia"] or normalize_text(s.get("categoria")) in {"website","adm","freelance"}
        confirmed=st.form_submit_button("CONFIRMAR E PUBLICAR ATUALIZAÇÃO")
    if confirmed:
        if imported_days:
            history.append({"data_importacao":datetime.now().isoformat(timespec="seconds"),"arquivo":source,"dias":[d.isoformat() for d in imported_days],"registros_arquivo":sum(x["data_venda"] in imported_days for x in rows)}); history=history[-90:]
        save_published(rows,cfg,source,history); st.success("Histórico atualizado e dashboard publicado."); st.rerun()
    if history:
        st.markdown("#### HISTÓRICO DE IMPORTAÇÕES"); view=[]
        for h in reversed(history[-20:]):view.append({"Importado em":h.get("data_importacao","").replace("T"," "),"Arquivo":h.get("arquivo",""),"Dia(s)":", ".join(h.get("dias",[])),"Registros":h.get("registros_arquivo",0)})
        st.dataframe(view,use_container_width=True,hide_index=True)
    if st.button("SAIR DA GESTÃO"):st.session_state.gestor_autenticado=False; st.rerun()

def render_app():
    import streamlit as st
    st.set_page_config(page_title="Painel Comercial — Afogados",page_icon="📊",layout="wide",initial_sidebar_state="collapsed")
    st.markdown(CSS,unsafe_allow_html=True)
    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
    try:rows,cfg,metadata=load_published(base)
    except Exception as exc:st.error(f"A base publicada não pôde ser carregada: {exc}");return
    mobile_client=is_mobile_client(st)
    if not mobile_client and not st.session_state.get("dashboard_autenticado",False):
        render_login(st,cfg)
        return
    if mobile_client and not st.session_state.get("dashboard_usuario"):
        st.session_state.dashboard_usuario="Acesso mobile"
    areas=["VISÃO GERAL","SEMANAL","PREMIAÇÕES"]
    if st.session_state.get("area") not in areas+ ["GESTÃO"]:st.session_state.area="VISÃO GERAL"
    head_main,head_menu=st.columns([18,1])
    with head_main:
        st.markdown('<div class="bi-topbar bi-topbar-nav"><div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div></div>',unsafe_allow_html=True)
    with head_menu:
        with st.popover("⋮"):
            st.caption(f'Usuário: {st.session_state.get("dashboard_usuario","")}')
            if st.button("GESTÃO",use_container_width=True,key="menu_gestao"):
                st.session_state.area="GESTÃO";st.rerun()
            if st.button("SAIR",use_container_width=True,key="menu_sair"):
                for key in ("dashboard_autenticado","dashboard_usuario","seller_detail","gestor_autenticado","login_duplicate_first"):
                    st.session_state.pop(key,None)
                st.session_state.area="VISÃO GERAL"
                st.rerun()
    if st.session_state.area=="GESTÃO":
        render_management(st,base,rows,cfg,metadata)
        return
    selected_area=st.segmented_control("Navegação",areas,default=st.session_state.area,key="top_nav_area",label_visibility="collapsed")
    if selected_area and selected_area != st.session_state.area:
        st.session_state.area=selected_area
        st.rerun()
    area=st.session_state.area
    try:summary,all_days,elapsed,official=summarize(rows,cfg)
    except Exception as exc:st.error(f"Falha ao processar relatório: {exc}");return
    data_until=max((x["data_venda"] for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]),default=date(cfg["ano"],cfg["mes"],1)); updated=datetime.fromisoformat(metadata["atualizado_em"])
    st.caption(f"Última atualização: {updated:%d/%m/%Y às %H:%M}  •  Dados acumulados até: {data_until:%d/%m/%Y}  •  Competência: {cfg['mes']:02d}/{cfg['ano']}")
    team=regular(summary); total=sum(x["vendas"] for x in summary); projection=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary); color=lambda x:performance(x["media"])[1]
    requested_seller=st.query_params.get("seller")
    if requested_seller:
        st.session_state.seller_detail=requested_seller
        try:del st.query_params["seller"]
        except KeyError:pass
    detail_name=st.session_state.get("seller_detail")
    if detail_name:
        detail=next((x for x in team if normalize_text(x["vendedor"])==normalize_text(detail_name)),None)
        if detail:open_seller_dialog(st,detail)
        else:st.session_state.pop("seller_detail",None)
    if area=="VISÃO GERAL":
        st.markdown(executive_kpis_html(cfg,total,projection,neo,team),unsafe_allow_html=True)
        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
        for x in team:counts[performance(x["media"])[0]]+=1
        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)
        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True); ranking=sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)
        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","FREELANCE","CANAL NACIONAL")}
        for item in summary:
            name=channel_name(item)
            if name!="ADM" and name in channels:channels[name]+=item["vendas"]
        st.markdown(channel_summary_html(channels,total),unsafe_allow_html=True)
        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)
    elif area=="SEMANAL":
        st.markdown('<div class="section">Acompanhamento semanal · segunda a domingo</div>',unsafe_allow_html=True)
        if not team:st.warning("Nenhum vendedor local ativo.");return
        max_weeks=max(len(x["semanas"]) for x in team); data=[]
        for x in team:
            row={"Vendedor":x["vendedor"]}
            for i in range(max_weeks):row[f"Semana {i+1}"]=x["semanas"][i]; row[f"Semanal S{i+1}"]=money(x["premios"][i])
            row["Semanais acumulados"]=money(x["premio_total"]); data.append(row)
        st.dataframe(data,use_container_width=True,hide_index=True,height=520)
    elif area=="PREMIAÇÕES":
        st.markdown('<div class="section">Premiações e cenários</div>',unsafe_allow_html=True); projected="maior_ou_igual_1000" if projection>=cfg["limite_cenario_maior"] else "abaixo_1000"
        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{projection} vendas"),("PREMIAÇÃO BASE ATUAL",money(sum(x["base"] for x in team)),"cyan",""),("PREMIAÇÃO PROJETADA",money(sum(x["comissao_proj"] for x in team)),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(sum(x["bonus_neo_proj"] for x in team)),"green",""),("BÔNUS (SE) 100% ADIM",money(sum(x["bonus_adim_proj"] for x in team)),"green",""),("SEMANAIS ACUMULADOS",money(sum(x["premio_total"] for x in team)),"cyan",""),("TOTAL VAR. PROJETADO",money(sum(x["total_variavel_proj"] for x in team)),"yellow","")])
        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Projeção":x["projecao"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base atual":x["base"],"Premiação projetada":x["comissao_proj"],"Bônus Neo proj.":x["bonus_neo_proj"],"BÔNUS (SE) 100% ADIM":x["bonus_adim_proj"],"Semanais":x["premio_total"],"Total atual":x["total"],"Total var. projetado":x["total_variavel_proj"]} for x in sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True)],use_container_width=True,hide_index=True)
    st.markdown('<div class="section">Relatório completo</div>',unsafe_allow_html=True)
    try:
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"Painel_Comercial_Afogados.xlsx"; write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official)); book=path.read_bytes()
        st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as exc:st.warning(f"Não foi possível gerar o Excel agora: {exc}")

if __name__=="__main__":render_app()
