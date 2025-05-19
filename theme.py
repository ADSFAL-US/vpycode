"""
Модуль с определением темы Kanagawa для редактора кода.
Содержит все цветовые константы, используемые в приложении.
"""

class KanagawaTheme:
    """Класс с цветовой схемой Kanagawa для редактора кода"""
    
    # Main colors
    BACKGROUND = "#1F1F28"
    FOREGROUND = "#DCD7BA"
    DARKER_BG = "#16161D"
    LIGHTER_BG = "#2A2A37"
    
    # Syntax highlighting colors
    KEYWORD = "#957FB8"     # Purple for keywords
    STRING = "#98BB6C"      # Green for strings
    COMMENT = "#727169"     # Gray for comments
    FUNCTION = "#7E9CD8"    # Blue for functions
    NUMBER = "#FF9E64"      # Orange for numbers
    CLASS = "#7FB4CA"       # Cyan for classes
    OPERATOR = "#FF5D62"    # Red for operators
    
    # UI colors
    SELECTION = "#2D4F67"
    CURSOR = "#C8C093"
    LINE_HIGHLIGHT = "#363646"
    SCROLLBAR = "#54546D"
    PANEL_BG = "#1F1F28"
    PANEL_FG = "#DCD7BA"
    BUTTON_BG = "#2A2A37"
    BUTTON_HOVER = "#363646"
    
    # Console colors
    CONSOLE_BG = "#1A1A22" 
    CONSOLE_FG = "#DCD7BA"
    CONSOLE_ERROR = "#E82424"
    CONSOLE_SUCCESS = "#98BB6C"
    CONSOLE_INFO = "#7FB4CA"
    
    # AI Chat colors
    AI_BG = "#1A1A22"
    AI_USER_MSG = "#DCD7BA"
    AI_BOT_MSG = "#7E9CD8"
    AI_ACCENT = "#957FB8" 