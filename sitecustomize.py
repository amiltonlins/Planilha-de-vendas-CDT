"""Project startup hooks.

Mantém os ajustes de inicialização do painel e usa um único seletor semanal
reutilizável no Comercial e na Conciliação.
"""
try:
    import conciliacao_visual as _conciliacao_visual
    from conciliacao_export_reference import ranking_png as _reference_ranking_png

    _conciliacao_visual.ranking_png = _reference_ranking_png
except Exception:
    pass


def _install_cross_month_commercial_weeks():
    """No SEMANAL Comercial, conta a semana completa mesmo quando cruza dois meses."""
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
        except Exception:
            pass

        return result, calendar_days, elapsed_days, official

    core.summarize = summarize_with_cross_month_weeks
    core._cross_month_commercial_weeks_installed = True


_install_cross_month_commercial_weeks()


def _install_shared_week_ranges():
    """Usa na Conciliação os mesmos períodos mensais exibidos no Comercial."""
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
    """Instala o mesmo seletor de períodos no Comercial e na Conciliação."""
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
/* SELETOR SEMANAL ÚNICO — COMERCIAL + CONCILIAÇÃO */
.st-key-week_nav_buttons,
.st-key-dashboard_view_controls .st-key-week_nav_buttons{
  width:auto!important;max-width:100%!important;min-width:0!important;
  margin:2px 0 0!important;padding:0!important;overflow:visible!important;
}
.st-key-week_nav_buttons [data-testid="stHorizontalBlock"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  justify-content:flex-start!important;align-items:center!important;
  width:auto!important;max-width:100%!important;min-width:0!important;
  gap:3px!important;overflow:visible!important;
}
.st-key-week_nav_buttons [data-testid="column"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
  flex:0 0 58px!important;width:58px!important;min-width:58px!important;max-width:58px!important;
  margin:0!important;padding:0!important;
}
.st-key-week_nav_buttons .stButton,
.st-key-week_nav_buttons .stButton>div,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div{
  width:58px!important;min-width:58px!important;max-width:58px!important;
  margin:0!important;padding:0!important;
}
.st-key-week_nav_buttons .stButton button,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
  width:58px!important;min-width:58px!important;max-width:58px!important;
  height:28px!important;min-height:28px!important;max-height:28px!important;
  margin:0!important;padding:0 4px!important;border-radius:6px!important;
  background:#FFFFFF!important;color:#64748B!important;border:1px solid #D7E0E8!important;
  box-shadow:none!important;font-size:.62rem!important;font-weight:850!important;
  letter-spacing:0!important;line-height:1!important;white-space:nowrap!important;
  overflow:visible!important;text-overflow:clip!important;justify-content:center!important;
}
.st-key-week_nav_buttons .stButton button:hover,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button:hover{
  background:#F8FAFC!important;color:#0F172A!important;border-color:#B8C5D1!important;
}
.st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-week_nav_buttons [data-testid="stBaseButton-primary"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stBaseButton-primary"]{
  background:#075B35!important;color:#FFFFFF!important;border-color:#075B35!important;
  box-shadow:none!important;font-weight:950!important;
}
.st-key-week_nav_buttons .stButton button p,
.st-key-week_nav_buttons .stButton button span,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button p,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button span{
  margin:0!important;padding:0!important;font:inherit!important;line-height:1!important;
  white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;
}
/* Remove definitivamente qualquer legenda antiga abaixo dos botões. */
.week-period-caption{display:none!important;height:0!important;margin:0!important;padding:0!important;}
@media(max-width:700px){
  .st-key-week_nav_buttons [data-testid="stHorizontalBlock"],
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
    gap:2px!important;flex-wrap:nowrap!important;
  }
  .st-key-week_nav_buttons [data-testid="column"],
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
    flex:0 0 55px!important;width:55px!important;min-width:55px!important;max-width:55px!important;
  }
  .st-key-week_nav_buttons .stButton,
  .st-key-week_nav_buttons .stButton>div,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div,
  .st-key-week_nav_buttons .stButton button,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    width:55px!important;min-width:55px!important;max-width:55px!important;
  }
  .st-key-week_nav_buttons .stButton button,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    height:27px!important;min-height:27px!important;max-height:27px!important;
    padding:0 3px!important;border-radius:5px!important;font-size:.58rem!important;
  }
}
</style>"""

    def format_period(period, fallback_index):
        if period:
            return f"{period[0].day:02d}–{period[1].day:02d}"
        return f"S{fallback_index + 1}"

    def commercial_period(index, frame):
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
        period = commercial_period(index, caller)
        st.markdown(WEEK_STYLE, unsafe_allow_html=True)
        return original_st_button(format_period(period, index), *args, **kwargs)

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
        self.markdown(WEEK_STYLE, unsafe_allow_html=True)
        return original_dg_button(self, format_period(period, index), *args, **kwargs)

    st.button = standardized_st_button
    DeltaGenerator.button = standardized_dg_button
    st._cdt_week_selector_standard_installed = True
    # Evita um segundo wrapper específico do Comercial sobre o mesmo componente.
    st._weekly_commercial_selector_runtime_installed = True


_install_week_selector_standard()


def _install_commercial_refresh_control():
    """Mantém o botão de atualização manual do Comercial no bloco de controles."""
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
  background:transparent!important;color:#64748b!important;border:0!important;
  min-height:26px!important;padding:0 5px!important;box-shadow:none!important;
}
@media(max-width:700px){
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5){
    grid-column:1/-1!important;grid-row:3!important;display:flex!important;justify-content:flex-end!important;
    width:100%!important;max-width:none!important;min-width:0!important;
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
