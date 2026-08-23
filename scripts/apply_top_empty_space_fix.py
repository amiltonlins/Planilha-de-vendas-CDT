from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
anchor='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
if anchor not in s:
    raise SystemExit('Ponto de inserção não encontrado; abortando.')

css=r'''
    st.markdown("""<style>
/* Correção final do espaço vazio superior do Streamlit.
   Não altera componentes, dados ou regras; apenas remove o espaçamento estrutural antes do painel. */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] section.main,
[data-testid="stMain"],
.stMain{
  margin-top:0!important;
  padding-top:0!important;
}

/* O header nativo do Streamlit estava reservando altura mesmo sem conteúdo útil. */
[data-testid="stHeader"]{
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  background:transparent!important;
}
[data-testid="stHeader"] > div{
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
}

/* Garante que o primeiro conteúdo real comece imediatamente no topo útil da aplicação. */
[data-testid="stMainBlockContainer"],
section.main > div.block-container,
.main .block-container,
.block-container{
  padding-top:.65rem!important;
  margin-top:0!important;
}
.st-key-cdt_top_header{
  margin-top:0!important;
}

@media(max-width:700px){
  [data-testid="stMainBlockContainer"],
  section.main > div.block-container,
  .main .block-container,
  .block-container{
    padding-top:.22rem!important;
    margin-top:0!important;
  }
}
</style>""",unsafe_allow_html=True)
'''

s=s.replace(anchor,css+anchor,1)
p.write_text(s,encoding='utf-8')
print('Espaço vazio superior removido no desktop e mobile.')
