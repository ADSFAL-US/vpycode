"""
Плагин для поддержки JavaScript в vpycode IDE.
"""
import os
import subprocess
import tkinter as tk
import customtkinter as ctk
from plugins.base import Plugin

class JavaScriptSupport(Plugin):
    """Плагин для работы с JavaScript в vpycode."""
    
    def __init__(self, app):
        super().__init__(app)
        self.name = "JavaScriptSupport"
        self.version = "1.0.0"
        self.description = "Поддержка JavaScript в vpycode"
        self.author = "vpycode Team"
        
        # JavaScript синтаксис для подсветки
        self.js_syntax = {
            "keywords": [
                "var", "let", "const", "function", "return", "if", 
                "else", "for", "while", "do", "switch", "case", 
                "break", "continue", "try", "catch", "finally", 
                "throw", "new", "delete", "typeof", "instanceof", 
                "void", "this", "super", "class", "extends", 
                "import", "export", "default", "async", "await"
            ],
            "operators": ["=>", "==", "===", "!=", "!==", "+", "-", "*", "/", "%", "&&", "||", "!"],
            "builtin": ["console", "document", "window", "Math", "Array", "Object", "String", "Number", "Boolean"]
        }
        
        # Боковая кнопка плагина и другие элементы интерфейса
        self.sidebar_button = None
        self.js_debug_window = None
        self.js_console = None
        self.nodejs_path = self._find_nodejs()
        
    def activate(self):
        """Активация плагина."""
        print(f"Активация плагина {self.name}")
        
        # Регистрируем JavaScript как поддерживаемый язык
        self.register_language(
            language_name="JavaScript",
            file_extensions=[".js", ".mjs", ".cjs"],
            run_command=self.run_javascript,
            syntax_keywords=self.js_syntax
        )
        
        # Добавляем кнопку в боковой панели
        self.sidebar_button = self.add_sidebar_button("JS", self.show_js_tools)
        
        # Добавляем команду в меню запуска
        self.add_menu_command("Запуск", "Запустить JavaScript", self.run_current_js)
        
        print(f"Плагин {self.name} активирован.")
        
        # Проверяем наличие Node.js
        if not self.nodejs_path:
            self.app.write_to_console("Внимание: Node.js не найден. Установите Node.js для запуска JavaScript.\n", "error")
        else:
            self.app.write_to_console(f"Node.js найден: {self.nodejs_path}\n", "info")
    
    def deactivate(self):
        """Деактивация плагина."""
        print(f"Деактивация плагина {self.name}")
        
        # Закрываем окно отладки, если оно открыто
        if self.js_debug_window and self.js_debug_window.winfo_exists():
            self.js_debug_window.destroy()
            
        print(f"Плагин {self.name} деактивирован.")
    
    def run_javascript(self, file_path):
        """
        Запускает JavaScript-файл с помощью Node.js.
        
        Args:
            file_path: Путь к JavaScript-файлу
            
        Returns:
            Процесс выполнения кода
        """
        if not self.nodejs_path:
            self.app.write_to_console("Ошибка: Node.js не найден.\n", "error")
            return None
            
        try:
            # Запускаем код через Node.js
            process = subprocess.Popen(
                [self.nodejs_path, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Возвращаем процесс
            return process
        except Exception as e:
            self.app.write_to_console(f"Ошибка запуска JavaScript: {str(e)}\n", "error")
            return None
    
    def run_current_js(self):
        """Запускает текущий JavaScript файл."""
        # Проверяем, что текущий файл - JavaScript
        current_file = self.app.current_file
        if not current_file or not current_file.lower().endswith(('.js', '.mjs', '.cjs')):
            self.app.write_to_console("Текущий файл не является JavaScript файлом.\n", "error")
            return
            
        # Убеждаемся, что консоль видима
        if not self.app.console_frame.winfo_viewable():
            self.app.toggle_console()
            
        # Очищаем консоль перед запуском
        self.app.clear_console()
        
        # Сохраняем текущий файл перед запуском
        self.app.save_file()
        
        # Запускаем файл
        self.app.write_to_console(f"Запуск JavaScript: {os.path.basename(current_file)}\n", "info")
        
        # Используем Node.js для запуска JavaScript
        process = self.run_javascript(current_file)
        if not process:
            return
            
        # Сохраняем ссылку на процесс
        self.app.current_process = process
        
        # Читаем вывод и ошибки в отдельном потоке
        def read_output():
            stdout, stderr = process.communicate()
            
            # Проверяем код возврата
            if process.returncode == 0:
                if stdout:
                    self.app.write_to_console(stdout)
                self.app.write_to_console("\nJavaScript выполнен успешно.\n", "success")
            else:
                if stdout:
                    self.app.write_to_console(stdout)
                if stderr:
                    self.app.write_to_console(stderr, "error")
                self.app.write_to_console(f"\nJavaScript завершился с ошибкой (код {process.returncode}).\n", "error")
            
            # Очищаем ссылку на процесс
            self.app.current_process = None
            
        # Запускаем чтение в отдельном потоке
        import threading
        threading.Thread(target=read_output).start()
    
    def show_js_tools(self):
        """Показывает окно инструментов JavaScript."""
        # Создаем новое окно для инструментов JavaScript
        self._create_js_tools_window()
    
    def _create_js_tools_window(self):
        """Создает окно с инструментами для JavaScript."""
        if self.js_debug_window and self.js_debug_window.winfo_exists():
            self.js_debug_window.focus_force()
            return
            
        # Создаем окно с помощью метода из базового класса
        self.js_debug_window = self.add_gui_window(
            "JavaScript Tools", 
            self._setup_js_tools_content, 
            width=600, 
            height=400
        )
    
    def _setup_js_tools_content(self, window):
        """Настраивает содержимое окна инструментов JavaScript."""
        # Настройка сетки окна
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        header = ctk.CTkFrame(window, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        header_label = ctk.CTkLabel(
            header, 
            text="Инструменты JavaScript", 
            font=("Arial", 14, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        header_label.pack(side="left", padx=10)
        
        # Notebook с вкладками
        notebook = ctk.CTkTabview(window)
        notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Вкладка консоли
        console_tab = notebook.add("Консоль")
        
        # Вкладка отладчика
        debugger_tab = notebook.add("Отладчик")
        
        # Вкладка NPM
        npm_tab = notebook.add("NPM")
        
        # Настраиваем консоль
        console_frame = ctk.CTkFrame(console_tab, fg_color="transparent")
        console_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.js_console = ctk.CTkTextbox(
            console_frame,
            fg_color=self.app.theme.CONSOLE_BG,
            text_color=self.app.theme.CONSOLE_FG,
            font=("Consolas", 11)
        )
        self.js_console.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Кнопки управления
        buttons_frame = ctk.CTkFrame(console_frame, fg_color="transparent", height=40)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        run_btn = ctk.CTkButton(
            buttons_frame, 
            text="Запустить текущий файл", 
            command=self.run_current_js,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER,
            text_color=self.app.theme.FOREGROUND
        )
        run_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            buttons_frame, 
            text="Очистить консоль", 
            command=lambda: self.js_console.delete("1.0", tk.END),
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER,
            text_color=self.app.theme.FOREGROUND
        )
        clear_btn.pack(side="left", padx=5)
        
        # Наполняем отладчик
        debugger_frame = ctk.CTkFrame(debugger_tab, fg_color="transparent")
        debugger_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        debugger_label = ctk.CTkLabel(
            debugger_frame,
            text="Интеграция с Chrome DevTools Protocol",
            font=("Arial", 12),
            text_color=self.app.theme.FOREGROUND
        )
        debugger_label.pack(pady=20)
        
        debugger_info = ctk.CTkLabel(
            debugger_frame,
            text="Функциональность отладчика JavaScript доступна в расширенной версии плагина.",
            text_color=self.app.theme.COMMENT
        )
        debugger_info.pack()
        
        # Наполняем NPM
        npm_frame = ctk.CTkFrame(npm_tab, fg_color="transparent")
        npm_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        npm_label = ctk.CTkLabel(
            npm_frame,
            text="Управление NPM пакетами",
            font=("Arial", 12),
            text_color=self.app.theme.FOREGROUND
        )
        npm_label.pack(pady=20)
        
        npm_info = ctk.CTkLabel(
            npm_frame,
            text="Функциональность управления пакетами NPM доступна в расширенной версии плагина.",
            text_color=self.app.theme.COMMENT
        )
        npm_info.pack()
        
        # Выбираем первую вкладку
        notebook.set("Консоль")
    
    def _find_nodejs(self):
        """Находит путь к Node.js в системе."""
        try:
            # Проверяем доступность Node.js
            if os.name == 'nt':  # Windows
                try:
                    # На Windows проверяем наличие node в PATH
                    result = subprocess.run(
                        ["where", "node"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True, 
                        shell=True
                    )
                    if result.returncode == 0:
                        return result.stdout.splitlines()[0].strip()
                except:
                    # Если 'where' не работает, пробуем прямую проверку путей
                    common_paths = [
                        r"C:\Program Files\nodejs\node.exe",
                        r"C:\Program Files (x86)\nodejs\node.exe"
                    ]
                    for path in common_paths:
                        if os.path.exists(path):
                            return path
                    return None
            else:  # Linux/Mac
                result = subprocess.run(
                    ["which", "node"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
                return None
        except Exception as e:
            print(f"Ошибка при поиске Node.js: {e}")
            return None 