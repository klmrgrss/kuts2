# klmrgrss/kuts2/kuts2-eval/app/ui/shared_components.py
from fasthtml.common import *
from config.qualification_data import QUALIFICATION_LEVEL_STYLES

def LevelPill(level_name: str, **kwargs) -> FT:
    """
    Renders a styled pill with an abbreviated qualification level.
    Looks up styles and abbreviations from QUALIFICATION_LEVEL_STYLES config.
    """
    # Get the style info for the given level, or use the default as a fallback
    style_info = QUALIFICATION_LEVEL_STYLES.get(level_name, QUALIFICATION_LEVEL_STYLES["default"])
    
    # Define the base classes for all pills
    base_classes = "px-2 py-0.5 rounded-full text-xs font-semibold"
    
    # Combine base classes with specific color classes and any extra classes passed in
    final_classes = f"{base_classes} {style_info['class']} {kwargs.pop('cls', '')}"
    
    return Span(style_info["abbr"], cls=final_classes, **kwargs)