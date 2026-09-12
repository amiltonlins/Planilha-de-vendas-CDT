"""Estilo de navegação da Conciliação alinhado ao menu Comercial."""

STYLE = """<style>
/* Mantém Visão Geral, Diário e Semanal agrupados, como no painel Comercial. */
.st-key-dashboard_view_controls .st-key-top_nav_buttons{
  width:min(100%,520px)!important;
  max-width:520px!important;
  margin:0!important;
}
.st-key-dashboard_view_controls .st-key-top_nav_buttons [data-testid="stHorizontalBlock"]{
  gap:.5rem!important;
}
@media(max-width:700px){
  .st-key-dashboard_view_controls .st-key-top_nav_buttons{
    width:100%!important;
    max-width:100%!important;
  }
}
</style>"""
