from pathlib import Path

patch=Path('scripts/patch_reorganizacao_funcional.py')
namespace={'__name__':'__main__','__file__':str(patch)}
exec(compile(patch.read_text(encoding='utf-8'),str(patch),'exec'),namespace)
