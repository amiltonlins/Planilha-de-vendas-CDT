from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
anchor='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
if anchor not in s:
    raise SystemExit('Ponto de inserção não encontrado; abortando.')
css=r'''
    st.markdown("""<style>
/* FIX DEFINITIVO DO ESPAÇO VAZIO SUPERIOR — Streamlit atual + versões anteriores.
   Somente posicionamento do conteúdo; não altera dados, lógica ou componentes. */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"]{
  margin-top:0!important;
  padding-top:0!important;
}
[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stMain"] .block-container,
.stMain .block-container,
.main .block-container,
.block-container{
  margin-top:0!important;
  padding-top:.55rem!important;
}
[data-testid="stMain"], .stMain, section.main, .main{
  margin-top:0!important;
  padding-top:0!important;
}
[data-testid="stHeader"], header[data-testid="stHeader"]{
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"]{
  margin-top:0!important;
}
.st-key-cdt_top_header{margin-top:0!important;}
@media(max-width:700px){
  [data-testid="stAppViewBlockContainer"],
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewContainer"] .block-container,
  [data-testid="stMain"] .block-container,
  .stMain .block-container,
  .main .block-container,
  .block-container{
    margin-top:0!important;
    padding-top:.18rem!important;
  }
}
</style>""",unsafe_allow_html=True)
'''
marker='FIX DEFINITIVO DO ESPAÇO VAZIO SUPERIOR'
if marker not in s:
    s=s.replace(anchor,css+anchor,1)
p.write_text(s,encoding='utf-8')
print('Top viewport fix applied.')
