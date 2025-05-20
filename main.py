"""
Главный модуль редактора кода.
"""

import os
import sys
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import re
import requests
import json

# Импортируем собственные модули
from theme import KanagawaTheme
from settings import EditorSettings
from system_utils import maximize_window, minimize_window, restore_window, is_window_maximized, setup_dpi_awareness, execute_code
from code_utils import get_language_from_file, simulate_line_replacement, simulate_range_replacement
from editor import CodeEditor
from terminal import Terminal
from file_explorer import FileExplorer
from ui import MenuBuilder, DialogBuilder, TitleBar
from ai_chat import AiChat

# Импортируем настройки ИИ по умолчанию
from ai_defaults import DEFAULT_AI_PROMPT, DEFAULT_API_SETTINGS, CODE_BLOCK_PATTERN, READ_FILE_PATTERN

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

# Настройка DPI для Windows
setup_dpi_awareness()

class CodeEditorApp(ctk.CTk):
    """Главный класс приложения редактора кода"""
    
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
        
        # Переменные для перетаскивания окна
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._dragging = False
        
        # Переменные для хранения текущего файла
        self.current_file = None
        
        # Для процесса выполнения кода
        self.process = None
        self.stop_thread = False
        
        # Для чтения вывода консоли
        self.shell_output_queue = None
        self.shell_input_queue = None
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Инициализация плагинов
        self.plugin_manager = PluginManager(self)
        self._activate_plugins()
        
        # Настройка горячих клавиш
        self.bind_hotkeys()
    
    def _activate_plugins(self):
        """Активирует плагины"""
        self.plugin_manager.load_plugins()
        self.plugin_manager.activate_all()
    
    def setup_ui(self):
        """Настройка интерфейса пользователя"""
        # Основной контейнер
        self.main_container = ctk.CTkFrame(self, fg_color=self.theme.BACKGROUND)
        self.main_container.pack(fill="both", expand=True)
        
        # Создаем заголовок окна
        title_bar = ctk.CTkFrame(self.main_container)
        title_bar.pack(fill="x", pady=0)
        self.title_bar = TitleBar(self, title_bar)
        
        # Создаем меню
        self.menu_builder = MenuBuilder(self)
        
        # Показываем статус внизу основного контейнера
        self.status_bar = ctk.CTkFrame(self.main_container, height=25, fg_color=self.theme.DARKER_BG)
        self.status_bar.pack(side="bottom", fill="x")
        
        # Информация о текущей позиции курсора
        self.cursor_position_label = ctk.CTkLabel(
            self.status_bar, 
            text="Строка: 1, Столбец: 0", 
            text_color=self.theme.FOREGROUND, 
            font=("Arial", 10)
        )
        self.cursor_position_label.pack(side="right", padx=10)
        
        # Информация о текущем файле
        self.file_info_label = ctk.CTkLabel(
            self.status_bar, 
            text="Новый файл", 
            text_color=self.theme.FOREGROUND, 
            font=("Arial", 10)
        )
        self.file_info_label.pack(side="left", padx=10)
        
        # Создаем контейнер для центрального содержимого
        self.center_container = ctk.CTkFrame(self.main_container, fg_color=self.theme.BACKGROUND)
        self.center_container.pack(fill="both", expand=True)
        
        # Панель для кнопок инструментов редактора (слева)
        self.tools_frame = ctk.CTkFrame(self.center_container, width=50, fg_color=self.theme.DARKER_BG)
        self.tools_frame.pack(side="left", fill="y", padx=(0, 0), pady=0)
        self.tools_frame.pack_propagate(False)  # Фиксированная ширина
        
        # Добавляем основные кнопки редактора
        self.create_editor_buttons()
        
        # Панель для проводника файлов (слева от редактора)
        self.explorer_frame = ctk.CTkFrame(self.center_container, width=200, fg_color=self.theme.BACKGROUND)
        self.explorer_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.explorer_frame.pack_propagate(False)  # Фиксированная ширина
        self.file_explorer = FileExplorer(self, self.explorer_frame)
        
        # Панель для AI чата (правая сторона)
        self.ai_chat_frame = ctk.CTkFrame(self.center_container, width=350, fg_color=self.theme.AI_BG)
        # По умолчанию AI чат скрыт
        self.ai_chat = AiChat(self, self.ai_chat_frame)
        
        # Контейнер для редактора и консоли (центр)
        self.editor_console_container = ctk.CTkFrame(self.center_container, fg_color=self.theme.BACKGROUND)
        self.editor_console_container.pack(side="left", fill="both", expand=True)
        
        # Панель для редактора кода
        self.editor_frame = ctk.CTkFrame(self.editor_console_container, fg_color=self.theme.BACKGROUND)
        self.editor_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.text_editor = CodeEditor(self, self.editor_frame)
        
        # Панель для консоли (внизу редактора)
        self.console_frame = ctk.CTkFrame(self.editor_console_container, height=150, fg_color=self.theme.CONSOLE_BG)
        self.terminal = Terminal(self, self.console_frame)
        
        # По умолчанию проводник показан, консоль и AI чат скрыты
        self.console_frame.pack_forget()
        self.ai_chat_frame.pack_forget()
        
        # Применяем настройки
        self.apply_settings()
    
    def start_window_drag(self, event):
        """Начинаем перетаскивание окна"""
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._dragging = True
    
    def stop_window_drag(self, event):
        """Останавливаем перетаскивание окна"""
        self._dragging = False
    
    def on_window_drag(self, event):
        """Обрабатываем перетаскивание окна"""
        if self._dragging:
            dx = event.x_root - self._drag_start_x
            dy = event.y_root - self._drag_start_y
            x = self.winfo_x() + dx
            y = self.winfo_y() + dy
            self.geometry(f"+{x}+{y}")
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
    
    def toggle_maximize(self):
        """Переключает максимизацию окна"""
        if os.name == 'nt':
            hwnd = ctk.windll.user32.GetParent(self.winfo_id())
            if is_window_maximized(hwnd):
                restore_window(hwnd)
            else:
                maximize_window(hwnd)
    
    def minimize(self):
        """Минимизирует окно"""
        if os.name == 'nt':
            hwnd = ctk.windll.user32.GetParent(self.winfo_id())
            minimize_window(hwnd)
        else:
            self.wm_iconify()
    
    def show_file_menu(self):
        """Показывает меню файла"""
        file_menu = self.menu_builder.create_file_menu()
        x = self.winfo_x() + 60
        y = self.winfo_y() + 30
        file_menu.post(x, y)
    
    def show_edit_menu(self):
        """Показывает меню редактирования"""
        edit_menu = self.menu_builder.create_edit_menu()
        x = self.winfo_x() + 120
        y = self.winfo_y() + 30
        edit_menu.post(x, y)
    
    def show_view_menu(self):
        """Показывает меню вида"""
        view_menu = self.menu_builder.create_view_menu()
        x = self.winfo_x() + 180
        y = self.winfo_y() + 30
        view_menu.post(x, y)
    
    def show_run_menu(self):
        """Показывает меню запуска"""
        run_menu = self.menu_builder.create_run_menu()
        x = self.winfo_x() + 240
        y = self.winfo_y() + 30
        run_menu.post(x, y)
    
    def show_settings_menu(self):
        """Показывает меню настроек"""
        settings_menu = self.menu_builder.create_settings_menu()
        x = self.winfo_x() + 310
        y = self.winfo_y() + 30
        settings_menu.post(x, y)
    
    def new_file(self):
        """Создает новый файл"""
        self.text_editor.set_current_file(None)
        self.text_editor.set_text("")
        self.current_file = None
        self.file_info_label.configure(text="Новый файл")
    
    def save_file_as(self):
        """Сохраняет файл с новым именем"""
        file_path = DialogBuilder.create_file_save_dialog(self)
        if file_path:
            # Добавляем расширение .py, если не указано другое
            if not os.path.splitext(file_path)[1]:
                file_path += '.py'
            
            # Сохраняем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_editor.get_text())
            
            self.text_editor.set_current_file(file_path)
            self.current_file = file_path
            
            # Обновляем заголовок окна и статус
            self.title(f"vpycode - {os.path.basename(file_path)}")
            self.file_info_label.configure(text=f"{os.path.basename(file_path)}")
            
            return True
        return False
    
    def save_file(self):
        """Сохраняет текущий файл"""
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.text_editor.get_text())
            return True
        else:
            return self.save_file_as()
    
    def open_file(self):
        """Открывает файл"""
        file_path = DialogBuilder.create_file_open_dialog(self)
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path, goto_line=None):
        """Загружает файл в редактор"""
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл {file_path} не существует")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.text_editor.set_current_file(file_path)
            self.text_editor.set_text(content)
            self.current_file = file_path
            
            # Обновляем заголовок окна и статус
            self.title(f"vpycode - {os.path.basename(file_path)}")
            self.file_info_label.configure(text=f"{os.path.basename(file_path)}")
            
            # Если указан номер строки, перемещаем курсор
            if goto_line:
                self.text_editor.text.mark_set(tk.INSERT, f"{goto_line}.0")
                self.text_editor.text.see(f"{goto_line}.0")
                self.text_editor._highlight_current_line()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def open_project(self):
        """Открывает проект (директорию)"""
        project_path = DialogBuilder.create_folder_select_dialog(self)
        if project_path:
            self.file_explorer.update_tree(project_path)
    
    def toggle_explorer(self):
        """Переключает видимость проводника файлов"""
        if self.explorer_frame.winfo_viewable():
            self.explorer_frame.pack_forget()
        else:
            # Показываем проводник справа от панели инструментов
            self.tools_frame.pack(side="left", fill="y", padx=(0, 0), pady=0)
            self.explorer_frame.pack(side="left", fill="y", padx=0, pady=0)
    
    def toggle_console(self):
        """Переключает видимость консоли"""
        if self.console_frame.winfo_manager():
            self.console_frame.pack_forget()
        else:
            # Устанавливаем размер консоли
            self.console_frame.configure(height=150)
            # Показываем консоль без указания высоты в pack
            self.console_frame.pack(fill="both", side="bottom", padx=0, pady=0, expand=False)
    
    def toggle_ai_chat(self):
        """Переключает видимость ИИ ассистента"""
        if self.ai_chat_frame.winfo_viewable():
            self.ai_chat_frame.pack_forget()
        else:
            # Размещаем AI чат в правой части окна
            self.ai_chat_frame.pack(side="right", fill="y", padx=0, pady=0, expand=False, width=350)
    
    def run_current_code(self):
        """Запускает текущий код"""
        # Сохраняем файл перед запуском
        if not self.save_file():
            return
        
        # Получаем язык программирования по расширению файла
        language = get_language_from_file(self.current_file)
        
        # Если язык поддерживается напрямую, запускаем
        if language in self.language_handlers:
            handler = self.language_handlers[language]
            if "run_command" in handler:
                handler["run_command"](self.current_file)
        else:
            # Для неподдерживаемых языков показываем диалог выбора плагина
            self.show_debugger_selection_dialog(self.current_file, os.path.splitext(self.current_file)[1])
    
    def run_python_code(self, file_path):
        """Запускает Python код"""
        # Очищаем консоль
        self.terminal.clear()
        
        # Показываем консоль
        if not self.console_frame.winfo_manager():
            self.toggle_console()
        
        # Запускаем процесс
        self.terminal.run_command(f"python {file_path}")
    
    def run_code_in_external_console(self):
        """Запускает код во внешней консоли"""
        if not self.save_file():
            return
        
        if os.name == 'nt':
            # Windows - используем cmd
            cmd = f'start cmd /K python "{self.current_file}"'
        else:
            # Unix - используем терминал
            cmd = f'xterm -e "python {self.current_file}; read -n 1 -s -p \'Нажмите любую клавишу для закрытия...\'"'
        
        try:
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить внешнюю консоль: {str(e)}")
    
    def show_debugger_selection_dialog(self, file_path, file_extension):
        """Показывает диалог выбора плагина для запуска кода"""
        # Получаем доступные плагины
        plugins = self.plugin_manager.get_plugins_for_extension(file_extension)
        
        if not plugins:
            messagebox.showinfo("Информация", f"Нет доступных плагинов для файлов с расширением {file_extension}")
            return
        
        # Создаем диалог выбора плагина
        dialog = ctk.CTkToplevel(self)
        dialog.title("Выбор плагина")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Делаем диалог модальным
        dialog.focus_set()
        
        # Заголовок
        header_label = ctk.CTkLabel(
            dialog, 
            text=f"Выберите плагин для запуска файла {os.path.basename(file_path)}", 
            font=("Arial", 12, "bold")
        )
        header_label.pack(pady=10)
        
        # Фрейм для списка плагинов
        plugins_frame = ctk.CTkFrame(dialog)
        plugins_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Переменная для хранения выбранного плагина
        selected_plugin = tk.StringVar()
        
        # Добавляем опции
        for i, plugin in enumerate(plugins):
            rb = ctk.CTkRadioButton(
                plugins_frame, 
                text=f"{plugin.name} - {plugin.description}", 
                variable=selected_plugin, 
                value=plugin.name
            )
            rb.pack(anchor="w", pady=5, padx=10)
            
            # По умолчанию выбираем первый плагин
            if i == 0:
                rb.select()
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Функция для запуска выбранного плагина
        def run_with_selected_plugin():
            plugin_name = selected_plugin.get()
            plugin = self.plugin_manager.get_plugin_by_name(plugin_name)
            if plugin:
                dialog.destroy()
                self.run_with_plugin(plugin, file_path, file_extension)
        
        # Кнопка запуска
        run_btn = ctk.CTkButton(
            buttons_frame, 
            text="Запустить", 
            command=run_with_selected_plugin
        )
        run_btn.pack(side="right", padx=5)
        
        # Кнопка отмены
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Отмена", 
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=5)
    
    def run_with_plugin(self, plugin, file_path, file_extension):
        """Запускает код с помощью плагина"""
        # Очищаем консоль
        self.terminal.clear()
        
        # Показываем консоль
        if not self.console_frame.winfo_manager():
            self.toggle_console()
        
        try:
            # Запускаем код с помощью плагина
            plugin.run(file_path, self)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при запуске плагина {plugin.name}: {str(e)}")
    
    def stop_execution(self):
        """Останавливает выполнение кода"""
        self.terminal.stop_command()
    
    def clear_console(self):
        """Очищает консоль"""
        self.terminal.clear()
    
    def apply_settings(self):
        """Применяет настройки к редактору"""
        # Настраиваем шрифт в редакторе
        font = self.settings.get_font()
        self.text_editor.text.configure(font=font)
        self.text_editor.line_numbers.configure(font=font)
        
        # Настраиваем отображение пробелов
        self.show_whitespace(self.settings.show_whitespace)
    
    def apply_theme(self):
        """Применяет текущую тему к интерфейсу"""
        try:
            # Основные цвета
            self.configure(fg_color=self.theme.BACKGROUND)
            
            # Обновляем цвета для панелей
            self.tools_frame.configure(fg_color=self.theme.DARKER_BG)
            self.explorer_frame.configure(fg_color=self.theme.BACKGROUND)
            self.editor_console_container.configure(fg_color=self.theme.BACKGROUND)
            self.editor_frame.configure(fg_color=self.theme.BACKGROUND)
            self.console_frame.configure(fg_color=self.theme.CONSOLE_BG)
            self.ai_chat_frame.configure(fg_color=self.theme.AI_BG)
            
            # Обновляем цвета для текстового редактора
            self.text_editor.apply_theme(self.theme)
            
            # Обновляем цвета для статус-бара
            self.status_bar.configure(fg_color=self.theme.DARKER_BG)
            self.cursor_position_label.configure(text_color=self.theme.FOREGROUND)
            self.file_info_label.configure(text_color=self.theme.FOREGROUND)
            
            # Обновляем разделитель для плагинов
            if hasattr(self, 'plugin_separator'):
                self.plugin_separator.configure(fg_color=self.theme.SCROLLBAR)
            
            print("Применена новая тема оформления")
            return True
        except Exception as e:
            print(f"Ошибка при применении темы: {e}")
            return False
            
    def write_to_console(self, text, message_type="normal"):
        """
        Выводит текст в консоль.
        
        Args:
            text: Текст для вывода
            message_type: Тип сообщения (normal, error, info, success)
        """
        if hasattr(self, 'terminal') and self.terminal:
            self.terminal.write(text, message_type)
            
            # Показываем консоль, если она скрыта
            if not self.console_frame.winfo_manager():
                self.toggle_console()
    
    def show_settings_dialog(self, section="general"):
        """Показывает диалог настроек"""
        # Создаем диалог
        dialog = ctk.CTkToplevel(self)
        dialog.title("Настройки")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Делаем диалог модальным
        dialog.focus_set()
        
        # Создаем вкладки
        tabview = ctk.CTkTabview(dialog, width=550, height=350)
        tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Добавляем вкладки
        tabview.add("Общие")
        tabview.add("Редактор")
        tabview.add("Горячие клавиши")
        tabview.add("ИИ")
        
        # Активируем нужную вкладку
        if section == "general":
            tabview.set("Общие")
        elif section == "editor":
            tabview.set("Редактор")
        elif section == "hotkeys":
            tabview.set("Горячие клавиши")
        elif section == "ai":
            tabview.set("ИИ")
        
        # Заполняем вкладку "Общие"
        general_frame = tabview.tab("Общие")
        
        # ...
        
        # Заполняем вкладку "Редактор"
        editor_frame = tabview.tab("Редактор")
        
        # Font settings
        font_label = ctk.CTkLabel(editor_frame, text="Шрифт:")
        font_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        font_family_var = tk.StringVar(value=self.settings.font_family)
        font_family_optionmenu = ctk.CTkOptionMenu(
            editor_frame,
            values=["Consolas", "Courier New", "DejaVu Sans Mono", "Fira Code", "Monospace"],
            variable=font_family_var
        )
        font_family_optionmenu.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        font_size_label = ctk.CTkLabel(editor_frame, text="Размер шрифта:")
        font_size_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        font_size_var = tk.IntVar(value=self.settings.font_size)
        font_size_slider = ctk.CTkSlider(
            editor_frame, 
            from_=8, 
            to=24, 
            number_of_steps=16,
            variable=font_size_var
        )
        font_size_slider.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        font_size_value = ctk.CTkLabel(editor_frame, text=str(self.settings.font_size))
        font_size_value.grid(row=1, column=2, padx=10, pady=10, sticky="w")
        
        # Функция обновления размера шрифта
        def update_font_size(value):
            font_size_value.configure(text=str(int(value)))
        
        font_size_slider.configure(command=update_font_size)
        
        # Whitespace settings
        show_whitespace_var = tk.BooleanVar(value=self.settings.show_whitespace)
        show_whitespace_checkbox = ctk.CTkCheckBox(
            editor_frame,
            text="Показывать пробелы и табуляцию",
            variable=show_whitespace_var
        )
        show_whitespace_checkbox.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Tab settings
        use_spaces_var = tk.BooleanVar(value=self.settings.use_spaces_for_tab)
        use_spaces_checkbox = ctk.CTkCheckBox(
            editor_frame,
            text="Использовать пробелы вместо табуляции",
            variable=use_spaces_var
        )
        use_spaces_checkbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        tab_size_label = ctk.CTkLabel(editor_frame, text="Размер табуляции:")
        tab_size_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        
        tab_size_var = tk.IntVar(value=self.settings.tab_size)
        tab_size_optionmenu = ctk.CTkOptionMenu(
            editor_frame,
            values=["2", "4", "8"],
            variable=tab_size_var
        )
        tab_size_optionmenu.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Функция для сохранения настроек
        def apply_settings():
            # Сохраняем настройки шрифта
            self.settings.font_family = font_family_var.get()
            self.settings.font_size = int(font_size_var.get())
            self.settings.show_whitespace = show_whitespace_var.get()
            self.settings.use_spaces_for_tab = use_spaces_var.get()
            self.settings.tab_size = int(tab_size_var.get())
            
            # Сохраняем настройки в файл
            self.settings.save_to_file()
            
            # Применяем настройки
            self.apply_settings()
            
            # Закрываем диалог
            dialog.destroy()
        
        # Кнопка сохранения
        save_btn = ctk.CTkButton(
            buttons_frame, 
            text="Сохранить", 
            command=apply_settings
        )
        save_btn.pack(side="right", padx=5)
        
        # Кнопка отмены
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Отмена", 
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=5)
    
    def show_plugins_dialog(self):
        """Показывает диалог управления плагинами"""
        # Создаем диалог
        dialog = ctk.CTkToplevel(self)
        dialog.title("Управление плагинами")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Делаем диалог модальным
        dialog.focus_set()
        
        # Заголовок
        header_label = ctk.CTkLabel(
            dialog, 
            text="Управление плагинами", 
            font=("Arial", 14, "bold")
        )
        header_label.pack(pady=10)
        
        # Фрейм для списка плагинов
        plugins_frame = ctk.CTkFrame(dialog)
        plugins_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Получаем список плагинов
        plugins = self.plugin_manager.get_all_plugins()
        
        # Создаем список
        plugins_list = ctk.CTkScrollableFrame(plugins_frame)
        plugins_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Добавляем плагины в список
        for plugin in plugins:
            plugin_frame = ctk.CTkFrame(plugins_list)
            plugin_frame.pack(fill="x", padx=5, pady=5)
            
            # Название и описание плагина
            plugin_name = ctk.CTkLabel(
                plugin_frame, 
                text=plugin.name, 
                font=("Arial", 12, "bold")
            )
            plugin_name.grid(row=0, column=0, sticky="w", padx=5, pady=2)
            
            plugin_desc = ctk.CTkLabel(
                plugin_frame, 
                text=plugin.description
            )
            plugin_desc.grid(row=1, column=0, sticky="w", padx=5, pady=2)
            
            # Кнопка включения/выключения плагина
            toggle_btn = ctk.CTkButton(
                plugin_frame, 
                text="Включен" if plugin.active else "Выключен", 
                width=80,
                command=lambda p=plugin: self.toggle_plugin(p.name, p.active)
            )
            toggle_btn.grid(row=0, column=1, rowspan=2, padx=5, pady=5)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(dialog)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            buttons_frame, 
            text="Закрыть", 
            command=dialog.destroy
        )
        close_btn.pack(side="right", padx=5)
    
    def toggle_plugin(self, plugin_name, current_state):
        """Переключает состояние плагина"""
        if current_state:
            self.plugin_manager.deactivate_plugin(plugin_name)
        else:
            self.plugin_manager.activate_plugin(plugin_name, self)
    
    def toggle_show_whitespace(self):
        """Переключает отображение пробелов"""
        self.settings.show_whitespace = not self.settings.show_whitespace
        self.show_whitespace(self.settings.show_whitespace)
        self.settings.save_to_file()
    
    def show_whitespace(self, show=True):
        """Показывает или скрывает пробелы"""
        if show:
            # Создаем теги для пробелов и табуляции
            self.text_editor.text.tag_configure("whitespace", foreground="gray")
            
            # Находим все пробелы и табуляции
            for m in re.finditer(r"[ ]+", self.text_editor.get_text()):
                start, end = m.span()
                start_index = f"1.0+{start}c"
                end_index = f"1.0+{end}c"
                self.text_editor.text.tag_add("whitespace", start_index, end_index)
            
            # Находим все табуляции
            for m in re.finditer(r"\t+", self.text_editor.get_text()):
                start, end = m.span()
                start_index = f"1.0+{start}c"
                end_index = f"1.0+{end}c"
                self.text_editor.text.tag_add("whitespace", start_index, end_index)
        else:
            # Удаляем теги
            self.text_editor.text.tag_remove("whitespace", "1.0", tk.END)
    
    def bind_hotkeys(self):
        """Привязывает горячие клавиши"""
        # Привязываем горячие клавиши из настроек
        for action, key in self.settings.hotkeys.items():
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
        """Показывает диалог поиска текста"""
        # TODO: Реализовать поиск текста
        pass
    
    def update_cursor_position(self):
        """Обновляет позицию курсора в статус-баре"""
        # Получаем текущую позицию курсора
        try:
            pos = self.text_editor.text.index(tk.INSERT)
            line, col = pos.split('.')
            self.cursor_position_label.configure(text=f"Строка: {line}, Столбец: {col}")
        except:
            pass

    def create_editor_buttons(self):
        """Создает кнопки инструментов редактора"""
        # Общие настройки для всех кнопок
        button_width = 35
        button_height = 35
        button_padx = 0
        button_pady = 5
        
        # Определяем кнопки основного интерфейса
        buttons = [
            ("📄", "Новый файл", self.new_file),
            ("📂", "Открыть файл", self.open_file),
            ("💾", "Сохранить файл", self.save_file),
            ("▶️", "Запустить код", self.run_current_code),
            ("🖥️", "Переключить консоль", self.toggle_console),
            ("🗂️", "Переключить проводник", self.toggle_explorer)
        ]
        
        # Добавляем каждую кнопку
        for text, tooltip, command in buttons:
            self.add_tool_button(text, command, tooltip=tooltip)

        # Визуальный разделитель для плагинов
        self.plugin_separator = ctk.CTkFrame(self.tools_frame, height=1, fg_color=self.theme.SCROLLBAR)
        self.plugin_separator.pack(side="top", fill="x", pady=10, padx=5)
        self.plugin_separator._is_plugin_separator = True
    
    def add_tool_button(self, text, command, tooltip=None, position="top"):
        """
        Добавляет кнопку в панель инструментов.
        
        Args:
            text: Текст/эмодзи кнопки
            command: Функция при нажатии
            tooltip: Подсказка при наведении
            position: Положение (top/bottom)
            
        Returns:
            Добавленная кнопка
        """
        # Создаем кнопку
        button = ctk.CTkButton(
            self.tools_frame,
            text=text,
            width=35,
            height=35,
            fg_color="transparent",
            hover_color=self.theme.SELECTION,
            text_color=self.theme.FOREGROUND,
            command=command
        )
        
        # Размещаем кнопку
        button.pack(side=position, pady=5, padx=0)
        
        # Сохраняем подсказку как атрибут (для будущего использования)
        if tooltip:
            button._tooltip = tooltip
            
        return button

if __name__ == "__main__":
    # Создаем и запускаем приложение
    app = CodeEditorApp()
    app.mainloop() 