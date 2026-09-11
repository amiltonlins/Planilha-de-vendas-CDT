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
