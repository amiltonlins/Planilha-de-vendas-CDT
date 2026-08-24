from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')

old='''        _,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))
'''
new='''        classification,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        performance_key=normalize_text(classification)
        status_emoji={
            "vermelho":"😟",
            "amarelo":"😐",
            "verde":"🙂",
            "azul":"😎",
        }.get(performance_key,"😟")
        status_message=""
'''
if old not in text:
    raise SystemExit('Trecho do ranking não encontrado; abortando para não alterar código incorreto.')
text=text.replace(old,new,1)
path.write_text(text,encoding='utf-8')
print('Emojis de performance sincronizados com as 4 classificações de cor.')
