from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# 1) Remove o KPI geral de ZEROS do topo.
s=s.replace("        f'<div class=\"exec-card secondary critical\"><small>ZEROS</small><strong>{zeros}</strong><span>Dias sem venda</span></div>'\n","")

# 2) Helpers visuais para performance e produção por canal.
marker='def daily_series(rows,cfg,data_until):\n'
helpers='''def performance_summary_html(counts):
    items=[
        ("AZUL",counts.get("Azul",0),"#0EA5E9"),
        ("VERDE",counts.get("Verde",0),"#22C55E"),
        ("AMARELO",counts.get("Amarelo",0),"#F59E0B"),
        ("VERMELHO",counts.get("Vermelho",0),"#EF4444"),
    ]
    inner=''.join(
        f'<div class="perf-mini" style="--perf:{color}"><span>{label}</span><strong>{value}</strong><small>vendedores</small></div>'
        for label,value,color in items
    )
    return f'<div class="perf-summary">{inner}</div>'


def channels_summary_html(channels,total):
    groups=[
        (("VENDEDORES FRANQUIA",channels.get("VENDEDORES FRANQUIA",0)),("WEBSITE",channels.get("WEBSITE",0))),
        (("FREELANCE",channels.get("FREELANCE",0)),("CANAL NACIONAL",channels.get("CANAL NACIONAL",0))),
    ]
    panels=[]
    for pair in groups:
        minis=[]
        for label,value in pair:
            share=pct(value/total if total else 0)
            minis.append(f'<div class="channel-mini"><span>{label}</span><strong>{value}</strong><small>{share} do total</small></div>')
        panels.append('<div class="channel-panel">'+''.join(minis)+'</div>')
    return '<div class="channel-grid">'+''.join(panels)+'</div>'

'''
if 'def performance_summary_html(counts):' not in s:
    if marker not in s: raise SystemExit('marker helper não encontrado')
    s=s.replace(marker,helpers+marker,1)

# 3) Performance em um único bloco com quatro mini indicadores internos.
old='''        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
        for x in team:counts[performance(x["media"])[0]]+=1
        tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],4)
'''
new='''        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
        for x in team:counts[performance(x["media"])[0]]+=1
        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)
'''
if old not in s: raise SystemExit('bloco performance não encontrado')
s=s.replace(old,new,1)

# 4) Produção por canal: remove ADM e organiza quatro indicadores em dois painéis grandes.
old='''        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","ADM","FREELANCE","CANAL NACIONAL")}
        for item in summary:channels[channel_name(item)]+=item["vendas"]
        cards(st,[(name,value,"cyan",pct(value/total if total else 0)+" do total") for name,value in channels.items()],5)
'''
new='''        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","FREELANCE","CANAL NACIONAL")}
        for item in summary:
            channel=channel_name(item)
            if channel=="ADM":
                continue
            if channel in channels:
                channels[channel]+=item["vendas"]
        st.markdown(channels_summary_html(channels,total),unsafe_allow_html=True)
'''
if old not in s: raise SystemExit('bloco canais não encontrado')
s=s.replace(old,new,1)

# 5) CSS desktop/mobile dos novos blocos + ranking mobile compacto.
css='''
.perf-summary{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;box-shadow:0 2px 12px rgba(15,23,42,.05)}
.perf-mini{position:relative;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;min-width:0;overflow:hidden}.perf-mini:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--perf)}.perf-mini span{display:block;color:#64748B;font-size:.65rem;font-weight:900;letter-spacing:.05em}.perf-mini strong{display:block;color:#0F172A;font-size:1.55rem;margin-top:6px}.perf-mini small{display:block;color:#94A3B8;font-size:.62rem;margin-top:3px}
.channel-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.channel-panel{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;box-shadow:0 2px 12px rgba(15,23,42,.05)}.channel-mini{background:#F8FAFC;border-radius:12px;border:1px solid #E2E8F0;border-left:5px solid #0EA5E9;padding:13px 14px;min-width:0}.channel-mini span{display:block;font-size:.64rem;font-weight:900;letter-spacing:.04em;color:#64748B}.channel-mini strong{display:block;font-size:1.65rem;line-height:1;margin-top:8px;color:#0F172A}.channel-mini small{display:block;font-size:.65rem;color:#94A3B8;margin-top:6px}
@media(max-width:720px){.perf-summary{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;padding:8px}.perf-mini{padding:9px 10px}.perf-mini strong{font-size:1.28rem}.channel-grid{grid-template-columns:1fr;gap:8px}.channel-panel{padding:8px;gap:7px}.channel-mini{padding:10px}.channel-mini strong{font-size:1.35rem}}
@media(max-width:560px){
  .rank-card{border-radius:12px;overflow:visible;background:transparent;border:0;box-shadow:none}
  .rank-row{display:grid!important;grid-template-columns:28px minmax(0,1fr)!important;gap:5px!important;padding:4px 0!important;border:0!important;align-items:start!important}
  .rank-pos{font-size:.7rem!important;padding-top:12px!important}
  .rank-name{display:block!important;padding:10px!important;border-radius:12px!important;box-shadow:0 2px 8px rgba(15,23,42,.10)!important}
  .rank-seller{padding:0 0 8px!important}.rank-seller b{font-size:.84rem!important;line-height:1.08!important}.rank-seller small{font-size:.56rem!important;margin-top:2px!important}
  .rank-inside{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:5px!important}
  .rank-inside span{min-height:40px!important;padding:4px 3px!important;border-left:0!important;border-radius:7px!important;background:rgba(255,255,255,.08);min-width:0!important}
  .rank-inside strong{font-size:.70rem!important;line-height:1.05!important;white-space:normal!important;overflow-wrap:anywhere!important}
  .rank-inside small{font-size:.43rem!important;line-height:1.05!important;margin-top:3px!important}
  .rank-inside .main-kpi{grid-column:span 2!important;background:rgba(15,23,42,.24)!important;min-height:58px!important}
  .rank-inside .main-kpi strong{font-size:1.38rem!important}.rank-inside .main-kpi small{font-size:.52rem!important;font-weight:900!important}
  .rank-inside .neo-highlight{background:rgba(255,255,255,.16)!important}.rank-inside .neo-highlight strong{font-size:.82rem!important}
  .rank-inside .total-highlight{grid-column:span 2!important;background:rgba(15,23,42,.28)!important}.rank-inside .total-highlight strong{font-size:.86rem!important}
}
'''
if '.perf-summary{' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
