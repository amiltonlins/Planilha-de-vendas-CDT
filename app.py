#!/usr/bin/env python3
"""Camada de interação sobre o núcleo existente do painel."""
import html
import math
from urllib.parse import quote
import app_core as _core

_original_general_report_xlsx = _core.general_report_xlsx_bytes
_original_team_card_html = _core.team_performance_card_html
_original_render_management = _core.render_management
_report_rendered_this_run = False


def _management_general_report_xlsx(team, all_days):
    """Renderiza a tabela do Relatório Geral uma única vez e preserva o Excel original."""
    global _report_rendered_this_run
    import streamlit as st

    if not _report_rendered_this_run:
        columns=[("equipe","EQUIPE"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","PREMIAÇÃO ATUAL"),("proj_fmt","PREMIAÇÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS (SE) 100% ADIM"),("premio_fmt","SEMANAIS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(day.day,str(day.day)) for day in all_days]
        display=_core.general_report_display(team)
        st.markdown(_core.table_html(display,columns,lambda item:_core.performance(item["media"])[1],True),unsafe_allow_html=True)
        _report_rendered_this_run = True

    return _original_general_report_xlsx(team,all_days)


def _is_awards_detail_table(data):
    """Identifica somente a tabela detalhada de PREMIAÇÕES E CENÁRIOS."""
    if not isinstance(data, list) or not data:
        return False
    first=data[0]
    if not isinstance(first, dict):
        return False
    required={"Vendedor","Premiação projetada","Total var. projetado"}
    return required.issubset(set(first.keys()))


def _render_management_without_awards_table(*args, **kwargs):
    """Mantém o Menu Gerencial, suprime a planilha de premiações e impede duplicação do Relatório Geral."""
    global _report_rendered_this_run
    import streamlit as st

    # Cada nova renderização do Menu Gerencial começa limpa. Dentro dela, o Relatório Geral
    # pode aparecer somente uma vez, mesmo que funções internas tentem chamá-lo novamente.
    _report_rendered_this_run = False
    original_dataframe=st.dataframe
    original_markdown=st.markdown
    original_download_button=st.download_button
    report_title_seen=False
    report_download_seen=False

    def guarded_dataframe(data=None, *df_args, **df_kwargs):
        if _is_awards_detail_table(data):
            return None
        return original_dataframe(data, *df_args, **df_kwargs)

    def guarded_markdown(body, *md_args, **md_kwargs):
        nonlocal report_title_seen
        normalized=str(body).strip().upper()
        if normalized == "#### RELATÓRIO GERAL DA EQUIPE":
            if report_title_seen:
                return None
            report_title_seen=True
        return original_markdown(body, *md_args, **md_kwargs)

    def guarded_download_button(label, *db_args, **db_kwargs):
        nonlocal report_download_seen
        normalized=str(label).strip().upper()
        if normalized == "BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)":
            if report_download_seen:
                return False
            report_download_seen=True
        return original_download_button(label, *db_args, **db_kwargs)

    st.dataframe=guarded_dataframe
    st.markdown=guarded_markdown
    st.download_button=guarded_download_button
    try:
        return _original_render_management(*args, **kwargs)
    finally:
        st.dataframe=original_dataframe
        st.markdown=original_markdown
        st.download_button=original_download_button


def _clickable_team_card(title,goal,metrics,tone="internal",performance_counts=None):
    """Mantém o card original como item direto do grid e adiciona clique sem quebrar o layout."""
    card=_original_team_card_html(title,goal,metrics,tone,performance_counts)
    return f'<a href="?team={quote(str(title))}" target="_self" style="display:contents;color:inherit;text-decoration:none" aria-label="Abrir detalhamento de {html.escape(str(title),quote=True)}">{card}</a>'


def _active_team_sellers(cfg,team_name):
    blocked={"website","adm","freelance","canal nacional"}
    return [s for s in cfg.get("vendedores",[]) if s.get("ativo",False) and s.get("equipe")==team_name and s.get("pertence_franquia",True) and _core.normalize_text(s.get("categoria","")) not in blocked]


def _popup_css():
    return """<style>
.team-dialog-shell{display:flex;flex-direction:column;gap:10px}.team-goal-hero{background:linear-gradient(120deg,#0F172A,#172554);color:#fff;border-radius:14px;padding:15px 16px}.team-goal-hero small{display:block;font-size:.60rem;font-weight:900;letter-spacing:.08em;color:#CBD5E1}.team-goal-hero strong{display:block;font-size:2.45rem;line-height:1;margin-top:7px;font-weight:950}.team-goal-hero span{display:block;margin-top:6px;font-size:.66rem;color:#E2E8F0}.team-dialog-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.team-dialog-kpi{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:10px;min-width:0}.team-dialog-kpi small{display:block;font-size:.53rem;color:#64748B;font-weight:900}.team-dialog-kpi strong{display:block;font-size:1.28rem;color:#0F172A;font-weight:950;margin-top:5px}.team-dialog-kpi.needed{background:#FFF7ED;border-color:#FED7AA}.team-dialog-kpi.needed strong{font-size:1.5rem;color:#9A3412}.team-capacity{background:#F8FAFC;border:1px solid #CBD5E1;border-radius:12px;padding:11px 12px}.team-capacity-title{font-size:.59rem;font-weight:950;letter-spacing:.07em;color:#475569;margin-bottom:8px}.team-capacity-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.team-capacity-grid>div{background:#fff;border:1px solid #E2E8F0;border-radius:9px;padding:8px;text-align:center}.team-capacity-grid small{display:block;font-size:.49rem;font-weight:900;color:#64748B}.team-capacity-grid strong{display:block;font-size:1.28rem;margin-top:4px;color:#0F172A}.team-capacity-note{font-size:.58rem;color:#64748B;margin-top:7px;line-height:1.35}.team-perf-popup{display:flex;align-items:center;gap:9px;flex-wrap:wrap;background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:8px 10px}.team-perf-popup small{font-size:.52rem;font-weight:900;color:#64748B}.team-perf-popup span{font-size:.70rem;font-weight:900;color:#334155}@media(max-width:700px){[data-testid="stDialog"] .team-dialog-shell{gap:6px!important}[data-testid="stDialog"] .team-goal-hero{padding:10px 11px!important}[data-testid="stDialog"] .team-goal-hero strong{font-size:1.85rem!important}[data-testid="stDialog"] .team-dialog-kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important}[data-testid="stDialog"] .team-dialog-kpi{padding:7px!important}[data-testid="stDialog"] .team-dialog-kpi strong{font-size:1rem!important}[data-testid="stDialog"] .team-capacity{padding:8px!important}[data-testid="stDialog"] .team-capacity-grid>div{padding:6px 4px!important}[data-testid="stDialog"] .team-capacity-grid strong{font-size:.96rem!important}}
</style>"""


def _open_team_dialog_if_requested():
    import streamlit as st
    requested=st.query_params.get("team")
    if requested not in ("Equipe Interna","Equipe Externa") or not st.session_state.get("dashboard_autenticado",False):return
    try:
        base=_core.json.loads((_core.ROOT/"config.json").read_text(encoding="utf-8"))
        rows,cfg,_=_core.load_published(base)
        summary,_,_,_=_core.summarize(rows,cfg)
        _core.apply_team_labels(summary,cfg)
        team=_core.regular(summary)
    except Exception as exc:
        st.error(f"Não foi possível abrir o detalhamento da equipe: {exc}");return
    team_name=requested
    goal=int(cfg.get("meta_equipe_interna" if team_name=="Equipe Interna" else "meta_equipe_externa",0) or 0)
    metrics=_core.team_performance_metrics(summary,team_name,goal)
    active_count=len(_active_team_sellers(cfg,team_name))
    headcount_ideal=math.ceil(goal/40) if goal>0 else 0
    hires_needed=max(0,headcount_ideal-active_count)
    distribution=_core.team_performance_distribution(team,team_name)
    sellers=sorted([x for x in team if x.get("equipe")==team_name],key=lambda x:(int(x.get("vendas",0) or 0),int(x.get("projecao",0) or 0)),reverse=True)

    @st.dialog(team_name,width="large")
    def _dialog():
        st.markdown(_popup_css(),unsafe_allow_html=True)
        st.markdown('<div class="team-dialog-shell"><div class="team-goal-hero"><small>META DA EQUIPE</small>'+f'<strong>{goal}</strong><span>{html.escape(team_name)} · referência: 40 vendas/vendedor/mês</span></div><div class="team-dialog-kpis">'+f'<div class="team-dialog-kpi"><small>VENDAS REALIZADAS</small><strong>{metrics["sales"]}</strong></div><div class="team-dialog-kpi"><small>% DA META</small><strong>{_core.pct(metrics["attainment"])}</strong></div><div class="team-dialog-kpi"><small>FALTAM PARA META</small><strong>{metrics["missing"]}</strong></div><div class="team-dialog-kpi needed"><small>PRECISA FAZER / DIA</small><strong>{metrics["needed"]:.1f}</strong></div><div class="team-dialog-kpi"><small>PROJEÇÃO</small><strong>{metrics["projection"]}</strong></div><div class="team-dialog-kpi"><small>MÉDIA / DIA</small><strong>{metrics["average"]:.1f}</strong></div><div class="team-dialog-kpi"><small>DIAS TRABALHADOS</small><strong>{metrics["elapsed"]}</strong></div><div class="team-dialog-kpi"><small>DIAS RESTANTES</small><strong>{metrics["remaining"]}</strong></div></div><div class="team-capacity"><div class="team-capacity-title">CAPACIDADE DA EQUIPE</div><div class="team-capacity-grid">'+f'<div><small>HEADCOUNT IDEAL</small><strong>{headcount_ideal}</strong></div><div><small>ATIVOS</small><strong>{active_count}</strong></div><div><small>NECESSÁRIO CONTRATAR</small><strong>{hires_needed}</strong></div></div><div class="team-capacity-note">Para uma meta de {goal} vendas, considerando 40 vendas por vendedor/mês, a equipe precisa de aproximadamente {headcount_ideal} vendedores ativos.</div></div><div class="team-perf-popup"><small>PERFORMANCE DA EQUIPE</small>'+f'<span>🔵 {distribution.get("Azul",0)}</span><span>🟢 {distribution.get("Verde",0)}</span><span>🟡 {distribution.get("Amarelo",0)}</span><span>🔴 {distribution.get("Vermelho",0)}</span></div></div>',unsafe_allow_html=True)
        st.markdown("##### RESULTADO POR VENDEDOR")
        seller_rows=[]
        for item in sellers:
            meta=int(item.get("meta_individual",0) or 0);realized=int(item.get("vendas",0) or 0)
            seller_rows.append({"Vendedor":item.get("vendedor",""),"Vendas":realized,"Média/dia":round(float(item.get("media",0) or 0),2),"Projeção":int(item.get("projecao",0) or 0),"% meta":round(realized/meta*100,1) if meta else 0.0})
        if seller_rows:st.dataframe(seller_rows,use_container_width=True,hide_index=True,height=min(330,40+len(seller_rows)*35))
        else:st.caption("Nenhum vendedor ativo nesta equipe.")
        if st.button("FECHAR",key=f"close_team_dialog_{_core.normalize_text(team_name)}",use_container_width=True):
            try:del st.query_params["team"]
            except KeyError:pass
            st.rerun()
    _dialog()


_core.general_report_xlsx_bytes=_management_general_report_xlsx
_core.render_general_report=lambda *args,**kwargs:None
_core.render_management=_render_management_without_awards_table
_core.team_performance_card_html=_clickable_team_card

if __name__=="__main__":
    _core.render_app()
    _open_team_dialog_if_requested()
