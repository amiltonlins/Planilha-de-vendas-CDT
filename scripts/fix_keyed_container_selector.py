from pathlib import Path
p=Path('app.py')
s=p.read_text(encoding='utf-8')
old='.st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]'
new='.st-key-header_control_strip > div[data-testid="stHorizontalBlock"]'
count=s.count(old)
if count==0:
    raise SystemExit('Seletor alvo nao encontrado')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print(f'{count} seletores corrigidos para o filho horizontal direto do container chaveado.')
