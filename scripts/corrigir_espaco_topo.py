from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')
marker='/* CORRECAO ESTRUTURAL DO ESPACO SUPERIOR - 2026-08 */'
css=r'''
/* CORRECAO ESTRUTURAL DO ESPACO SUPERIOR - 2026-08 */
html,body{margin:0!important;padding:0!important}
[data-testid="stAppViewContainer"]{margin-top:0!important;padding-top:0!important}
[data-testid="stAppViewContainer"]>.main{margin-top:0!important;padding-top:0!important}
[data-testid="stAppViewBlockContainer"]{margin-top:0!important;padding-top:.35rem!important}
section.main>div{margin-top:0!important;padding-top:.35rem!important}
.block-container{margin-top:0!important;padding-top:.35rem!important}
@media(max-width:900px){
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewContainer"]>.main,
  [data-testid="stAppViewBlockContainer"],
  section.main>div,
  .block-container{margin-top:0!important;padding-top:.18rem!important}
}
'''
if marker not in text:
    pos=text.rfind('</style>')
    if pos<0:
        raise SystemExit('Nao encontrei </style> no CSS principal')
    text=text[:pos]+css+'\n'+text[pos:]
path.write_text(text,encoding='utf-8')
print('Correcao estrutural do espaco superior aplicada.')
