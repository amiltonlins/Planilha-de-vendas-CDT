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

def ranking_html(ranking):
    medals=("🥇","🥈","🥉")
    rows=[]
    for i,x in enumerate(ranking):
        _,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        rows.append(
            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'
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
            f'<span><strong>{money(x["base"])}</strong><small>COMISSÃO ATUAL</small></span>'
            f'<span><strong>{money(x["comissao_proj"])}</strong><small>COMISSÃO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_neo_proj"])}</strong><small>BÔNUS NEO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_adim_proj"])}</strong><small>BÔNUS ADIM. PROJ.</small></span>'
            f'<span><strong>{money(x["premio_total"])}</strong><small>PRÊMIOS</small></span>'
            f'<span class="total-highlight"><strong>{money(x["total_variavel_proj"])}</strong><small>TOTAL VAR. PROJ.</small></span>'
            f'</div></div></div>'
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
</style>"""

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
    if "area" not in st.session_state:st.session_state.area="VISÃO GERAL"
    top_left,top_menu=st.columns([18,1])
    with top_left:st.markdown('<div class="bi-topbar"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>',unsafe_allow_html=True)
    with top_menu:
        with st.popover("⋮"):
            st.markdown("**NAVEGAÇÃO**")
            areas=["VISÃO GERAL","VENDEDORES","SEMANAL","COMISSÕES","GESTÃO"]
            st.session_state.area=st.radio("Área",areas,index=areas.index(st.session_state.area),label_visibility="collapsed")
            st.caption("Menu gerencial")
    area=st.session_state.area
    if area=="GESTÃO":render_management(st,base,rows,cfg,metadata);return
    try:summary,all_days,elapsed,official=summarize(rows,cfg)
    except Exception as exc:st.error(f"Falha ao processar relatório: {exc}");return
    data_until=max((x["data_venda"] for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]),default=date(cfg["ano"],cfg["mes"],1)); updated=datetime.fromisoformat(metadata["atualizado_em"])
    st.caption(f"Última atualização: {updated:%d/%m/%Y às %H:%M}  •  Dados acumulados até: {data_until:%d/%m/%Y}  •  Competência: {cfg['mes']:02d}/{cfg['ano']}")
    team=regular(summary); total=sum(x["vendas"] for x in summary); projection=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary); color=lambda x:performance(x["media"])[1]
    if area=="VISÃO GERAL":
        cards(st,[("META DO MÊS",cfg["meta_empresa"],"yellow","Objetivo comercial"),("VENDAS REALIZADAS",total,"cyan","Histórico acumulado"),("PROJEÇÃO",projection,"yellow","Fechamento estimado"),("% DA META",pct(total/cfg["meta_empresa"] if cfg["meta_empresa"] else 0),"green","Realizado"),("FALTAM PARA META",max(0,cfg["meta_empresa"]-total),"red","Vendas necessárias"),("VENDAS NEO",neo,"cyan","Neoenergia"),("% NEO",pct(neo/total if total else 0),"green","Participação"),("ZEROS",sum(x["zeros"] for x in team),"red","Dias sem venda")])
        left,right=st.columns([1.7,1],gap="small")
        with left:
            st.markdown('<div class="section">Evolução comercial</div>',unsafe_allow_html=True); cumulative,ideal=daily_series(rows,cfg,data_until); st.line_chart({"Realizado acumulado":cumulative,"Ritmo da meta":ideal},height=245)
        with right:
            st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
            for x in team:counts[performance(x["media"])[0]]+=1
            tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],2)
        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True); ranking=sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)
        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","ADM","FREELANCE","CANAL NACIONAL")}
        for item in summary:channels[channel_name(item)]+=item["vendas"]
        cards(st,[(name,value,"cyan",pct(value/total if total else 0)+" do total") for name,value in channels.items()],5)
    elif area=="VENDEDORES":
        if not team:st.warning("Nenhum vendedor local ativo. Entre em GESTÃO e classifique/ative os vendedores.");return
        chosen=st.selectbox("SELECIONE O VENDEDOR",[x["vendedor"] for x in team]); x=next(v for v in team if v["vendedor"]==chosen); status,c,tone=performance(x["media"])
        st.markdown(f'<div class="bi-panel" style="border-left:5px solid {c}"><b>{html.escape(x["vendedor"])}</b><br><span style="color:#64748B;font-size:.75rem">{html.escape(x["setor"])} · Performance {status}</span></div>',unsafe_allow_html=True)
        cards(st,[("VENDAS",x["vendas"],"cyan",""),("MÉDIA",f'{x["media"]:.2f}',tone,f'{x["dias"]} dias'),("PROJEÇÃO",x["projecao"],tone,f'Meta {x["meta_individual"]}'),("% DA META",pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),tone,""),("ZEROS",x["zeros"],"red",f'Semana {x["zeros_semana"]}'),("NEO",x["neo"],"cyan",""),("% NEO",pct(x["neo_pct"]),"green",""),("COMISSÃO ATUAL",money(x["base"]),"green",""),("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(x["bonus_neo_proj"]),"green",""),("BÔNUS ADIM. PROJ.",money(x["bonus_adim_proj"]),"green",""),("PRÊMIOS",money(x["premio_total"]),"green","Acumulados"),("TOTAL VAR. ATUAL",money(x["total"]),"cyan",""),("TOTAL VAR. PROJETADO",money(x["total_variavel_proj"]),"yellow","")])
        st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True)
        cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS ADIM. PROJ."),("premio_fmt","PRÊMIOS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]; display=[]
        for item in sorted(team,key=lambda z:(z["vendas"],z["projecao"]),reverse=True):display.append(item|{"media":f'{item["media"]:.2f}',"meta_pct":pct(item["projecao"]/item["meta_individual"] if item["meta_individual"] else 0),"neo_pct_fmt":pct(item["neo_pct"]),"base_fmt":money(item["base"]),"proj_fmt":money(item["comissao_proj"]),"neo_proj_fmt":money(item["bonus_neo_proj"]),"adim_proj_fmt":money(item["bonus_adim_proj"]),"premio_fmt":money(item["premio_total"]),"total_proj_fmt":money(item["total_variavel_proj"])})
        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)
        try:
            with tempfile.TemporaryDirectory() as folder:
                general_path=Path(folder)/"Relatorio_Geral_Equipe_Afogados.xlsx"
                general_sheet=next(s for s in build_sheets(rows,cfg,summary,all_days,elapsed,official) if s.name=="RELATORIO GERAL")
                write_xlsx(general_path,[general_sheet]); general_book=general_path.read_bytes()
            st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as exc:st.warning(f"Não foi possível gerar o Relatório Geral agora: {exc}")
    elif area=="SEMANAL":
        st.markdown('<div class="section">Acompanhamento semanal · segunda a domingo</div>',unsafe_allow_html=True)
        if not team:st.warning("Nenhum vendedor local ativo.");return
        max_weeks=max(len(x["semanas"]) for x in team); data=[]
        for x in team:
            row={"Vendedor":x["vendedor"]}
            for i in range(max_weeks):row[f"Semana {i+1}"]=x["semanas"][i]; row[f"Prêmio S{i+1}"]=money(x["premios"][i])
            row["Premiação acumulada"]=money(x["premio_total"]); data.append(row)
        st.dataframe(data,use_container_width=True,hide_index=True,height=520)
    elif area=="COMISSÕES":
        st.markdown('<div class="section">Comissões e cenários</div>',unsafe_allow_html=True); projected="maior_ou_igual_1000" if projection>=cfg["limite_cenario_maior"] else "abaixo_1000"
        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{projection} vendas"),("COMISSÃO BASE ATUAL",money(sum(x["base"] for x in team)),"cyan",""),("COMISSÃO PROJETADA",money(sum(x["comissao_proj"] for x in team)),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(sum(x["bonus_neo_proj"] for x in team)),"green",""),("BÔNUS ADIM. PROJ.",money(sum(x["bonus_adim_proj"] for x in team)),"green",""),("PRÊMIOS ACUMULADOS",money(sum(x["premio_total"] for x in team)),"cyan",""),("TOTAL VAR. PROJETADO",money(sum(x["total_variavel_proj"] for x in team)),"yellow","")])
        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Projeção":x["projecao"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base atual":x["base"],"Comissão projetada":x["comissao_proj"],"Bônus Neo proj.":x["bonus_neo_proj"],"Bônus M2 proj.":x["bonus_adim_proj"],"Prêmios":x["premio_total"],"Total atual":x["total"],"Total var. projetado":x["total_variavel_proj"]} for x in sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True)],use_container_width=True,hide_index=True)
    st.markdown('<div class="section">Relatório completo</div>',unsafe_allow_html=True)
    try:
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"Painel_Comercial_Afogados.xlsx"; write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official)); book=path.read_bytes()
        st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as exc:st.warning(f"Não foi possível gerar o Excel agora: {exc}")

if __name__=="__main__":render_app()
