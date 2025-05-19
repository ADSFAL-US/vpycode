"""
Базовые классы для создания плагинов.
"""
from abc import ABC, abstractmethod
import tkinter as tk
import customtkinter as ctk
import traceback

class Plugin(ABC):
    """Базовый класс для всех плагинов vpycode."""
    
    def __init__(self, app):
        """
        Инициализация плагина.
        
        Args:
            app: Экземпляр основного приложения vpycode
        """
        self.app = app
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = "Базовый плагин"
        self.author = "Unknown"
        
    @abstractmethod
    def activate(self):
        """Активация плагина. Вызывается при загрузке плагина."""
        pass
        
    @abstractmethod
    def deactivate(self):
        """Деактивация плагина. Вызывается при выгрузке плагина."""
        pass
    
    def add_sidebar_button(self, text, command, position="top"):
        """
        Добавляет кнопку в боковую панель.
        
        Args:
            text: Текст кнопки (emoji или текст)
            command: Функция, вызываемая при нажатии
            position: Позиция кнопки ("top" или "bottom")
        
        Returns:
            Созданная кнопка
        """
        print(f"[DEBUG] {self.name}: Попытка добавить кнопку в боковую панель")
        sidebar_frame = self._find_sidebar_frame()
        if not sidebar_frame:
            print(f"[ERROR] {self.name}: Не удалось найти фрейм боковой панели")
            return None
            
        button = ctk.CTkButton(
            sidebar_frame, 
            text=text, 
            width=40, 
            height=40,
            fg_color="transparent", 
            hover_color=self.app.theme.SELECTION,
            text_color=self.app.theme.FOREGROUND, 
            command=command
        )
        
        if position == "top":
            button.pack(side="top", pady=5)
        else:
            button.pack(side="bottom", pady=5)
            
        print(f"[DEBUG] {self.name}: Кнопка успешно добавлена в боковую панель")
        return button
    
    def _find_sidebar_frame(self):
        """Находит фрейм боковой панели в структуре приложения."""
        print(f"[DEBUG] {self.name}: Поиск фрейма боковой панели")
        
        # Проходим по главным фреймам приложения
        for child in self.app.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                # Ищем содержащий фрейм с контентом
                if hasattr(child, 'grid_info'):
                    info = child.grid_info()
                    # Проверяем, что это главный контент-фрейм (row=2)
                    if info and info.get('row') == 2:
                        for subchild in child.winfo_children():
                            # Ищем боковую панель в левой части с фиксированной шириной
                            if (isinstance(subchild, ctk.CTkFrame) and
                                hasattr(subchild, 'grid_info')):
                                sub_info = subchild.grid_info()
                                if (sub_info and sub_info.get('column') == 0 and 
                                    not subchild.grid_propagate()):
                                    print(f"[DEBUG] {self.name}: Найден фрейм боковой панели по grid_info")
                                    return subchild
        
        # Резервный метод: найдем любой узкий высокий фрейм, прикрепленный к левой стороне
        for child in self.app.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ctk.CTkFrame):
                        # Проверяем наличие кнопок с эмодзи - характерный признак боковой панели
                        emoji_buttons = False
                        for btn in subchild.winfo_children():
                            if isinstance(btn, ctk.CTkButton) and len(btn.cget("text")) == 1:
                                emoji_buttons = True
                                break
                        
                        if emoji_buttons:
                            print(f"[DEBUG] {self.name}: Найден фрейм боковой панели по emoji кнопкам")
                            return subchild
        
        # Ещё один резервный способ - ищем первую панель с кнопками слева
        content_frames = [child for child in self.app.winfo_children() if isinstance(child, ctk.CTkFrame)]
        if len(content_frames) > 0:
            main_content = content_frames[0]  # Предполагаем, что первый фрейм - основной
            for subchild in main_content.winfo_children():
                if isinstance(subchild, ctk.CTkFrame) and len(subchild.winfo_children()) > 0:
                    # Проверяем наличие кнопок
                    has_buttons = any(isinstance(item, ctk.CTkButton) for item in subchild.winfo_children())
                    if has_buttons:
                        print(f"[DEBUG] {self.name}: Найден фрейм боковой панели как первая панель с кнопками")
                        return subchild
        
        print(f"[ERROR] {self.name}: Фрейм боковой панели не найден")
        return None
    
    def change_theme(self, theme_dict):
        """
        Изменяет тему редактора.
        
        Args:
            theme_dict: Словарь с цветами темы
        """
        print(f"[DEBUG] {self.name}: Изменение темы редактора")
        try:
            # Обновляем объект темы в приложении
            for key, value in theme_dict.items():
                if hasattr(self.app.theme, key):
                    print(f"[DEBUG] {self.name}: Изменение цвета {key}: {value}")
                    setattr(self.app.theme, key, value)
            
            # Применяем тему к интерфейсу
            self.app.apply_theme()
            print(f"[DEBUG] {self.name}: Тема успешно изменена")
            return True
        except Exception as e:
            print(f"[ERROR] {self.name}: Ошибка при изменении темы: {e}")
            traceback.print_exc()
            return False
    
    def add_menu_command(self, menu_name, command_label, command_func):
        """
        Добавляет команду в главное меню.
        
        Args:
            menu_name: Имя меню ("Файл", "Правка", "Вид" и т.д.)
            command_label: Название команды
            command_func: Функция, вызываемая при выборе команды
            
        Returns:
            True если команда добавлена, иначе False
        """
        print(f"[DEBUG] {self.name}: Попытка добавить команду '{command_label}' в меню '{menu_name}'")
        
        # Определяем метод для показа соответствующего меню
        menu_method_map = {
            "Файл": "show_file_menu",
            "Правка": "show_edit_menu",
            "Вид": "show_view_menu",
            "Запуск": "show_run_menu",
            "Настройки": "show_settings_menu"
        }
        
        # Проверяем, существует ли такое меню
        if menu_name not in menu_method_map:
            print(f"[ERROR] {self.name}: Меню '{menu_name}' не существует")
            return False
        
        # Получаем имя метода
        menu_method_name = menu_method_map[menu_name]
        
        try:
            # Создаем новую команду меню
            menu_commands = getattr(self.app, f"_{menu_name.lower()}_menu_commands", [])
            if not hasattr(self.app, f"_{menu_name.lower()}_menu_commands"):
                # Если атрибут не существует, создаем его
                setattr(self.app, f"_{menu_name.lower()}_menu_commands", [])
                menu_commands = getattr(self.app, f"_{menu_name.lower()}_menu_commands")
                
            # Добавляем команду в список
            menu_commands.append((command_label, command_func))
            
            # Переопределяем метод показа меню
            original_method = getattr(self.app, menu_method_name)
            
            def new_menu_method(original=original_method, commands=menu_commands):
                # Вызываем оригинальный метод для создания меню
                original()
                
                # Находим последнее созданное меню
                menu = None
                for widget in self.app.winfo_children():
                    if isinstance(widget, tk.Menu) and widget.winfo_ismapped():
                        menu = widget
                        break
                
                if menu:
                    # Добавляем все наши команды в меню
                    for cmd_label, cmd_func in commands:
                        menu.add_command(label=cmd_label, command=cmd_func)
                
            # Заменяем оригинальный метод
            setattr(self.app, menu_method_name, new_menu_method)
            print(f"[DEBUG] {self.name}: Команда '{command_label}' успешно добавлена в меню '{menu_name}'")
            return True
        except Exception as e:
            print(f"[ERROR] {self.name}: Ошибка при добавлении команды в меню: {e}")
            traceback.print_exc()
            return False
    
    def register_language(self, language_name, file_extensions, run_command, syntax_keywords=None):
        """
        Регистрирует новый язык программирования в IDE.
        
        Args:
            language_name: Имя языка
            file_extensions: Список расширений файлов
            run_command: Функция для запуска кода на этом языке
            syntax_keywords: Словарь с ключевыми словами для подсветки
            
        Returns:
            True если язык зарегистрирован, иначе False
        """
        print(f"[DEBUG] {self.name}: Регистрация языка {language_name}")
        try:
            # Проверяем, что language_handlers существует
            if not hasattr(self.app, 'language_handlers'):
                print(f"[ERROR] {self.name}: language_handlers не существует в приложении")
                return False

            # Регистрируем новый обработчик запуска для этого языка
            self.app.language_handlers[language_name] = {
                "extensions": file_extensions,
                "run_command": run_command,
                "syntax": syntax_keywords or {}
            }
            print(f"[DEBUG] {self.name}: Язык {language_name} успешно зарегистрирован")
            
            # Выводим информацию о расширениях
            ext_str = ", ".join(file_extensions)
            print(f"[DEBUG] {self.name}: Зарегистрированы расширения: {ext_str}")
            return True
        except Exception as e:
            print(f"[ERROR] {self.name}: Ошибка при регистрации языка {language_name}: {e}")
            traceback.print_exc()
            return False
    
    def add_gui_window(self, title, content_callback, width=500, height=400):
        """
        Создает новое окно GUI и возвращает его.
        
        Args:
            title: Заголовок окна
            content_callback: Функция для заполнения содержимого окна
            width: Ширина окна
            height: Высота окна
            
        Returns:
            Созданное окно
        """
        window = ctk.CTkToplevel(self.app)
        window.title(title)
        window.geometry(f"{width}x{height}")
        window.focus_set()
        window.resizable(True, True)
        window.configure(fg_color=self.app.theme.BACKGROUND)
        
        # Вызываем функцию для заполнения содержимого
        content_callback(window)
        
        return window 