from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

status_line = '            f\'<span class="rank-projection-status"><strong class="rank-status-emoji">{status_emoji}</strong><small>{html.escape(status_message)}</small></span>\'\n'
base_line = '            f\'<span><strong>{money(x["base"])}</strong><small>PREMIAÇÃO ATUAL</small></span>\'\n'
total_line = '            f\'<span class="total-highlight"><strong>{money(x["total_variavel_proj"])}</strong><small>TOTAL VAR. PROJ.</small></span>\'\n'

current = status_line + base_line
if current not in text:
    raise SystemExit("Posição atual do indicador não encontrada; nenhuma alteração aplicada.")
text = text.replace(current, base_line, 1)

target = total_line + "            f'</div></div></div>'\n"
replacement = total_line + status_line + "            f'</div></div></div>'\n"
if target not in text:
    raise SystemExit("Final do ranking não encontrado; nenhuma alteração aplicada.")
text = text.replace(target, replacement, 1)

path.write_text(text, encoding="utf-8")
