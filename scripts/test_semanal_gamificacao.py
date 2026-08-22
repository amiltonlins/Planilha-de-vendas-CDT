from datetime import date
import json
from pathlib import Path
import app

cfg=json.loads(Path('config.json').read_text(encoding='utf-8'))

# Usa as faixas reais do sistema: não replica regra de premiação.
assert app.weekly_game_level(0,cfg)==0
assert app.weekly_game_level(9,cfg)==0
assert app.weekly_game_level(10,cfg)>=1
assert app.weekly_game_level(30,cfg)==6
assert app.weekly_game_level(35,cfg)==6
assert app.weekly_next_goal(0,cfg)=={'target':10,'missing':10,'prize':50.0}
assert app.weekly_next_goal(10,cfg)=={'target':14,'missing':4,'prize':100.0}
assert app.weekly_next_goal(22,cfg)=={'target':25,'missing':3,'prize':200.0}
assert app.weekly_next_goal(30,cfg) is None

# 22/08/2026 pertence ao bloco 17-23/08 segundo a definição segunda-domingo já existente.
idx=app.weekly_current_index(cfg,6,date(2026,8,22))
assert idx==3, idx
labels=app.weekly_week_labels(cfg,6,idx)
assert labels[0].startswith('✓') and 'ATUAL' in labels[idx]

team=[
 {'vendedor':'A','semanas':[0,0,0,22], 'premios':[0,0,0,150]},
 {'vendedor':'B','semanas':[0,0,0,25], 'premios':[0,0,0,200]},
 {'vendedor':'C','semanas':[0,0,0,0], 'premios':[0,0,0,0]},
]
current=app.weekly_rank_gamified_html(team,3,cfg,True)
history=app.weekly_rank_gamified_html(team,3,cfg,False)
assert current.index('B') < current.index('A') < current.index('C')
assert 'Faltam <b>3</b> vendas para <b>R$ 200,00</b>' in current
assert 'weekly-target' not in history
# Quem está zerado não recebe emoji; o card de C deve terminar sem sequência de gamificação.
c_start=current.index('C')
c_piece=current[c_start:c_start+220]
assert '🤑' not in c_piece
print('OK: semanal gamificada validada')
