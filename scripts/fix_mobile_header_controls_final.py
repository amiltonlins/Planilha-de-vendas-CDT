from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

# Corrige apenas seletores mobile que estavam amplos demais e atingiam
# também os stHorizontalBlock/stColumn internos dos próprios botões.
# Não altera cores, tamanhos, textos, lógica, desktop ou componentes.
replacements={
    '.st-key-header_control_strip [data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:wrap!important;gap:7px 8px!important}':
    '.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:wrap!important;gap:7px 8px!important}',

    '.st-key-header_control_strip [data-testid="stHorizontalBlock"]{gap:5px 6px!important}':
    '.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{gap:5px 6px!important}',

    '.st-key-header_control_strip [data-testid="column"]:nth-child(1){flex:1 1 40%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(2){flex:1 1 52%!important}':
    '.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1){flex:1 1 40%!important}.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){flex:1 1 52%!important}',

    '.st-key-header_control_strip [data-testid="column"]:nth-child(3){flex:0 0 31%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(4){flex:1 1 65%!important;overflow:hidden!important}':
    '.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){flex:0 0 31%!important}.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){flex:1 1 65%!important;overflow:hidden!important}',

    '.st-key-header_control_strip [data-testid="column"]:nth-child(1){flex-basis:100%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(2){flex-basis:58%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(3){flex-basis:36%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(4){flex-basis:100%!important}':
    '.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1){flex-basis:100%!important}.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){flex-basis:58%!important}.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){flex-basis:36%!important}.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){flex-basis:100%!important}',

    '  .st-key-header_control_strip [data-testid="stHorizontalBlock"]{\n    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;\n    gap:6px 8px!important;width:100%!important;align-items:center!important;\n  }':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{\n    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;\n    gap:6px 8px!important;width:100%!important;align-items:center!important;\n  }',

    '  .st-key-header_control_strip [data-testid="column"]{width:100%!important;min-width:0!important;max-width:none!important;flex:none!important;}':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{width:100%!important;min-width:0!important;max-width:none!important;flex:none!important;}',

    '  .st-key-header_control_strip [data-testid="column"]:nth-child(1){grid-column:1 / -1!important;grid-row:1!important;}':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1){grid-column:1 / -1!important;grid-row:1!important;}',
    '  .st-key-header_control_strip [data-testid="column"]:nth-child(2){grid-column:1!important;grid-row:2!important;}':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){grid-column:1!important;grid-row:2!important;}',
    '  .st-key-header_control_strip [data-testid="column"]:nth-child(3){grid-column:2!important;grid-row:2!important;}':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){grid-column:2!important;grid-row:2!important;}',
    '  .st-key-header_control_strip [data-testid="column"]:nth-child(4){grid-column:1 / -1!important;grid-row:3!important;width:100%!important;overflow:hidden!important;}':
    '  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){grid-column:1 / -1!important;grid-row:3!important;width:100%!important;overflow:hidden!important;}',
}

changed=0
for old,new in replacements.items():
    if old in s:
        s=s.replace(old,new)
        changed+=1

if changed==0:
    raise SystemExit('Nenhum seletor conflitante encontrado; abortando para evitar alteração indevida.')

path.write_text(s,encoding='utf-8')
print(f'{changed} seletor(es) mobile restringido(s) ao container externo.')
