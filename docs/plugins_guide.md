# Руководство по созданию плагинов для vpycode

Данное руководство объясняет, как создавать плагины для расширения функциональности IDE vpycode.

## Структура плагина

Каждый плагин представляет собой отдельный Python-файл, расположенный в одной из директорий плагинов:

- `./plugins/` - директория с плагинами, поставляемыми вместе с IDE
- `~/.vpycode/plugins/` - директория с плагинами, установленными пользователем

Плагин должен содержать класс, наследующийся от базового класса `Plugin` из модуля `plugins.base`.

## Базовый шаблон плагина

Минимальный код плагина выглядит следующим образом:

```python
from plugins.base import Plugin

class MyPlugin(Plugin):
    def __init__(self, app):
        super().__init__(app)
        self.name = "MyPlugin"  # Название плагина
        self.version = "1.0.0"  # Версия плагина
        self.description = "Мой первый плагин"  # Описание плагина
        self.author = "Ваше имя"  # Автор плагина
    
    def activate(self):
        """Активация плагина."""
        print(f"Плагин {self.name} активирован")
    
    def deactivate(self):
        """Деактивация плагина."""
        print(f"Плагин {self.name} деактивирован")
```

## Основные методы плагина

### Инициализация

```python
def __init__(self, app):
    super().__init__(app)
    # Ваш код инициализации
```

В методе `__init__` выполняется инициализация плагина. Параметр `app` - это экземпляр основного приложения vpycode.

### Активация

```python
def activate(self):
    """Активация плагина."""
    # Ваш код активации
```

Метод `activate` вызывается при активации плагина. В этом методе следует добавлять элементы интерфейса, регистрировать
обработчики событий и выполнять другие действия, связанные с добавлением функциональности.

### Деактивация

```python
def deactivate(self):
    """Деактивация плагина."""
    # Ваш код деактивации
```

Метод `deactivate` вызывается при деактивации плагина. В этом методе следует удалять добавленные элементы интерфейса,
отменять регистрацию обработчиков событий и выполнять другие действия, связанные с удалением функциональности.

## Доступные возможности для плагинов

### Добавление кнопки в боковую панель

```python
def activate(self):
    self.sidebar_button = self.add_sidebar_button("🔍", self.my_function)
```

Метод `add_sidebar_button` добавляет кнопку в боковую панель IDE. Первый параметр - текст кнопки (можно использовать emoji),
второй параметр - функция, вызываемая при нажатии на кнопку.

### Изменение темы редактора

```python
def change_to_dark_theme(self):
    theme_colors = {
        "BACKGROUND": "#121212",
        "FOREGROUND": "#E0E0E0",
        "DARKER_BG": "#0A0A0A",
        # Другие цвета...
    }
    self.change_theme(theme_colors)
```

Метод `change_theme` позволяет изменить цветовую схему редактора. Параметром является словарь с цветами, где ключи -
это названия элементов интерфейса, а значения - цвета в формате HEX.

### Добавление пункта в меню

```python
def activate(self):
    self.add_menu_command("Вид", "Мой пункт меню", self.my_function)
```

Метод `add_menu_command` добавляет пункт в одно из главных меню IDE. Первый параметр - название меню
("Файл", "Правка", "Вид", "Запуск", "Настройки"), второй параметр - название пункта, третий параметр - функция,
вызываемая при выборе пункта меню.

### Поддержка новых языков программирования

```python
def activate(self):
    self.register_language(
        language_name="JavaScript",
        file_extensions=[".js", ".mjs", ".cjs"],
        run_command=self.run_javascript,
        syntax_keywords={
            "keywords": ["var", "let", "const", "function", ...],
            "operators": ["+", "-", "==", "===", ...],
            # Другие категории ключевых слов...
        }
    )
```

Метод `register_language` регистрирует новый язык программирования в IDE. Параметры:
- `language_name` - название языка
- `file_extensions` - список расширений файлов этого языка
- `run_command` - функция для запуска кода на этом языке
- `syntax_keywords` - словарь с ключевыми словами для подсветки синтаксиса

### Добавление нового окна интерфейса

```python
def show_my_window(self):
    window = self.add_gui_window("Моё окно", self.setup_window_content, width=600, height=400)

def setup_window_content(self, window):
    # Добавление элементов в окно
    label = ctk.CTkLabel(window, text="Привет, мир!")
    label.pack(pady=20)
    
    button = ctk.CTkButton(window, text="Нажми меня", command=self.do_something)
    button.pack()
```

Метод `add_gui_window` создает новое окно интерфейса. Параметры:
- `title` - заголовок окна
- `content_callback` - функция для заполнения содержимого окна
- `width` - ширина окна
- `height` - высота окна

## Полезные свойства и методы основного приложения

- `self.app.current_file` - путь к текущему открытому файлу
- `self.app.current_project` - путь к текущему открытому проекту
- `self.app.code_editor` - текстовый виджет редактора кода
- `self.app.console_output` - текстовый виджет консольного вывода
- `self.app.write_to_console(text, tag)` - вывод текста в консоль с опциональным тегом стиля ("error", "info", "success")
- `self.app.status_text` - виджет строки состояния в нижней части IDE

## Пример полноценного плагина

Вот пример плагина, который добавляет функциональность форматирования кода Python:

```python
import subprocess
from plugins.base import Plugin
import tkinter as tk
import customtkinter as ctk

class PythonFormatter(Plugin):
    def __init__(self, app):
        super().__init__(app)
        self.name = "PythonFormatter"
        self.version = "1.0.0"
        self.description = "Форматирование Python-кода с помощью Black"
        self.author = "vpycode Team"
        
        # Проверяем наличие Black
        self.black_available = self._check_black_available()
        
    def activate(self):
        """Активация плагина."""
        # Добавляем кнопку в боковую панель
        self.sidebar_button = self.add_sidebar_button("🧹", self.show_format_options)
        
        # Добавляем команду в меню "Правка"
        self.add_menu_command("Правка", "Форматировать код", self.format_current_file)
        
        if not self.black_available:
            self.app.write_to_console("Предупреждение: Black не установлен. Установите его через pip install black\n", "error")
    
    def deactivate(self):
        """Деактивация плагина."""
        # Ничего особенного при деактивации не делаем
        pass
    
    def _check_black_available(self):
        """Проверяет, установлен ли Black"""
        try:
            subprocess.run(["black", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False
    
    def format_current_file(self):
        """Форматирует текущий файл с помощью Black"""
        if not self.black_available:
            self.app.write_to_console("Black не установлен. Установите его через pip install black\n", "error")
            return
            
        # Проверяем, что открыт Python-файл
        current_file = self.app.current_file
        if not current_file or not current_file.lower().endswith('.py'):
            self.app.write_to_console("Текущий файл не является Python-файлом.\n", "error")
            return
            
        try:
            # Сохраняем текущий файл
            self.app.save_file()
            
            # Запускаем Black для форматирования файла
            result = subprocess.run(
                ["black", current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                self.app.write_to_console("Файл успешно отформатирован.\n", "success")
                
                # Перезагружаем файл, чтобы увидеть изменения
                self.app.load_file(current_file)
            else:
                self.app.write_to_console(f"Ошибка форматирования: {result.stderr}\n", "error")
                
        except Exception as e:
            self.app.write_to_console(f"Ошибка: {str(e)}\n", "error")
    
    def show_format_options(self):
        """Показывает окно с настройками форматирования"""
        options_window = self.add_gui_window(
            "Настройки форматирования", 
            self._setup_options_content, 
            width=400, 
            height=300
        )
    
    def _setup_options_content(self, window):
        """Настраивает содержимое окна настроек форматирования"""
        # Заголовок
        header_label = ctk.CTkLabel(
            window, 
            text="Настройки форматирования Python-кода", 
            font=("Arial", 14, "bold"),
            text_color=self.app.theme.FOREGROUND
        )
        header_label.pack(pady=(20, 10))
        
        # Опции форматирования
        options_frame = ctk.CTkFrame(window, fg_color="transparent")
        options_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Переключатель для опции "Форматировать при сохранении"
        format_on_save_var = tk.BooleanVar(value=False)
        format_on_save = ctk.CTkCheckBox(
            options_frame, 
            text="Форматировать при сохранении", 
            variable=format_on_save_var,
            text_color=self.app.theme.FOREGROUND
        )
        format_on_save.pack(anchor="w", pady=10)
        
        # Кнопка "Форматировать сейчас"
        format_now_btn = ctk.CTkButton(
            options_frame,
            text="Форматировать текущий файл",
            fg_color=self.app.theme.BUTTON_BG,
            hover_color=self.app.theme.BUTTON_HOVER,
            text_color=self.app.theme.FOREGROUND,
            command=self.format_current_file
        )
        format_now_btn.pack(pady=10)
        
        # Информация о Black
        info_label = ctk.CTkLabel(
            options_frame, 
            text="Используется форматтер Black",
            text_color=self.app.theme.COMMENT,
            font=("Arial", 10)
        )
        info_label.pack(pady=(20, 0))
        
        # Статус Black
        status_text = "Установлен" if self.black_available else "Не установлен"
        status_color = self.app.theme.CONSOLE_SUCCESS if self.black_available else self.app.theme.CONSOLE_ERROR
        status_label = ctk.CTkLabel(
            options_frame, 
            text=f"Статус Black: {status_text}",
            text_color=status_color,
            font=("Arial", 10)
        )
        status_label.pack(pady=(5, 0))
```

## Рекомендации по разработке плагинов

1. **Проверяйте наличие зависимостей**: Если ваш плагин использует внешние библиотеки, проверяйте их наличие при активации и информируйте пользователя, если что-то не установлено.

2. **Обрабатывайте ошибки**: Всегда оборачивайте потенциально опасный код в блоки try-except, чтобы ошибки в вашем плагине не приводили к падению всего приложения.

3. **Информируйте пользователя**: Используйте метод `self.app.write_to_console` и строку состояния для информирования пользователя о выполняемых действиях и возникающих проблемах.

4. **Корректно освобождайте ресурсы**: В методе `deactivate` освобождайте все ресурсы, которые были захвачены во время работы плагина.

5. **Следуйте стилю интерфейса**: Используйте цвета из `self.app.theme` для согласованного внешнего вида вашего плагина с остальной частью IDE.

6. **Тестируйте на разных платформах**: Убедитесь, что ваш плагин работает как в Windows, так и в Linux/macOS, если он содержит платформозависимый код. 