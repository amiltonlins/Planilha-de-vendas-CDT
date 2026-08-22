from pathlib import Path
import re

path=Path('app.py')
s=path.read_text(encoding='utf-8')

# Remove PREMIAÇÕES da navegação aberta da equipe.
s=s.replace('areas=["VISÃO GERAL","SEMANAL","PREMIAÇÕES"]','areas=["VISÃO GERAL","SEMANAL"]',1)

# Move a mesma visualização para a área gerencial, sem alterar cálculos ou campos existentes.
anchor='''    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")'''
block='''    st.markdown("#### PREMIAÇÕES E CENÁRIOS")\n    st.caption("Visão restrita à Gestão. Os valores abaixo reutilizam exatamente os mesmos cálculos já existentes no sistema.")\n    try:\n        if 'management_summary' not in locals():\n            management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)\n            apply_team_labels(management_summary,cfg)\n            management_team=regular(management_summary)\n        management_total=sum(x["vendas"] for x in management_summary)\n        management_projection=sum(x["projecao"] for x in management_summary)\n        management_projected="maior_ou_igual_1000" if management_projection>=cfg["limite_cenario_maior"] else "abaixo_1000"\n        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if management_official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{management_total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if management_projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{management_projection} vendas"),("PREMIAÇÃO BASE ATUAL",money(sum(x["base"] for x in management_team)),"cyan",""),("PREMIAÇÃO PROJETADA",money(sum(x["comissao_proj"] for x in management_team)),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(sum(x["bonus_neo_proj"] for x in management_team)),"green",""),("BÔNUS (SE) 100% ADIM",money(sum(x["bonus_adim_proj"] for x in management_team)),"green",""),("SEMANAIS ACUMULADOS",money(sum(x["premio_total"] for x in management_team)),"cyan",""),("TOTAL VAR. PROJETADO",money(sum(x["total_variavel_proj"] for x in management_team)),"yellow","")])\n        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Projeção":x["projecao"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base atual":x["base"],"Premiação projetada":x["comissao_proj"],"Bônus Neo proj.":x["bonus_neo_proj"],"BÔNUS (SE) 100% ADIM":x["bonus_adim_proj"],"Semanais":x["premio_total"],"Total atual":x["total"],"Total var. projetado":x["total_variavel_proj"]} for x in sorted(management_team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True)],use_container_width=True,hide_index=True)\n    except Exception as exc:\n        st.error(f"Não foi possível montar a área de Premiações: {exc}")\n\n'''
if '#### PREMIAÇÕES E CENÁRIOS' not in s:
    s=s.replace(anchor,block+anchor,1)

# Remove somente a antiga tela pública de PREMIAÇÕES.
pattern=r'''    elif area=="PREMIAÇÕES":\n.*?(?=\nif __name__=="__main__":render_app\(\))'''
s,count=re.subn(pattern,'',s,count=1,flags=re.S)
if count!=1:
    raise SystemExit('Bloco público PREMIAÇÕES não localizado')

path.write_text(s,encoding='utf-8')
