"""CATANA core: creative direction separated from execution.

    spec          ShotSpec — the 13-field production spec every prompt is built from
    camera        camera movement library (data/camera_movements.json)
    prompt_engine natural language -> ShotSpec -> provider-ready prompt
    qc            prompt validation checklist with actionable fixes
    providers     capability manifest, provider selection, retry/fallback, run log
    director      idea -> production plan -> compiled shot prompts + storyboard

Standard library only (Python 3.9+), so it runs anywhere the skill is installed.
"""
__version__ = "2.0.0"
