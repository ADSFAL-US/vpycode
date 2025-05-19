"""
Плагин, добавляющий темную тему для редактора.
"""
from plugins.base import Plugin

class DarkTheme(Plugin):
    """Плагин с темной темой для vpycode."""
    
    def __init__(self, app):
        super().__init__(app)
        self.name = "DarkTheme"
        self.version = "1.0.0"
        self.description = "Темная тема для vpycode"
        self.author = "vpycode Team"
        
        # Определяем цвета темы
        self.theme_colors = {
            "BACKGROUND": "#121212",
            "FOREGROUND": "#E0E0E0",
            "DARKER_BG": "#0A0A0A",
            "LIGHTER_BG": "#1E1E1E",
            
            "KEYWORD": "#BB86FC",     # Фиолетовый для ключевых слов
            "STRING": "#03DAC6",      # Бирюзовый для строк
            "COMMENT": "#6B6B6B",     # Серый для комментариев
            "FUNCTION": "#82AAFF",    # Голубой для функций
            "NUMBER": "#CF6679",      # Розовый для чисел
            "CLASS": "#4DD0E1",       # Светло-голубой для классов
            "OPERATOR": "#FF5252",    # Красный для операторов
            
            "SELECTION": "#515151",
            "CURSOR": "#FFFFFF",
            "LINE_HIGHLIGHT": "#1F1F1F",
            "SCROLLBAR": "#333333",
            "PANEL_BG": "#121212",
            "PANEL_FG": "#E0E0E0",
            "BUTTON_BG": "#2C2C2C",
            "BUTTON_HOVER": "#383838",
            
            "CONSOLE_BG": "#0E0E0E",
            "CONSOLE_FG": "#E0E0E0",
            "CONSOLE_ERROR": "#CF6679",
            "CONSOLE_SUCCESS": "#00C853",
            "CONSOLE_INFO": "#03DAC6",
            
            "AI_BG": "#0E0E0E",
            "AI_USER_MSG": "#E0E0E0",
            "AI_BOT_MSG": "#82AAFF",
            "AI_ACCENT": "#BB86FC"
        }
        
        # Кнопка в боковой панели для активации темы
        self.sidebar_button = None
    
    def activate(self):
        """Активация плагина."""
        print(f"Активация плагина {self.name}")
        
        # Добавляем кнопку в боковой панели
        self.sidebar_button = self.add_sidebar_button("🌙", self.apply_dark_theme)
        
        # Добавляем команду в меню "Вид"
        self.add_menu_command("Вид", "Темная тема", self.apply_dark_theme)
        
        print(f"Плагин {self.name} активирован.")
    
    def deactivate(self):
        """Деактивация плагина."""
        print(f"Деактивация плагина {self.name}")
        
        # При деактивации плагина ничего специально не делаем
        # Тему не меняем обратно, так как пользователь мог уже привыкнуть
        
        print(f"Плагин {self.name} деактивирован.")
    
    def apply_dark_theme(self):
        """Применяет темную тему к редактору."""
        # Изменяем тему редактора
        self.change_theme(self.theme_colors)
        
        # Выводим сообщение в консоль
        self.app.write_to_console("Применена темная тема\n", "info") 