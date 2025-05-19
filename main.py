import os
import sys
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, Python3Lexer
from pygments.formatters import get_formatter_by_name
import subprocess
import tempfile
import threading
import io
import queue
import time
from contextlib import redirect_stdout, redirect_stderr
import re
import requests
import json

# Импортируем настройки ИИ по умолчанию
from ai_defaults import DEFAULT_AI_PROMPT, DEFAULT_API_SETTINGS, CODE_BLOCK_PATTERN, READ_FILE_PATTERN, CODE_BLOCK_LINE_PATTERN, CODE_BLOCK_LINES_PATTERN

# Импортируем систему плагинов
from plugins.manager import PluginManager

# Импортируем модули для работы с чтением файлов
try:
    import read_file_handler
    import ai_chat_patch
    FILE_READER_AVAILABLE = True
except ImportError:
    print("Модули для чтения файлов не найдены, функция будет недоступна")
    FILE_READER_AVAILABLE = False

# Для Windows необходимы эти импорты для правильной максимизации/минимизации
if os.name == 'nt':
    import ctypes
    from ctypes import windll, wintypes
    user32 = ctypes.WinDLL('user32')
    
    # Константы для работы с окнами Windows
    SW_MAXIMIZE = 3
    SW_MINIMIZE = 6
    SW_RESTORE = 9
    
    # Установка DPI awareness для корректного отображения на экранах с высоким разрешением
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass

# Kanagawa theme colors
class KanagawaTheme:
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
    
    # Code diff colors
    ADDITION = "#315001"    # Темно-зеленый для добавленных строк
    DELETION = "#5E1512"    # Темно-красный для удаленных строк
    
    # Dialog buttons colors
    BUTTON_ACCEPT = "#1C672A"  # Зеленый для кнопки принятия изменений
    BUTTON_REJECT = "#A73628"  # Красный для кнопки отклонения изменений

# Settings class for editor configuration
class EditorSettings:
    def __init__(self):
        # Default settings
        self.font_size = 11
        self.font_family = "Consolas"
        self.tab_size = 4
        self.use_spaces_for_tab = True
        self.show_whitespace = True
        
        # AI settings
        self.ai_api_key = ""  # OpenRouter API key для доступа к DeepSeek и другим моделям
        self.ai_initial_prompt = DEFAULT_AI_PROMPT
        
        # Hotkeys dictionary - format: {'action': 'key binding'}
        self.hotkeys = {
            'run_code': 'F5',
            'save_file': 'Control-s',
            'open_file': 'Control-o',
            'new_file': 'Control-n',
            'find': 'Control-f',
            'toggle_console': 'Control-grave',  # Control + `
            'toggle_explorer': 'Control-b'
        }
        
    def get_font(self):
        """Returns the font tuple based on current settings"""
        return (self.font_family, self.font_size)
    
    def save_to_file(self, filepath="settings.json"):
        """Save settings to a JSON file"""
        import json
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'font_size': self.font_size,
                    'font_family': self.font_family,
                    'tab_size': self.tab_size,
                    'use_spaces_for_tab': self.use_spaces_for_tab,
                    'show_whitespace': self.show_whitespace,
                    'hotkeys': self.hotkeys,
                    'ai_api_key': self.ai_api_key,
                    'ai_initial_prompt': self.ai_initial_prompt
                }, f, indent=4)
            return True
        except Exception:
            return False
    
    def load_from_file(self, filepath="settings.json"):
        """Load settings from a JSON file"""
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.font_size = data.get('font_size', self.font_size)
                self.font_family = data.get('font_family', self.font_family)
                self.tab_size = data.get('tab_size', self.tab_size)
                self.use_spaces_for_tab = data.get('use_spaces_for_tab', self.use_spaces_for_tab)
                self.show_whitespace = data.get('show_whitespace', self.show_whitespace)
                self.hotkeys = data.get('hotkeys', self.hotkeys)
                self.ai_api_key = data.get('ai_api_key', self.ai_api_key)
                self.ai_initial_prompt = data.get('ai_initial_prompt', self.ai_initial_prompt)
            return True
        except Exception:
            # If the file doesn't exist or is invalid, keep defaults
            return False

class CodeEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Настройка основного окна - НЕ используем overrideredirect, чтобы сохранить таскбар
        self.title("vpycode")
        self.geometry("1200x700")
        self.minsize(800, 500)  # Минимальный размер окна
        
        # Initialize settings
        self.settings = EditorSettings()
        self.settings.load_from_file()  # Try to load saved settings
        
        # Инициализируем тему
        self.theme = KanagawaTheme()
        
        # Применяем тему
        self.configure(fg_color=self.theme.BACKGROUND)
        
        # Инициализируем менеджер языков программирования
        self.language_handlers = {
            "Python": {
                "extensions": [".py"],
                "run_command": self.run_python_code,
                "syntax": {}  # Базовые правила подсветки синтаксиса уже реализованы
            }
        }
        
        # Отключаем стандартную строку заголовка только в Windows
        if os.name == 'nt':
            self.protocol("WM_DELETE_WINDOW", self.quit)
            # Установим правильный стиль для окна
            try:
                HWND = ctypes.windll.user32.GetParent(self.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(HWND, -16)  # GWL_STYLE
                style &= ~0x00C00000  # WS_CAPTION - отключаем стандартный заголовок
                style &= ~0x00080000  # WS_SYSMENU - отключаем системное меню (кнопки в углу)
                ctypes.windll.user32.SetWindowLongW(HWND, -16, style)
            except:
                print("Не удалось изменить стиль окна Windows")
        
        # Переменные для отслеживания текущего проекта и файла
        self.current_file = None
        self.current_project = None
        self.temp_file = None
        self.current_filetype = '.py'  # По умолчанию Python для подсветки
        
        # Номера строк и активная строка
        self.active_line = None
        
        # Для перемещения окна
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Для максимизации/восстановления окна
        self.is_maximized = False
        self.last_size = (1200, 700)
        self.last_position = (None, None)
        
        # Консольные процессы
        self.current_process = None
        self.shell_process = None
        self.command_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # ИИ чат
        self.chat_messages = []  # История сообщений для контекста
        self.is_first_message = True  # Флаг для отправки начальной инструкции
        self.is_generating = False  # Флаг активной генерации ответа
        
        # Инициализация плагинов (но их активация произойдет позже)
        self.plugin_manager = PluginManager(self)
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Теперь когда интерфейс создан, загружаем и активируем плагины
        print("[DEBUG] Начинаем загрузку и активацию плагинов")
        self.plugin_manager.load_plugins()
        # Применяем небольшую задержку перед активацией, чтобы UI полностью инициализировался
        self.after(100, self._activate_plugins)
        
        # Запуск консольной оболочки
        self.start_shell()
        
    def _activate_plugins(self):
        """Активирует все плагины после полной инициализации UI."""
        print("[DEBUG] Активация плагинов...")
        self.plugin_manager.activate_all()
        print("[DEBUG] Активация плагинов завершена")
    
    def setup_ui(self):
        # Основной контейнер
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Основное содержимое имеет больший вес
        
        # Верхняя панель с кнопками управления окном (замена стандартной)
        title_bar = ctk.CTkFrame(self, fg_color=KanagawaTheme.DARKER_BG, height=30)
        title_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        title_bar.pack_propagate(False)
        
        # Обработка перетаскивания окна
        title_bar.bind("<ButtonPress-1>", self.start_window_drag)
        title_bar.bind("<ButtonRelease-1>", self.stop_window_drag)
        title_bar.bind("<B1-Motion>", self.on_window_drag)
        
        # Заголовок редактора
        app_title = ctk.CTkLabel(title_bar, text="vpycode", 
                               text_color=KanagawaTheme.FOREGROUND,
                               font=("Arial", 10))
        app_title.pack(side="left", padx=10)
        
        # Кнопки управления окном (закрыть, свернуть, развернуть)
        close_btn = ctk.CTkButton(title_bar, text="✕", width=30, height=25, 
                                fg_color="transparent", hover_color="#E82424",
                                text_color=KanagawaTheme.FOREGROUND, command=self.quit)
        close_btn.pack(side="right", padx=0)
        
        max_btn = ctk.CTkButton(title_bar, text="□", width=30, height=25, 
                              fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                              text_color=KanagawaTheme.FOREGROUND, command=self.toggle_maximize)
        max_btn.pack(side="right", padx=0)
        
        min_btn = ctk.CTkButton(title_bar, text="_", width=30, height=25, 
                              fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                              text_color=KanagawaTheme.FOREGROUND, command=self.minimize)
        min_btn.pack(side="right", padx=0)
        
        # Перемещаем меню редактора сразу под заголовок
        menu_bar = ctk.CTkFrame(self, fg_color=KanagawaTheme.DARKER_BG, height=30)
        menu_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        menu_bar.pack_propagate(False)
        
        # Меню файл с выпадающим списком
        file_menu_btn = ctk.CTkButton(menu_bar, text="Файл", width=60, height=25, 
                                    fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                    text_color=KanagawaTheme.FOREGROUND, command=self.show_file_menu)
        file_menu_btn.pack(side="left", padx=5)
        
        # Меню правка
        edit_menu_btn = ctk.CTkButton(menu_bar, text="Правка", width=60, height=25, 
                                    fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                    text_color=KanagawaTheme.FOREGROUND, command=self.show_edit_menu)
        edit_menu_btn.pack(side="left", padx=5)
        
        # Меню вид
        view_menu_btn = ctk.CTkButton(menu_bar, text="Вид", width=60, height=25, 
                                    fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                    text_color=KanagawaTheme.FOREGROUND, command=self.show_view_menu)
        view_menu_btn.pack(side="left", padx=5)
        
        # Меню запуск
        run_menu_btn = ctk.CTkButton(menu_bar, text="Запуск", width=60, height=25, 
                                   fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                   text_color=KanagawaTheme.FOREGROUND, command=self.show_run_menu)
        run_menu_btn.pack(side="left", padx=5)
        
        # Меню настройки
        settings_menu_btn = ctk.CTkButton(menu_bar, text="Настройки", width=80, height=25, 
                                        fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                        text_color=KanagawaTheme.FOREGROUND, command=self.show_settings_menu)
        settings_menu_btn.pack(side="left", padx=5)
        
        # Кнопки для быстрых действий
        run_btn = ctk.CTkButton(menu_bar, text="▶ Запустить", width=100, height=25, 
                              fg_color=KanagawaTheme.BUTTON_BG, hover_color=KanagawaTheme.BUTTON_HOVER,
                              text_color=KanagawaTheme.FOREGROUND, command=self.run_current_code)
        run_btn.pack(side="right", padx=5)
        
        save_btn = ctk.CTkButton(menu_bar, text="💾 Сохранить", width=100, height=25, 
                               fg_color=KanagawaTheme.BUTTON_BG, hover_color=KanagawaTheme.BUTTON_HOVER,
                               text_color=KanagawaTheme.FOREGROUND, command=self.save_file)
        save_btn.pack(side="right", padx=5)
        
        # Основной фрейм содержимого
        content_frame = ctk.CTkFrame(self, fg_color=KanagawaTheme.BACKGROUND)
        content_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        content_frame.grid_columnconfigure(2, weight=3)  # Колонка с редактором должна расширяться больше
        content_frame.grid_columnconfigure(3, weight=1)  # Колонка для чата с ИИ
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Боковая панель в стиле VS Code
        sidebar_frame = ctk.CTkFrame(content_frame, fg_color=KanagawaTheme.DARKER_BG, width=50)
        sidebar_frame.grid(row=0, column=0, sticky="ns", padx=0, pady=0)
        
        # Иконки для боковой панели (эмулируем с помощью текста)
        explorer_icon = ctk.CTkButton(sidebar_frame, text="📁", width=40, height=40,
                                    fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                    text_color=KanagawaTheme.FOREGROUND, command=self.toggle_explorer)
        explorer_icon.pack(side="top", pady=5)
        
        search_icon = ctk.CTkButton(sidebar_frame, text="🔍", width=40, height=40,
                                  fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                  text_color=KanagawaTheme.FOREGROUND)
        search_icon.pack(side="top", pady=5)
        
        terminal_icon = ctk.CTkButton(sidebar_frame, text="💻", width=40, height=40,
                                    fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                    text_color=KanagawaTheme.FOREGROUND, command=self.toggle_console)
        terminal_icon.pack(side="top", pady=5)
        
        ai_chat_icon = ctk.CTkButton(sidebar_frame, text="🤖", width=40, height=40,
                                   fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                   text_color=KanagawaTheme.FOREGROUND, command=self.toggle_ai_chat)
        ai_chat_icon.pack(side="top", pady=5)
        
        extensions_icon = ctk.CTkButton(sidebar_frame, text="🧩", width=40, height=40,
                                      fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                      text_color=KanagawaTheme.FOREGROUND, command=self.show_plugins_dialog)
        extensions_icon.pack(side="top", pady=5)
        
        # Иконка для настроек в боковой панели
        settings_icon = ctk.CTkButton(sidebar_frame, text="⚙️", width=40, height=40,
                                     fg_color="transparent", hover_color=KanagawaTheme.SELECTION,
                                     text_color=KanagawaTheme.FOREGROUND, command=self.show_settings_dialog)
        settings_icon.pack(side="bottom", pady=5)
        
        # Левая панель (проводник проекта)
        self.project_frame = ctk.CTkFrame(content_frame, fg_color=KanagawaTheme.DARKER_BG, width=250)
        self.project_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.project_frame.grid_propagate(False)  # Фиксированный размер
        
        # Заголовок проводника проекта в стиле VS Code
        explorer_header = ctk.CTkFrame(self.project_frame, fg_color="transparent", height=30)
        explorer_header.pack(fill="x", pady=(10, 5))
        
        explorer_label = ctk.CTkLabel(explorer_header, text="ПРОВОДНИК", text_color=KanagawaTheme.FOREGROUND,
                                    font=("Arial", 11, "bold"))
        explorer_label.pack(side="left", padx=10)
        
        # Секция ОТКРЫТЫЕ РЕДАКТОРЫ
        open_editors_frame = ctk.CTkFrame(self.project_frame, fg_color="transparent")
        open_editors_frame.pack(fill="x", pady=(10, 0))
        
        open_editors_header = ctk.CTkFrame(open_editors_frame, fg_color="transparent", height=25)
        open_editors_header.pack(fill="x")
        
        open_editors_label = ctk.CTkLabel(open_editors_header, text="ОТКРЫТЫЕ РЕДАКТОРЫ", 
                                       text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10))
        open_editors_label.pack(side="left", padx=10)
        
        # Дерево файлов проекта
        self.project_tree = tk.Listbox(self.project_frame, bg=KanagawaTheme.DARKER_BG, 
                                    fg=KanagawaTheme.FOREGROUND, bd=0, highlightthickness=0,
                                    selectbackground=KanagawaTheme.SELECTION,
                                    font=("Consolas", 10))
        self.project_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.project_tree.bind("<Double-Button-1>", self.open_file_from_tree)
        
        # Главная панель для редактора и консоли
        main_panel = ctk.CTkFrame(content_frame, fg_color=KanagawaTheme.BACKGROUND)
        main_panel.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)
        main_panel.grid_rowconfigure(0, weight=3)  # Редактор занимает 3/4
        main_panel.grid_rowconfigure(1, weight=1)  # Консоль занимает 1/4
        main_panel.grid_columnconfigure(0, weight=1)
        
        # Фрейм для редактора с номерами строк
        editor_frame = ctk.CTkFrame(main_panel, fg_color=KanagawaTheme.BACKGROUND)
        editor_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(1, weight=1)
        
        # Номера строк
        self.line_numbers = tk.Text(editor_frame, width=4, padx=5, pady=5, bd=0,
                                 bg=KanagawaTheme.BACKGROUND, fg=KanagawaTheme.COMMENT,
                                 insertbackground=KanagawaTheme.CURSOR,
                                 selectbackground=KanagawaTheme.SELECTION,
                                 font=self.settings.get_font(), takefocus=0)
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.line_numbers.insert("1.0", "1")
        self.line_numbers.configure(state="disabled")
        
        # Текстовый редактор
        self.code_editor = tk.Text(editor_frame, wrap="none", bd=0, padx=5, pady=5,
                                bg=KanagawaTheme.BACKGROUND, fg=KanagawaTheme.FOREGROUND,
                                insertbackground=KanagawaTheme.CURSOR,
                                selectbackground=KanagawaTheme.SELECTION,
                                font=self.settings.get_font())
        self.code_editor.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Настройка визуализации пробелов
        self.code_editor.tag_configure("whitespace", foreground="#404040")
        
        # Настройка табуляции
        self.code_editor.configure(tabs=self.settings.tab_size * 7)  # Примерный размер в пикселях
        
        # Привязываем события редактора
        self.code_editor.bind("<KeyRelease>", self.on_text_change)
        self.code_editor.bind("<Button-1>", self.highlight_current_line)
        self.code_editor.bind("<ButtonRelease-1>", self.highlight_current_line)
        self.code_editor.bind("<Tab>", self.handle_tab)
        self.code_editor.bind("<Shift-Tab>", self.handle_shift_tab)
        
        # Добавляем обработку нажатия Enter для автоматической табуляции
        self.code_editor.bind("<Return>", self.handle_return)
        
        # Горячие клавиши
        self.bind_hotkeys()
        
        # Полосы прокрутки для редактора
        y_scrollbar = ctk.CTkScrollbar(editor_frame, command=self.on_scroll_y,
                                     button_color=KanagawaTheme.SCROLLBAR,
                                     button_hover_color=KanagawaTheme.FOREGROUND)
        y_scrollbar.grid(row=0, column=2, sticky="ns")
        self.code_editor.configure(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ctk.CTkScrollbar(editor_frame, command=self.code_editor.xview, 
                                     orientation="horizontal",
                                     button_color=KanagawaTheme.SCROLLBAR,
                                     button_hover_color=KanagawaTheme.FOREGROUND)
        x_scrollbar.grid(row=1, column=1, sticky="ew")
        self.code_editor.configure(xscrollcommand=x_scrollbar.set)
        
        # Консоль (изначально скрыта) - теперь с функциональностью командной строки
        self.console_frame = ctk.CTkFrame(main_panel, fg_color=KanagawaTheme.CONSOLE_BG)
        self.console_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)
        
        # Заголовок консоли
        console_header = ctk.CTkFrame(self.console_frame, fg_color=KanagawaTheme.DARKER_BG, height=25)
        console_header.pack(fill="x")
        
        console_label = ctk.CTkLabel(console_header, text="ТЕРМИНАЛ", 
                                   text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        console_label.pack(side="left", padx=10)
        
        # Кнопки управления консолью
        clear_btn = ctk.CTkButton(console_header, text="🗑️", width=25, height=20, 
                                fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                text_color=KanagawaTheme.FOREGROUND, command=self.clear_console)
        clear_btn.pack(side="right", padx=5)
        
        # Контейнер для консоли
        console_container = ctk.CTkFrame(self.console_frame, fg_color=KanagawaTheme.CONSOLE_BG)
        console_container.pack(fill="both", expand=True)
        console_container.grid_rowconfigure(0, weight=1)
        console_container.grid_columnconfigure(0, weight=1)
        
        # Текстовое поле консоли с возможностью ввода
        self.console_output = scrolledtext.ScrolledText(
            console_container, 
            wrap="word", 
            bd=0,
            bg=KanagawaTheme.CONSOLE_BG, 
            fg=KanagawaTheme.CONSOLE_FG,
            insertbackground=KanagawaTheme.CURSOR,
            font=(self.settings.font_family, self.settings.font_size), 
            padx=5, 
            pady=5
        )
        self.console_output.pack(fill="both", expand=True)
        
        # Устанавливаем теги для разных типов вывода
        self.console_output.tag_configure("error", foreground=KanagawaTheme.CONSOLE_ERROR)
        self.console_output.tag_configure("success", foreground=KanagawaTheme.CONSOLE_SUCCESS)
        self.console_output.tag_configure("info", foreground=KanagawaTheme.CONSOLE_INFO)
        self.console_output.tag_configure("prompt", foreground=KanagawaTheme.FUNCTION)
        
        # Добавляем привязки для обработки ввода в консоли
        self.console_output.bind("<Return>", self.handle_console_input)
        
        # По умолчанию консоль скрыта
        self.console_frame.grid_remove()
        
        # Панель чата с нейросетью (изначально скрыта)
        self.ai_chat_frame = ctk.CTkFrame(content_frame, fg_color=KanagawaTheme.AI_BG, width=300)
        self.ai_chat_frame.grid(row=0, column=3, sticky="nsew", padx=0, pady=0)
        self.ai_chat_frame.grid_rowconfigure(0, weight=1)
        self.ai_chat_frame.grid_columnconfigure(0, weight=1)
        
        # Заголовок чата
        ai_header = ctk.CTkFrame(self.ai_chat_frame, fg_color=KanagawaTheme.DARKER_BG, height=30)
        ai_header.pack(fill="x")
        
        ai_label = ctk.CTkLabel(ai_header, text="ИИ АССИСТЕНТ", 
                               text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        ai_label.pack(side="left", padx=10)
        
        # Контейнер для чата
        chat_container = ctk.CTkFrame(self.ai_chat_frame, fg_color=KanagawaTheme.AI_BG)
        chat_container.pack(fill="both", expand=True, padx=5, pady=5)
        chat_container.pack_propagate(False)
        
        # История сообщений чата
        self.chat_history = tk.Text(
            chat_container, 
            wrap="word", 
            bd=0,
            bg=KanagawaTheme.AI_BG, 
            fg=KanagawaTheme.AI_USER_MSG,
            insertbackground=KanagawaTheme.CURSOR,
            font=(self.settings.font_family, self.settings.font_size), 
            padx=5, 
            pady=5
        )
        self.chat_history.pack(fill="both", expand=True, side="top")
        self.chat_history.configure(state="disabled")
        
        # Теги для разных типов сообщений
        self.chat_history.tag_configure("user", foreground=KanagawaTheme.AI_USER_MSG)
        self.chat_history.tag_configure("bot", foreground=KanagawaTheme.AI_BOT_MSG)
        self.chat_history.tag_configure("system", foreground=KanagawaTheme.AI_ACCENT)
        
        # Панель ввода сообщения
        input_frame = ctk.CTkFrame(chat_container, fg_color=KanagawaTheme.DARKER_BG, height=60)
        input_frame.pack(fill="x", side="bottom", pady=(5, 0))
        
        self.chat_input = ctk.CTkTextbox(
            input_frame, 
            height=40,
            fg_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND,
            border_width=1,
            border_color=KanagawaTheme.SELECTION
        )
        self.chat_input.pack(fill="x", side="left", expand=True, padx=5, pady=10)
        
        send_btn = ctk.CTkButton(
            input_frame, 
            text="▶", 
            width=40, 
            height=30,
            fg_color=KanagawaTheme.AI_ACCENT,
            hover_color=KanagawaTheme.BUTTON_HOVER,
            text_color=KanagawaTheme.FOREGROUND,
            command=self.send_ai_message
        )
        send_btn.pack(side="right", padx=5, pady=10)
        
        # Кнопка остановки генерации (изначально скрыта)
        self.stop_generation_btn = ctk.CTkButton(
            input_frame, 
            text="■", 
            width=40, 
            height=30,
            fg_color=KanagawaTheme.CONSOLE_ERROR,
            hover_color=KanagawaTheme.BUTTON_HOVER,
            text_color=KanagawaTheme.FOREGROUND,
            command=self.stop_ai_generation
        )
        # Кнопка не отображается по умолчанию (pack_forget)
        
        # По умолчанию чат скрыт
        self.ai_chat_frame.grid_remove()
        
        # Нижняя строка состояния (как в VS Code)
        status_bar = ctk.CTkFrame(self, fg_color=KanagawaTheme.DARKER_BG, height=25)
        status_bar.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        
        self.status_text = ctk.CTkLabel(status_bar, text="Готов", text_color=KanagawaTheme.FOREGROUND)
        self.status_text.pack(side="left", padx=10)
        
        self.line_col_indicator = ctk.CTkLabel(status_bar, text="Строка: 1, Символ: 1", 
                                            text_color=KanagawaTheme.FOREGROUND)
        self.line_col_indicator.pack(side="right", padx=10)
        
        # Подсвечиваем текущую строку при запуске
        self.highlight_current_line()
        
        # Отображаем проводник по умолчанию
        self.project_frame.grid()
    
    def start_shell(self):
        """Запускаем командную оболочку в фоновом режиме"""
        if os.name == 'nt':  # Windows
            cmd = 'cmd.exe'
        else:  # Linux/Mac
            cmd = '/bin/bash'
            
        try:
            # Запускаем процесс оболочки с перенаправлением stdin/stdout
            self.shell_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Запускаем поток для чтения вывода оболочки
            threading.Thread(target=self._read_shell_output, daemon=True).start()
            
            # Запускаем поток для отправки команд оболочке
            threading.Thread(target=self._send_shell_commands, daemon=True).start()
            
            # Добавляем приветственное сообщение в консоль
            self.write_to_console("Терминал готов к работе. Введите команду и нажмите Enter.\n", "info")
            self.write_to_console("$ ", "prompt")
        except Exception as e:
            print(f"Ошибка запуска командной оболочки: {e}")
    
    def _read_shell_output(self):
        """Читает вывод из оболочки и отправляет его в консоль"""
        if not self.shell_process:
            return
            
        while self.shell_process.poll() is None:
            try:
                line = self.shell_process.stdout.readline()
                if line:
                    self.output_queue.put(line)
                    # Обновляем консоль в основном потоке
                    self.after(10, self._update_console_from_queue)
            except:
                break
    
    def _send_shell_commands(self):
        """Отправляет команды в оболочку из очереди"""
        if not self.shell_process:
            return
            
        while self.shell_process.poll() is None:
            try:
                if not self.command_queue.empty():
                    cmd = self.command_queue.get()
                    self.shell_process.stdin.write(f"{cmd}\n")
                    self.shell_process.stdin.flush()
            except:
                break
            # Небольшая задержка, чтобы не нагружать CPU
            time.sleep(0.1)
    
    def _update_console_from_queue(self):
        """Обновляет консоль выводом из очереди"""
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()
                self.write_to_console(line)
                
            # Добавляем новый промпт после вывода
            if not self.output_queue.empty():
                # Если в очереди еще есть данные, продолжаем обработку
                self.after(10, self._update_console_from_queue)
            else:
                # Если очередь пуста, добавляем промпт
                self.write_to_console("$ ", "prompt")
        except:
            pass
    
    def handle_console_input(self, event):
        """Обрабатывает ввод в консоли"""
        # Получаем последнюю строку (текущий ввод)
        input_text = self.console_output.get("insert linestart", "insert")
        
        # Проверяем, что ввод начинается с промпта ($)
        if input_text.startswith("$ "):
            # Извлекаем команду (убираем промпт)
            command = input_text[2:].strip()
            
            # Добавляем новую строку после ввода
            self.console_output.insert("insert", "\n")
            
            # Отправляем команду в оболочку
            self.command_queue.put(command)
            
            # Предотвращаем стандартное поведение клавиши Enter
            return "break"
    
    def toggle_ai_chat(self):
        """Переключение видимости чата с нейросетью"""
        if self.ai_chat_frame.winfo_viewable():
            self.ai_chat_frame.grid_remove()
        else:
            # Сбрасываем историю чата при открытии панели
            self.clear_chat_history()
            # Показываем панель
            self.ai_chat_frame.grid()
            
            # Добавляем системное сообщение с инструкцией по использованию
            self.chat_history.configure(state="normal")
            message = "AI assistant ready to help!\n\n"
            
            # Добавляем информацию о возможности чтения файлов
            if FILE_READER_AVAILABLE:
                message += "Ассистент может читать файлы, когда вы пришлете запрос 'прочитай файл X'.\n" + \
                           "Также ассистент может самостоятельно запрашивать чтение файлов используя тег <read-file>путь_к_файлу</read-file>.\n\n"
            
            self.chat_history.insert(tk.END, message, "system")
            self.chat_history.configure(state="disabled")
    
    def send_ai_message(self):
        """Отправляет сообщение в чат с нейросетью и получает ответ"""
        # Получаем текст сообщения
        message = self.chat_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Очищаем поле ввода
        self.chat_input.delete("1.0", tk.END)
        
        # Обработка специальных команд
        if message.lower() in ["тест структуры", "проверка структуры", "структура проекта"]:
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "Вы: ", "system")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user")
            
            # Получаем структуру проекта
            project_dir = self.current_project if self.current_project else os.getcwd()
            structure = self._get_project_structure(project_dir)
            
            # Добавляем ответ с информацией
            self.chat_history.insert(tk.END, "Ассистент: ", "system")
            info = f"Проверка структуры проекта:\n\n"
            info += f"Текущая директория: {project_dir}\n"
            info += f"Структура получена: {'Да' if structure else 'Нет'}\n"
            info += f"Размер структуры: {len(structure)} символов\n\n"
            info += f"Структура проекта:\n```\n{structure}\n```\n\n"
            info += "Эта структура будет отправлена с каждым запросом к ИИ."
            
            self.chat_history.insert(tk.END, info, "bot")
            self.chat_history.insert(tk.END, "\n\n")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
            return
            
        # Обработка запросов на чтение файлов
        read_file_match = re.search(r'прочитай файл\s+(.+?)(?:\s|$)', message.lower())
        if read_file_match and FILE_READER_AVAILABLE:
            file_path = read_file_match.group(1).strip()
            
            # Отображаем запрос пользователя
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "Вы: ", "system")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user")
            
            # Добавляем ответ с информацией о чтении файла
            self.chat_history.insert(tk.END, "Ассистент: ", "system")
            self.chat_history.insert(tk.END, f"Читаю файл: {file_path}\n", "system")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
            
            # Читаем файл и отправляем его содержимое
            self._handle_file_read_request(file_path)
            return
        
        # Добавляем сообщение пользователя в историю
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, "Вы: ", "system")
        self.chat_history.insert(tk.END, f"{message}\n\n", "user")
        
        # Добавляем индикатор загрузки
        self.chat_history.insert(tk.END, "Ассистент: ", "system")
        loading_indicator = "Думаю..."
        loading_tag = "loading"
        self.chat_history.insert(tk.END, loading_indicator, loading_tag)
        self.chat_history.tag_configure(loading_tag, foreground=KanagawaTheme.AI_BOT_MSG)
        self.chat_history.see(tk.END)
        self.chat_history.configure(state="disabled")
        
        # Показываем кнопку остановки генерации
        self.stop_generation_btn.pack(side="right", padx=5, pady=10)
        
        # Сохраняем сообщение пользователя в истории
        self.chat_messages.append({"role": "user", "content": message})
        
        # Проверяем доступность интернета быстрым методом
        try:
            requests.get("https://8.8.8.8", timeout=1)
            has_internet = True
        except:
            has_internet = False
        
        # Если интернет доступен, используем онлайн API, иначе используем локальные ответы
        if has_internet:
            # Устанавливаем флаг активной генерации
            self.is_generating = True
            
            # Запускаем генерацию ответа в отдельном потоке
            self.generation_thread = threading.Thread(target=self._generate_ai_response)
            self.generation_thread.daemon = True
            self.generation_thread.start()
        else:
            # Простые базовые ответы для офлайн режима
            self._generate_offline_response(message)
    
    def stop_ai_generation(self):
        """Останавливает процесс генерации ответа нейросети"""
        if hasattr(self, 'is_generating') and self.is_generating:
            self.is_generating = False
            
            # Обновляем интерфейс
            self._update_ai_response("Генерация ответа прервана пользователем.")
            
            # Скрываем кнопку остановки
            self.stop_generation_btn.pack_forget()
    
    def _generate_ai_response(self):
        """Генерирует ответ от нейросети"""
        api_key = self.settings.ai_api_key
        
        if not api_key:
            self._update_ai_response(
                "Ошибка: API ключ OpenRouter не настроен. Пожалуйста, добавьте ключ в настройках (⚙️ → ИИ-ассистент)."
            )
            return
        
        # Подготавливаем сообщения для API
        messages = []
        
        # Если это первое сообщение в сессии, добавляем системную инструкцию
        if self.is_first_message and self.settings.ai_initial_prompt:
            # Добавляем инструкцию об ограничениях команд
            system_prompt = self.settings.ai_initial_prompt
            if "Поддерживаемые команды:" not in system_prompt:
                system_prompt += "\n\nВАЖНО: Поддерживаемые команды: read_file, replace_file, modify_file и code_insert. ТОЧНЫЙ ФОРМАТ КОМАНД:\n1. Для read_file: {\"type\": \"read_file\", \"path\": \"путь/к/файлу\"}\n2. Для replace_file/modify_file: {\"type\": \"replace_file\", \"path\": \"путь/к/файлу\", \"content\": \"полное содержимое файла\"}\n3. Для code_insert: {\"type\": \"code_insert\", \"insert_type\": \"line\", \"line\": 42, \"code\": \"код для вставки\"}\nНЕ ИСПОЛЬЗУЙТЕ поля actions, remove_line или другие неподдерживаемые структуры. Для удаления строк используйте replace_file с новым содержимым без этих строк."
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            self.is_first_message = False
        
        # Получаем структуру файлов проекта и добавляем ее в сообщения
        try:
            # Определяем директорию проекта
            project_dir = self.current_project if self.current_project else os.getcwd()
            structure = self._get_project_structure(project_dir)
            
            if structure:
                structure_message = {
                    "role": "system",
                    "content": f"Текущая структура файловой системы проекта:\n{structure}"
                }
                messages.append(structure_message)
                print(f"Структура проекта добавлена в запрос: {len(structure)} символов")
            else:
                print("Предупреждение: Не удалось получить структуру проекта")
        except Exception as e:
            print(f"Ошибка при сборе структуры проекта: {str(e)}")
        
        # Добавляем историю сообщений (максимум последние 10 для экономии токенов)
        messages.extend(self.chat_messages[-10:])
        
        try:
            # Проверяем соединение с интернетом перед отправкой запроса
            try:
                # Пробуем подключиться к надежному DNS-серверу Google
                test_connection = requests.get("https://8.8.8.8", timeout=2)
                # Если это удалось, но домен не разрешается, это проблема DNS
                if test_connection.status_code != 200:
                    raise Exception("Соединение с интернетом нестабильно")
            except:
                # Если не удалось подключиться к 8.8.8.8, значит нет доступа к интернету
                raise Exception("Нет подключения к интернету. Проверьте ваше соединение.")
            
            # Отправляем запрос к API
            response = self._call_deepseek_api(messages)
            
            # Получаем ответ из результата API
            if response and "choices" in response and response["choices"] and self.is_generating:
                ai_message = response["choices"][0]["message"]["content"]
                
                # Сохраняем ответ в истории
                self.chat_messages.append({"role": "assistant", "content": ai_message})
                
                # Показываем консоль, если она скрыта
                if not self.console_frame.winfo_viewable():
                    self.toggle_console()
                
                # Обновляем интерфейс
                self._update_ai_response(ai_message)
            elif not self.is_generating:
                # Если генерация была остановлена, ничего не делаем
                pass
            else:
                self._update_ai_response("Ошибка: Не удалось получить ответ от API.")
        except requests.exceptions.RequestException as e:
            if "NameResolutionError" in str(e):
                self._update_ai_response(
                    "Ошибка: Не удается разрешить домен api.openrouter.ai. "
                    "Возможные причины:\n"
                    "1. Проблема с DNS-сервером\n"
                    "2. Нет доступа к интернету\n"
                    "3. Сайт OpenRouter.ai недоступен\n\n"
                    "Проверьте подключение к интернету или попробуйте позже."
                )
            else:
                self._update_ai_response(f"Ошибка сети: {str(e)}")
        except Exception as e:
            self._update_ai_response(f"Ошибка: {str(e)}")
        finally:
            # В любом случае сбрасываем флаг генерации и скрываем кнопку остановки
            self.is_generating = False
            self.after(0, lambda: self.stop_generation_btn.pack_forget())
    
    def _get_project_structure(self, directory):
        """Получает простую структуру проекта без глубокой рекурсии"""
        structure = ""
        
        try:
            files = []
            dirs = []
            
            # Получаем список файлов и директорий
            for item in os.listdir(directory):
                if item.startswith('.'):
                    continue
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            # Сортируем списки
            dirs.sort()
            files.sort()
            
            # Формируем структуру
            for d in dirs:
                structure += f"📁 {d}/\n"
                # Показываем содержимое директорий (только первый уровень)
                try:
                    subdir = os.path.join(directory, d)
                    subitems = sorted(os.listdir(subdir))[:10]  # Первые 10 элементов
                    for subitem in subitems:
                        if subitem.startswith('.'):
                            continue
                        if os.path.isdir(os.path.join(subdir, subitem)):
                            structure += f"  📁 {d}/{subitem}/\n"
                        else:
                            structure += f"  📄 {d}/{subitem}\n"
                    
                    # Если есть еще файлы, показываем счетчик
                    total_items = len(os.listdir(subdir))
                    if total_items > 10:
                        structure += f"  ... и еще {total_items-10} элементов\n"
                except Exception as e:
                    structure += f"  ⚠️ Ошибка чтения директории: {str(e)}\n"
            
            # Выводим файлы в корневой директории
            for f in files:
                structure += f"📄 {f}\n"
                
            return structure
        except Exception as e:
            print(f"Ошибка при получении структуры проекта: {str(e)}")
            return f"Ошибка: {str(e)}"
    
    def _call_deepseek_api(self, messages):
        """Вызывает DeepSeek API и возвращает результат"""
        api_key = self.settings.ai_api_key
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Добавляем системное сообщение с ограничениями, если его нет
        has_command_limitation = False
        for msg in messages:
            if msg["role"] == "system" and "Поддерживаемые команды:" in msg["content"]:
                has_command_limitation = True
                break
        
        if not has_command_limitation:
            messages.insert(0, {
                "role": "system",
                "content": "ВАЖНО: Поддерживаемые команды: read_file, replace_file, modify_file и code_insert. ТОЧНЫЙ ФОРМАТ КОМАНД:\n1. Для read_file: {\"type\": \"read_file\", \"path\": \"путь/к/файлу\"}\n2. Для replace_file/modify_file: {\"type\": \"replace_file\", \"path\": \"путь/к/файлу\", \"content\": \"полное содержимое файла\"}\n3. Для code_insert: {\"type\": \"code_insert\", \"insert_type\": \"line\", \"line\": 42, \"code\": \"код для вставки\"}\nНЕ ИСПОЛЬЗУЙТЕ поля actions, remove_line или другие неподдерживаемые структуры. Для удаления строк используйте replace_file с новым содержимым без этих строк."
            })
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek/deepseek-r1",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"API Error ({response.status_code}): {response.text}"
            raise Exception(error_msg)
    
    def _update_ai_response(self, message):
        """Обновляет интерфейс чата с ответом от ИИ"""
        # Обновляем в основном потоке
        def update():
            self.chat_history.configure(state="normal")
            # Удаляем индикатор загрузки
            self.chat_history.delete("end-1l linestart+10c", "end-1l lineend")
            
            # Дублируем ответ нейросети в консоль
            self.write_to_console("--- Ответ ИИ-ассистента ---\n", "info")
            self.write_to_console(message + "\n")
            
            # Проверяем, есть ли запрос на чтение файла
            file_read_match = re.search(READ_FILE_PATTERN, message, re.DOTALL)
                
            if file_read_match and FILE_READER_AVAILABLE:
                # Извлекаем путь к файлу
                file_path = file_read_match.group(1).strip()
                self.chat_history.insert(tk.END, f"Читаю файл: {file_path}\n", "system")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                
                # Читаем файл и отправляем новый запрос с его содержимым
                self._handle_file_read_request(file_path)
                return
                
            # Сначала обрабатываем специальные теги кода для вставки
            processed_message = message
            
            # Обработка блоков кода с указанием диапазона строк
            lines_blocks = re.findall(CODE_BLOCK_LINES_PATTERN, processed_message, re.DOTALL)
            if lines_blocks:
                for match in lines_blocks:
                    start_line = match[0]
                    end_line = match[1]
                    code = match[2]
                    tag_content = f'###CODE_INSERT:{start_line}-{end_line}\n{code}\n###END_INSERT'
                    replacement = f"\n```python\n{code}\n```\n"
                    processed_message = processed_message.replace(tag_content, replacement)
                    
                    # Создаем блок кода для вставки
                    code_block = self._create_code_block(tag_content)
                    
                    # Заменяем в сообщении текст на виджет
                    self.chat_history.insert(tk.END, processed_message.split(replacement)[0])
                    self.chat_history.window_create(tk.END, window=code_block)
                    processed_message = processed_message.split(replacement, 1)[1] if len(processed_message.split(replacement, 1)) > 1 else ""
            
            # Обработка блоков кода с указанием конкретной строки
            line_blocks = re.findall(CODE_BLOCK_LINE_PATTERN, processed_message, re.DOTALL)
            if line_blocks:
                for match in line_blocks:
                    line_num = match[0]
                    code = match[1]
                    tag_content = f'###CODE_INSERT:{line_num}\n{code}\n###END_INSERT'
                    replacement = f"\n```python\n{code}\n```\n"
                    processed_message = processed_message.replace(tag_content, replacement)
                    
                    # Создаем блок кода для вставки
                    code_block = self._create_code_block(tag_content)
                    
                    # Заменяем в сообщении текст на виджет
                    self.chat_history.insert(tk.END, processed_message.split(replacement)[0])
                    self.chat_history.window_create(tk.END, window=code_block)
                    processed_message = processed_message.split(replacement, 1)[1] if len(processed_message.split(replacement, 1)) > 1 else ""
            
            # Обработка стандартных блоков кода
            standard_blocks = re.findall(CODE_BLOCK_PATTERN, processed_message, re.DOTALL)
            if standard_blocks:
                for match in standard_blocks:
                    code = match
                    tag_content = f'###CODE_INSERT\n{code}\n###END_INSERT'
                    replacement = f"\n```python\n{code}\n```\n"
                    processed_message = processed_message.replace(tag_content, replacement)
                    
                    # Создаем блок кода для вставки
                    code_block = self._create_code_block(tag_content)
                    
                    # Заменяем в сообщении текст на виджет
                    self.chat_history.insert(tk.END, processed_message.split(replacement)[0])
                    self.chat_history.window_create(tk.END, window=code_block)
                    processed_message = processed_message.split(replacement, 1)[1] if len(processed_message.split(replacement, 1)) > 1 else ""
            
            # Вставляем оставшийся текст
            if processed_message:
                # Проверяем, есть ли в оставшемся сообщении блоки кода с тройными кавычками
                if "```" in processed_message:
                    # Разбиваем сообщение на части по маркеру кода
                    parts = processed_message.split("```")
                    
                    # Первая часть - обычный текст (если есть)
                    if parts[0]:
                        self.chat_history.insert(tk.END, parts[0], "bot")
                    
                    # Обрабатываем части попарно (код и текст после него)
                    for i in range(1, len(parts), 2):
                        if i < len(parts):
                            code_lang = parts[i].split('\n', 1)[0].strip() if '\n' in parts[i] else ""
                            code_content = parts[i].split('\n', 1)[1] if '\n' in parts[i] and code_lang else parts[i]
                            
                            # Проверка на JSON команды
                            is_json_command = False
                            if code_lang.lower() == "json":
                                try:
                                    # Пытаемся распарсить JSON
                                    json_data = json.loads(code_content)
                                    if isinstance(json_data, dict) and "type" in json_data:
                                        cmd_type = json_data.get("type")
                                        # Список поддерживаемых команд
                                        supported_commands = ["read_file", "replace_file", "modify_file", "code_insert"]
                                        
                                        # Обрабатываем команды чтения файла
                                        if cmd_type == "read_file" and "path" in json_data and FILE_READER_AVAILABLE:
                                            file_path = json_data.get("path")
                                            self.chat_history.insert(tk.END, f"\nОбнаружена команда чтения файла: {file_path}\n", "system")
                                            # Вставляем содержимое файла вместо команды
                                            self._handle_file_read_request(file_path)
                                            is_json_command = True
                                        # Обработка команды replace_file
                                        elif cmd_type == "replace_file" and "path" in json_data and "content" in json_data:
                                            file_path = json_data.get("path")
                                            content = json_data.get("content")
                                            self.chat_history.insert(tk.END, f"\nОбнаружена команда замены файла: {file_path}\n", "system")
                                            # Запускаем замену с предварительным просмотром
                                            threading.Thread(target=self._handle_replace_file_request, 
                                                        args=(file_path, content)).start()
                                            is_json_command = True
                                        # Обработка команды modify_file (алиас для replace_file)
                                        elif cmd_type == "modify_file" and "path" in json_data and "content" in json_data:
                                            file_path = json_data.get("path")
                                            content = json_data.get("content")
                                            self.chat_history.insert(tk.END, f"\nОбнаружена команда модификации файла: {file_path}\n", "system")
                                            # Запускаем замену с предварительным просмотром
                                            threading.Thread(target=self._handle_replace_file_request, 
                                                        args=(file_path, content)).start()
                                            is_json_command = True
                                        # Обработка команды code_insert
                                        elif cmd_type == "code_insert" and "code" in json_data:
                                            insert_type = json_data.get("insert_type", "standard")
                                            line_num = json_data.get("line", None)
                                            code = json_data.get("code", "")
                                            self.chat_history.insert(tk.END, f"\nОбнаружена команда вставки кода (тип: {insert_type})\n", "system")
                                            # Создаем блок кода для вставки с соответствующими параметрами
                                            if insert_type == "line" and line_num:
                                                tag_content = f'###CODE_INSERT:{line_num}\n{code}\n###END_INSERT'
                                            else:
                                                tag_content = f'###CODE_INSERT\n{code}\n###END_INSERT'
                                            
                                            # Создаем блок кода и добавляем его в интерфейс
                                            code_block = self._create_code_block(tag_content)
                                            self.chat_history.window_create(tk.END, window=code_block)
                                            is_json_command = True
                                        # Обработка неподдерживаемых команд
                                        elif cmd_type not in supported_commands:
                                            self.chat_history.insert(tk.END, f"\n❌ Неподдерживаемая команда: {cmd_type}\n", "error")
                                            self.chat_history.insert(tk.END, f"Поддерживаются только команды: {', '.join(supported_commands)}\n", "info")
                                            is_json_command = True
                                except json.JSONDecodeError:
                                    # Если не удалось распарсить как JSON, обрабатываем как обычный код
                                    pass
                                except Exception as e:
                                    self.chat_history.insert(tk.END, f"\nОшибка при обработке JSON: {str(e)}\n", "error")
                                    is_json_command = True  # Отмечаем, что это была JSON команда с ошибкой
                            
                            # Если это не JSON команда, обрабатываем как обычный блок кода
                            if not is_json_command:
                                # Более гибкая проверка указания строки в разных форматах
                                line_matches = []
                                # Проверка русского формата "строка: 42" или "строка 42"
                                line_matches.append(re.search(r'строка[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                # Проверка английского формата "line: 42" или "line 42"
                                line_matches.append(re.search(r'line[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                # Проверка формата комментария "# строка 42" или "# line 42"
                                line_matches.append(re.search(r'#.*строка[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                line_matches.append(re.search(r'#.*line[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                # Проверка формата комментария "// строка 42" или "// line 42" для других языков
                                line_matches.append(re.search(r'//.*строка[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                line_matches.append(re.search(r'//.*line[:]?\s*(\d+)', code_content, re.IGNORECASE))
                                
                                # Используем первое найденное совпадение
                                line_match = None
                                for match in line_matches:
                                    if match:
                                        line_match = match
                                        break
                                
                                if line_match:
                                    line_num = int(line_match.group(1))
                                    # Создаем тег для создания блока кода с указанием строки для вставки
                                    tag_content = f'###CODE_INSERT:{line_num}\n{code_content}\n###END_INSERT'
                                else:
                                    # Создаем стандартный тег для создания блока кода с кнопкой вставки
                                    tag_content = f'###CODE_INSERT\n{code_content}\n###END_INSERT'
                                
                                # Создаем блок кода для вставки
                                code_block = self._create_code_block(tag_content)
                                
                                # Вставляем виджет кода с кнопкой
                                self.chat_history.window_create(tk.END, window=code_block)
                                self.chat_history.insert(tk.END, "\n\n")
                            else:
                                # Для JSON команд просто отображаем блок кода без кнопки вставки
                                self.chat_history.insert(tk.END, f"\n```{code_lang}\n{code_content}\n```\n\n")
                        
                        # Если есть текст после блока кода, добавляем его
                        if i+1 < len(parts):
                            self.chat_history.insert(tk.END, parts[i+1], "bot")
                else:
                    # Если нет блоков кода, просто вставляем текст
                    self.chat_history.insert(tk.END, processed_message, "bot")
            
            self.chat_history.insert(tk.END, "\n\n")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
            
            # Скрываем кнопку остановки генерации
            self.stop_generation_btn.pack_forget()
        
        # Запускаем обновление в главном потоке
        self.after(0, update)
    
    def _create_code_block(self, code):
        """Создает виджет для блока кода с кнопкой вставки"""
        # Проверка на специальные теги вставки кода
        line_match = re.search(CODE_BLOCK_LINE_PATTERN, code, re.DOTALL)
        lines_match = re.search(CODE_BLOCK_LINES_PATTERN, code, re.DOTALL)
        standard_match = re.search(CODE_BLOCK_PATTERN, code, re.DOTALL)
        
        # Параметры вставки кода
        insert_type = "standard"
        line_num = None
        start_line = None
        end_line = None
        code_to_insert = code
        language = "python"  # По умолчанию предполагаем Python
        
        # Извлекаем параметры в зависимости от типа тега
        if line_match:
            insert_type = "line"
            line_num = int(line_match.group(1))
            # Извлекаем только содержимое между тегами
            code_to_insert = line_match.group(2)
            # Убираем маркеры из отображаемого кода
            code = code_to_insert
            
            # Удаляем также любые упоминания строки из кода
            code = re.sub(r'строка[:]?\s*\d+', '', code, flags=re.IGNORECASE)
        elif lines_match:
            insert_type = "range"
            start_line = int(lines_match.group(1))
            end_line = int(lines_match.group(2))
            # Извлекаем только содержимое между тегами
            code_to_insert = lines_match.group(3)
            # Убираем маркеры из отображаемого кода
            code = code_to_insert
            
            # Удаляем также любые упоминания диапазона строк из кода
            code = re.sub(r'строки[:]?\s*\d+\s*-\s*\d+', '', code, flags=re.IGNORECASE)
        elif standard_match:
            insert_type = "standard"
            # Извлекаем только содержимое между тегами
            code_to_insert = standard_match.group(1)
            # Убираем маркеры из отображаемого кода
            code = code_to_insert
        
        # Удаляем все маркеры из кода
        code = re.sub(r'###CODE_INSERT.*', '', code)
        code = re.sub(r'###END_INSERT', '', code)
        
        # Определяем язык по первой строке или содержимому
        code_lines = code.split("\n")
        if code_lines and code_lines[0].strip().startswith("#"):
            # Возможно это Python
            language = "python"
        elif code_lines and (code_lines[0].strip().startswith("//") or 
                            code_lines[0].strip().startswith("/*") or
                            "{" in code):
            # Похоже на JavaScript, Java, C, C++, и т.д.
            language = "javascript"
        
        # Создаем фрейм с закругленными углами для блока кода
        code_frame = ctk.CTkFrame(
            self.chat_history, 
            fg_color=KanagawaTheme.DARKER_BG, 
            corner_radius=10,
            border_width=1,
            border_color=KanagawaTheme.SELECTION
        )
        
        # Создаем заголовок, который показывает куда будет вставлен код
        insert_location_text = "📥 Вставка в: текущую позицию курсора"
        if insert_type == "line" and line_num is not None:
            insert_location_text = f"📥 Вставка в: строку {line_num}"
        elif insert_type == "range" and start_line is not None and end_line is not None:
            insert_location_text = f"📥 Замена строк {start_line}-{end_line}"
        
        insert_location_label = ctk.CTkLabel(
            code_frame, 
            text=insert_location_text, 
            text_color=KanagawaTheme.AI_ACCENT,
            font=(self.settings.font_family, 10, "bold")
        )
        insert_location_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Добавляем метку с языком программирования, если он указан
        if language:
            lang_label = ctk.CTkLabel(
                code_frame, 
                text=f"{language}", 
                text_color=KanagawaTheme.COMMENT,
                font=(self.settings.font_family, 10)
            )
            lang_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Добавляем текстовое поле для кода
        code_text = ctk.CTkTextbox(
            code_frame, 
            width=400, 
            height=max(100, len(code_lines)*20),  # Высота зависит от количества строк
            fg_color=KanagawaTheme.BACKGROUND, 
            text_color=KanagawaTheme.FOREGROUND,
            font=(self.settings.font_family, self.settings.font_size)
        )
        code_text.pack(padx=10, pady=5, fill="both", expand=True)
        code_text.insert("1.0", code)
        code_text.configure(state="disabled")
        
        # Текст кнопки в зависимости от типа вставки
        button_text = "Вставить код"
        if insert_type == "line":
            button_text = f"Вставить код в строку {line_num}"
        elif insert_type == "range":
            button_text = f"Заменить строки {start_line}-{end_line}"
        
        # Добавляем кнопку для вставки кода в редактор
        insert_btn = ctk.CTkButton(
            code_frame, 
            text=button_text, 
            fg_color=KanagawaTheme.FUNCTION, 
            hover_color=KanagawaTheme.SELECTION,
            text_color=KanagawaTheme.FOREGROUND,
            height=30,
            command=lambda: self._insert_code_to_editor(code_to_insert, insert_type, line_num, start_line, end_line)
        )
        insert_btn.pack(pady=(0, 10), padx=10)
        
        return code_frame
    
    def _insert_code_to_editor(self, code, insert_type="standard", line_num=None, start_line=None, end_line=None):
        """Вставляет предложенный код в редактор с учетом указанного типа вставки"""
        # Удаляем все маркеры формата из кода
        code = re.sub(r'###CODE_INSERT.*', '', code)
        code = re.sub(r'###END_INSERT', '', code)
        
        # Удаляем различные указания на строку из кода
        patterns_to_clean = [
            r'строка[:]?\s*\d+',           # строка: 42 или строка 42
            r'line[:]?\s*\d+',             # line: 42 или line 42
            r'#.*строка[:]?\s*\d+',        # # строка 42
            r'#.*line[:]?\s*\d+',          # # line 42
            r'//.*строка[:]?\s*\d+',       # // строка 42
            r'//.*line[:]?\s*\d+',         # // line 42
            r'строки[:]?\s*\d+\s*-\s*\d+', # строки: 10-15
            r'lines[:]?\s*\d+\s*-\s*\d+',  # lines: 10-15
        ]
        
        for pattern in patterns_to_clean:
            code = re.sub(pattern, '', code, flags=re.IGNORECASE)
        
        # Проверяем, открыт ли файл в редакторе
        if not self.current_file:
            # Если файл не открыт, просто вставляем код в текущую позицию
            self.code_editor.insert(tk.INSERT, code)
            self.status_text.configure(text="Код вставлен в редактор")
            return
        
        # Импортируем код для просмотра изменений
        try:
            import code_review
        except ImportError:
            # Если модуль не найден, используем стандартное поведение
            self._do_insert_code(code, insert_type, line_num, start_line, end_line)
            return
            
        # Получаем текущее содержимое файла
        current_content = self.code_editor.get("1.0", tk.END)
        
        # Формируем новое содержимое с учетом вставки кода
        if insert_type == "line" and line_num is not None:
            # Предварительный просмотр замены указанной строки
            new_content = self._simulate_line_replacement(current_content, line_num, code)
            review_line = line_num
        elif insert_type == "range" and start_line is not None and end_line is not None:
            # Предварительный просмотр замены диапазона строк
            new_content = self._simulate_range_replacement(current_content, start_line, end_line, code)
            review_line = start_line
        else:
            # Вставка в текущую позицию (для предпросмотра используем позицию курсора)
            cursor_pos = self.code_editor.index(tk.INSERT)
            cursor_line = int(cursor_pos.split('.')[0])
            new_content = self._simulate_insertion_at_cursor(current_content, cursor_pos, code)
            review_line = cursor_line
        
        # Показываем диалог предварительного просмотра изменений
        def accept_changes(content):
            # При принятии изменений применяем их к редактору
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.load_file(self.current_file, goto_line=review_line)
            self.status_text.configure(text="Изменения применены")
        
        def reject_changes():
            # При отказе просто закрываем диалог
            self.status_text.configure(text="Изменения отклонены")
        
        code_review.show_code_review(
            self, 
            self.current_file, 
            current_content, 
            new_content, 
            line_num=review_line, 
            on_accept=accept_changes, 
            on_reject=reject_changes,
            theme=self.theme
        )
    
    def _do_insert_code(self, code, insert_type="standard", line_num=None, start_line=None, end_line=None):
        """Непосредственно вставляет код в редактор без предварительного просмотра"""
        if insert_type == "line" and line_num is not None:
            # Вставка на указанную строку (заменяя существующую строку)
            insert_position = f"{line_num}.0"
            
            # Проверяем, существует ли такая строка в файле
            total_lines = int(self.code_editor.index('end-1c').split('.')[0])
            
            # Если указанная строка больше, чем общее количество строк,
            # добавляем пустые строки
            if line_num > total_lines:
                missing_lines = line_num - total_lines
                self.code_editor.insert('end', '\n' * missing_lines)
                # Заменяем последнюю строку (которая пустая)
                self.code_editor.insert(f"{line_num}.0", code)
                self.status_text.configure(text=f"Код вставлен в строку {line_num}")
            else:
                # Удаляем существующую строку и вставляем новый код
                self.code_editor.delete(f"{line_num}.0", f"{line_num}.end+1c")  # +1c для включения символа новой строки
                self.code_editor.insert(f"{line_num}.0", code)
                self.status_text.configure(text=f"Заменена строка {line_num}")
        
        elif insert_type == "range" and start_line is not None and end_line is not None:
            # Замена указанного диапазона строк
            total_lines = int(self.code_editor.index('end-1c').split('.')[0])
            
            # Если начальная строка за пределами файла, добавляем строки
            if start_line > total_lines:
                missing_lines = start_line - total_lines
                self.code_editor.insert('end', '\n' * missing_lines)
            
            # Устанавливаем точку начала замены
            start_position = f"{start_line}.0"
            
            # Устанавливаем точку конца замены
            if end_line > int(self.code_editor.index('end-1c').split('.')[0]):
                end_position = 'end-1c'
            else:
                end_position = f"{end_line}.end+1c"  # +1c для включения символа новой строки
            
            # Удаляем старый текст и вставляем новый
            self.code_editor.delete(start_position, end_position)
            self.code_editor.insert(start_position, code)
            self.status_text.configure(text=f"Заменены строки {start_line}-{end_line}")
            
        else:
            # Стандартная вставка в текущую позицию курсора
            self.code_editor.insert(tk.INSERT, code)
            self.status_text.configure(text="Код вставлен в редактор")
        
        # Обновляем подсветку синтаксиса
        self.highlight_syntax()
        
        # Фокусируемся на редакторе
        self.code_editor.focus_set()
    
    def _simulate_line_replacement(self, content, line_num, new_code):
        """Симулирует замену строки для предварительного просмотра"""
        lines = content.splitlines()
        total_lines = len(lines)
        
        # Если нужная строка за пределами файла, добавляем пустые строки
        while total_lines < line_num:
            lines.append("")
            total_lines += 1
        
        # Заменяем строку
        if line_num <= total_lines:
            lines[line_num - 1] = new_code
        else:
            lines.append(new_code)
        
        # Формируем новое содержимое
        return "\n".join(lines)
    
    def _simulate_range_replacement(self, content, start_line, end_line, new_code):
        """Симулирует замену диапазона строк для предварительного просмотра"""
        lines = content.splitlines()
        total_lines = len(lines)
        
        # Если начальная строка за пределами файла, добавляем пустые строки
        while total_lines < start_line:
            lines.append("")
            total_lines += 1
        
        # Удаляем строки в указанном диапазоне
        if end_line > total_lines:
            end_line = total_lines
        
        if start_line <= total_lines:
            # Удаляем строки и вставляем новые
            del lines[start_line - 1:end_line]
            # Вставляем новые строки
            new_lines = new_code.splitlines()
            for i, line in enumerate(new_lines):
                lines.insert(start_line - 1 + i, line)
        else:
            # Если начало диапазона за пределами файла, просто добавляем новый код
            new_lines = new_code.splitlines()
            lines.extend(new_lines)
        
        # Формируем новое содержимое
        return "\n".join(lines)
    
    def _simulate_insertion_at_cursor(self, content, cursor_pos, new_code):
        """Симулирует вставку кода в позицию курсора для предварительного просмотра"""
        # Разбиваем позицию курсора на строку и колонку
        line, col = cursor_pos.split('.')
        line_num = int(line)
        col_num = int(col)
        
        lines = content.splitlines()
        
        # Если строка существует, вставляем код
        if line_num <= len(lines):
            current_line = lines[line_num - 1]
            # Вставляем новый код в текущую строку
            if col_num <= len(current_line):
                # Разбиваем строку по позиции курсора
                left = current_line[:col_num]
                right = current_line[col_num:]
                
                # Вставляем новый код между частями
                new_lines = new_code.splitlines()
                if new_lines:
                    # Первую строку нового кода добавляем к левой части текущей строки
                    lines[line_num - 1] = left + new_lines[0]
                    
                    # Последнюю строку нового кода соединяем с правой частью текущей строки
                    if len(new_lines) > 1:
                        # Вставляем промежуточные строки
                        for i, new_line in enumerate(new_lines[1:-1], 1):
                            lines.insert(line_num - 1 + i, new_line)
                        
                        # Последняя строка + оставшаяся часть
                        lines.insert(line_num - 1 + len(new_lines) - 1, new_lines[-1] + right)
                    else:
                        # Если новый код - одна строка, просто добавляем правую часть
                        lines[line_num - 1] += right
            else:
                # Если курсор за пределами строки, просто добавляем код
                lines[line_num - 1] += new_code
        else:
            # Если строка за пределами файла, добавляем пустые строки и код
            while len(lines) < line_num - 1:
                lines.append("")
            lines.append(new_code)
        
        # Формируем новое содержимое
        return "\n".join(lines)
    
    def clear_chat_history(self):
        """Очищает историю чата и сбрасывает контекст"""
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state="disabled")
        self.chat_messages = []
        self.is_first_message = True
    
    def start_window_drag(self, event):
        """Начало перетаскивания окна"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def stop_window_drag(self, event):
        """Окончание перетаскивания окна"""
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def on_window_drag(self, event):
        """Перетаскивание окна"""
        if not self.is_maximized:  # Только если окно не развернуто
            x = self.winfo_x() - self.drag_start_x + event.x
            y = self.winfo_y() - self.drag_start_y + event.y
            self.geometry(f"+{x}+{y}")
    
    def toggle_maximize(self):
        """Переключение полноэкранного режима без использования fullscreen"""
        if not self.is_maximized:
            # Сохраняем текущий размер и позицию
            self.last_size = (self.winfo_width(), self.winfo_height())
            self.last_position = (self.winfo_x(), self.winfo_y())
            
            # Максимизируем по-разному в зависимости от платформы
            if os.name == 'nt':  # Windows
                self.state('zoomed')  # Встроенный метод Tkinter для максимизации
            else:  # Linux/Mac
                # Для других платформ используем геометрию экрана
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                self.geometry(f"{screen_width}x{screen_height}+0+0")
            
            self.is_maximized = True
        else:
            # Восстанавливаем предыдущий размер
            if os.name == 'nt':  # Windows
                self.state('normal')  # Возвращаем к обычному размеру
            else:  # Linux/Mac
                width, height = self.last_size
                x, y = self.last_position if self.last_position[0] is not None else (0, 0)
                self.geometry(f"{width}x{height}+{x}+{y}")
            
            self.is_maximized = False
    
    def minimize(self):
        """Сворачивание окна"""
        self.iconify()  # Встроенный метод Tkinter для минимизации
    
    def show_file_menu(self):
        """Показать выпадающее меню файла"""
        menu = tk.Menu(self, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND,
                    activebackground=KanagawaTheme.SELECTION, activeforeground=KanagawaTheme.FOREGROUND)
        menu.add_command(label="Новый файл", command=self.new_file)
        menu.add_command(label="Открыть файл...", command=self.open_file)
        menu.add_command(label="Открыть папку...", command=self.open_project)
        menu.add_separator()
        menu.add_command(label="Сохранить", command=self.save_file)
        menu.add_command(label="Сохранить как...", command=self.save_file_as)
        menu.add_separator()
        menu.add_command(label="Выход", command=self.quit)
        
        # Отображаем меню в позиции кнопки
        x = self.winfo_rootx() + 5
        y = self.winfo_rooty() + 60  # Под кнопкой меню
        menu.post(x, y)
    
    def show_edit_menu(self):
        """Показать выпадающее меню правки"""
        menu = tk.Menu(self, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND,
                    activebackground=KanagawaTheme.SELECTION, activeforeground=KanagawaTheme.FOREGROUND)
        menu.add_command(label="Отменить", command=lambda: self.code_editor.event_generate("<<Undo>>"))
        menu.add_command(label="Повторить", command=lambda: self.code_editor.event_generate("<<Redo>>"))
        menu.add_separator()
        menu.add_command(label="Вырезать", command=lambda: self.code_editor.event_generate("<<Cut>>"))
        menu.add_command(label="Копировать", command=lambda: self.code_editor.event_generate("<<Copy>>"))
        menu.add_command(label="Вставить", command=lambda: self.code_editor.event_generate("<<Paste>>"))
        
        # Отображаем меню в позиции кнопки
        x = self.winfo_rootx() + 65
        y = self.winfo_rooty() + 60  # Под кнопкой меню
        menu.post(x, y)
    
    def show_view_menu(self):
        """Показать выпадающее меню вид"""
        menu = tk.Menu(self, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND,
                    activebackground=KanagawaTheme.SELECTION, activeforeground=KanagawaTheme.FOREGROUND)
        menu.add_command(label="Проводник", command=self.toggle_explorer)
        menu.add_command(label="Терминал", command=self.toggle_console)
        
        # Отображаем меню в позиции кнопки
        x = self.winfo_rootx() + 125
        y = self.winfo_rooty() + 60  # Под кнопкой меню
        menu.post(x, y)
    
    def show_run_menu(self):
        """Показать выпадающее меню запуска"""
        menu = tk.Menu(self, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND,
                    activebackground=KanagawaTheme.SELECTION, activeforeground=KanagawaTheme.FOREGROUND)
        menu.add_command(label="Запустить", command=self.run_current_code)
        menu.add_command(label="Запустить в отдельном окне", command=self.run_code_in_external_console)
        menu.add_command(label="Остановить выполнение", command=self.stop_execution)
        
        # Отображаем меню в позиции кнопки
        x = self.winfo_rootx() + 185
        y = self.winfo_rooty() + 60  # Под кнопкой меню
        menu.post(x, y)
    
    def new_file(self):
        """Создать новый файл"""
        self.current_file = None
        self.code_editor.delete("1.0", tk.END)
        self.title("VSKode Editor - Новый файл - Kanagawa")
        self.update_line_numbers()
        self.status_text.configure(text="Новый файл")
    
    def save_file_as(self):
        """Сохранить файл как..."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                ("Python files", "*.py"), 
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.current_file = file_path
            self.save_file()
    
    def on_text_change(self, event=None):
        """Обработчик изменения текста в редакторе"""
        self.update_line_numbers()
        self.highlight_syntax()
        self.highlight_current_line()
        self.update_cursor_position()
        
        # Показываем пробелы в текущей строке, если включено
        if self.settings.show_whitespace:
            self.show_whitespace(True)
    
    def highlight_current_line(self, event=None):
        """Подсвечивает текущую строку курсора"""
        self.update_cursor_position()
        
        # Удаляем предыдущую подсветку
        self.code_editor.tag_remove("current_line", "1.0", tk.END)
        
        # Получаем текущую позицию курсора
        current_position = self.code_editor.index(tk.INSERT)
        line = current_position.split('.')[0]
        
        # Подсвечиваем текущую строку
        self.code_editor.tag_add("current_line", f"{line}.0", f"{line}.end+1c")
        self.code_editor.tag_config("current_line", background=KanagawaTheme.LINE_HIGHLIGHT)
        
        # Обновляем активную строку в номерах строк
        if self.active_line != line:
            self.active_line = line
            self.update_line_numbers()
    
    def update_cursor_position(self):
        """Обновляет индикатор позиции курсора в строке состояния"""
        current_position = self.code_editor.index(tk.INSERT)
        line, col = current_position.split('.')
        self.line_col_indicator.configure(text=f"Строка: {line}, Символ: {int(col)+1}")
    
    def update_line_numbers(self):
        """Обновляет номера строк"""
        # Получаем текущий текст и считаем строки
        text_content = self.code_editor.get("1.0", tk.END)
        lines = text_content.count('\n') + 1
        
        # Подготавливаем текст для номеров строк
        line_numbers_text = ''
        for i in range(1, lines + 1):
            # Выделяем активную строку жирным
            if str(i) == self.active_line:
                line_numbers_text += f"{i}\n"
            else:
                line_numbers_text += f"{i}\n"
        
        # Обновляем номера строк
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.configure(state="disabled")
    
    def on_scroll_y(self, *args):
        """Синхронизирует прокрутку редактора и номеров строк"""
        self.code_editor.yview(*args)
        self.line_numbers.yview(*args)
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Python files", "*.py"), 
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.current_file = file_path
            self.load_file(file_path)
    
    def load_file(self, file_path, goto_line=None):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert("1.0", content)
            self.title(f"VSKode Editor - {os.path.basename(file_path)} - Kanagawa")
            self.status_text.configure(text=f"Файл загружен: {os.path.basename(file_path)}")
            
            # Обновляем интерфейс
            self.update_line_numbers()
            self.highlight_syntax()
            
            # Если указана строка, переходим к ней
            if goto_line:
                self.code_editor.mark_set(tk.INSERT, f"{goto_line}.0")
                self.code_editor.see(f"{goto_line}.0")
                
                # Подсвечиваем строку
                self.code_editor.tag_remove("active_change", "1.0", tk.END)
                self.code_editor.tag_add("active_change", f"{goto_line}.0", f"{goto_line}.end+1c")
                self.code_editor.tag_configure("active_change", background="#2D5D36")  # Зеленый фон для измененной строки
                
                # Установим таймер на автоматическое удаление подсветки через 3 секунды
                self.after(3000, lambda: self.code_editor.tag_remove("active_change", "1.0", tk.END))
            
            self.highlight_current_line()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")
    
    def save_file(self):
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[
                    ("Python files", "*.py"), 
                    ("All files", "*.*")
                ]
            )
        
        if self.current_file:
            try:
                content = self.code_editor.get("1.0", tk.END)
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_text.configure(text=f"Файл сохранен: {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
    
    def open_project(self):
        project_path = filedialog.askdirectory()
        
        if project_path:
            self.current_project = project_path
            self.update_project_tree(project_path)
            
            # Показываем проводник проекта, если он был скрыт
            if not self.project_frame.winfo_viewable():
                self.project_frame.grid()
    
    def update_project_tree(self, path):
        self.project_tree.delete(0, tk.END)
        self.project_tree.insert(tk.END, "..")
        
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    self.project_tree.insert(tk.END, f"📁 {item}")
                else:
                    self.project_tree.insert(tk.END, f"📄 {item}")
                    
            self.title(f"vpycode - {os.path.basename(path)}")
            self.status_text.configure(text=f"Проект загружен: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить проект: {e}")
    
    def open_file_from_tree(self, event):
        selection = self.project_tree.curselection()
        if selection:
            item = self.project_tree.get(selection[0])
            
            if item == "..":
                # Переход на уровень выше
                parent_dir = os.path.dirname(self.current_project)
                self.current_project = parent_dir
                self.update_project_tree(parent_dir)
                return
            
            # Убираем иконки из названия
            if item.startswith("📁 "):
                item = item[2:].strip()
                item_path = os.path.join(self.current_project, item)
                self.current_project = item_path
                self.update_project_tree(item_path)
            elif item.startswith("📄 "):
                item = item[2:].strip()
                file_path = os.path.join(self.current_project, item)
                self.current_file = file_path
                self.load_file(file_path)
    
    def highlight_syntax(self, event=None):
        """Подсветка синтаксиса, работает даже для несохраненных файлов"""
        # Форматируем код для отображения в редакторе
        self.code_editor.tag_remove("keyword", "1.0", tk.END)
        self.code_editor.tag_remove("string", "1.0", tk.END)
        self.code_editor.tag_remove("comment", "1.0", tk.END)
        self.code_editor.tag_remove("function", "1.0", tk.END)
        self.code_editor.tag_remove("class", "1.0", tk.END)
        self.code_editor.tag_remove("number", "1.0", tk.END)
        self.code_editor.tag_remove("operator", "1.0", tk.END)
        
        # Настройка тегов для подсветки в цветах Kanagawa
        self.code_editor.tag_configure("keyword", foreground=KanagawaTheme.KEYWORD)
        self.code_editor.tag_configure("string", foreground=KanagawaTheme.STRING)
        self.code_editor.tag_configure("comment", foreground=KanagawaTheme.COMMENT)
        self.code_editor.tag_configure("function", foreground=KanagawaTheme.FUNCTION)
        self.code_editor.tag_configure("class", foreground=KanagawaTheme.CLASS)
        self.code_editor.tag_configure("number", foreground=KanagawaTheme.NUMBER)
        self.code_editor.tag_configure("operator", foreground=KanagawaTheme.OPERATOR)
        
        # Определяем тип файла для подсветки
        use_python_lexer = True
        if self.current_file:
            if not self.current_file.endswith('.py'):
                try:
                    extension = os.path.splitext(self.current_file)[1]
                    self.current_filetype = extension
                    use_python_lexer = False
                except:
                    use_python_lexer = True
        
        # Подсветка для Python (работает даже для несохраненных файлов)
        if use_python_lexer or self.current_filetype == '.py':
            # Ключевые слова
            keywords = ["def", "class", "if", "else", "elif", "while", "for", "in", "try", 
                       "except", "finally", "import", "from", "as", "return", "break", 
                       "continue", "pass", "True", "False", "None", "and", "or", "not",
                       "with", "async", "await", "yield", "lambda", "assert", "del", "global",
                       "nonlocal", "raise", "is"]
            
            for keyword in keywords:
                start_pos = "1.0"
                while True:
                    start_pos = self.code_editor.search(f"\\y{keyword}\\y", start_pos, tk.END, regexp=True)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(keyword)}c"
                    self.code_editor.tag_add("keyword", start_pos, end_pos)
                    start_pos = end_pos
            
            # Операторы
            operators = ["+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "=", "+=", "-=", "*=", "/="]
            for op in operators:
                start_pos = "1.0"
                while True:
                    start_pos = self.code_editor.search(f"{op}", start_pos, tk.END)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(op)}c"
                    self.code_editor.tag_add("operator", start_pos, end_pos)
                    start_pos = end_pos
            
            # Числа
            start_pos = "1.0"
            while True:
                start_pos = self.code_editor.search(r'\y\d+\y', start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                end_pos = self.code_editor.search(r'\W', start_pos, tk.END, regexp=True)
                if not end_pos:
                    end_pos = tk.END
                self.code_editor.tag_add("number", start_pos, end_pos)
                start_pos = end_pos
            
            # Строки
            for quote in ['"', "'"]:
                start_pos = "1.0"
                while True:
                    start_pos = self.code_editor.search(f'{quote}', start_pos, tk.END)
                    if not start_pos:
                        break
                    end_pos = self.code_editor.search(f'{quote}', f"{start_pos}+1c", tk.END)
                    if not end_pos:
                        break
                    end_pos = f"{end_pos}+1c"
                    self.code_editor.tag_add("string", start_pos, end_pos)
                    start_pos = end_pos
            
            # Комментарии
            start_pos = "1.0"
            while True:
                start_pos = self.code_editor.search('#', start_pos, tk.END)
                if not start_pos:
                    break
                line = int(float(start_pos))
                end_pos = f"{line}.end"
                self.code_editor.tag_add("comment", start_pos, end_pos)
                start_pos = f"{line+1}.0"
            
            # Функции
            start_pos = "1.0"
            while True:
                start_pos = self.code_editor.search('def ', start_pos, tk.END)
                if not start_pos:
                    break
                name_start = f"{start_pos}+4c"
                name_end = self.code_editor.search('\\(', name_start, tk.END)
                if not name_end:
                    break
                self.code_editor.tag_add("function", name_start, name_end)
                start_pos = name_end
            
            # Классы
            start_pos = "1.0"
            while True:
                start_pos = self.code_editor.search('class ', start_pos, tk.END)
                if not start_pos:
                    break
                name_start = f"{start_pos}+6c"
                name_end = self.code_editor.search('\\(|:', name_start, tk.END, regexp=True)
                if not name_end:
                    break
                self.code_editor.tag_add("class", name_start, name_end)
                start_pos = name_end
    
    def run_current_code(self):
        """Запускает текущий код и выводит результат в консоль"""
        # Убеждаемся, что консоль видима
        if not self.console_frame.winfo_viewable():
            self.toggle_console()
            
        # Очищаем консоль перед запуском
        self.clear_console()
        
        # Получаем текущий код из редактора
        code = self.code_editor.get("1.0", tk.END)
        
        # Если нет кода, ничего не делаем
        if not code.strip():
            self.write_to_console("Ошибка: нет кода для запуска\n", "error")
            return
        
        # Если файл не сохранен, создаем временный файл
        if self.current_file:
            # Сохраняем текущий файл перед запуском
            self.save_file()
            file_to_run = self.current_file
            file_extension = os.path.splitext(file_to_run)[1]
        else:
            # Создаем временный файл
            try:
                if self.temp_file:
                    # Используем уже существующий временный файл
                    temp_file = self.temp_file
                else:
                    # Создаем новый временный файл с расширением .py
                    temp_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
                    self.temp_file = temp_file.name
                    temp_file.close()
                
                # Записываем код во временный файл
                with open(self.temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                file_to_run = self.temp_file
                file_extension = '.py'  # Предположим, что это Python для временных файлов
            except Exception as e:
                self.write_to_console(f"Ошибка создания временного файла: {str(e)}\n", "error")
                return
        
        # Проверяем, есть ли обработчик для данного расширения файла
        handler_found = False
        language_name = None
        
        for lang, info in self.language_handlers.items():
            if file_extension in info["extensions"]:
                handler_found = True
                language_name = lang
                break
        
        if handler_found:
            # Если найден обработчик, используем его
            self.write_to_console(f"Запуск {language_name}: {os.path.basename(file_to_run)}\n", "info")
            # Запускаем код в отдельном потоке
            threading.Thread(target=self._execute_code, args=(file_to_run, language_name)).start()
        else:
            # Если обработчик не найден, показываем диалог выбора дебаггера
            self.show_debugger_selection_dialog(file_to_run, file_extension)
    
    def show_debugger_selection_dialog(self, file_path, file_extension):
        """Показывает диалог выбора отладчика для неподдерживаемого типа файла"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Выбор отладчика")
        dialog.geometry("400x300")
        dialog.focus_set()
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.theme.BACKGROUND)
        
        # Заголовок
        header_label = ctk.CTkLabel(
            dialog, 
            text=f"Выберите отладчик для файла {os.path.basename(file_path)}",
            font=("Arial", 14, "bold"),
            text_color=self.theme.FOREGROUND
        )
        header_label.pack(pady=(20, 5))
        
        # Информация о типе файла
        file_info = ctk.CTkLabel(
            dialog,
            text=f"Тип файла: {file_extension}",
            text_color=self.theme.FOREGROUND
        )
        file_info.pack(pady=5)
        
        # Предупреждение
        warning_label = ctk.CTkLabel(
            dialog,
            text="В системе не найден обработчик для этого типа файла.\nВыберите подходящий плагин или установите новый.",
            text_color=self.theme.CONSOLE_INFO
        )
        warning_label.pack(pady=10)
        
        # Фрейм для списка плагинов
        plugins_frame = ctk.CTkFrame(dialog, fg_color=self.theme.DARKER_BG)
        plugins_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Список доступных плагинов-отладчиков
        debugger_plugins = []
        
        # Получаем список плагинов, которые реализуют метод run_code
        for name, plugin in self.plugin_manager.active_plugins.items():
            # Проверяем, имеет ли плагин метод запуска кода
            if hasattr(plugin, 'run_code') or hasattr(plugin, 'run_javascript') or hasattr(plugin, 'run_any_code'):
                debugger_plugins.append((name, plugin))
        
        # Переменная для хранения выбранного плагина
        selected_plugin = tk.StringVar()
        
        if not debugger_plugins:
            # Если нет подходящих плагинов
            no_plugins_label = ctk.CTkLabel(
                plugins_frame,
                text="Нет доступных плагинов-отладчиков.\nУстановите подходящий плагин для этого типа файла.",
                text_color=self.theme.FOREGROUND
            )
            no_plugins_label.pack(pady=30)
        else:
            # Создаем список доступных отладчиков
            for name, plugin in debugger_plugins:
                plugin_frame = ctk.CTkFrame(plugins_frame, fg_color="transparent", height=30)
                plugin_frame.pack(fill="x", pady=5)
                
                # Радиокнопка для выбора плагина
                plugin_radio = ctk.CTkRadioButton(
                    plugin_frame,
                    text=name,
                    variable=selected_plugin,
                    value=name,
                    font=("Arial", 12),
                    text_color=self.theme.FOREGROUND,
                    fg_color=self.theme.SELECTION,
                    hover_color=self.theme.BUTTON_HOVER,
                )
                plugin_radio.pack(side="left", padx=10)
                
                # Описание плагина
                plugin_desc = ctk.CTkLabel(
                    plugin_frame,
                    text=plugin.description,
                    text_color=self.theme.COMMENT
                )
                plugin_desc.pack(side="left", padx=10)
            
            # По умолчанию выбираем первый плагин
            if debugger_plugins:
                selected_plugin.set(debugger_plugins[0][0])
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent", height=40)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def run_with_selected_plugin():
            plugin_name = selected_plugin.get()
            if plugin_name:
                dialog.destroy()
                
                # Получаем выбранный плагин
                plugin = self.plugin_manager.active_plugins[plugin_name]
                
                # Проверяем, какой метод запуска кода имеет плагин
                if hasattr(plugin, 'run_code'):
                    # Универсальный метод запуска
                    threading.Thread(
                        target=lambda: self.run_with_plugin(plugin, file_path, file_extension)
                    ).start()
                elif hasattr(plugin, 'run_javascript') and file_extension in ['.js', '.mjs', '.cjs']:
                    # Специализированный метод для JavaScript
                    threading.Thread(
                        target=lambda: self.run_with_javascript_plugin(plugin, file_path)
                    ).start()
                else:
                    # Используем метод запуска любого кода, если доступен
                    threading.Thread(
                        target=lambda: self.run_with_any_plugin(plugin, file_path, file_extension)
                    ).start()
        
        # Кнопка "Запустить"
        run_btn = ctk.CTkButton(
            buttons_frame,
            text="Запустить",
            width=100,
            fg_color=self.theme.CONSOLE_SUCCESS,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.FOREGROUND,
            command=run_with_selected_plugin
        )
        run_btn.pack(side="right", padx=5)
        
        # Кнопка "Отмена"
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            width=100,
            fg_color=self.theme.BUTTON_BG,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.FOREGROUND,
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=5)
    
    def run_with_plugin(self, plugin, file_path, file_extension):
        """Запускает код с использованием плагина с универсальным интерфейсом"""
        try:
            self.write_to_console(f"Запуск через плагин {plugin.name}: {os.path.basename(file_path)}\n", "info")
            
            # Вызываем метод run_code плагина
            process = plugin.run_code(file_path, file_extension)
            
            # Если плагин вернул процесс, обрабатываем его вывод
            if process:
                self.current_process = process
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    if stdout:
                        self.write_to_console(stdout)
                    self.write_to_console("\nПрограмма завершена успешно.\n", "success")
                else:
                    if stdout:
                        self.write_to_console(stdout)
                    if stderr:
                        self.write_to_console(stderr, "error")
                    self.write_to_console(f"\nПрограмма завершена с ошибкой (код {process.returncode}).\n", "error")
                
                # Очищаем ссылку на процесс
                self.current_process = None
        except Exception as e:
            self.write_to_console(f"Ошибка при запуске кода через плагин: {str(e)}\n", "error")
    
    def run_with_javascript_plugin(self, plugin, file_path):
        """Запускает JavaScript код через специализированный плагин"""
        try:
            self.write_to_console(f"Запуск JavaScript через плагин {plugin.name}: {os.path.basename(file_path)}\n", "info")
            
            # Вызываем специализированный метод для JavaScript
            process = plugin.run_javascript(file_path)
            
            # Аналогично обработке стандартного процесса
            if process:
                self.current_process = process
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    if stdout:
                        self.write_to_console(stdout)
                    self.write_to_console("\nJavaScript выполнен успешно.\n", "success")
                else:
                    if stdout:
                        self.write_to_console(stdout)
                    if stderr:
                        self.write_to_console(stderr, "error")
                    self.write_to_console(f"\nJavaScript завершился с ошибкой (код {process.returncode}).\n", "error")
                
                self.current_process = None
        except Exception as e:
            self.write_to_console(f"Ошибка при запуске JavaScript: {str(e)}\n", "error")
    
    def run_with_any_plugin(self, plugin, file_path, file_extension):
        """Запускает любой код через плагин с методом run_any_code"""
        try:
            self.write_to_console(f"Запуск через универсальный плагин {plugin.name}: {os.path.basename(file_path)}\n", "info")
            
            # Вызываем универсальный метод для любого типа файла
            process = plugin.run_any_code(file_path, file_extension)
            
            # Обработка вывода процесса
            if process:
                self.current_process = process
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    if stdout:
                        self.write_to_console(stdout)
                    self.write_to_console("\nПрограмма завершена успешно.\n", "success")
                else:
                    if stdout:
                        self.write_to_console(stdout)
                    if stderr:
                        self.write_to_console(stderr, "error")
                    self.write_to_console(f"\nПрограмма завершена с ошибкой (код {process.returncode}).\n", "error")
                
                self.current_process = None
        except Exception as e:
            self.write_to_console(f"Ошибка при запуске кода: {str(e)}\n", "error")
    
    def _execute_code(self, file_path, language_name="Python"):
        """Выполняет код из указанного файла и перехватывает вывод"""
        try:
            # Используем соответствующий обработчик языка
            run_command = self.language_handlers.get(language_name, {}).get("run_command")
            
            if not run_command:
                self.write_to_console(f"Ошибка: Нет обработчика для языка {language_name}\n", "error")
                return
                
            # Выполняем код через обработчик
            process = run_command(file_path)
            
            if not process:
                self.write_to_console("Ошибка запуска процесса\n", "error")
                return
                
            # Сохраняем ссылку на процесс
            self.current_process = process
            
            # Читаем вывод и ошибки
            stdout, stderr = process.communicate()
            
            # Проверяем код возврата
            if process.returncode == 0:
                if stdout:
                    self.write_to_console(stdout)
                self.write_to_console("\nПрограмма завершена успешно.\n", "success")
            else:
                if stdout:
                    self.write_to_console(stdout)
                if stderr:
                    self.write_to_console(stderr, "error")
                self.write_to_console(f"\nПрограмма завершена с ошибкой (код {process.returncode}).\n", "error")
            
            # Очищаем ссылку на процесс
            self.current_process = None
            
        except Exception as e:
            self.write_to_console(f"Ошибка выполнения: {str(e)}\n", "error")
    
    def run_code_in_external_console(self):
        """Запускает код в отдельном окне консоли"""
        # Получаем текущий код из редактора
        code = self.code_editor.get("1.0", tk.END)
        
        # Если нет кода, ничего не делаем
        if not code.strip():
            messagebox.showerror("Ошибка", "Нет кода для запуска")
            return
        
        # Если файл не сохранен, создаем временный файл
        if self.current_file:
            # Сохраняем текущий файл перед запуском
            self.save_file()
            file_to_run = self.current_file
        else:
            # Создаем временный файл
            try:
                if self.temp_file:
                    # Используем уже существующий временный файл
                    temp_file = self.temp_file
                else:
                    # Создаем новый временный файл с расширением .py
                    temp_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
                    self.temp_file = temp_file.name
                    temp_file.close()
                
                # Записываем код во временный файл
                with open(self.temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                file_to_run = self.temp_file
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать временный файл: {e}")
                return
        
        # Запускаем код в отдельном окне консоли
        try:
            subprocess.Popen(
                [sys.executable, file_to_run],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.status_text.configure(text=f"Запущен в отдельном окне: {os.path.basename(file_to_run)}")
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))
    
    def stop_execution(self):
        """Останавливает выполнение текущего процесса"""
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.write_to_console("\nВыполнение прервано пользователем.\n", "error")
                self.current_process = None
            except Exception as e:
                self.write_to_console(f"\nОшибка при остановке выполнения: {str(e)}\n", "error")
        else:
            self.write_to_console("\nНет активных процессов для остановки.\n", "info")
    
    def toggle_explorer(self):
        """Переключает видимость проводника проекта"""
        if self.project_frame.winfo_viewable():
            self.project_frame.grid_remove()
        else:
            self.project_frame.grid()
    
    def toggle_console(self):
        """Переключение видимости консоли"""
        if self.console_frame.winfo_viewable():
            self.console_frame.grid_remove()
        else:
            self.console_frame.grid()
    
    def clear_console(self):
        """Очистка содержимого консоли"""
        self.console_output.delete("1.0", tk.END)
    
    def write_to_console(self, text, tag=None):
        """Запись текста в консоль с опциональным тегом"""
        self.console_output.configure(state="normal")
        if tag:
            self.console_output.insert(tk.END, text, tag)
        else:
            self.console_output.insert(tk.END, text)
        self.console_output.configure(state="disabled")
        self.console_output.see(tk.END)

    def run_python_code(self, file_path):
        """Запускает Python код из указанного файла."""
        return self._execute_code(file_path)
    
    def apply_theme(self):
        """Применяет текущую тему ко всем элементам интерфейса."""
        # Обновляем цвета основного окна
        self.configure(fg_color=self.theme.BACKGROUND)
        
        # Обновляем цвета для редактора кода
        self.code_editor.configure(
            bg=self.theme.BACKGROUND, 
            fg=self.theme.FOREGROUND,
            insertbackground=self.theme.CURSOR,
            selectbackground=self.theme.SELECTION
        )
        
        # Обновляем номера строк
        self.line_numbers.configure(
            bg=self.theme.BACKGROUND, 
            fg=self.theme.COMMENT,
            insertbackground=self.theme.CURSOR,
            selectbackground=self.theme.SELECTION
        )
        
        # Обновляем теги для подсветки синтаксиса
        self.code_editor.tag_configure("keyword", foreground=self.theme.KEYWORD)
        self.code_editor.tag_configure("string", foreground=self.theme.STRING)
        self.code_editor.tag_configure("comment", foreground=self.theme.COMMENT)
        self.code_editor.tag_configure("function", foreground=self.theme.FUNCTION)
        self.code_editor.tag_configure("class", foreground=self.theme.CLASS)
        self.code_editor.tag_configure("number", foreground=self.theme.NUMBER)
        self.code_editor.tag_configure("operator", foreground=self.theme.OPERATOR)
        
        # Обновляем цвета консоли
        self.console_output.configure(
            bg=self.theme.CONSOLE_BG, 
            fg=self.theme.CONSOLE_FG
        )
        
        # Обновляем теги консоли
        self.console_output.tag_configure("error", foreground=self.theme.CONSOLE_ERROR)
        self.console_output.tag_configure("success", foreground=self.theme.CONSOLE_SUCCESS)
        self.console_output.tag_configure("info", foreground=self.theme.CONSOLE_INFO)
        
        # Обновляем теги чата с ИИ
        self.chat_history.tag_configure("user", foreground=self.theme.AI_USER_MSG)
        self.chat_history.tag_configure("bot", foreground=self.theme.AI_BOT_MSG)
        self.chat_history.tag_configure("system", foreground=self.theme.AI_ACCENT)
        
        # Обновляем тег для подсветки текущей строки
        self.code_editor.tag_config("current_line", background=self.theme.LINE_HIGHLIGHT)
        
        # Перерисовываем интерфейс
        self.update()
    
    def show_settings_menu(self):
        """Показать выпадающее меню настроек"""
        menu = tk.Menu(self, tearoff=0, bg=self.theme.DARKER_BG, fg=self.theme.FOREGROUND,
                    activebackground=self.theme.SELECTION, activeforeground=self.theme.FOREGROUND)
        menu.add_command(label="Шрифт...", command=lambda: self.show_settings_dialog("font"))
        menu.add_command(label="Размер шрифта...", command=lambda: self.show_settings_dialog("font_size"))
        menu.add_command(label="Горячие клавиши...", command=lambda: self.show_settings_dialog("hotkeys"))
        menu.add_separator()
        menu.add_command(label="Показывать пробелы", command=self.toggle_show_whitespace)
        menu.add_command(label="Настройки табуляции...", command=lambda: self.show_settings_dialog("tab"))
        menu.add_separator()
        menu.add_command(label="Плагины...", command=self.show_plugins_dialog)
        menu.add_separator()
        menu.add_command(label="Сохранить настройки", command=self.save_settings)
        
        # Отображаем меню в позиции кнопки
        x = self.winfo_rootx() + 195
        y = self.winfo_rooty() + 60  # Под кнопкой меню
        menu.post(x, y)
    
    def show_settings_dialog(self, section="general"):
        """Показать диалог настроек"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("400x500")
        settings_window.focus_set()
        settings_window.resizable(False, False)
        settings_window.configure(fg_color=KanagawaTheme.BACKGROUND)
        
        # Хак для Windows, чтобы сделать окно модальным
        settings_window.grab_set()
        
        # Заголовок
        header_label = ctk.CTkLabel(settings_window, text="Настройки редактора",
                                   font=("Arial", 16, "bold"), text_color=KanagawaTheme.FOREGROUND)
        header_label.pack(pady=(20, 10))
        
        # Фрейм с вкладками для разных секций
        tab_view = ctk.CTkTabview(settings_window, fg_color=KanagawaTheme.DARKER_BG)
        tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Создаем вкладки
        font_tab = tab_view.add("Шрифт")
        tab_tab = tab_view.add("Табуляция")
        hotkeys_tab = tab_view.add("Горячие клавиши")
        ai_tab = tab_view.add("ИИ-ассистент")
        
        # Содержимое вкладки Шрифт
        font_frame = ctk.CTkFrame(font_tab, fg_color="transparent")
        font_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        font_size_label = ctk.CTkLabel(font_frame, text="Размер шрифта:", text_color=KanagawaTheme.FOREGROUND)
        font_size_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # Use DoubleVar instead of StringVar for the slider
        font_size_var = tk.DoubleVar(value=float(self.settings.font_size))
        font_size_display = tk.StringVar(value=str(self.settings.font_size))
        
        # Update the display variable whenever the slider changes
        def update_font_size(value):
            size = int(value)
            font_size_display.set(str(size))
            return size
        
        font_size_slider = ctk.CTkSlider(font_frame, from_=8, to=24, number_of_steps=16,
                                      variable=font_size_var, command=update_font_size)
        font_size_slider.pack(fill="x", padx=10, pady=(5, 20))
        
        font_size_value = ctk.CTkLabel(font_frame, textvariable=font_size_display, text_color=KanagawaTheme.FOREGROUND)
        font_size_value.pack(anchor="center", pady=(0, 20))
        
        font_family_label = ctk.CTkLabel(font_frame, text="Шрифт:", text_color=KanagawaTheme.FOREGROUND)
        font_family_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        font_options = ["Consolas", "Courier New", "Fira Code", "Source Code Pro", "Monospace", "Monaco"]
        font_var = tk.StringVar(value=self.settings.font_family)
        font_dropdown = ctk.CTkOptionMenu(font_frame, values=font_options, variable=font_var,
                                        fg_color=KanagawaTheme.DARKER_BG,
                                        button_color=KanagawaTheme.BUTTON_BG,
                                        button_hover_color=KanagawaTheme.BUTTON_HOVER,
                                        dropdown_fg_color=KanagawaTheme.DARKER_BG,
                                        dropdown_hover_color=KanagawaTheme.SELECTION)
        font_dropdown.pack(fill="x", padx=10, pady=(5, 20))
        
        # Предпросмотр шрифта
        preview_label = ctk.CTkLabel(font_frame, text="Предпросмотр:", text_color=KanagawaTheme.FOREGROUND)
        preview_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # Создаем предпросмотр с контрастными цветами
        preview_text = tk.Text(font_frame, height=4, width=30, bd=1, relief="solid",
                             bg="#2A2A37", fg="#DCD7BA",  # Явно используем контрастные цвета
                             insertbackground=KanagawaTheme.CURSOR,
                             font=(font_var.get(), int(float(font_size_var.get()))))
        preview_text.pack(fill="x", padx=10, pady=(5, 10))
        preview_text.insert("1.0", "def hello_world():\n    print('Hello, World!')\n    return True")
        preview_text.configure(state="disabled")
        
        # Обновление предпросмотра при изменении настроек
        def update_preview(*args):
            preview_text.configure(state="normal")
            preview_text.configure(font=(font_var.get(), int(float(font_size_var.get()))))
            preview_text.configure(state="disabled")
        
        font_var.trace_add("write", update_preview)
        font_size_var.trace_add("write", update_preview)
        font_size_display.trace_add("write", update_preview)
        
        # Содержимое вкладки Табуляция
        tab_frame = ctk.CTkFrame(tab_tab, fg_color="transparent")
        tab_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_size_label = ctk.CTkLabel(tab_frame, text="Размер табуляции:", text_color=KanagawaTheme.FOREGROUND)
        tab_size_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        tab_sizes = ["2", "4", "8"]
        tab_size_var = tk.StringVar(value=str(self.settings.tab_size))
        tab_size_dropdown = ctk.CTkOptionMenu(tab_frame, values=tab_sizes, variable=tab_size_var,
                                           fg_color=KanagawaTheme.DARKER_BG,
                                           button_color=KanagawaTheme.BUTTON_BG,
                                           button_hover_color=KanagawaTheme.BUTTON_HOVER,
                                           dropdown_fg_color=KanagawaTheme.DARKER_BG,
                                           dropdown_hover_color=KanagawaTheme.SELECTION)
        tab_size_dropdown.pack(fill="x", padx=10, pady=(5, 20))
        
        use_spaces_var = tk.BooleanVar(value=self.settings.use_spaces_for_tab)
        use_spaces_check = ctk.CTkCheckBox(tab_frame, text="Заменять табуляцию пробелами",
                                         variable=use_spaces_var, text_color=KanagawaTheme.FOREGROUND,
                                         fg_color=KanagawaTheme.BUTTON_BG,
                                         hover_color=KanagawaTheme.BUTTON_HOVER,
                                         checkbox_height=20, checkbox_width=20)
        use_spaces_check.pack(anchor="w", padx=10, pady=(10, 20))
        
        show_whitespace_var = tk.BooleanVar(value=self.settings.show_whitespace)
        show_whitespace_check = ctk.CTkCheckBox(tab_frame, text="Показывать символы пробелов",
                                              variable=show_whitespace_var, text_color=KanagawaTheme.FOREGROUND,
                                              fg_color=KanagawaTheme.BUTTON_BG,
                                              hover_color=KanagawaTheme.BUTTON_HOVER,
                                              checkbox_height=20, checkbox_width=20)
        show_whitespace_check.pack(anchor="w", padx=10, pady=(0, 20))
        
        # Содержимое вкладки Горячие клавиши
        hotkeys_frame = ctk.CTkFrame(hotkeys_tab, fg_color="transparent")
        hotkeys_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        hotkeys_label = ctk.CTkLabel(hotkeys_frame, text="Горячие клавиши:", text_color=KanagawaTheme.FOREGROUND)
        hotkeys_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # Создаем таблицу для отображения и редактирования горячих клавиш
        hotkeys_table = ctk.CTkFrame(hotkeys_frame, fg_color=KanagawaTheme.DARKER_BG)
        hotkeys_table.pack(fill="both", expand=True, padx=10, pady=(10, 20))
        
        # Заголовки таблицы
        header_frame = ctk.CTkFrame(hotkeys_table, fg_color="transparent", height=30)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        action_header = ctk.CTkLabel(header_frame, text="Действие", width=150, 
                                   text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        action_header.pack(side="left", padx=5)
        
        key_header = ctk.CTkLabel(header_frame, text="Клавиша", width=120,
                                text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        key_header.pack(side="left", padx=5)
        
        # Создаем переменные для хранения горячих клавиш
        hotkey_vars = {}
        
        # Функция для создания строки таблицы
        def create_hotkey_row(action, key, parent):
            row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=30)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # Перевод названия действия
            action_translations = {
                'run_code': 'Запуск кода',
                'save_file': 'Сохранить файл',
                'open_file': 'Открыть файл',
                'new_file': 'Новый файл',
                'find': 'Поиск',
                'toggle_console': 'Показать/скрыть консоль',
                'toggle_explorer': 'Показать/скрыть проводник'
            }
            
            action_name = action_translations.get(action, action)
            
            action_label = ctk.CTkLabel(row_frame, text=action_name, width=150,
                                      text_color=KanagawaTheme.FOREGROUND)
            action_label.pack(side="left", padx=5)
            
            key_var = tk.StringVar(value=key)
            hotkey_vars[action] = key_var
            
            key_entry = ctk.CTkEntry(row_frame, width=120, textvariable=key_var,
                                   fg_color=KanagawaTheme.LIGHTER_BG, 
                                   text_color=KanagawaTheme.FOREGROUND)
            key_entry.pack(side="left", padx=5)
            
            # Функция для захвата нажатия клавиш
            def capture_key(event):
                # Печатаем информацию о нажатой клавише для отладки
                print(f"Key pressed: {event.keysym}, State: {event.state}")
                
                # Если пользователь нажал Enter или Escape, снимаем фокус с поля ввода
                if event.keysym in ['Return', 'Escape']:
                    row_frame.focus_set()
                    return "break"
                
                # Если нажаты только модификаторы, игнорируем
                if event.keysym in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R']:
                    return "break"
                
                # Формируем новую комбинацию клавиш с нуля
                modifiers = []
                
                # Проверяем только реально нажатые модификаторы
                # state & 4 = Control, state & 1 = Shift, state & 8 = Alt
                if event.state & 4:
                    modifiers.append("Control")
                if event.state & 1:
                    modifiers.append("Shift")
                
                # Используем эвристику, чтобы определить, нажат ли Alt на самом деле
                # Во многих окружениях Alt может быть добавлен к event.state даже если не нажат
                real_alt_pressed = False
                
                # Alt на Windows обычно имеет state = 8 или содержит его
                if (event.state & 8) and event.keysym not in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']:
                    # Для функциональных клавиш не добавляем Alt автоматически
                    if event.state != 8:  # Только если есть другие модификаторы, считаем Alt реально нажатым
                        real_alt_pressed = True
                
                if real_alt_pressed:
                    modifiers.append("Alt")
                
                # Формируем окончательную строку комбинации клавиш
                if modifiers:
                    hotkey = "-".join(modifiers) + "-" + event.keysym
                else:
                    hotkey = event.keysym
                
                # Устанавливаем значение
                key_var.set(hotkey)
                
                return "break"
            
            key_entry.bind("<Key>", capture_key)
            key_entry.bind("<FocusIn>", lambda e: key_entry.delete(0, 'end'))
        
        # Создаем строки для каждой горячей клавиши
        for action, key in self.settings.hotkeys.items():
            create_hotkey_row(action, key, hotkeys_table)
        
        # Кнопки внизу окна
        button_frame = ctk.CTkFrame(settings_window, fg_color="transparent", height=40)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Функция для применения настроек
        def apply_settings():
            # Сохраняем настройки шрифта
            self.settings.font_size = int(float(font_size_var.get()))
            self.settings.font_family = font_var.get()
            
            # Сохраняем настройки табуляции
            self.settings.tab_size = int(tab_size_var.get())
            self.settings.use_spaces_for_tab = use_spaces_var.get()
            self.settings.show_whitespace = show_whitespace_var.get()
            
            # Сохраняем горячие клавиши
            for action, var in hotkey_vars.items():
                self.settings.hotkeys[action] = var.get()
            
            # Обновляем интерфейс
            self.apply_settings()
            
            # Закрываем окно настроек
            settings_window.destroy()
        
        # Кнопки
        apply_btn = ctk.CTkButton(button_frame, text="Применить", width=100,
                                 fg_color=KanagawaTheme.BUTTON_BG, 
                                 hover_color=KanagawaTheme.BUTTON_HOVER,
                                 text_color=KanagawaTheme.FOREGROUND,
                                 command=apply_settings)
        apply_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Отмена", width=100,
                                  fg_color=KanagawaTheme.BUTTON_BG, 
                                  hover_color=KanagawaTheme.BUTTON_HOVER,
                                  text_color=KanagawaTheme.FOREGROUND,
                                  command=settings_window.destroy)
        cancel_btn.pack(side="right", padx=5)
        
        # Автоматически выбираем нужную вкладку
        if section == "font":
            tab_view.set("Шрифт")
        elif section == "font_size":
            tab_view.set("Шрифт")
        elif section == "tab":
            tab_view.set("Табуляция")
        elif section == "hotkeys":
            tab_view.set("Горячие клавиши")
        elif section == "ai":
            tab_view.set("ИИ-ассистент")
        
        # Содержимое вкладки ИИ-ассистент
        ai_frame = ctk.CTkFrame(ai_tab, fg_color="transparent")
        ai_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        api_key_label = ctk.CTkLabel(ai_frame, text="API ключ OpenRouter:", 
                                   text_color=KanagawaTheme.FOREGROUND)
        api_key_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        api_key_var = tk.StringVar(value=self.settings.ai_api_key)
        api_key_entry = ctk.CTkEntry(ai_frame, textvariable=api_key_var, width=350,
                                  fg_color=KanagawaTheme.LIGHTER_BG, 
                                  text_color=KanagawaTheme.FOREGROUND,
                                  show="•")  # Скрываем ключ API
        api_key_entry.pack(fill="x", padx=10, pady=(5, 20))
        
        # Кнопка для отображения/скрытия ключа API
        show_key_state = tk.BooleanVar(value=False)
        
        def toggle_key_visibility():
            if show_key_state.get():
                api_key_entry.configure(show="")
            else:
                api_key_entry.configure(show="•")
        
        show_key_check = ctk.CTkCheckBox(ai_frame, text="Показать ключ",
                                       variable=show_key_state, text_color=KanagawaTheme.FOREGROUND,
                                       fg_color=KanagawaTheme.BUTTON_BG,
                                       hover_color=KanagawaTheme.BUTTON_HOVER,
                                       checkbox_height=20, checkbox_width=20,
                                       command=toggle_key_visibility)
        show_key_check.pack(anchor="w", padx=10, pady=(0, 20))
        
        initial_prompt_label = ctk.CTkLabel(ai_frame, text="Начальная инструкция для ИИ:", 
                                         text_color=KanagawaTheme.FOREGROUND)
        initial_prompt_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        initial_prompt_text = ctk.CTkTextbox(ai_frame, height=150,
                                          fg_color=KanagawaTheme.LIGHTER_BG,
                                          text_color=KanagawaTheme.FOREGROUND)
        initial_prompt_text.pack(fill="x", padx=10, pady=(5, 20))
        initial_prompt_text.insert("1.0", self.settings.ai_initial_prompt)
        
        ai_instructions = ctk.CTkLabel(ai_frame, text="Эта инструкция будет отправляться с первым запросом\nк нейросети в каждой сессии чата.", 
                                    text_color=KanagawaTheme.COMMENT,
                                    font=("Arial", 10))
        ai_instructions.pack(anchor="w", padx=10, pady=(0, 20))
        
        # Кнопки внизу окна
        button_frame = ctk.CTkFrame(settings_window, fg_color="transparent", height=40)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Функция для применения настроек
        def apply_settings():
            # Сохраняем настройки шрифта
            self.settings.font_size = int(float(font_size_var.get()))
            self.settings.font_family = font_var.get()
            
            # Сохраняем настройки табуляции
            self.settings.tab_size = int(tab_size_var.get())
            self.settings.use_spaces_for_tab = use_spaces_var.get()
            self.settings.show_whitespace = show_whitespace_var.get()
            
            # Сохраняем горячие клавиши
            for action, var in hotkey_vars.items():
                self.settings.hotkeys[action] = var.get()
            
            # Сохраняем настройки ИИ
            self.settings.ai_api_key = api_key_var.get()
            self.settings.ai_initial_prompt = initial_prompt_text.get("1.0", "end-1c")
            
            # Обновляем интерфейс
            self.apply_settings()
            
            # Закрываем окно настроек
            settings_window.destroy()
        
        # Кнопки
        apply_btn = ctk.CTkButton(button_frame, text="Применить", width=100,
                                 fg_color=KanagawaTheme.BUTTON_BG, 
                                 hover_color=KanagawaTheme.BUTTON_HOVER,
                                 text_color=KanagawaTheme.FOREGROUND,
                                 command=apply_settings)
        apply_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Отмена", width=100,
                                  fg_color=KanagawaTheme.BUTTON_BG, 
                                  hover_color=KanagawaTheme.BUTTON_HOVER,
                                  text_color=KanagawaTheme.FOREGROUND,
                                  command=settings_window.destroy)
        cancel_btn.pack(side="right", padx=5)
        
        # Автоматически выбираем нужную вкладку
        if section == "font":
            tab_view.set("Шрифт")
        elif section == "font_size":
            tab_view.set("Шрифт")
        elif section == "tab":
            tab_view.set("Табуляция")
        elif section == "hotkeys":
            tab_view.set("Горячие клавиши")
        elif section == "ai":
            tab_view.set("ИИ-ассистент")
    
    def apply_settings(self):
        """Применить настройки к редактору"""
        # Обновляем шрифт
        self.code_editor.configure(font=self.settings.get_font())
        self.line_numbers.configure(font=self.settings.get_font())
        self.console_output.configure(font=(self.settings.font_family, self.settings.font_size))
        self.chat_history.configure(font=(self.settings.font_family, self.settings.font_size))
        
        # Настройки табуляции
        self.code_editor.configure(tabs=self.settings.tab_size * 7)  # Примерное соответствие в пикселях
        
        # Привязываем горячие клавиши заново
        self.bind_hotkeys()
        
        # Показываем/скрываем пробелы
        self.show_whitespace(self.settings.show_whitespace)
        
        # Обновляем номера строк
        self.update_line_numbers()
    
    def save_settings(self):
        """Сохранить настройки в файл"""
        if self.settings.save_to_file():
            self.status_text.configure(text="Настройки сохранены")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки")
    
    def toggle_show_whitespace(self):
        """Переключить отображение пробелов"""
        self.settings.show_whitespace = not self.settings.show_whitespace
        self.show_whitespace(self.settings.show_whitespace)
    
    def show_whitespace(self, show=True):
        """Показать или скрыть пробелы"""
        # Сначала удаляем все существующие теги whitespace
        self.code_editor.tag_remove("whitespace", "1.0", tk.END)
        
        if show:
            # Находим все пробелы в тексте и применяем тег
            content = self.code_editor.get("1.0", tk.END)
            start_idx = "1.0"
            
            # Применяем тег только к выделенной строке
            # Получаем текущую позицию курсора
            current_line = int(float(self.code_editor.index(tk.INSERT)))
            line_start = f"{current_line}.0"
            line_end = f"{current_line}.end"
            
            # Получаем содержимое строки
            line_content = self.code_editor.get(line_start, line_end)
            
            # Ищем пробелы и добавляем тег
            for i, char in enumerate(line_content):
                if char == ' ':
                    self.code_editor.tag_add("whitespace", f"{current_line}.{i}", f"{current_line}.{i+1}")
    
    def handle_tab(self, event):
        """Обработка нажатия Tab"""
        # Получаем границы выделения
        try:
            sel_start = self.code_editor.index(tk.SEL_FIRST)
            sel_end = self.code_editor.index(tk.SEL_LAST)
            
            # Проверяем, охватывает ли выделение несколько строк
            start_line = int(sel_start.split('.')[0])
            end_line = int(sel_end.split('.')[0])
            
            if start_line != end_line:
                # Выделено несколько строк - добавляем отступ к каждой строке
                for line in range(start_line, end_line + 1):
                    line_start = f"{line}.0"
                    
                    # Добавляем табуляцию в начало строки
                    if self.settings.use_spaces_for_tab:
                        # Используем пробелы вместо табуляции
                        self.code_editor.insert(line_start, ' ' * self.settings.tab_size)
                    else:
                        # Используем символ табуляции
                        self.code_editor.insert(line_start, '\t')
                
                # Обновляем выделение
                new_sel_start = f"{start_line}.0"
                if self.code_editor.get(f"{end_line}.0", f"{end_line}.end") in ['\n', '']:
                    new_sel_end = f"{end_line}.0"
                else:
                    new_sel_end = f"{end_line}.end"
                
                self.code_editor.tag_remove(tk.SEL, "1.0", tk.END)
                self.code_editor.tag_add(tk.SEL, new_sel_start, new_sel_end)
                self.code_editor.mark_set(tk.INSERT, new_sel_end)
                
                return "break"  # Предотвращаем стандартное поведение Tab
            else:
                # Выделена одна строка или нет выделения
                if self.settings.use_spaces_for_tab:
                    # Вставляем пробелы вместо табуляции
                    self.code_editor.insert(tk.INSERT, ' ' * self.settings.tab_size)
                    return "break"
        except:
            # Нет выделения
            if self.settings.use_spaces_for_tab:
                # Вставляем пробелы вместо табуляции
                self.code_editor.insert(tk.INSERT, ' ' * self.settings.tab_size)
                return "break"
        
        # Возвращаем None для стандартной обработки табуляции
        return None
    
    def handle_shift_tab(self, event):
        """Обработка нажатия Shift+Tab"""
        try:
            # Получаем границы выделения
            sel_start = self.code_editor.index(tk.SEL_FIRST)
            sel_end = self.code_editor.index(tk.SEL_LAST)
            
            # Проверяем, охватывает ли выделение несколько строк
            start_line = int(sel_start.split('.')[0])
            end_line = int(sel_end.split('.')[0])
            
            # Уменьшаем отступ для каждой строки
            for line in range(start_line, end_line + 1):
                line_start = f"{line}.0"
                line_content = self.code_editor.get(line_start, f"{line}.end")
                
                # Проверяем начало строки
                if line_content.startswith('\t'):
                    # Удаляем табуляцию
                    self.code_editor.delete(line_start, f"{line}.1")
                elif line_content.startswith(' '):
                    # Удаляем пробелы (до self.settings.tab_size)
                    spaces_to_remove = min(sum(1 for c in line_content if c == ' ' and line_content.index(c) < self.settings.tab_size), 
                                         self.settings.tab_size)
                    if spaces_to_remove > 0:
                        self.code_editor.delete(line_start, f"{line}.{spaces_to_remove}")
            
            # Обновляем выделение
            new_sel_start = f"{start_line}.0"
            if self.code_editor.get(f"{end_line}.0", f"{end_line}.end") in ['\n', '']:
                new_sel_end = f"{end_line}.0"
            else:
                new_sel_end = f"{end_line}.end"
            
            self.code_editor.tag_remove(tk.SEL, "1.0", tk.END)
            self.code_editor.tag_add(tk.SEL, new_sel_start, new_sel_end)
            self.code_editor.mark_set(tk.INSERT, new_sel_end)
            
            return "break"
        except:
            # Нет выделения, пытаемся уменьшить отступ в текущей строке
            current_line = int(float(self.code_editor.index(tk.INSERT)))
            line_start = f"{current_line}.0"
            line_content = self.code_editor.get(line_start, f"{current_line}.end")
            
            if line_content.startswith('\t'):
                self.code_editor.delete(line_start, f"{current_line}.1")
            elif line_content.startswith(' '):
                spaces_to_remove = min(sum(1 for c in line_content if c == ' ' and line_content.index(c) < self.settings.tab_size), 
                                     self.settings.tab_size)
                if spaces_to_remove > 0:
                    self.code_editor.delete(line_start, f"{current_line}.{spaces_to_remove}")
            
            return "break"
    
    def bind_hotkeys(self):
        """Привязать горячие клавиши"""
        # Сначала удаляем все существующие привязки
        for action, key in self.settings.hotkeys.items():
            try:
                self.unbind_all(f"<{key}>")
            except:
                pass
        
        # Добавляем новые привязки
        for action, key in self.settings.hotkeys.items():
            if not key:  # Пропускаем пустые привязки
                continue
                
            if action == 'run_code':
                self.bind(f"<{key}>", lambda e: self.run_current_code())
            elif action == 'save_file':
                self.bind(f"<{key}>", lambda e: self.save_file())
            elif action == 'open_file':
                self.bind(f"<{key}>", lambda e: self.open_file())
            elif action == 'new_file':
                self.bind(f"<{key}>", lambda e: self.new_file())
            elif action == 'find':
                self.bind(f"<{key}>", lambda e: self.find_text())
            elif action == 'toggle_console':
                self.bind(f"<{key}>", lambda e: self.toggle_console())
            elif action == 'toggle_explorer':
                self.bind(f"<{key}>", lambda e: self.toggle_explorer())
    
    def find_text(self):
        """Функция поиска текста (заглушка)"""
        messagebox.showinfo("Поиск", "Функция поиска пока не реализована")
    
    def handle_return(self, event):
        """Обработка нажатия Enter для автоматической табуляции"""
        # Получаем текущую строку
        current_line_num = int(float(self.code_editor.index(tk.INSERT)))
        current_line = self.code_editor.get(f"{current_line_num}.0", f"{current_line_num}.end")
        
        # Проверяем, заканчивается ли строка на двоеточие (блок кода Python)
        if current_line.rstrip().endswith(':'):
            # Позволяем стандартной обработке Enter сначала сработать
            self.code_editor.after(1, lambda: self.add_auto_indent())
            return None  # Даем стандартной обработке выполниться
        
        # Если текущая строка имеет отступ, сохраняем его для новой строки
        indent_match = re.match(r'^(\s+)', current_line)
        if indent_match:
            indent = indent_match.group(1)
            # Позволяем стандартной обработке Enter сначала сработать
            self.code_editor.after(1, lambda indent=indent: self.preserve_indent(indent))
            
        return None  # Даем стандартной обработке выполниться
    
    def add_auto_indent(self):
        """Добавляет дополнительный отступ после двоеточия"""
        # Получаем номер новой строки (текущая позиция курсора после Enter)
        current_pos = self.code_editor.index(tk.INSERT)
        line_num = int(float(current_pos))
        
        # Получаем отступ предыдущей строки
        prev_line = self.code_editor.get(f"{line_num-1}.0", f"{line_num-1}.end")
        indent_match = re.match(r'^(\s+)', prev_line)
        
        if indent_match:
            # Используем тот же отступ плюс дополнительную табуляцию
            base_indent = indent_match.group(1)
        else:
            base_indent = ""
            
        # Добавляем отступ в начало новой строки
        if self.settings.use_spaces_for_tab:
            # Используем пробелы для табуляции
            additional_indent = " " * self.settings.tab_size
        else:
            # Используем символ табуляции
            additional_indent = "\t"
            
        # Вставляем дополнительный отступ (стандартный отступ уже добавлен Enter)
        self.code_editor.insert(f"{line_num}.0", additional_indent)
    
    def preserve_indent(self, indent):
        """Сохраняет отступ при переходе на новую строку"""
        # Получаем номер новой строки (текущая позиция курсора после Enter)
        current_pos = self.code_editor.index(tk.INSERT)
        line_num = int(float(current_pos))
        
        # Вставляем отступ в начало новой строки
        self.code_editor.insert(f"{line_num}.0", indent)
    
    def on_text_change(self, event=None):
        """Обработчик изменения текста в редакторе"""
        self.update_line_numbers()
        self.highlight_syntax()
        self.highlight_current_line()
        self.update_cursor_position()
        
        # Показываем пробелы в текущей строке, если включено
        if self.settings.show_whitespace:
            self.show_whitespace(True)
    
    def _generate_offline_response(self, message):
        """Генерирует простые ответы в офлайн-режиме"""
        # Словарь с простыми ответами на частые вопросы
        responses = {
            "привет": "Привет! Я офлайн-версия ассистента. Интернет-соединение недоступно, поэтому я могу отвечать только на базовые вопросы.",
            "как дела": "Я работаю в офлайн-режиме. Интернет-соединение недоступно.",
            "что ты умеешь": "Обычно я помогаю с кодом, но сейчас я работаю в офлайн-режиме с ограниченной функциональностью из-за отсутствия интернета.",
            "помоги": "Я хотел бы помочь, но сейчас я работаю в офлайн-режиме. Проверьте подключение к интернету.",
            "python": "Python - популярный язык программирования. Сейчас я работаю в офлайн-режиме и не могу дать подробную информацию.",
        }
        
        # Преобразуем сообщение в нижний регистр для поиска ключевых слов
        message_lower = message.lower()
        
        # Ищем совпадения с ключевыми словами
        response = None
        for key, value in responses.items():
            if key in message_lower:
                response = value
                break
        
        # Если нет совпадений, используем стандартный ответ
        if not response:
            response = "Извините, я сейчас работаю в офлайн-режиме из-за отсутствия подключения к интернету. Пожалуйста, проверьте ваше соединение с интернетом."
        
        # Имитируем задержку для правдоподобности
        time.sleep(1)
        
        # Добавляем ответ в историю
        self.chat_messages.append({"role": "assistant", "content": response})
        
        # Обновляем интерфейс
        self._update_ai_response(response)
    
    def _handle_file_read_request(self, file_path):
        """Обрабатывает запрос на чтение файла от ассистента"""
        try:
            # Нормализуем путь - проверяем абсолютный или относительный
            if not os.path.isabs(file_path):
                if self.current_project:
                    file_path = os.path.join(self.current_project, file_path)
                else:
                    # Если нет текущего проекта, используем каталог запуска
                    file_path = os.path.join(os.getcwd(), file_path)
            
            print(f"Обрабатываем запрос на чтение файла: {file_path}")
            
            # Добавляем сообщение о чтении файла в историю чата
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, f"👀 Читаю файл: {os.path.basename(file_path)}...\n\n", "system")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
            
            # Проверка существования файла
            if not os.path.exists(file_path):
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"❌ Ошибка: Файл '{file_path}' не найден.\n\n", "error")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                return
            
            # Лимит на размер файла (например, 1 МБ)
            max_file_size = 1024 * 1024
            if os.path.getsize(file_path) > max_file_size:
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"❌ Ошибка: Файл '{file_path}' слишком большой для чтения (> 1 МБ).\n\n", "error")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                return
            
            # Читаем содержимое файла
            try:
                content = read_file_handler.read_file_content(file_path, max_file_size)
                print(f"Файл успешно прочитан: {len(content)} символов")
                
                # Показываем в истории успешное чтение
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"✅ Файл успешно прочитан: {len(content)} символов\n\n", "success")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
            except Exception as e:
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"❌ Ошибка при чтении файла: {str(e)}\n\n", "error")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                return
            
            # Формируем новый запрос с содержимым файла
            message = f"Содержимое файла '{file_path}':\n\n```\n{content}\n```\n\nПродолжи выполнение предыдущего запроса с учетом этого файла."
            
            # Сохраняем в историю чата
            self.chat_messages.append({"role": "user", "content": message})
            
            # Устанавливаем флаг активной генерации
            self.is_generating = True
            
            # Запускаем генерацию ответа в отдельном потоке
            self.generation_thread = threading.Thread(target=self._generate_ai_response)
            self.generation_thread.daemon = True
            self.generation_thread.start()
            
        except Exception as e:
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, f"❌ Ошибка при обработке запроса на чтение файла: {str(e)}\n\n", "error")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
    
    def _handle_replace_file_request(self, file_path, content):
        """Обрабатывает запрос на замену содержимого файла"""
        try:
            # Нормализуем путь - проверяем абсолютный или относительный
            if not os.path.isabs(file_path):
                if self.current_project:
                    file_path = os.path.join(self.current_project, file_path)
                else:
                    # Если нет текущего проекта, используем каталог запуска
                    file_path = os.path.join(os.getcwd(), file_path)
            
            print(f"Обрабатываем запрос на замену файла: {file_path}")
            
            # Добавляем сообщение о замене файла в историю чата
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, f"📝 Заменяю содержимое файла: {os.path.basename(file_path)}...\n\n", "system")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
            
            # Сохраняем содержимое в файл
            try:
                # Проверяем существование файла
                file_exists = os.path.exists(file_path)
                old_content = ""
                
                if file_exists:
                    # Если файл существует, читаем его содержимое для сравнения
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                
                # Создаем директории при необходимости
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # Используем диалог предварительного просмотра, если файл существует и содержимое различается
                if file_exists and old_content != content:
                    try:
                        import code_review
                        
                        # Функция для принятия изменений
                        def accept_changes(new_content):
                            # Записываем содержимое в файл
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(new_content)
                            
                            # Показываем сообщение об успешной замене
                            self.chat_history.configure(state="normal")
                            self.chat_history.insert(tk.END, f"✅ Файл успешно обновлен: {os.path.basename(file_path)}\n\n", "success")
                            
                            # Если это текущий открытый файл, обновляем его в редакторе
                            if self.current_file and os.path.abspath(self.current_file) == os.path.abspath(file_path):
                                # При загрузке перейти на начало файла для лучшего обзора изменений
                                self.load_file(self.current_file, goto_line=1)
                                self.chat_history.insert(tk.END, "📄 Содержимое редактора обновлено\n\n", "info")
                            
                            self.chat_history.see(tk.END)
                            self.chat_history.configure(state="disabled")
                            
                            # Формируем сообщение об успешной замене для нейросети
                            message = f"Файл {file_path} успешно обновлен."
                            
                            # Добавляем в историю чата сообщение для продолжения диалога
                            self.chat_messages.append({"role": "user", "content": message})
                            
                            # Запускаем генерацию ответа в отдельном потоке
                            self.is_generating = True
                            self.generation_thread = threading.Thread(target=self._generate_ai_response)
                            self.generation_thread.daemon = True
                            self.generation_thread.start()
                        
                        # Функция для отказа от изменений
                        def reject_changes():
                            self.chat_history.configure(state="normal")
                            self.chat_history.insert(tk.END, f"❌ Изменения отклонены пользователем\n\n", "error")
                            self.chat_history.see(tk.END)
                            self.chat_history.configure(state="disabled")
                            
                            # Формируем сообщение об отказе для нейросети
                            message = f"Изменения в файле {file_path} были отклонены пользователем."
                            
                            # Добавляем в историю чата сообщение для продолжения диалога
                            self.chat_messages.append({"role": "user", "content": message})
                            
                            # Запускаем генерацию ответа в отдельном потоке
                            self.is_generating = True
                            self.generation_thread = threading.Thread(target=self._generate_ai_response)
                            self.generation_thread.daemon = True
                            self.generation_thread.start()
                        
                        # Показываем диалог предварительного просмотра
                        code_review.show_code_review(
                            self, 
                            file_path, 
                            old_content, 
                            content, 
                            line_num=None, 
                            on_accept=accept_changes, 
                            on_reject=reject_changes,
                            theme=self.theme
                        )
                        
                        # Возвращаемся, т.к. дальнейшая обработка будет в callback-функциях
                        return
                    except ImportError:
                        # Если модуль code_review не доступен, используем стандартное поведение
                        pass
                
                # Стандартное поведение без предварительного просмотра 
                # (для новых файлов или если модуль code_review недоступен)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Показываем сообщение об успешной замене
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"✅ Файл успешно обновлен: {os.path.basename(file_path)}\n\n", "success")
                
                # Если это текущий открытый файл, обновляем его в редакторе
                if self.current_file and os.path.abspath(self.current_file) == os.path.abspath(file_path):
                    self.code_editor.delete("1.0", tk.END)
                    self.code_editor.insert("1.0", content)
                    self.highlight_syntax()
                    self.update_line_numbers()
                    self.chat_history.insert(tk.END, "📄 Содержимое редактора обновлено\n\n", "info")
                
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                
                # Формируем сообщение об успешной замене для нейросети
                message = f"Файл {file_path} успешно обновлен."
                
                # Добавляем в историю чата сообщение для продолжения диалога
                self.chat_messages.append({"role": "user", "content": message})
                
                # Запускаем генерацию ответа в отдельном потоке
                self.is_generating = True
                self.generation_thread = threading.Thread(target=self._generate_ai_response)
                self.generation_thread.daemon = True
                self.generation_thread.start()
                
            except Exception as e:
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, f"❌ Ошибка при записи файла: {str(e)}\n\n", "error")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
                return
            
        except Exception as e:
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, f"❌ Ошибка при обработке запроса на замену файла: {str(e)}\n\n", "error")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
    
    def show_plugins_dialog(self):
        """Показать диалог управления плагинами"""
        plugins_window = ctk.CTkToplevel(self)
        plugins_window.title("Управление плагинами")
        plugins_window.geometry("600x500")
        plugins_window.focus_set()
        plugins_window.resizable(False, False)
        plugins_window.configure(fg_color=self.theme.BACKGROUND)
        
        # Хак для Windows, чтобы сделать окно модальным
        plugins_window.grab_set()
        
        # Заголовок
        header_label = ctk.CTkLabel(plugins_window, text="Управление плагинами",
                                   font=("Arial", 16, "bold"), text_color=self.theme.FOREGROUND)
        header_label.pack(pady=(20, 10))
        
        # Фрейм для списка плагинов
        plugins_frame = ctk.CTkFrame(plugins_window, fg_color=self.theme.DARKER_BG)
        plugins_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Получаем информацию о плагинах
        plugins_info = self.plugin_manager.get_plugin_info()
        
        # Переменная для хранения выбранного плагина
        selected_plugin = tk.StringVar()
        
        if not plugins_info:
            # Если нет плагинов, показываем сообщение
            no_plugins_label = ctk.CTkLabel(
                plugins_frame, 
                text="Нет доступных плагинов", 
                text_color=self.theme.FOREGROUND
            )
            no_plugins_label.pack(pady=50)
        else:
            # Создаем заголовок таблицы
            header_frame = ctk.CTkFrame(plugins_frame, fg_color="transparent", height=30)
            header_frame.pack(fill="x", padx=5, pady=5)
            
            select_header = ctk.CTkLabel(header_frame, text="Выбор", width=40, 
                                      text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            select_header.pack(side="left", padx=5)
            
            name_header = ctk.CTkLabel(header_frame, text="Название", width=120, 
                                     text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            name_header.pack(side="left", padx=5)
            
            version_header = ctk.CTkLabel(header_frame, text="Версия", width=60,
                                       text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            version_header.pack(side="left", padx=5)
            
            author_header = ctk.CTkLabel(header_frame, text="Автор", width=100,
                                      text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            author_header.pack(side="left", padx=5)
            
            desc_header = ctk.CTkLabel(header_frame, text="Описание", width=160,
                                    text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            desc_header.pack(side="left", padx=5)
            
            status_header = ctk.CTkLabel(header_frame, text="Статус", width=60,
                                      text_color=self.theme.FOREGROUND, font=("Arial", 10, "bold"))
            status_header.pack(side="left", padx=5)
            
            # Создаем скроллируемый фрейм для списка плагинов
            plugins_scroll_frame = ctk.CTkScrollableFrame(plugins_frame, fg_color="transparent")
            plugins_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Выводим список плагинов
            for plugin_info in plugins_info:
                plugin_frame = ctk.CTkFrame(plugins_scroll_frame, fg_color=self.theme.LIGHTER_BG, 
                                         corner_radius=5, height=40)
                plugin_frame.pack(fill="x", padx=5, pady=5)
                
                # Радиокнопка для выбора плагина
                select_radio = ctk.CTkRadioButton(
                    plugin_frame,
                    text="",
                    variable=selected_plugin,
                    value=plugin_info["name"],
                    radiobutton_height=16,
                    radiobutton_width=16,
                    fg_color=self.theme.SELECTION,
                    border_color=self.theme.FOREGROUND
                )
                select_radio.pack(side="left", padx=15)
                
                name_label = ctk.CTkLabel(plugin_frame, text=plugin_info["name"], width=120, 
                                       text_color=self.theme.FOREGROUND)
                name_label.pack(side="left", padx=5, pady=5)
                
                version_label = ctk.CTkLabel(plugin_frame, text=plugin_info["version"], width=60,
                                          text_color=self.theme.FOREGROUND)
                version_label.pack(side="left", padx=5, pady=5)
                
                author_label = ctk.CTkLabel(plugin_frame, text=plugin_info["author"], width=100,
                                         text_color=self.theme.FOREGROUND)
                author_label.pack(side="left", padx=5, pady=5)
                
                desc_label = ctk.CTkLabel(plugin_frame, text=plugin_info["description"], width=160,
                                       text_color=self.theme.FOREGROUND)
                desc_label.pack(side="left", padx=5, pady=5)
                
                # Индикатор состояния плагина
                status_color = self.theme.CONSOLE_SUCCESS if plugin_info["active"] else self.theme.COMMENT
                status_text = "Активен" if plugin_info["active"] else "Неактивен"
                
                status_label = ctk.CTkLabel(
                    plugin_frame, 
                    text=status_text, 
                    width=60,
                    text_color=status_color
                )
                status_label.pack(side="left", padx=5, pady=5)
            
            # Устанавливаем первый плагин как выбранный по умолчанию, если есть плагины
            if plugins_info:
                selected_plugin.set(plugins_info[0]["name"])
        
        # Фрейм для кнопок действий с плагинами
        actions_frame = ctk.CTkFrame(plugins_window, fg_color="transparent", height=40)
        actions_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        # Функции для действий с плагинами
        def enable_selected_plugin():
            plugin_name = selected_plugin.get()
            if plugin_name:
                result = self.plugin_manager.activate_plugin(plugin_name)
                if result:
                    messagebox.showinfo("Активация плагина", f"Плагин {plugin_name} успешно активирован")
                    # Перезагружаем диалог, чтобы обновить статусы
                    plugins_window.destroy()
                    self.show_plugins_dialog()
                else:
                    messagebox.showerror("Ошибка", f"Не удалось активировать плагин {plugin_name}")
        
        def disable_selected_plugin():
            plugin_name = selected_plugin.get()
            if plugin_name:
                result = self.plugin_manager.deactivate_plugin(plugin_name)
                if result:
                    messagebox.showinfo("Деактивация плагина", f"Плагин {plugin_name} успешно деактивирован")
                    # Перезагружаем диалог, чтобы обновить статусы
                    plugins_window.destroy()
                    self.show_plugins_dialog()
                else:
                    messagebox.showerror("Ошибка", f"Не удалось деактивировать плагин {plugin_name}")
        
        def delete_selected_plugin():
            plugin_name = selected_plugin.get()
            if plugin_name:
                # Запрашиваем подтверждение
                if messagebox.askyesno("Удаление плагина", 
                                     f"Вы уверены, что хотите удалить плагин {plugin_name}? Это действие нельзя отменить."):
                    # Деактивируем плагин перед удалением
                    if plugin_name in self.plugin_manager.active_plugins:
                        self.plugin_manager.deactivate_plugin(plugin_name)
                    
                    # Удаляем из словаря плагинов
                    if plugin_name in self.plugin_manager.plugins:
                        del self.plugin_manager.plugins[plugin_name]
                        messagebox.showinfo("Удаление плагина", f"Плагин {plugin_name} удален из списка")
                        # Перезагружаем диалог
                        plugins_window.destroy()
                        self.show_plugins_dialog()
        
        # Кнопки действий
        enable_btn = ctk.CTkButton(
            actions_frame,
            text="Включить",
            width=100,
            fg_color=self.theme.CONSOLE_SUCCESS,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.BACKGROUND,
            command=enable_selected_plugin
        )
        enable_btn.pack(side="left", padx=5)
        
        disable_btn = ctk.CTkButton(
            actions_frame,
            text="Отключить",
            width=100,
            fg_color=self.theme.COMMENT,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.BACKGROUND,
            command=disable_selected_plugin
        )
        disable_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="Удалить",
            width=100,
            fg_color=self.theme.CONSOLE_ERROR,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.FOREGROUND,
            command=delete_selected_plugin
        )
        delete_btn.pack(side="left", padx=5)
        
        # Кнопки внизу диалога
        button_frame = ctk.CTkFrame(plugins_window, fg_color="transparent", height=40)
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        refresh_btn = ctk.CTkButton(
            button_frame, 
            text="Обновить", 
            width=100,
            fg_color=self.theme.BUTTON_BG,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.FOREGROUND,
            command=lambda: (self.plugin_manager.load_plugins(), plugins_window.destroy(), self.show_plugins_dialog())
        )
        refresh_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            button_frame, 
            text="Закрыть", 
            width=100,
            fg_color=self.theme.BUTTON_BG,
            hover_color=self.theme.BUTTON_HOVER,
            text_color=self.theme.FOREGROUND,
            command=plugins_window.destroy
        )
        close_btn.pack(side="right", padx=5)
    
    def toggle_plugin(self, plugin_name, current_state):
        """Переключает состояние плагина между активным и неактивным"""
        if current_state:
            result = self.plugin_manager.deactivate_plugin(plugin_name)
            message = f"Плагин {plugin_name} деактивирован" if result else f"Ошибка при деактивации плагина {plugin_name}"
        else:
            result = self.plugin_manager.activate_plugin(plugin_name)
            message = f"Плагин {plugin_name} активирован" if result else f"Ошибка при активации плагина {plugin_name}"
            
        # Отображаем сообщение в строке состояния
        self.status_text.configure(text=message)

if __name__ == "__main__":
    app = CodeEditor()
    app.mainloop()





