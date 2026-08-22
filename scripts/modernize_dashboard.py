from pathlib import Path
import re

path=Path('app.py')
text=path.read_text(encoding='utf-8')

helpers=r'''
def ranking_html(ranking):
    medals=("🥇","🥈","🥉")
    rows=[]
    for i,x in enumerate(ranking[:8]):
        status,color,_=performance(x["projecao"],x["meta_individual"])
        medal=medals[i] if i<3 else f"{i+1}º"
        rows.append(
            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'
            f'<div class="rank-name"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'
            f'<div class="rank-kpi"><b>{x["vendas"]}</b><small>vendas</small></div>'
            f'<div class="rank-kpi"><b>{x["neo"]}</b><small>NEO</small></div>'
            f'<div class="rank-kpi"><b>{pct(x["neo_pct"])}</b><small>% NEO</small></div>'
            f'<div class="rank-status" style="color:{color};background:{color}16;border-color:{color}44">{status}</div></div>'
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
'''
if 'def ranking_html(' not in text:
    text=text.replace('\nCSS="""<style>',helpers+'\nCSS="""<style>',1)

new_css=r'''CSS="""<style>
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none!important}
:root{--navy:#0F172A;--ink:#111827;--muted:#64748B;--line:#E2E8F0;--surface:#FFFFFF;--bg:#F4F7FB;--cyan:#0EA5E9;--green:#22C55E;--amber:#F59E0B;--red:#EF4444}
.stApp{background:var(--bg);color:var(--ink)}.block-container{padding:1rem 1.5rem 2.5rem;max-width:1920px}[data-testid="stSidebar"]{display:none!important}
.bi-topbar{background:linear-gradient(110deg,#0F172A,#172554);color:white;border-radius:14px;padding:18px 22px;margin:0 0 10px;box-shadow:0 8px 30px rgba(15,23,42,.12)}.bi-topbar h1{font-size:1.42rem;margin:0;font-weight:800;letter-spacing:-.02em}.bi-topbar p{margin:4px 0 0;color:#CBD5E1;font-size:.78rem}
.section{font-size:.83rem;font-weight:800;color:#334155;padding:5px 0;margin:14px 0 7px;letter-spacing:.035em;text-transform:uppercase}.metric{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 14px;min-height:92px;margin:2px 0 5px;box-shadow:0 2px 10px rgba(15,23,42,.045);overflow:hidden}.metric:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--cyan)}.metric span{display:block;font-size:.66rem;font-weight:800;color:#64748B;letter-spacing:.05em;text-transform:uppercase}.metric strong{display:block;font-size:1.65rem;line-height:1.15;color:#0F172A;margin-top:8px;font-weight:800}.metric small{display:block;font-size:.68rem;color:#94A3B8;margin-top:5px}.metric.green:before{background:var(--green)}.metric.yellow:before{background:var(--amber)}.metric.red:before{background:var(--red)}
.bi-panel{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(15,23,42,.04)}.rank-card{background:white;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(15,23,42,.04)}.rank-row{display:grid;grid-template-columns:54px minmax(180px,1.5fr) 90px 75px 90px 105px;align-items:center;gap:8px;padding:10px 13px;border-bottom:1px solid #EEF2F7}.rank-row:last-child{border-bottom:0}.rank-pos{font-weight:900;text-align:center}.rank-name{display:flex;flex-direction:column;min-width:0}.rank-name b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.81rem}.rank-name small,.rank-kpi small{font-size:.62rem;color:#94A3B8}.rank-kpi{display:flex;flex-direction:column;text-align:center}.rank-kpi b{font-size:.87rem}.rank-status{font-size:.68rem;font-weight:800;text-align:center;border:1px solid;border-radius:999px;padding:4px 7px}
.table-wrap{overflow:auto;max-height:590px;border:1px solid var(--line);border-radius:12px;background:white}.report{border-collapse:separate;border-spacing:0;white-space:nowrap;width:100%;font-size:.72rem}.report th{position:sticky;top:0;background:#0F172A;color:white;padding:8px 9px;z-index:2;font-size:.65rem}.report td{border-right:1px solid #EEF2F7;border-bottom:1px solid #EEF2F7;padding:6px 8px;text-align:center}.report tr:hover td{background-color:#F8FAFC}.empty-bi{background:white;border:1px dashed #CBD5E1;border-radius:12px;padding:22px;text-align:center;color:#64748B}
.stButton button,.stDownloadButton button{border-radius:9px;background:#0F172A;color:white;border:0;font-weight:750;min-height:40px}.stButton button:hover,.stDownloadButton button:hover{background:#1E293B;color:white;border:0}[data-testid="stPopover"] button{border-radius:10px!important;background:#0F172A!important;color:white!important;border:1px solid #334155!important;min-width:48px!important;font-size:1.35rem!important}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}.element-container{margin-bottom:.2rem}
@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px minmax(150px,1fr) 70px 65px 80px}.metric strong{font-size:1.35rem}}@media(max-width:720px){.bi-topbar{padding:14px}.bi-topbar h1{font-size:1.05rem}.rank-row{grid-template-columns:42px 1fr 62px 82px}.block-container{padding:.5rem}}
</style>"""'''
text=re.sub(r'CSS="""<style>.*?</style>"""',new_css,text,count=1,flags=re.S)

new_render=r'''def render_app():
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
    team=regular(summary); total=sum(x["vendas"] for x in summary); projection=sum(x["projecao"] for x in summary); neo=sum(x["neo"] for x in summary); color=lambda x:performance(x["projecao"],x["meta_individual"])[1]
    if area=="VISÃO GERAL":
        cards(st,[("META DO MÊS",cfg["meta_empresa"],"yellow","Objetivo comercial"),("VENDAS REALIZADAS",total,"cyan","Histórico acumulado"),("PROJEÇÃO",projection,"yellow","Fechamento estimado"),("% DA META",pct(total/cfg["meta_empresa"] if cfg["meta_empresa"] else 0),"green","Realizado"),("FALTAM PARA META",max(0,cfg["meta_empresa"]-total),"red","Vendas necessárias"),("VENDAS NEO",neo,"cyan","Neoenergia"),("% NEO",pct(neo/total if total else 0),"green","Participação"),("ZEROS",sum(x["zeros"] for x in team),"red","Dias sem venda")])
        left,right=st.columns([1.7,1],gap="small")
        with left:
            st.markdown('<div class="section">Evolução comercial</div>',unsafe_allow_html=True); cumulative,ideal=daily_series(rows,cfg,data_until); st.line_chart({"Realizado acumulado":cumulative,"Ritmo da meta":ideal},height=245)
        with right:
            st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
            for x in team:counts[performance(x["projecao"],x["meta_individual"])[0]]+=1
            tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],2)
        left,right=st.columns([1.65,1],gap="small")
        with left:
            st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True); ranking=sorted(team,key=lambda x:(x["vendas"],x["neo_pct"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section">Realizado x meta</div>',unsafe_allow_html=True); gap=max(0,cfg["meta_empresa"]-total); st.bar_chart({"Vendas":[total,gap]},height=185)
            st.markdown('<div class="section">Participação NEO</div>',unsafe_allow_html=True); st.bar_chart({"Vendas":[neo,max(0,total-neo)]},height=160)
        st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True); cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA")]+[(d.day,str(d.day)) for d in all_days]; display=[]
        for x in team:display.append(x|{"media":f'{x["media"]:.2f}',"meta_pct":pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),"neo_pct_fmt":pct(x["neo_pct"]),"base_fmt":money(x["base"]),"proj_fmt":money(x["comissao_proj"])})
        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)
        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","ADM","FREELANCE","CANAL NACIONAL")}
        for item in summary:channels[channel_name(item)]+=item["vendas"]
        cards(st,[(name,value,"cyan",pct(value/total if total else 0)+" do total") for name,value in channels.items()],5)
    elif area=="VENDEDORES":
        if not team:st.warning("Nenhum vendedor local ativo. Entre em GESTÃO e classifique/ative os vendedores.");return
        chosen=st.selectbox("SELECIONE O VENDEDOR",[x["vendedor"] for x in team]); x=next(v for v in team if v["vendedor"]==chosen); status,c,tone=performance(x["projecao"],x["meta_individual"])
        st.markdown(f'<div class="bi-panel" style="border-left:5px solid {c}"><b>{html.escape(x["vendedor"])}</b><br><span style="color:#64748B;font-size:.75rem">{html.escape(x["setor"])} · Performance {status}</span></div>',unsafe_allow_html=True)
        cards(st,[("VENDAS",x["vendas"],"cyan",""),("MÉDIA",f'{x["media"]:.2f}',"cyan",f'{x["dias"]} dias'),("PROJEÇÃO",x["projecao"],tone,f'Meta {x["meta_individual"]}'),("% DA META",pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),tone,""),("ZEROS",x["zeros"],"red",f'Semana {x["zeros_semana"]}'),("NEO",x["neo"],"cyan",""),("% NEO",pct(x["neo_pct"]),"green",""),("COMISSÃO ATUAL",money(x["base"]),"green",""),("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow",""),("PRÊMIOS",money(x["premio_total"]),"green",""),("TOTAL VARIÁVEL",money(x["total"]),"green","")])
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
        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{projection} vendas"),("COMISSÃO BASE",money(sum(x["base"] for x in team)),"cyan",""),("BÔNUS NEO",money(sum(x["bonus_neo"] for x in team)),"green",""),("BÔNUS ADIM.",money(sum(x["bonus_adim"] for x in team)),"green",""),("PRÊMIOS",money(sum(x["premio_total"] for x in team)),"yellow",""),("TOTAL VARIÁVEL",money(sum(x["total"] for x in team)),"green",""),("TOTAL PROJETADO",money(sum(x["comissao_proj"] for x in team)),"yellow","")])
        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base":x["base"],"Bônus Neo":x["bonus_neo"],"Bônus M2":x["bonus_adim"],"Prêmios":x["premio_total"],"Total":x["total"],"Projetada":x["comissao_proj"]} for x in team],use_container_width=True,hide_index=True)
    st.markdown('<div class="section">Relatório completo</div>',unsafe_allow_html=True)
    try:
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"Painel_Comercial_Afogados.xlsx"; write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official)); book=path.read_bytes()
        st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as exc:st.warning(f"Não foi possível gerar o Excel agora: {exc}")

if __name__=="__main__":render_app()
'''
text=re.sub(r'def render_app\(\):.*\Z',new_render,text,flags=re.S)
path.write_text(text,encoding='utf-8')
