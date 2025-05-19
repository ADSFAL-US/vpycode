"""
Тестовый плагин, демонстрирующий возможности плагинной системы vpycode.
"""
import random
import tkinter as tk
import customtkinter as ctk
from plugins.base import Plugin

class TestPlugin(Plugin):
    """Демонстрационный плагин для vpycode."""
    
    def __init__(self, app):
        super().__init__(app)
        self.name = "TestPlugin"
        self.version = "1.0.0"
        self.description = "Демонстрирует возможности плагинной системы"
        self.author = "vpycode Team"
        
        # Кнопки и другие элементы, создаваемые плагином
        self.sidebar_button = None
        self.menu_items_added = False
        self.demo_window = None
    
    def activate(self):
        """Активация плагина."""
        print(f"Активация плагина {self.name}")
        
        # Добавляем кнопку в боковой панели
        self.sidebar_button = self.add_sidebar_button("🧪", self.show_demo_window)
        
        # Добавляем команды в меню
        self.add_menu_command("Правка", "Перевернуть строку", self.reverse_current_line)
        self.add_menu_command("Вид", "Изменить фон", self.change_background_color)
        self.add_menu_command("Запуск", "Тестовое сообщение", self.send_console_message)
        
        self.menu_items_added = True
        print(f"Плагин {self.name} активирован.")
    
    def deactivate(self):
        """Деактивация плагина."""
        print(f"Деактивация плагина {self.name}")
        
        # Закрываем демонстрационное окно, если оно открыто
        if self.demo_window and self.demo_window.winfo_exists():
            self.demo_window.destroy()
        
        # Удаляем кнопку из боковой панели происходит автоматически
        
        print(f"Плагин {self.name} деактивирован.")
    
    def show_demo_window(self):
        """Показывает демонстрационное окно с возможностями плагина."""
        if self.demo_window and self.demo_window.winfo_exists():
            self.demo_window.focus_set()
            return
            
        # Создаем окно с помощью метода из базового класса
        self.demo_window = self.add_gui_window(
            "Демонстрация плагина", 
            self._setup_demo_content, 
            width=600, 
            height=400
        )
    
    def _setup_demo_content(self, window):
        """Настраивает содержимое демонстрационного окна."""
        # Настройка сетки окна
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        header = ctk.CTkFrame(window, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        header_label = ctk.CTkLabel(
            header, 
            text="Демонстрация возможностей плагинной системы", 
            font=("Arial", 14, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        header_label.pack(side="left", padx=10)
        
        # Notebook с вкладками
        notebook = ctk.CTkTabview(window)
        notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Вкладка UI
        ui_tab = notebook.add("Интерфейс")
        
        # Вкладка Редактор
        editor_tab = notebook.add("Редактор")
        
        # Вкладка Консоль
        console_tab = notebook.add("Консоль/Терминал")
        
        # Настраиваем вкладку UI
        ui_frame = ctk.CTkFrame(ui_tab, fg_color="transparent")
        ui_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Демонстрация изменения темы
        theme_label = ctk.CTkLabel(
            ui_frame,
            text="Изменение цветов интерфейса",
            font=("Arial", 12, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        theme_label.pack(pady=(10, 5))
        
        theme_buttons_frame = ctk.CTkFrame(ui_frame, fg_color="transparent")
        theme_buttons_frame.pack(pady=10)
        
        # Кнопка случайного цвета фона
        bg_btn = ctk.CTkButton(
            theme_buttons_frame,
            text="Случайный фон",
            command=self.change_background_color,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        bg_btn.pack(side="left", padx=5)
        
        # Кнопка возврата к стандартной теме
        reset_btn = ctk.CTkButton(
            theme_buttons_frame,
            text="Сбросить тему",
            command=self.reset_theme,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        reset_btn.pack(side="left", padx=5)
        
        # Настраиваем вкладку Редактор
        editor_frame = ctk.CTkFrame(editor_tab, fg_color="transparent")
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        editor_label = ctk.CTkLabel(
            editor_frame,
            text="Операции с текстом редактора",
            font=("Arial", 12, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        editor_label.pack(pady=(10, 5))
        
        editor_buttons_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        editor_buttons_frame.pack(pady=10)
        
        # Кнопка для переворачивания текста
        reverse_btn = ctk.CTkButton(
            editor_buttons_frame,
            text="Перевернуть строку",
            command=self.reverse_current_line,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        reverse_btn.pack(side="left", padx=5)
        
        # Кнопка для добавления текста
        add_text_btn = ctk.CTkButton(
            editor_buttons_frame,
            text="Добавить текст",
            command=self.add_demo_text,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        add_text_btn.pack(side="left", padx=5)
        
        # Настраиваем вкладку Консоль/Терминал
        console_frame = ctk.CTkFrame(console_tab, fg_color="transparent")
        console_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        console_label = ctk.CTkLabel(
            console_frame,
            text="Взаимодействие с консолью",
            font=("Arial", 12, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        console_label.pack(pady=(10, 5))
        
        console_buttons_frame = ctk.CTkFrame(console_frame, fg_color="transparent")
        console_buttons_frame.pack(pady=10)
        
        # Кнопка для отправки сообщений разных типов
        message_btn = ctk.CTkButton(
            console_buttons_frame,
            text="Отправить сообщение",
            command=self.send_console_message,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        message_btn.pack(side="left", padx=5)
        
        # Кнопка для очистки консоли
        clear_btn = ctk.CTkButton(
            console_buttons_frame,
            text="Очистить консоль",
            command=self.app.clear_console,
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER
        )
        clear_btn.pack(side="left", padx=5)
        
        # Выбираем первую вкладку
        notebook.set("Интерфейс")
    
    def reverse_current_line(self):
        """Переворачивает текст текущей строки в редакторе."""
        try:
            # Получаем текущую позицию курсора
            current_pos = self.app.code_editor.index(tk.INSERT)
            line_num = int(float(current_pos))
            
            # Получаем содержимое текущей строки
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_content = self.app.code_editor.get(line_start, line_end)
            
            # Переворачиваем текст
            reversed_text = line_content[::-1]
            
            # Заменяем текст в строке
            self.app.code_editor.delete(line_start, line_end)
            self.app.code_editor.insert(line_start, reversed_text)
            
            # Показываем сообщение
            self.app.status_text.configure(text="Строка перевернута")
            
        except Exception as e:
            print(f"Ошибка при переворачивании строки: {e}")
    
    def change_background_color(self):
        """Изменяет цвет фона редактора на случайный."""
        try:
            # Генерируем случайный цвет в формате hex
            r = random.randint(10, 60)  # Используем темные цвета
            g = random.randint(10, 60)
            b = random.randint(10, 60)
            
            bg_color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Создаем новую тему на основе текущей
            new_theme = {
                "BACKGROUND": bg_color,
                "DARKER_BG": self._darken_color(bg_color, 20),  # Затемняем на 20%
                "LIGHTER_BG": self._lighten_color(bg_color, 20), # Осветляем на 20%
                "PANEL_BG": bg_color
            }
            
            # Применяем изменения темы
            self.change_theme(new_theme)
            
            # Показываем сообщение
            self.app.status_text.configure(text=f"Цвет фона изменен на {bg_color}")
            
        except Exception as e:
            print(f"Ошибка при изменении фона: {e}")
    
    def _darken_color(self, hex_color, percent):
        """Затемняет цвет на указанный процент."""
        # Убираем символ # в начале строки, если есть
        hex_color = hex_color.lstrip('#')
        
        # Преобразуем в RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Уменьшаем яркость
        factor = (100 - percent) / 100
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        # Возвращаем новый hex-цвет
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _lighten_color(self, hex_color, percent):
        """Осветляет цвет на указанный процент."""
        # Убираем символ # в начале строки, если есть
        hex_color = hex_color.lstrip('#')
        
        # Преобразуем в RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Увеличиваем яркость
        factor = (100 + percent) / 100
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        # Возвращаем новый hex-цвет
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def send_console_message(self):
        """Отправляет тестовое сообщение в консоль."""
        # Убеждаемся, что консоль видима
        if not self.app.console_frame.winfo_viewable():
            self.app.toggle_console()
        
        # Отправляем разные типы сообщений
        self.app.write_to_console("=== Тестовые сообщения от плагина ===\n", "info")
        self.app.write_to_console("Это обычное сообщение\n")
        self.app.write_to_console("Это информационное сообщение\n", "info")
        self.app.write_to_console("Это сообщение об успехе\n", "success")
        self.app.write_to_console("Это сообщение об ошибке\n", "error")
    
    def reset_theme(self):
        """Возвращает стандартную тему Kanagawa."""
        from main import KanagawaTheme
        
        # Создаем словарь с оригинальными значениями темы
        original_theme = {attr: getattr(KanagawaTheme, attr) for attr in dir(KanagawaTheme) 
                         if not attr.startswith('_') and isinstance(getattr(KanagawaTheme, attr), str)}
        
        # Применяем оригинальную тему
        self.change_theme(original_theme)
        self.app.status_text.configure(text="Восстановлена стандартная тема")
    
    def add_demo_text(self):
        """Добавляет демонстрационный текст в редактор."""
        demo_text = """# Демонстрационный код от плагина
def демо_функция():
    \"\"\"Это демонстрационная функция.\"\"\"
    print("Привет от плагина!")
    return True

# Пример класса
class ДемоКласс:
    def __init__(self):
        self.сообщение = "Это демонстрация плагинной системы vpycode!"
        
    def показать(self):
        print(self.сообщение)

# Создание и использование
демо = ДемоКласс()
демо.показать()
"""
        
        # Вставляем текст в текущую позицию курсора
        self.app.code_editor.insert(tk.INSERT, demo_text)
        self.app.highlight_syntax()  # Обновляем подсветку синтаксиса
        self.app.status_text.configure(text="Добавлен демонстрационный код")
    
    def run_any_code(self, file_path, file_extension):
        """
        Универсальный обработчик для запуска файлов любого типа.
        Демонстрирует интерфейс для плагинов-отладчиков.
        """
        import subprocess
        
        try:
            self.app.write_to_console(f"TestPlugin: Попытка запуска файла {file_path}\n", "info")
            self.app.write_to_console(f"Это демонстрация работы плагина-отладчика.\n", "info")
            self.app.write_to_console(f"Расширение файла: {file_extension}\n", "info")
            
            # Просто имитируем запуск - в реальном плагине должна быть реальная логика
            self.app.write_to_console("Файл успешно обработан тестовым плагином.\n", "success")
            
            # Возвращаем None, т.к. реального запуска нет
            return None
        except Exception as e:
            self.app.write_to_console(f"Ошибка запуска файла: {str(e)}\n", "error")
            return None 