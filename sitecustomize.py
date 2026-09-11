"""Project startup hooks.

Keep the on-screen Conciliação layout untouched and replace only its PNG export
with the approved mobile reference renderer before conciliacao_ui imports it.
"""
try:
    import conciliacao_visual as _conciliacao_visual
    from conciliacao_export_reference import ranking_png as _reference_ranking_png

    _conciliacao_visual.ranking_png = _reference_ranking_png
except Exception:
    # Never block application startup because of an optional presentation hook.
    pass
