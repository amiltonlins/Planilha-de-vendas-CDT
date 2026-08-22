#!/usr/bin/env python3
"""Interface Streamlit do Painel Comercial Afogados.

Uploads são processados exclusivamente em memória. Arquivos temporários usados
para entregar o Excel são apagados assim que seus bytes são lidos.
"""
from __future__ import annotations

import copy
import csv
import io
import json
import re
import tempfile
import unicodedata
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

from gerar_painel import ROOT, build_sheets, summarize, write_xlsx

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
ALIASES = {
    "data_venda": ("data venda", "data da venda", "data", "dt venda", "criado em", "data cadastro"),
    "vendedor": ("vendedor", "colaborador", "consultor", "nome vendedor", "usuario", "responsavel"),
    "setor": ("setor", "equipe", "canal"), "categoria": ("categoria", "tipo vendedor", "perfil"),
    "neoenergia": ("neoenergia", "neoenergia celpe", "produto", "prospeccao", "prospeccao produto", "convenio"),
    "adimplencia_m2": ("adimplencia m2", "m2", "pago m2", "status m2", "adimplencia"),
    "status": ("status", "situacao", "estado"), "id_venda": ("id venda", "id", "codigo", "numero", "proposta"),
}
REQUIRED = tuple(ALIASES)


def normalize_text(value):
    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()


def detect_columns(headers):
    normalized={normalize_text(h):h for h in headers if h is not None}; result={}
    for target,aliases in ALIASES.items():
        for alias in aliases:
            key=normalize_text(alias)
            if key in normalized: result[target]=normalized[key]; break
        if target not in result:
            for key,original in normalized.items():
                if any(normalize_text(a) in key for a in aliases): result[target]=original; break
    if "data_venda" not in result or "vendedor" not in result:
        raise ValueError("Não foi possível identificar as colunas de data e vendedor. Verifique os cabeçalhos.")
    return result


def excel_date(value):
    if isinstance(value,(int,float)) or str(value).replace(".","",1).isdigit():
        return (date(1899,12,30)+timedelta(days=int(float(value)))).isoformat()
    text=str(value).strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M"):
        try: return datetime.strptime(text,fmt).date().isoformat()
        except ValueError: pass
    raise ValueError(f"Data inválida: {text}")


def rows_from_csv(data):
    text=data.decode("utf-8-sig",errors="replace"); sample=text[:4096]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\t|")
    except csv.Error: dialect=csv.excel
    return list(csv.DictReader(io.StringIO(text),dialect=dialect))


def _xlsx_sheets(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml")); shared=["".join(x.text or "" for x in si.iterfind(".//m:t",NS)) for si in root.findall("m:si",NS)]
        workbook=ET.fromstring(z.read("xl/workbook.xml")); relroot=ET.fromstring(z.read("xl/_rels/workbook.xml.rels")); rels={x.attrib["Id"]:x.attrib["Target"] for x in relroot}
        for sheet in workbook.findall(".//m:sheet",NS):
            target=rels[sheet.attrib[f"{{{NS['r']}}}id"]]; path="xl/"+target.lstrip("/")
            root=ET.fromstring(z.read(path)); table=[]
            for row in root.findall(".//m:sheetData/m:row",NS):
                values={}
                for cell in row.findall("m:c",NS):
                    letters=re.match(r"[A-Z]+",cell.attrib["r"]).group(); idx=0
                    for ch in letters: idx=idx*26+ord(ch)-64
                    typ=cell.attrib.get("t"); value=""
                    if typ=="inlineStr": value="".join(x.text or "" for x in cell.findall(".//m:t",NS))
                    else:
                        node=cell.find("m:v",NS); value=node.text if node is not None else ""
                        if typ=="s" and value: value=shared[int(value)]
                    values[idx-1]=value
                if values: table.append([values.get(i,"") for i in range(max(values)+1)])
            yield sheet.attrib["name"],table


def rows_from_xlsx(data):
    best=None
    for name,table in _xlsx_sheets(data):
        for index,row in enumerate(table[:30]):
            try: mapping=detect_columns(row)
            except ValueError: continue
            score=len(mapping)
            if best is None or score>best[0]: best=(score,row,table[index+1:])
    if not best: raise ValueError("Nenhuma aba com colunas de data e vendedor foi encontrada no XLSX.")
    _,headers,body=best
    return [{str(headers[i]):row[i] if i<len(row) else "" for i in range(len(headers)) if str(headers[i]).strip()} for row in body if any(str(x).strip() for x in row)]


def canonicalize(raw_rows, base_config):
    if not raw_rows: raise ValueError("O relatório está vazio.")
    mapping=detect_columns(raw_rows[0].keys()); output=[]; seen=set()
    valid={normalize_text(x) for x in base_config["status_validos"]}
    for number,row in enumerate(raw_rows,1):
        try: day=excel_date(row.get(mapping["data_venda"],""))
        except ValueError: continue
        seller=str(row.get(mapping["vendedor"],"")).strip()
        if not seller: continue
        product=str(row.get(mapping.get("neoenergia",""),"")); status=str(row.get(mapping.get("status",""),"Aprovada") or "Aprovada")
        identifier=str(row.get(mapping.get("id_venda",""),"") or f"UPLOAD-{number}")
        if identifier in seen or normalize_text(status) not in valid: continue
        seen.add(identifier); output.append({"data_venda":datetime.strptime(day,"%Y-%m-%d").date(),"vendedor":seller,"setor":str(row.get(mapping.get("setor",""),"NÃO INFORMADO") or "NÃO INFORMADO"),"categoria":str(row.get(mapping.get("categoria",""),"Vendedor") or "Vendedor"),"neoenergia":"Sim" if "neoenergia" in normalize_text(product) or normalize_text(product) in ("sim","1","true") else "Não","adimplencia_m2":str(row.get(mapping.get("adimplencia_m2",""),"0") or "0"),"status":status,"id_venda":identifier})
    if not output: raise ValueError("Nenhuma venda válida foi encontrada após aplicar data, status e duplicidade.")
    return output,mapping


def prepare_config(base, rows, month, year):
    cfg=copy.deepcopy(base); cfg["mes"],cfg["ano"]=month,year
    existing={x["vendedor"]:x for x in cfg["vendedores"]}; sellers=[]
    for name in sorted({x["vendedor"] for x in rows}):
        sample=next(x for x in rows if x["vendedor"]==name); old=existing.get(name,{})
        sellers.append({"vendedor":name,"setor":sample["setor"],"categoria":sample["categoria"],"experiencia":old.get("experiencia",False),"meta_individual":old.get("meta_individual",70)})
    cfg["vendedores"]=sellers; return cfg


def performance(projected,target):
    ratio=projected/target if target else 0
    if ratio>=1.5:return "Azul","#19A7CE","🔵"
    if ratio>=1:return "Verde","#2EAD67","🟢"
    if ratio>=.7:return "Amarelo","#F4C542","🟡"
    return "Vermelho","#E55353","🔴"


def excel_bytes(rows,cfg,summary,all_days,elapsed,official):
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/"Painel_Comercial_Afogados.xlsx"
        write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official))
        return path.read_bytes()


def render_app():
    import streamlit as st
    st.set_page_config(page_title="Painel Comercial — Afogados",page_icon="📊",layout="wide")
    st.markdown("<style>.block-container{padding-top:1.5rem}.kpi{border-radius:12px;padding:16px;color:white;font-weight:700}.seller{padding:12px;border-radius:10px;color:white;font-size:1.05rem;font-weight:700}</style>",unsafe_allow_html=True)
    st.title("Painel Comercial — Afogados")
    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8")); now=date.today()
    c1,c2=st.columns(2); month=c1.selectbox("Mês",range(1,13),index=base["mes"]-1,format_func=lambda x:("Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")[x-1]); year=c2.number_input("Ano",2020,2100,value=base["ano"])
    uploaded=st.file_uploader("Importe o relatório de vendas",type=["xlsx","csv"],help="O arquivo é processado em memória e não é salvo permanentemente.")
    if not uploaded:
        st.info("Envie o relatório .xlsx baixado do sistema ou um arquivo .csv para iniciar."); return
    try:
        data=uploaded.getvalue(); raw=rows_from_xlsx(data) if uploaded.name.lower().endswith(".xlsx") else rows_from_csv(data); rows,mapping=canonicalize(raw,base); cfg=prepare_config(base,rows,int(month),int(year))
    except Exception as exc:
        st.error(f"Não foi possível processar o arquivo: {exc}"); return
    with st.expander("⚙️ Configurações",expanded=False):
        a,b,c=st.columns(3); cfg["meta_empresa"]=a.number_input("Meta mensal",1,value=int(cfg["meta_empresa"])); cfg["limite_cenario_maior"]=b.number_input("Limite do cenário maior",1,value=int(cfg["limite_cenario_maior"])); cfg["dia_referencia"]=c.number_input("Dia de referência",1,31,value=min(base["dia_referencia"],31))
        a,b,c=st.columns(3); cfg["bonus_neoenergia"]["percentual_minimo"]=a.number_input("Neo mínimo (%)",0.,100.,value=cfg["bonus_neoenergia"]["percentual_minimo"]*100)/100; cfg["bonus_neoenergia"]["percentual_bonus"]=b.number_input("Bônus Neo (%)",0.,100.,value=cfg["bonus_neoenergia"]["percentual_bonus"]*100)/100; cfg["bonus_adimplencia"]["percentual_bonus"]=c.number_input("Bônus adimplência (%)",0.,100.,value=cfg["bonus_adimplencia"]["percentual_bonus"]*100)/100
        st.subheader("Vendedores")
        for i,seller in enumerate(cfg["vendedores"]):
            a,b=st.columns(2); seller["meta_individual"]=a.number_input(f"Meta — {seller['vendedor']}",1,value=int(seller["meta_individual"]),key=f"meta_{i}"); seller["experiencia"]=b.checkbox(f"Em experiência — {seller['vendedor']}",value=seller["experiencia"],key=f"exp_{i}")
        st.subheader("Premiações semanais")
        cols=st.columns(5)
        for i,item in enumerate(cfg["premiacao_semanal"]): item["vendas"]=cols[i].number_input(f"Faixa {i+1}",1,value=int(item["vendas"]),key=f"tier_{i}"); item["premio"]=cols[i].number_input(f"Prêmio {i+1} (R$)",0.,value=float(item["premio"]),key=f"prize_{i}")
        scenario=st.radio("Régua para simulação",["Automático","Empresa ≥ 1.000","Empresa < 1.000"],horizontal=True)
        for key,label in (("maior_ou_igual_1000","Régua ≥ 1.000"),("abaixo_1000","Régua < 1.000")):
            st.caption(label); cols=st.columns(4)
            for i,item in enumerate(cfg["reguas_comissao"][key]):
                col=cols[i%4]; item["vendas"]=col.number_input(f"Vendas {label} • faixa {i+1}",1,value=int(item["vendas"]),key=f"rule_qty_{key}_{i}"); item["valor_por_venda"]=col.number_input(f"R$/venda {label} • faixa {i+1}",0.,value=float(item["valor_por_venda"]),key=f"rule_value_{key}_{i}")
        if scenario!="Automático": cfg["limite_cenario_maior"]=0 if "≥" in scenario else 10**9
    try: summary,all_days,elapsed,official=summarize(rows,cfg)
    except Exception as exc: st.error(f"Erro nos cálculos: {exc}"); return
    total=sum(x["vendas"] for x in summary); projection=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary)
    st.success(f"{len(rows)} vendas válidas processadas. Colunas identificadas automaticamente: {', '.join(mapping)}.")
    st.subheader("Visão geral")
    metrics=[("Vendas totais",total),("Meta",cfg["meta_empresa"]),("% da meta",f"{total/cfg['meta_empresa']:.1%}"),("Projeção",projection),("Neoenergia",neo),("% Neoenergia",f"{neo/total:.1%}" if total else "0%"),("Dias zerados",sum(x["zeros"] for x in summary)),("Comissão atual",f"R$ {sum(x['total'] for x in summary):,.2f}"),("Comissão projetada",f"R$ {sum(x['comissao_proj'] for x in summary):,.2f}")]
    for start in range(0,len(metrics),3):
        cols=st.columns(3)
        for col,(label,value) in zip(cols,metrics[start:start+3]): col.metric(label,value)
    st.subheader("Vendas por setor"); sectors={}
    for x in summary: sectors[x["setor"]]=sectors.get(x["setor"],0)+x["vendas"]
    st.bar_chart(sectors)
    st.subheader("Ranking dos vendedores")
    ranking=sorted(summary,key=lambda x:x["vendas"],reverse=True)
    for pos,x in enumerate(ranking,1):
        _,color,icon=performance(x["projecao"],x["meta_individual"]); st.markdown(f'<div class="seller" style="background:{color}">{pos}º {icon} {x["vendedor"]} — {x["vendas"]} vendas | projeção {x["projecao"]} / meta {x["meta_individual"]}</div><br>',unsafe_allow_html=True)
    st.subheader("Desempenho semanal, premiações e comissões"); st.dataframe([{"Vendedor":x["vendedor"],**{f"S{i+1}":v for i,v in enumerate(x["semanas"])},"Premiações":x["premio_total"],"Comissão atual":x["total"],"Comissão projetada":x["comissao_proj"]} for x in ranking],use_container_width=True,hide_index=True)
    st.subheader("Painel individual"); chosen=st.selectbox("Vendedor",[x["vendedor"] for x in ranking]); seller=next(x for x in summary if x["vendedor"]==chosen); status,color,icon=performance(seller["projecao"],seller["meta_individual"]); st.markdown(f'<div class="seller" style="background:{color}">{icon} {chosen} — desempenho {status}</div>',unsafe_allow_html=True)
    individual=[("Vendas",seller["vendas"]),("Média",f"{seller['media']:.2f}"),("Projeção",seller["projecao"]),("% da meta",f"{seller['projecao']/seller['meta_individual']:.1%}"),("Dias zerados",seller["zeros"]),("Neoenergia",seller["neo"]),("% Neoenergia",f"{seller['neo_pct']:.1%}"),("Prêmios",f"R$ {seller['premio_total']:,.2f}"),("Comissão atual",f"R$ {seller['base']:,.2f}"),("Bônus Neo",f"R$ {seller['bonus_neo']:,.2f}"),("Bônus adimpl.",f"R$ {seller['bonus_adim']:,.2f}"),("Comissão total",f"R$ {seller['total']:,.2f}"),("Comissão projetada",f"R$ {seller['comissao_proj']:,.2f}"),("Próxima faixa",seller["proxima"]),("Faltam",seller["faltam_proxima"])]
    for start in range(0,len(individual),3):
        cols=st.columns(3)
        for col,(label,value) in zip(cols,individual[start:start+3]): col.metric(label,value)
    st.dataframe([{"Semana":f"Semana {i+1}","Vendas":seller["semanas"][i],"Premiação":seller["premios"][i]} for i in range(5)],use_container_width=True,hide_index=True)
    book=excel_bytes(rows,cfg,summary,all_days,elapsed,official); st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")


if __name__ == "__main__": render_app()
