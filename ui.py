"""
Модуль для работы с пользовательским интерфейсом редактора кода.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog

from theme import KanagawaTheme
from system_utils import maximize_window, minimize_window, restore_window, is_window_maximized

class MenuBuilder:
    """Класс для создания меню редактора кода"""
    
    def __init__(self, parent):
        """
        Инициализация построителя меню
        
        Args:
            parent: родительский экземпляр приложения
        """
        self.parent = parent
        
    def create_file_menu(self):
        """Создает меню файла"""
        file_menu = tk.Menu(self.parent, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND)
        file_menu.add_command(label="Новый файл", command=self.parent.new_file)
        file_menu.add_command(label="Открыть...", command=self.parent.open_file)
        file_menu.add_command(label="Сохранить", command=self.parent.save_file)
        file_menu.add_command(label="Сохранить как...", command=self.parent.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.parent.quit)
        return file_menu
    
    def create_edit_menu(self):
        """Создает меню редактирования"""
        edit_menu = tk.Menu(self.parent, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND)
        edit_menu.add_command(label="Отменить", command=lambda: self.parent.text_editor.text.edit_undo())
        edit_menu.add_command(label="Повторить", command=lambda: self.parent.text_editor.text.edit_redo())
        edit_menu.add_separator()
        edit_menu.add_command(label="Вырезать", command=lambda: self.parent.text_editor.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Копировать", command=lambda: self.parent.text_editor.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Вставить", command=lambda: self.parent.text_editor.text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Найти...", command=self.parent.find_text)
        return edit_menu
    
    def create_view_menu(self):
        """Создает меню вида"""
        view_menu = tk.Menu(self.parent, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND)
        view_menu.add_command(label="Проводник файлов", command=self.parent.toggle_explorer)
        view_menu.add_command(label="Консоль", command=self.parent.toggle_console)
        view_menu.add_command(label="ИИ Ассистент", command=self.parent.toggle_ai_chat)
        view_menu.add_separator()
        
        whitespace_var = tk.BooleanVar(value=self.parent.settings.show_whitespace)
        view_menu.add_checkbutton(label="Показать пробелы/табы", variable=whitespace_var, 
                                command=self.parent.toggle_show_whitespace)
        
        return view_menu
    
    def create_run_menu(self):
        """Создает меню запуска"""
        run_menu = tk.Menu(self.parent, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND)
        run_menu.add_command(label="Запустить", command=self.parent.run_current_code)
        run_menu.add_command(label="Запустить в консоли", command=self.parent.run_code_in_external_console)
        run_menu.add_command(label="Остановить выполнение", command=self.parent.stop_execution)
        return run_menu
    
    def create_settings_menu(self):
        """Создает меню настроек"""
        settings_menu = tk.Menu(self.parent, tearoff=0, bg=KanagawaTheme.DARKER_BG, fg=KanagawaTheme.FOREGROUND)
        settings_menu.add_command(label="Общие настройки", command=lambda: self.parent.show_settings_dialog("general"))
        settings_menu.add_command(label="Настройки редактора", command=lambda: self.parent.show_settings_dialog("editor"))
        settings_menu.add_command(label="Горячие клавиши", command=lambda: self.parent.show_settings_dialog("hotkeys"))
        settings_menu.add_command(label="Настройки ИИ", command=lambda: self.parent.show_settings_dialog("ai"))
        settings_menu.add_separator()
        settings_menu.add_command(label="Плагины", command=self.parent.show_plugins_dialog)
        return settings_menu

class DialogBuilder:
    """Класс для создания диалоговых окон"""
    
    @staticmethod
    def create_message_dialog(parent, title, message, dialog_type="info"):
        """
        Создает диалоговое окно с сообщением
        
        Args:
            parent: родительское окно
            title (str): Заголовок окна
            message (str): Сообщение
            dialog_type (str): Тип диалога (info, warning, error, question)
            
        Returns:
            bool: Результат диалога (True/False)
        """
        if dialog_type == "info":
            return messagebox.showinfo(title, message)
        elif dialog_type == "warning":
            return messagebox.showwarning(title, message)
        elif dialog_type == "error":
            return messagebox.showerror(title, message)
        elif dialog_type == "question":
            return messagebox.askyesno(title, message)
        else:
            return messagebox.showinfo(title, message)
    
    @staticmethod
    def create_file_open_dialog(parent, title="Открыть файл", filetypes=None):
        """
        Создает диалоговое окно для открытия файла
        
        Args:
            parent: родительское окно
            title (str): Заголовок окна
            filetypes (list): Список типов файлов
            
        Returns:
            str: Путь к выбранному файлу
        """
        if filetypes is None:
            filetypes = [("Python файлы", "*.py"), ("Все файлы", "*.*")]
        
        return filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )
    
    @staticmethod
    def create_file_save_dialog(parent, title="Сохранить файл", filetypes=None):
        """
        Создает диалоговое окно для сохранения файла
        
        Args:
            parent: родительское окно
            title (str): Заголовок окна
            filetypes (list): Список типов файлов
            
        Returns:
            str: Путь к выбранному файлу
        """
        if filetypes is None:
            filetypes = [("Python файлы", "*.py"), ("Все файлы", "*.*")]
        
        return filedialog.asksaveasfilename(
            title=title,
            filetypes=filetypes
        )
    
    @staticmethod
    def create_folder_select_dialog(parent, title="Выбрать папку"):
        """
        Создает диалоговое окно для выбора папки
        
        Args:
            parent: родительское окно
            title (str): Заголовок окна
            
        Returns:
            str: Путь к выбранной папке
        """
        return filedialog.askdirectory(title=title)

class TitleBar:
    """Класс для создания заголовка окна"""
    
    def __init__(self, parent, frame):
        """
        Инициализация заголовка окна
        
        Args:
            parent: родительский экземпляр приложения
            frame: фрейм, в котором размещается заголовок
        """
        self.parent = parent
        self.frame = frame
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса заголовка"""
        # Заголовок
        self.frame.configure(fg_color=KanagawaTheme.DARKER_BG, height=30)
        
        # Логотип и заголовок
        logo_label = ctk.CTkLabel(
            self.frame, 
            text="vpycode", 
            text_color=KanagawaTheme.FOREGROUND, 
            font=("Arial", 10, "bold")
        )
        logo_label.pack(side="left", padx=10)
        
        # Кнопки меню
        file_btn = ctk.CTkButton(
            self.frame, 
            text="Файл", 
            width=50, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.show_file_menu
        )
        file_btn.pack(side="left", padx=5)
        
        edit_btn = ctk.CTkButton(
            self.frame, 
            text="Правка", 
            width=50, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.show_edit_menu
        )
        edit_btn.pack(side="left", padx=5)
        
        view_btn = ctk.CTkButton(
            self.frame, 
            text="Вид", 
            width=50, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.show_view_menu
        )
        view_btn.pack(side="left", padx=5)
        
        run_btn = ctk.CTkButton(
            self.frame, 
            text="Запуск", 
            width=50, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.show_run_menu
        )
        run_btn.pack(side="left", padx=5)
        
        settings_btn = ctk.CTkButton(
            self.frame, 
            text="Настройки", 
            width=70, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.show_settings_menu
        )
        settings_btn.pack(side="left", padx=5)
        
        # Кнопки управления окном
        minimize_btn = ctk.CTkButton(
            self.frame, 
            text="—", 
            width=25, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.minimize
        )
        minimize_btn.pack(side="right", padx=5)
        
        maximize_btn = ctk.CTkButton(
            self.frame, 
            text="□", 
            width=25, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.toggle_maximize
        )
        maximize_btn.pack(side="right", padx=5)
        
        close_btn = ctk.CTkButton(
            self.frame, 
            text="×", 
            width=25, 
            height=20, 
            fg_color="transparent", 
            hover_color="#E82424",
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.quit
        )
        close_btn.pack(side="right", padx=5)
        
        # Обработчики событий перетаскивания окна
        self.frame.bind("<ButtonPress-1>", self.parent.start_window_drag)
        self.frame.bind("<ButtonRelease-1>", self.parent.stop_window_drag)
        self.frame.bind("<B1-Motion>", self.parent.on_window_drag)
        
        # Обработчики щелчка мыши на заголовке
        self.frame.bind("<Double-Button-1>", lambda e: self.parent.toggle_maximize()) 