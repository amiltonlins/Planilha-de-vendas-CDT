"""Conciliação presentation facade.

Screen rendering stays on the current panel version; weekly presentation receives an explicit highlight for the next prize target, while PNG export keeps the current reference renderer.
"""
from conciliacao_visual_screen import *
from conciliacao_weekly_highlight import ranking_html, STYLE
from conciliacao_export_highlight import ranking_png
