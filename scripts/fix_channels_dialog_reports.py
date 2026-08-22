from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

anchor='''def render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color):\n'''
helper='''def general_report_xlsx_bytes(team,all_days):\n    """Gera XLSX padrão e validável pelo Microsoft Excel."""\n    from openpyxl import Workbook, load_workbook\n    from openpyxl.styles import Font, PatternFill, Alignment\n    from openpyxl.utils import get_column_letter\n    output=io.BytesIO()\n    wb=Workbook()\n    ws=wb.active\n    ws.title="RELATORIO GERAL"\n    headers=["EQUIPE","VENDEDOR","TOTAL","PROJEÇÃO","MÉDIA","ZEROS","% META","NEO","% NEO","PREMIAÇÃO ATUAL","PREMIAÇÃO PROJETADA","BÔNUS NEO PROJ.","BÔNUS (SE) 100% ADIM","SEMANAIS","TOTAL VAR. PROJ."]+[str(d.day) for d in all_days]\n    ws.append(headers)\n    for cell in ws[1]:\n        cell.fill=PatternFill("solid",fgColor="0F172A")\n        cell.font=Font(color="FFFFFF",bold=True)\n        cell.alignment=Alignment(horizontal="center")\n    for item in sorted(team,key=lambda z:(z["vendas"],z["projecao"]),reverse=True):\n        meta_pct=item["projecao"]/item["meta_individual"] if item.get("meta_individual") else 0\n        values=[item.get("equipe",""),item.get("vendedor",""),int(item.get("vendas",0) or 0),int(item.get("projecao",0) or 0),float(item.get("media",0) or 0),int(item.get("zeros",0) or 0),meta_pct,int(item.get("neo",0) or 0),float(item.get("neo_pct",0) or 0),float(item.get("base",0) or 0),float(item.get("comissao_proj",0) or 0),float(item.get("bonus_neo_proj",0) or 0),float(item.get("bonus_adim_proj",0) or 0),float(item.get("premio_total",0) or 0),float(item.get("total_variavel_proj",0) or 0)]\n        elapsed_days=item.get("dias_decorridos",set())\n        daily=item.get("diario",{})\n        for d in all_days:\n            values.append(int(daily.get(d.day,0) or 0) if d.day in elapsed_days else None)\n        ws.append(values)\n    ws.freeze_panes="A2"\n    ws.auto_filter.ref=ws.dimensions\n    ws.column_dimensions["A"].width=18\n    ws.column_dimensions["B"].width=34\n    for col in range(3,16):ws.column_dimensions[get_column_letter(col)].width=18\n    for col in range(16,16+len(all_days)):ws.column_dimensions[get_column_letter(col)].width=5\n    for row in ws.iter_rows(min_row=2):\n        row[6].number_format='0.0%'\n        row[8].number_format='0.0%'\n        for idx in range(9,15):row[idx].number_format='R$ #,##0.00'\n    wb.save(output)\n    data=output.getvalue()\n    load_workbook(io.BytesIO(data),read_only=True,data_only=True).close()\n    return data\n\n'''
if 'def general_report_xlsx_bytes(' not in s:
    if anchor not in s:raise SystemExit('anchor render_general_report não encontrado')
    s=s.replace(anchor,helper+anchor,1)

start=s.index('def render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color):')
end=s.index('\ndef manager_password',start)
new_render='''def render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color):\n    st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True)\n    cols=[("equipe","EQUIPE"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","PREMIAÇÃO ATUAL"),("proj_fmt","PREMIAÇÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS (SE) 100% ADIM"),("premio_fmt","SEMANAIS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]\n    display=general_report_display(team)\n    st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)\n'''
s=s[:start]+new_render+s[end:]

start=s.index('def channel_summary_html(channels,total):')
end=s.index('\ndef projection_status_visual',start)
new_channels='''def channel_summary_html(channels,total):\n    pair=(("VENDEDORES FRANQUIA",channels.get("VENDEDORES FRANQUIA",0)),("CANAL NACIONAL",channels.get("CANAL NACIONAL",0)))\n    inner=''.join(f'<div class="channel-mini"><span>{name}</span><strong>{value}</strong><small>{pct(value/total if total else 0)} do total</small></div>' for name,value in pair)\n    return '<div class="channel-summary"><div class="channel-group">'+inner+'</div></div>'\n'''
s=s[:start]+new_channels+s[end:]

old='''        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","WEBSITE","FREELANCE","CANAL NACIONAL")}\n        for item in summary:\n            name=channel_name(item)\n            if name!="ADM" and name in channels:channels[name]+=item["vendas"]\n'''
new='''        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","CANAL NACIONAL")}\n        for item in summary:\n            name=channel_name(item)\n            if name in channels:channels[name]+=item["vendas"]\n'''
if old not in s:raise SystemExit('bloco produção por canal não encontrado')
s=s.replace(old,new,1)

old='''    requested_seller=st.query_params.get("seller")\n    if requested_seller:\n        st.session_state.seller_detail=requested_seller\n        try:del st.query_params["seller"]\n        except KeyError:pass\n    detail_name=st.session_state.get("seller_detail")\n    if detail_name:\n        detail=next((x for x in team if normalize_text(x["vendedor"])==normalize_text(detail_name)),None)\n        if detail:open_seller_dialog(st,detail)\n        else:st.session_state.pop("seller_detail",None)\n'''
new='''    # Abrir detalhamento somente após clique explícito no vendedor.\n    # Limpa estado legado para filtros/equipe não reabrirem o último popup.\n    st.session_state.pop("seller_detail",None)\n    requested_seller=st.query_params.get("seller")\n    if requested_seller:\n        try:del st.query_params["seller"]\n        except KeyError:pass\n        detail=next((x for x in team if normalize_text(x["vendedor"])==normalize_text(requested_seller)),None)\n        if detail:open_seller_dialog(st,detail)\n'''
if old not in s:raise SystemExit('bloco seller_detail não encontrado')
s=s.replace(old,new,1)

anchor='''    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")\n    audit=[]\n'''
insert='''    st.markdown("#### RELATÓRIO GERAL DA EQUIPE")\n    try:\n        management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)\n        apply_team_labels(management_summary,cfg)\n        management_team=regular(management_summary)\n        general_book=general_report_xlsx_bytes(management_team,management_days)\n        validate_xlsx_bytes(general_book,"RELATORIO GERAL")\n        st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="gestao_download_relatorio_geral")\n    except Exception as exc:\n        st.error(f"Não foi possível gerar o Relatório Geral em Excel: {exc}")\n\n    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")\n    audit=[]\n'''
if anchor not in s:raise SystemExit('anchor conferência não encontrado')
s=s.replace(anchor,insert,1)

marker='''    st.markdown('<div class="section">Relatório completo</div>',unsafe_allow_html=True)\n    try:\n        with tempfile.TemporaryDirectory() as folder:\n            path=Path(folder)/"Painel_Comercial_Afogados.xlsx"; write_xlsx(path,build_sheets(rows,cfg,summary,all_days,elapsed,official)); book=path.read_bytes()\n        st.download_button("BAIXAR RELATÓRIO COMPLETO EM EXCEL",book,"Painel_Comercial_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")\n    except Exception as exc:st.warning(f"Não foi possível gerar o Excel agora: {exc}")\n'''
if marker not in s:raise SystemExit('bloco relatório completo não encontrado')
s=s.replace(marker,'',1)

path.write_text(s,encoding='utf-8')
req=Path('requirements.txt')
r=req.read_text(encoding='utf-8')
if 'openpyxl' not in r.lower():req.write_text(r.rstrip()+"\nopenpyxl>=3.1,<4\n",encoding='utf-8')
