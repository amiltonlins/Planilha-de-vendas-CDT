#!/usr/bin/env python3
"""Aplicação web do Painel Comercial — Afogados.

O relatório enviado é transformado em memória e nunca é persistido. As funções
puras deste módulo também são usadas pelos testes de upload e cálculo.
"""
from __future__ import annotations
import copy, csv, hmac, html, io, json, os, re, tempfile, unicodedata, zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET
from gerar_painel import ROOT, build_sheets, summarize, tier_value, weekly_prize, write_xlsx

NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships","p":"http://schemas.openxmlformats.org/package/2006/relationships"}
PUBLISHED_PATH=Path(os.environ.get("PAINEL_DATA_PATH",ROOT/"data"/"dados_publicados.json"))
ALIASES={
 "data_venda":("data venda","data da venda","data","dt venda","criado em","data cadastro"),
 "vendedor":("vendedor","colaborador","consultor","nome vendedor","usuario","responsavel"),
 "setor":("setor","equipe","canal","franquia"), "categoria":("categoria","tipo vendedor","perfil"),
 "neoenergia":("nome","neoenergia","neoenergia celpe","produto","prospeccao","prospeccao produto","convenio","meio"),
 "adimplencia_m2":("adimplencia m2","m2","pago m2","status m2","adimplencia"),
 "status":("status","situacao","estado"), "id_venda":("id venda","id","codigo","numero","proposta","matricula")}

def normalize_text(value):
 text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",text).strip()

def detect_columns(headers):
 normalized={normalize_text(h):h for h in headers if h is not None}; result={}
 for target,aliases in ALIASES.items():
  for alias in aliases:
   if normalize_text(alias) in normalized: result[target]=normalized[normalize_text(alias)]; break
  if target not in result:
   for key,original in normalized.items():
    if any(len(normalize_text(a))>3 and normalize_text(a) in key for a in aliases): result[target]=original; break
 if not {"data_venda","vendedor"}<=result.keys(): raise ValueError("Não foi possível identificar as colunas de data e vendedor.")
 return result

def excel_date(value):
 if isinstance(value,(int,float)) or (str(value).replace(".","",1).isdigit() and float(value)>1000): return (date(1899,12,30)+timedelta(days=int(float(value)))).isoformat()
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
   root=ET.fromstring(z.read("xl/sharedStrings.xml")); shared=["".join(x.text or "" for x in si.iterfind(".//m:t",NS)) for si in root.findall("m:si",NS)]
  workbook=ET.fromstring(z.read("xl/workbook.xml")); relroot=ET.fromstring(z.read("xl/_rels/workbook.xml.rels")); rels={x.attrib["Id"]:x.attrib["Target"] for x in relroot}
  for sheet in workbook.findall(".//m:sheet",NS):
   target=rels[sheet.attrib[f"{{{NS['r']}}}id"]]; path=target.lstrip("/"); path=path if path.startswith("xl/") else "xl/"+path
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
 mapping=detect_columns(raw_rows[0].keys()); output=[]; seen=set(); valid={normalize_text(x) for x in base_config["status_validos"]}
 for number,row in enumerate(raw_rows,1):
  try:day=excel_date(row.get(mapping["data_venda"],""))
  except ValueError:continue
  seller=str(row.get(mapping["vendedor"],"")).strip()
  if not seller:continue
  product=str(row.get(mapping.get("neoenergia",""),"")); status=str(row.get(mapping.get("status",""),"Aprovada") or "Aprovada"); identifier=str(row.get(mapping.get("id_venda",""),"") or f"UPLOAD-{number}")
  if identifier in seen or normalize_text(status) not in valid:continue
  seen.add(identifier); output.append({"data_venda":datetime.strptime(day,"%Y-%m-%d").date(),"vendedor":seller,"setor":str(row.get(mapping.get("setor",""),"NÃO INFORMADO") or "NÃO INFORMADO"),"categoria":str(row.get(mapping.get("categoria",""),"Vendedor") or "Vendedor"),"neoenergia":"Sim" if "neoenergia celpe" in normalize_text(product) or normalize_text(product) in ("neoenergia","sim","1","true") else "Não","adimplencia_m2":str(row.get(mapping.get("adimplencia_m2",""),"0") or "0"),"status":status,"id_venda":identifier})
 if not output:raise ValueError("Nenhuma venda válida após filtros de status e duplicidade.")
 return output,mapping

def prepare_config(base,rows,month,year):
 cfg=copy.deepcopy(base); cfg["mes"],cfg["ano"]=month,year; existing={normalize_text(x["vendedor"]):x for x in cfg["vendedores"]}; sellers=[]
 for name in sorted({x["vendedor"] for x in rows}):
  sample=next(x for x in rows if x["vendedor"]==name); old=existing.get(normalize_text(name),{})
  inferred=next((label for label in ("Website","ADM","Freelance") if normalize_text(label) in normalize_text(name)),sample["categoria"])
  registered=bool(old); belongs=old.get("pertence_franquia",registered)
  sellers.append({"vendedor":name,"setor":old.get("setor",sample["setor"]),"categoria":old.get("categoria",inferred if registered else "Canal Nacional"),"pertence_franquia":belongs,"classificado":registered,"ativo":old.get("ativo",registered),"experiencia":old.get("experiencia",False),"meta_individual":old.get("meta_individual",70),"trabalha_sabado":old.get("trabalha_sabado",True),"trabalha_domingo":old.get("trabalha_domingo",False),"data_inicio":old.get("data_inicio",f"{year}-01-01"),"data_desligamento":old.get("data_desligamento",""),"folgas":old.get("folgas",[])})
 cfg["vendedores"]=sellers; return cfg

def performance(projected,target):
 ratio=projected/target if target else 0
 if ratio>=1.5:return "Azul","#0891B2","🔵"
 if ratio>=1:return "Verde","#16A34A","🟢"
 if ratio>=.7:return "Amarelo","#F59E0B","🟡"
 return "Vermelho","#DC2626","🔴"
def performance_tone(status):return {"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}[status]

def excel_bytes(rows,cfg,summary,all_days,elapsed,official):
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/"Painel_Comercial_Afogados.xlsx"; write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official)); return path.read_bytes()

def money(value):return f"R$ {value:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def pct(value):return f"{value:.1%}".replace(".",",")
def card(label,value,tone="blue",sub=""):
 return f'<div class="metric {tone}"><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong><small>{html.escape(sub)}</small></div>'
def cards(st,items,columns=4):
 cols=st.columns(columns)
 for i,item in enumerate(items):cols[i%columns].markdown(card(*item),unsafe_allow_html=True)
def regular(summary):return [x for x in summary if x.get("elegivel_individual",True)]
def specials(summary):return [x for x in summary if normalize_text(x["categoria"]) in {"website","adm","freelance"}]

def channel_name(item):
 if not item.get("pertence_franquia",True) or normalize_text(item.get("categoria"))=="canal nacional":return "CANAL NACIONAL"
 category=normalize_text(item.get("categoria"))
 if category in {"website","adm","freelance"}:return category.upper()
 return "VENDEDORES FRANQUIA"

def save_published(rows,cfg,source_name,updated_at=None):
 """Publica somente os campos canônicos necessários, usando troca atômica."""
 updated_at=updated_at or datetime.now(); PUBLISHED_PATH.parent.mkdir(parents=True,exist_ok=True)
 payload={"atualizado_em":updated_at.isoformat(timespec="seconds"),"arquivo":Path(source_name).name,"config":cfg,"vendas":[{**row,"data_venda":row["data_venda"].isoformat()} for row in rows]}
 temporary=PUBLISHED_PATH.with_suffix(".tmp"); temporary.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8"); temporary.replace(PUBLISHED_PATH)

def load_published(base):
 if PUBLISHED_PATH.exists():
  payload=json.loads(PUBLISHED_PATH.read_text(encoding="utf-8")); rows=payload["vendas"]
  for row in rows:row["data_venda"]=datetime.strptime(row["data_venda"],"%Y-%m-%d").date()
  return rows,payload["config"],payload
 raw=rows_from_csv((ROOT/"dados_exemplo.csv").read_bytes()); rows,_=canonicalize(raw,base); cfg=prepare_config(base,rows,base["mes"],base["ano"])
 return rows,cfg,{"atualizado_em":datetime(base["ano"],base["mes"],base["dia_referencia"],8).isoformat(),"arquivo":"dados_exemplo.csv","demonstracao":True}

def manager_password(st):
 try:return str(st.secrets["GESTOR_SENHA"])
 except (KeyError,FileNotFoundError):return os.environ.get("GESTOR_SENHA","")

def table_html(records,columns,row_color=None,daily=False):
 heads="".join(f"<th>{html.escape(str(label))}</th>" for _,label in columns)
 body=[]
 for rec in records:
  color=row_color(rec) if row_color else "#fff"; cells=[]
  for key,_ in columns:
   value=rec.get(key,""); style=""
   if key in ("vendedor","projecao") and row_color:style=f"background:{color};color:white;font-weight:800"
   if daily and isinstance(key,int):
    dias_decorridos=rec.get("dias_decorridos",set())
    dias_agendados=rec.get("dias_agendados",set())
    diario=rec.get("diario",{})
    if key not in dias_decorridos:style="background:#F1F5F9;color:#94A3B8"; value=""
    elif key in dias_agendados and diario.get(key,0)==0:style="background:#FEE2E2;color:#B91C1C;font-weight:800"; value=0
    elif diario.get(key,0)>=3:style="background:#CFFAFE;color:#155E75;font-weight:800"
   cells.append(f'<td style="{style}">{html.escape(str(value))}</td>')
  body.append(f'<tr>{"".join(cells)}</tr>')
 return f'<div class="table-wrap"><table class="report"><thead><tr>{heads}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'

CSS="""<style>
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none!important}.stApp{background:#F6F8FA;color:#172033}.block-container{padding:1.1rem 2rem 3rem;max-width:1800px}.brand{background:#172033;color:#fff;padding:16px 22px;border-left:7px solid #06B6D4;margin-bottom:18px}.brand h1{font-size:1.55rem;margin:0}.brand p{margin:3px 0 0;color:#CBD5E1;font-size:.82rem}.section{font-weight:900;color:#172033;border-bottom:2px solid #172033;padding:8px 0 5px;margin:20px 0 12px;letter-spacing:.04em}.metric{background:white;border:1px solid #D9E1E8;border-top:4px solid #0891B2;padding:13px 15px;min-height:92px;margin:5px 0;box-shadow:0 2px 5px #0f172a0d}.metric span{display:block;font-size:.7rem;font-weight:800;color:#64748B;letter-spacing:.06em}.metric strong{display:block;font-size:1.75rem;line-height:1.2;color:#172033}.metric small{font-size:.7rem;color:#64748B}.metric.green{border-top-color:#16A34A}.metric.yellow{border-top-color:#F59E0B}.metric.red{border-top-color:#DC2626}.metric.cyan{border-top-color:#06B6D4}.seller-head{padding:16px 20px;color:#fff;font-size:1.25rem;font-weight:900;border-radius:3px}.table-wrap{overflow:auto;max-height:590px;border:1px solid #CBD5E1;background:white}.report{border-collapse:collapse;white-space:nowrap;width:100%;font-size:.76rem}.report th{position:sticky;top:0;background:#172033;color:white;padding:8px 9px;z-index:2}.report td{border:1px solid #E2E8F0;padding:6px 8px;text-align:center}.report tr:nth-child(even) td{background-color:#F8FAFC}.podium{background:white;border:1px solid #D9E1E8;padding:12px;margin:4px 0;border-left:6px solid}.scenario{background:#fff;border:1px solid #CBD5E1;padding:14px;font-weight:800}.stButton button,.stDownloadButton button{border-radius:2px;background:#172033;color:#fff;border:0;font-weight:800}.stSidebar{background:#172033}.stSidebar *{color:#E2E8F0}.stSidebar [role="radiogroup"] label{padding:7px}.stSidebar [aria-checked="true"]{background:#0891B2}
@media(max-width:900px){.block-container{padding:.7rem}.metric strong{font-size:1.3rem}}
</style>"""

def render_management(st,base,current_rows,current_cfg,metadata):
 st.markdown('<div class="section">GESTÃO · ACESSO RESTRITO</div>',unsafe_allow_html=True)
 if not st.session_state.get("gestor_autenticado"):
  password=manager_password(st)
  if not password:
   st.error("A senha do gestor não foi configurada. Defina GESTOR_SENHA nos Secrets do Streamlit."); return
  supplied=st.text_input("Senha do gestor",type="password")
  if st.button("ENTRAR NA GESTÃO"):
   if hmac.compare_digest(supplied,password):st.session_state.gestor_autenticado=True; st.rerun()
   else:st.error("Senha inválida.")
  return
 st.caption("Sessão autenticada. Uploads só são publicados depois da confirmação.")
 uploaded=st.file_uploader("IMPORTAR NOVO RELATÓRIO",type=["xlsx","csv"],key="gestao_upload")
 rows=current_rows; cfg=copy.deepcopy(current_cfg); source=metadata.get("arquivo","base atual")
 if uploaded:
  try:
   raw=rows_from_xlsx(uploaded.getvalue()) if uploaded.name.lower().endswith(".xlsx") else rows_from_csv(uploaded.getvalue())
   rows,_=canonicalize(raw,base); dates=[x["data_venda"] for x in rows]; cfg=prepare_config(current_cfg,rows,dates[-1].month,dates[-1].year); cfg["dia_referencia"]=max(d.day for d in dates if d.month==cfg["mes"] and d.year==cfg["ano"]); source=uploaded.name
  except Exception as exc:st.error(f"O relatório não pôde ser validado: {exc}"); return
 dates=[x["data_venda"] for x in rows]; unknown=sum(not x.get("classificado",True) for x in cfg["vendedores"]); local=sum(x.get("pertence_franquia",False) for x in cfg["vendedores"]); national=len(cfg["vendedores"])-local
 cards(st,[("ARQUIVO",source,"cyan","Pronto para conferência"),("PERÍODO",f"{min(dates):%d/%m/%Y} a {max(dates):%d/%m/%Y}","cyan","Identificado"),("VENDAS",len(rows),"green","Registros válidos"),("VENDEDORES",len(cfg["vendedores"]),"cyan",f"{local} locais · {national} nacionais")])
 if unknown:st.warning(f"{unknown} vendedores ainda não classificados. Eles permanecem agrupados em CANAL NACIONAL.")
 with st.form("gestao_config"):
  st.markdown("#### METAS E BÔNUS"); a,b,c=st.columns(3); cfg["meta_empresa"]=int(a.number_input("Meta mensal",1,value=int(cfg["meta_empresa"]))); cfg["limite_cenario_maior"]=int(b.number_input("Limite do cenário maior",1,value=int(cfg["limite_cenario_maior"]))); cfg["dia_referencia"]=int(c.number_input("Dados até o dia",1,31,value=min(int(cfg["dia_referencia"]),31)))
  a,b,c=st.columns(3); cfg["bonus_neoenergia"]["percentual_minimo"]=a.number_input("Neo mínimo (%)",0.,100.,value=float(cfg["bonus_neoenergia"]["percentual_minimo"]*100))/100; cfg["bonus_neoenergia"]["percentual_bonus"]=b.number_input("Bônus Neo (%)",0.,100.,value=float(cfg["bonus_neoenergia"]["percentual_bonus"]*100))/100; cfg["bonus_adimplencia"]["percentual_bonus"]=c.number_input("Bônus M2 (%)",0.,100.,value=float(cfg["bonus_adimplencia"]["percentual_bonus"]*100))/100
  st.markdown("#### PREMIAÇÕES SEMANAIS"); cols=st.columns(len(cfg["premiacao_semanal"]))
  for i,item in enumerate(cfg["premiacao_semanal"]):item["vendas"]=int(cols[i].number_input(f"Faixa {i+1}",1,value=int(item["vendas"]),key=f"gfq{i}")); item["premio"]=cols[i].number_input("Prêmio R$",0.,value=float(item["premio"]),key=f"gfp{i}")
  st.markdown("#### RÉGUAS DE COMISSÃO")
  for rule,label in (("abaixo_1000","EMPRESA ABAIXO DE 1.000"),("maior_ou_igual_1000","EMPRESA COM 1.000 OU MAIS")):
   st.caption(label); cols=st.columns(4)
   for i,item in enumerate(cfg["reguas_comissao"][rule]):
    item["vendas"]=int(cols[i%4].number_input(f"Faixa {i+1}",1,value=int(item["vendas"]),key=f"gq{rule}{i}")); item["valor_por_venda"]=cols[i%4].number_input("R$/venda",0.,value=float(item["valor_por_venda"]),key=f"gv{rule}{i}")
  st.markdown("#### CADASTRO E CLASSIFICAÇÃO")
  for i,s in enumerate(cfg["vendedores"]):
   marker="⚠️ " if not s.get("classificado",True) else ""
   with st.expander(marker+s["vendedor"]):
    a,b,c,d=st.columns(4); s["setor"]=a.text_input("Setor",s.get("setor",""),key=f"gset{i}"); s["pertence_franquia"]=b.checkbox("Pertence à franquia",s.get("pertence_franquia",False),key=f"gfr{i}"); s["ativo"]=c.checkbox("Ativo no dashboard",s.get("ativo",False),key=f"gat{i}"); s["experiencia"]=d.checkbox("Em experiência",s.get("experiencia",False),key=f"gex{i}")
    a,b,c=st.columns(3); s["meta_individual"]=int(a.number_input("Meta individual",1,value=int(s.get("meta_individual",70)),key=f"gme{i}")); s["trabalha_sabado"]=b.checkbox("Trabalha sábado",s.get("trabalha_sabado",True),key=f"gsa{i}"); s["trabalha_domingo"]=c.checkbox("Trabalha domingo",s.get("trabalha_domingo",False),key=f"gdo{i}")
    a,b=st.columns(2); s["data_inicio"]=a.text_input("Data de início",s.get("data_inicio",""),key=f"gdi{i}"); s["data_desligamento"]=b.text_input("Data de desligamento",s.get("data_desligamento",""),key=f"gdd{i}"); s["folgas"]=[v.strip() for v in st.text_input("Folgas/afastamentos",",".join(s.get("folgas",[])),key=f"gfo{i}").split(",") if v.strip()]; s["classificado"]=s["pertence_franquia"] or normalize_text(s.get("categoria")) in {"website","adm","freelance"}
  confirmed=st.form_submit_button("CONFIRMAR ATUALIZAÇÃO")
 if confirmed:
  save_published(rows,cfg,source); st.success("Base publicada. O dashboard da equipe já foi atualizado."); st.rerun()
 if st.button("SAIR DA GESTÃO"):st.session_state.gestor_autenticado=False; st.rerun()

def render_app():
 import streamlit as st
 st.set_page_config(page_title="Painel Comercial — Afogados",page_icon="📊",layout="wide",initial_sidebar_state="expanded"); st.markdown(CSS,unsafe_allow_html=True)
 base=json.loads((ROOT/"config.json").read_text(encoding="utf-8")); st.markdown('<div class="brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Produção, performance e remuneração variável</p></div>',unsafe_allow_html=True)
 try:rows,cfg,metadata=load_published(base)
 except Exception as exc:st.error(f"A base publicada não pôde ser carregada: {exc}");return
 with st.sidebar:
  st.markdown("### PAINEL COMERCIAL"); area=st.radio("Navegação",["VISÃO GERAL","VENDEDORES","SEMANAL","COMISSÕES","GESTÃO"],label_visibility="collapsed")
 if area=="GESTÃO":render_management(st,base,rows,cfg,metadata);return
 try:
  summary,all_days,elapsed,official=summarize(rows,cfg)
 except Exception as exc:st.error(f"Falha ao processar relatório: {exc}");return
 updated=datetime.fromisoformat(metadata["atualizado_em"]); data_until=max((x["data_venda"] for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]),default=date(cfg["ano"],cfg["mes"],1)); st.caption(f"Última atualização: {updated:%d/%m/%Y às %H:%M}  ·  Dados até: {data_until:%d/%m/%Y}")
 team=regular(summary); extra=specials(summary); total=sum(x["vendas"] for x in summary); projection=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary)
 projected_scenario="maior_ou_igual_1000" if projection>=cfg["limite_cenario_maior"] else "abaixo_1000"
 color=lambda x:performance(x["projecao"],x["meta_individual"])[1]
 if area=="VISÃO GERAL":
  cards(st,[("META DO MÊS",cfg["meta_empresa"],"yellow","Objetivo comercial"),("VENDAS REALIZADAS",total,"cyan","Produção validada"),("PROJEÇÃO",projection,"yellow","Fechamento estimado"),("% DA META",pct(total/cfg["meta_empresa"] if cfg["meta_empresa"] else 0),"green","Realizado"),("FALTAM PARA META",max(0,cfg["meta_empresa"]-total),"red","Vendas necessárias"),("VENDAS NEOENERGIA",neo,"cyan","NEOENERGIA CELPE"),("% NEOENERGIA",pct(neo/total if total else 0),"green","Participação"),("TOTAL DE ZEROS",sum(x["zeros"] for x in team),"red","Dias previstos sem venda")])
  st.markdown('<div class="section">DISTRIBUIÇÃO DE PERFORMANCE</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
  for x in team:counts[performance(x["projecao"],x["meta_individual"])[0]]+=1
  cards(st,[(f"VENDEDORES {k.upper()}",v,performance_tone(k),"") for k,v in counts.items()])
  st.markdown('<div class="section">RANKING DA EQUIPE</div>',unsafe_allow_html=True); criterion=st.selectbox("Ordenar por",["Vendas","Projeção","% da meta","% Neo","Menos zeros","Comissão"],label_visibility="collapsed"); keys={"Vendas":lambda x:x["vendas"],"Projeção":lambda x:x["projecao"],"% da meta":lambda x:x["projecao"]/x["meta_individual"],"% Neo":lambda x:x["neo_pct"],"Menos zeros":lambda x:-x["zeros"],"Comissão":lambda x:x["total"]}; ranking=sorted(team,key=keys[criterion],reverse=True)
  cols=st.columns(3)
  for i,x in enumerate(ranking[:3]):cols[i].markdown(f'<div class="podium" style="border-left-color:{color(x)}"><b>{i+1}º {html.escape(x["vendedor"])}</b><br>{x["vendas"]} vendas · projeção {x["projecao"]}</div>',unsafe_allow_html=True)
  st.markdown('<div class="section">RELATÓRIO GERAL DA EQUIPE</div>',unsafe_allow_html=True); cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base","COMISSÃO ATUAL"),("comissao_proj","COMISSÃO PROJETADA")]+[(d.day,str(d.day)) for d in all_days]
  display=[]
  for x in team:display.append(x|{"media":f'{x["media"]:.2f}',"meta_pct":pct(x["projecao"]/x["meta_individual"]),"neo_pct_fmt":pct(x["neo_pct"]),"base":money(x["base"]),"comissao_proj":money(x["comissao_proj"])})
  st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)
  st.markdown('<div class="section">PRODUÇÃO POR CANAL</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","ADM","FREELANCE","CANAL NACIONAL")}
  for item in summary:channels[channel_name(item)]+=item["vendas"]
  cards(st,[(name,value,"cyan",pct(value/total if total else 0)+" do total") for name,value in channels.items()],5)
 elif area=="VENDEDORES":
  chosen=st.selectbox("SELECIONE O VENDEDOR",[x["vendedor"] for x in team]); x=next(v for v in team if v["vendedor"]==chosen); status,c,_=performance(x["projecao"],x["meta_individual"]); st.markdown(f'<div class="seller-head" style="background:{c}">{html.escape(x["vendedor"])} · {html.escape(x["setor"])} · Experiência: {x["experiencia"]} · {status}</div>',unsafe_allow_html=True)
  cards(st,[("VENDAS",x["vendas"],"cyan",""),("MÉDIA",f'{x["media"]:.2f}',"cyan",f'{x["dias"]} dias decorridos'),("PROJEÇÃO",x["projecao"],performance_tone(status),f'Meta {x["meta_individual"]}'),("% DA META",pct(x["projecao"]/x["meta_individual"]),performance_tone(status),""),("ZEROS NO MÊS",x["zeros"],"red",f'Semana {x["zeros_semana"]} · sequência {x["sequencia_zeros"]}'),("MAIOR SEQUÊNCIA",x["maior_sequencia_zeros"],"red","dias zerados"),("NEO",x["neo"],"cyan","Elegível: "+("SIM" if x["neo_elegivel"] else "NÃO")),("% NEO",pct(x["neo_pct"]),"green",""),("COMISSÃO ATUAL",money(x["base"]),"green",f'R$ {x["taxa"]:.2f}/venda'),("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow",f'R$ {x["taxa_proj"]:.2f}/venda'),("PREMIAÇÃO SEMANAL",money(x["premio_total"]),"green","Acumulada"),("TOTAL VARIÁVEL",money(x["total"]),"green","Base + bônus + prêmios")])
  st.markdown('<div class="section">PRÓXIMA FAIXA DE COMISSÃO</div>',unsafe_allow_html=True); cards(st,[("ATUAL",f'{x["vendas"]} vendas',"cyan",f'{money(x["base"])} · R$ {x["taxa"]:.2f}/venda'),("PRÓXIMA",x["proxima"],"yellow",f'{money(x["proxima_comissao"])} · R$ {x["proxima_taxa"]:.2f}/venda'),("FALTAM",x["faltam_proxima"],"red","vendas"),("GANHO ADICIONAL",money(x["ganho_proxima"]),"green","ao atingir a faixa")])
  st.markdown('<div class="section">COMPOSIÇÃO DA REMUNERAÇÃO</div>',unsafe_allow_html=True); cards(st,[("COMISSÃO BASE",money(x["base"]),"cyan",""),("BÔNUS NEO",money(x["bonus_neo"]),"green",""),("BÔNUS ADIMPLÊNCIA",money(x["bonus_adim"]),"green",""),("PRÊMIOS",money(x["premio_total"]),"yellow","")])
 elif area=="SEMANAL":
  st.markdown('<div class="section">ACOMPANHAMENTO SEMANAL · SEGUNDA A DOMINGO</div>',unsafe_allow_html=True); max_weeks=max(len(x["semanas"]) for x in team); data=[]
  for x in team:
   row={"Vendedor":x["vendedor"]}
   for i in range(max_weeks):row[f"Semana {i+1}"]=x["semanas"][i]; row[f"Prêmio S{i+1}"]=money(x["premios"][i]); row[f"Status S{i+1}"]="Premiada" if x["premios"][i] else "Abaixo da faixa"
   row["Premiação acumulada"]=money(x["premio_total"]); data.append(row)
  st.dataframe(data,use_container_width=True,hide_index=True,height=520)
 elif area=="COMISSÕES":
  st.markdown('<div class="section">CENÁRIOS DE COMISSÃO</div>',unsafe_allow_html=True); a,b,c=st.columns(3); a.markdown(f'<div class="scenario">CENÁRIO REAL ATUAL<br>{total} vendas · {"ACIMA" if official=="maior_ou_igual_1000" else "ABAIXO"} DE 1.000</div>',unsafe_allow_html=True); b.markdown(f'<div class="scenario">CENÁRIO PROJETADO<br>{projection} vendas · {"ACIMA" if projected_scenario=="maior_ou_igual_1000" else "ABAIXO"} DE 1.000</div>',unsafe_allow_html=True); simulation=c.selectbox("SIMULAR COMISSÃO",["Não simular","Abaixo de 1.000","Acima de 1.000"])
  sim_key="abaixo_1000" if simulation=="Abaixo de 1.000" else "maior_ou_igual_1000"; simulated=sum(x["vendas"]*tier_value(x["vendas"],cfg["reguas_comissao"][sim_key]) for x in team if x["vendas"]>=x["minimo"]) if simulation!="Não simular" else None
  cards(st,[("COMISSÃO BASE",money(sum(x["base"] for x in team)),"cyan","Acumulada"),("BÔNUS NEO",money(sum(x["bonus_neo"] for x in team)),"green","Acumulado"),("BÔNUS ADIMPLÊNCIA",money(sum(x["bonus_adim"] for x in team)),"green","Acumulado"),("PREMIAÇÕES",money(sum(x["premio_total"] for x in team)),"yellow","Acumuladas"),("TOTAL VARIÁVEL",money(sum(x["total"] for x in team)),"green","Atual"),("TOTAL PROJETADO",money(sum(x["comissao_proj"] for x in team)),"yellow","No fechamento")]+([("BASE SIMULADA",money(simulated),"cyan",simulation)] if simulated is not None else []),3)
  st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base":x["base"],"Bônus Neo":x["bonus_neo"],"Bônus M2":x["bonus_adim"],"Prêmios":x["premio_total"],"Total":x["total"],"Projetada":x["comissao_proj"]} for x in team],use_container_width=True,hide_index=True)
 st.markdown('<div class="section">RELATÓRIO COMPLETO</div>',unsafe_allow_html=True); book=excel_bytes(rows,cfg,summary,all_days,elapsed,official); st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__=="__main__":render_app()
