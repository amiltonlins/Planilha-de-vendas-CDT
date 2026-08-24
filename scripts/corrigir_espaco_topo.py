from pathlib import Path

path = Path('app.py')
text = path.read_text(encoding='utf-8')
marker = '/* FIX DEFINITIVO: BLOCOS TECNICOS DE CSS SEM ESPACO VERTICAL - 2026-08-24 */'
anchor = '/* AJUSTE ESTRUTURAL FINAL DE TOPO + PERFORMANCE POR EQUIPE - 2026-08 */\n'

css = r'''/* FIX DEFINITIVO: BLOCOS TECNICOS DE CSS SEM ESPACO VERTICAL - 2026-08-24 */
/* Os vários st.markdown(<style>) anteriores não podem criar itens visuais no fluxo. */
[data-testid="stElementContainer"]:has(style){
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
}

/* Remove qualquer reserva estrutural acima do primeiro conteúdo útil. */
html,body,.stApp,[data-testid="stAppViewContainer"]{
  margin-top:0!important;
  padding-top:0!important;
}
[data-testid="stAppViewContainer"]>.main,
[data-testid="stMain"],
.stMain{
  margin-top:0!important;
  padding-top:0!important;
  top:0!important;
}
[data-testid="stHeader"]{
  position:static!important;
  inset:0!important;
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section.main>div,
.main .block-container,
.block-container{
  margin-top:0!important;
  padding-top:.20rem!important;
}
@media(max-width:900px){
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewBlockContainer"],
  section.main>div,
  .main .block-container,
  .block-container{
    margin-top:0!important;
    padding-top:.08rem!important;
  }
}
'''

if marker not in text:
    if anchor not in text:
        raise SystemExit('Nao encontrei o bloco estrutural final do topo')
    text = text.replace(anchor, anchor + css, 1)
    path.write_text(text, encoding='utf-8')
    print('Correcao definitiva do espaco superior aplicada.')
else:
    print('Correcao definitiva ja estava aplicada.')
