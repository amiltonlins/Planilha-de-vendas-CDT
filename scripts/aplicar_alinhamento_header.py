from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

s=s.replace('from datetime import date, datetime, timedelta\n', 'from datetime import date, datetime, timedelta\nfrom zoneinfo import ZoneInfo\n', 1)
s=s.replace('BASE_SELLER_DEFAULTS=[]\n', 'BASE_SELLER_DEFAULTS=[]\nRECIFE_TZ=ZoneInfo("America/Recife")\n', 1)

old='''def save_published(rows,cfg,source_name,history=None,updated_at=None):\n    updated_at=updated_at or datetime.now(); PUBLISHED_PATH.parent.mkdir(parents=True,exist_ok=True)\n    payload={"atualizado_em":updated_at.isoformat(timespec="seconds"),"arquivo":Path(source_name).name,\n'''
new='''def save_published(rows,cfg,source_name,history=None,updated_at=None):\n    if updated_at is None:\n        updated_at=datetime.now(RECIFE_TZ)\n    elif updated_at.tzinfo is not None:\n        updated_at=updated_at.astimezone(RECIFE_TZ)\n    PUBLISHED_PATH.parent.mkdir(parents=True,exist_ok=True)\n    payload={"atualizado_em":updated_at.isoformat(timespec="seconds"),"arquivo":Path(source_name).name,\n'''
if old not in s: raise SystemExit('save_published nao encontrado')
s=s.replace(old,new,1)

s=s.replace('''            history.append({"importacao_id":pending_import_id,"data_importacao":datetime.now().isoformat(timespec="seconds"),"arquivo":source,''', '''            history.append({"importacao_id":pending_import_id,"data_importacao":datetime.now(RECIFE_TZ).isoformat(timespec="seconds"),"arquivo":source,''', 1)
s=s.replace('''        save_published(rows,cfg,source,history); st.success("Histórico atualizado e dashboard publicado."); st.rerun()''', '''        report_updated_at=datetime.now(RECIFE_TZ) if imported_days else datetime.fromisoformat(metadata["atualizado_em"])\n        save_published(rows,cfg,source,history,updated_at=report_updated_at); st.success("Histórico atualizado e dashboard publicado."); st.rerun()''', 1)

s=s.replace('''    updated=datetime.fromisoformat(metadata["atualizado_em"])\n''', '''    updated=datetime.fromisoformat(metadata["atualizado_em"])\n    if updated.tzinfo is not None:\n        updated=updated.astimezone(RECIFE_TZ)\n''', 1)

s=s.replace('''st.markdown(f'<div class="header-meta header-update"><span class="header-meta-icon">◷</span>{html.escape(update_text)}</div>',unsafe_allow_html=True)''', '''st.markdown(f'<div class="header-meta header-update">{html.escape(update_text)}</div>',unsafe_allow_html=True)''')
s=s.replace('''st.markdown(f'<div class="header-meta header-month"><span class="header-meta-icon">▦</span>{html.escape(competence_text)}</div>',unsafe_allow_html=True)''', '''st.markdown(f'<div class="header-meta header-month">{html.escape(competence_text)}</div>',unsafe_allow_html=True)''')

needle='''@media(max-width:600px){\n  .st-key-cdt_top_header{padding:12px 12px 8px!important;border-radius:24px!important}\n'''
insert='''@media(max-width:600px){\n  .st-key-cdt_top_header{padding:12px 12px 8px!important;border-radius:24px!important;position:relative!important}\n  .st-key-header_control_strip [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;gap:6px 8px!important;align-items:center!important}\n  .st-key-header_control_strip [data-testid="column"]:nth-child(1){grid-column:1!important;grid-row:1!important;width:100%!important}\n  .st-key-header_control_strip [data-testid="column"]:nth-child(2){grid-column:1!important;grid-row:2!important;width:100%!important}\n  .st-key-header_control_strip [data-testid="column"]:nth-child(3){grid-column:2!important;grid-row:2!important;width:100%!important}\n  .st-key-cdt_top_header [data-testid="stPopover"]{position:absolute!important;right:12px!important;bottom:44px!important;width:calc(50% - 16px)!important;z-index:5!important}\n  .st-key-cdt_top_header [data-testid="stPopover"]>button{width:100%!important;height:36px!important;min-height:36px!important;justify-content:center!important;border-radius:10px!important;font-size:.68rem!important}\n  .st-key-header_control_strip [data-testid="stSegmentedControl"] button{height:36px!important;min-height:36px!important}\n  .header-meta{font-size:.64rem!important;line-height:1.1!important;padding:1px 0!important}\n'''
if needle not in s: raise SystemExit('media mobile alvo nao encontrado')
s=s.replace(needle,insert,1)

path.write_text(s,encoding='utf-8')
