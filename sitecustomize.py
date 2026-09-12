"""Project startup hooks.

Keep the on-screen Conciliação layout untouched and replace only its PNG export
with the approved mobile reference renderer before conciliacao_ui imports it.
Also inject the Commercial manual refresh control into the existing dashboard
control row without changing app_core's business logic.
"""
try:
    import conciliacao_visual as _conciliacao_visual
    from conciliacao_export_reference import ranking_png as _reference_ranking_png

    _conciliacao_visual.ranking_png = _reference_ranking_png
except Exception:
    # Never block application startup because of an optional presentation hook.
    pass


def _install_cross_month_commercial_weeks():
    """No SEMANAL Comercial, conta a semana completa mesmo quando cruza dois meses.

    Os cálculos mensais permanecem exatamente como estão. Somente as listas
    ``semanas`` e ``premios`` usadas pela aba SEMANAL passam a considerar o bloco
    real de segunda a domingo, inclusive dias da competência anterior/seguinte.
    """
    try:
        from datetime import timedelta
        import app_core as core
    except Exception:
        return

    if getattr(core, "_cross_month_commercial_weeks_installed", False):
        return

    original_summarize = core.summarize

    def summarize_with_cross_month_weeks(rows, cfg):
        result, calendar_days, elapsed_days, official = original_summarize(rows, cfg)
        try:
            clipped_weeks = core.month_weeks(int(cfg["ano"]), int(cfg["mes"]))
            full_weeks = []
            for start, _end in clipped_weeks:
                full_start = start - timedelta(days=start.weekday())
                full_weeks.append((full_start, full_start + timedelta(days=6)))

            awards = list(cfg.get("premiacao_semanal", []) or [])

            def weekly_award(qty):
                eligible = [
                    float(item.get("premio", 0) or 0)
                    for item in awards
                    if qty >= int(item.get("vendas", 0) or 0)
                ]
                return eligible[-1] if eligible else 0

            rows_by_seller = {}
            for row in rows:
                key = core.normalize_text(row.get("vendedor", ""))
                if key:
                    rows_by_seller.setdefault(key, []).append(row)

            for item in result:
                seller_rows = rows_by_seller.get(core.normalize_text(item.get("vendedor", "")), [])
                weekly_sales = [
                    sum(start <= row.get("data_venda") <= end for row in seller_rows)
                    for start, end in full_weeks
                ]
                item["semanas"] = weekly_sales
                item["premios"] = [
                    weekly_award(qty) if item.get("elegivel_individual", False) else 0
                    for qty in weekly_sales
                ]
                # Não recalcular premio_total/total_variavel: a alteração é exclusiva
                # da aba SEMANAL e não muda fechamento, comissão ou visão mensal.
        except Exception:
            # Em qualquer cenário inesperado, preserva o resumo mensal original.
            pass

        return result, calendar_days, elapsed_days, official

    core.summarize = summarize_with_cross_month_weeks
    core._cross_month_commercial_weeks_installed = True


_install_cross_month_commercial_weeks()


def _install_shared_week_ranges():
    """Usa no Conciliação os mesmos blocos semanais exibidos no Comercial."""
    try:
        import app_core as core
        import conciliacao as conc
    except Exception:
        return

    if getattr(conc, "_shared_week_ranges_installed", False):
        return

    def shared_weeks(year, month):
        return core.month_weeks(int(year), int(month))

    conc.weeks = shared_weeks
    conc._shared_week_ranges_installed = True


_install_shared_week_ranges()


def _install_week_selector_standard():
    """Padroniza nome, período e visual do seletor semanal nos dois painéis."""
    try:
        import inspect
        import re
        import streamlit as st
        from streamlit.delta_generator import DeltaGenerator
        import app_core as core
    except Exception:
        return

    if getattr(st, "_cdt_week_selector_standard_installed", False):
        return

    original_st_button = st.button
    original_dg_button = DeltaGenerator.button

    WEEK_STYLE = """<style>
.st-key-dashboard_view_controls .st-key-week_nav_buttons,
.st-key-week_nav_buttons{
  width:100%!important;max-width:100%!important;min-width:0!important;
  margin:6px 0 2px!important;padding:0!important;overflow:visible!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"],
.st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  width:100%!important;min-width:0!important;max-width:100%!important;
  gap:7px!important;align-items:flex-start!important;overflow:visible!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"],
.st-key-week_nav_buttons [data-testid="column"]{
  flex:1 1 0!important;width:auto!important;min-width:0!important;max-width:none!important;
  margin:0!important;padding:0!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
.st-key-week_nav_buttons .stButton,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div,
.st-key-week_nav_buttons .stButton>div{
  width:100%!important;min-width:0!important;max-width:100%!important;margin:0!important;padding:0!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button,
.st-key-week_nav_buttons .stButton button{
  width:100%!important;min-width:0!important;max-width:100%!important;
  height:38px!important;min-height:38px!important;max-height:38px!important;
  margin:0!important;padding:0 8px!important;border-radius:8px!important;
  background:#FFFFFF!important;color:#475569!important;border:1px solid #D8E3EE!important;
  box-shadow:none!important;font-size:.72rem!important;font-weight:900!important;
  letter-spacing:.01em!important;line-height:1!important;white-space:nowrap!important;
  overflow:hidden!important;text-overflow:clip!important;justify-content:center!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button:hover,
.st-key-week_nav_buttons .stButton button:hover{
  background:#F8FAFC!important;color:#0F172A!important;border-color:#B8C7D6!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stBaseButton-primary"],
.st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-week_nav_buttons [data-testid="stBaseButton-primary"]{
  background:#075B35!important;color:#FFFFFF!important;border-color:#075B35!important;
  box-shadow:none!important;font-weight:950!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button p,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button span,
.st-key-week_nav_buttons .stButton button p,
.st-key-week_nav_buttons .stButton button span{
  margin:0!important;padding:0!important;font:inherit!important;line-height:1!important;
  white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;
}
.week-period-caption{
  margin:4px 0 0!important;padding:0!important;text-align:center!important;
  color:#94A3B8!important;font-size:.54rem!important;font-weight:650!important;
  line-height:1.05!important;white-space:nowrap!important;
}
@media(max-width:700px){
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"],
  .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{gap:3px!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"],
  .st-key-week_nav_buttons [data-testid="column"]{
    flex:1 1 0!important;width:auto!important;min-width:0!important;max-width:none!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div,
  .st-key-week_nav_buttons .stButton>div{
    width:100%!important;min-width:0!important;max-width:100%!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button,
  .st-key-week_nav_buttons .stButton button{
    width:100%!important;min-width:0!important;max-width:100%!important;
    height:34px!important;min-height:34px!important;max-height:34px!important;
    padding:0 3px!important;border-radius:7px!important;font-size:clamp(.56rem,2.1vw,.66rem)!important;
  }
  .week-period-caption{font-size:clamp(.43rem,1.8vw,.51rem)!important;margin-top:3px!important;}
}
</style>"""

    def render_period(target, start, end):
        target.markdown(WEEK_STYLE, unsafe_allow_html=True)
        target.markdown(
            f'<div class="week-period-caption">{start:%d/%m} a {end:%d/%m}</div>',
            unsafe_allow_html=True,
        )

    def commercial_week_period(index, frame):
        cfg = frame.f_locals.get("cfg") if frame is not None else None
        if not isinstance(cfg, dict):
            return None
        try:
            ranges = core.month_weeks(int(cfg["ano"]), int(cfg["mes"]))
            return ranges[index] if 0 <= index < len(ranges) else None
        except Exception:
            return None

    def standardized_st_button(label, *args, **kwargs):
        key = kwargs.get("key")
        match = re.fullmatch(r"week_btn_(\d+)", str(key or ""))
        if not match:
            return original_st_button(label, *args, **kwargs)

        index = int(match.group(1))
        caller = inspect.currentframe().f_back
        period = commercial_week_period(index, caller)
        result = original_st_button(f"S - {index + 1}", *args, **kwargs)
        if period:
            render_period(st, period[0], period[1])
        return result

    def standardized_dg_button(self, label, *args, **kwargs):
        key = kwargs.get("key")
        match = re.fullmatch(r"conc_week_btn_(\d+)_(\d+)_(\d+)", str(key or ""))
        if not match:
            return original_dg_button(self, label, *args, **kwargs)

        year, month, index = map(int, match.groups())
        try:
            ranges = core.month_weeks(year, month)
            period = ranges[index] if 0 <= index < len(ranges) else None
        except Exception:
            period = None
        result = original_dg_button(self, f"S - {index + 1}", *args, **kwargs)
        if period:
            render_period(self, period[0], period[1])
        return result

    st.button = standardized_st_button
    DeltaGenerator.button = standardized_dg_button
    st._cdt_week_selector_standard_installed = True


_install_week_selector_standard()


def _install_commercial_refresh_control():
    """Reuse the Conciliação refresh pattern in the Commercial control row."""
    try:
        import inspect
        import streamlit as st
    except Exception:
        return

    if getattr(st, "_cdt_commercial_refresh_columns_patched", False):
        return

    original_columns = st.columns
    target_spec = [2.15, 2.05, 1.15, 4.65]

    def columns_with_commercial_refresh(spec, *args, **kwargs):
        caller = inspect.currentframe().f_back
        is_commercial_control_row = (
            isinstance(spec, (list, tuple))
            and list(spec) == target_spec
            and caller is not None
            and caller.f_code.co_name == "render_app"
            and str(caller.f_code.co_filename).endswith("app_core.py")
        )
        if not is_commercial_control_row:
            return original_columns(spec, *args, **kwargs)

        columns = original_columns([2.15, 2.05, 1.15, 3.65, 1.0], *args, **kwargs)
        with columns[4]:
            st.markdown(
                """<style>
.st-key-commercial_refresh button{
  background:transparent!important;
  color:#64748b!important;
  border:0!important;
  min-height:26px!important;
  padding:0 5px!important;
  box-shadow:none!important;
}
@media(max-width:700px){
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5){
    grid-column:1/-1!important;
    grid-row:3!important;
    display:flex!important;
    justify-content:flex-end!important;
    width:100%!important;
    max-width:none!important;
    min-width:0!important;
  }
  .st-key-commercial_refresh{margin-left:auto!important;width:auto!important;}
}
</style>""",
                unsafe_allow_html=True,
            )
            if st.button(
                "↻ Atualizar dados",
                key="commercial_refresh",
                help="Consultar novamente os resultados da planilha",
            ):
                st.session_state["commercial_force_refresh"] = True
                st.rerun()

        return columns[:4]

    st.columns = columns_with_commercial_refresh
    st._cdt_commercial_refresh_columns_patched = True


_install_commercial_refresh_control()
