"""
Модуль редактора кода с подсветкой синтаксиса и другими функциями.
"""

import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox

from theme import KanagawaTheme

class CodeEditor:
    """Класс редактора кода"""
    
    def __init__(self, parent, frame):
        """
        Инициализация редактора кода
        
        Args:
            parent: родительский экземпляр приложения
            frame: фрейм, в котором размещается редактор
        """
        self.parent = parent
        self.frame = frame
        
        self.current_file = None
        self.current_filetype = '.py'  # По умолчанию Python
        self.active_line = None
        
        self._setup_ui()
        self._setup_key_bindings()
    
    def _setup_ui(self):
        """Настройка интерфейса редактора кода"""
        editor_frame = self.frame
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(1, weight=1)
        
        # Номера строк
        self.line_numbers = tk.Text(
            editor_frame, 
            width=4, 
            padx=5, 
            pady=5, 
            bd=0,
            bg=KanagawaTheme.BACKGROUND, 
            fg=KanagawaTheme.COMMENT,
            insertbackground=KanagawaTheme.CURSOR,
            selectbackground=KanagawaTheme.SELECTION,
            font=("Consolas", 11), 
            takefocus=0
        )
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.line_numbers.insert("1.0", "1")
        self.line_numbers.configure(state="disabled")
        
        # Текстовый редактор
        self.text = tk.Text(
            editor_frame, 
            wrap="none", 
            bd=0, 
            padx=5, 
            pady=5,
            bg=KanagawaTheme.BACKGROUND, 
            fg=KanagawaTheme.FOREGROUND,
            insertbackground=KanagawaTheme.CURSOR,
            selectbackground=KanagawaTheme.SELECTION,
            font=("Consolas", 11),
            undo=True  # Включаем возможность отмены/повтора
        )
        self.text.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Полосы прокрутки
        y_scrollbar = ctk.CTkScrollbar(
            editor_frame, 
            command=self._on_scroll_y,
            button_color=KanagawaTheme.SCROLLBAR,
            button_hover_color=KanagawaTheme.FOREGROUND
        )
        y_scrollbar.grid(row=0, column=2, sticky="ns")
        self.text.configure(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ctk.CTkScrollbar(
            editor_frame, 
            command=self.text.xview, 
            orientation="horizontal",
            button_color=KanagawaTheme.SCROLLBAR,
            button_hover_color=KanagawaTheme.FOREGROUND
        )
        x_scrollbar.grid(row=1, column=1, sticky="ew")
        self.text.configure(xscrollcommand=x_scrollbar.set)
        
        # Настройка тегов для подсветки синтаксиса
        self.text.tag_configure("keyword", foreground=KanagawaTheme.KEYWORD)
        self.text.tag_configure("string", foreground=KanagawaTheme.STRING)
        self.text.tag_configure("comment", foreground=KanagawaTheme.COMMENT)
        self.text.tag_configure("function", foreground=KanagawaTheme.FUNCTION)
        self.text.tag_configure("class", foreground=KanagawaTheme.CLASS)
        self.text.tag_configure("number", foreground=KanagawaTheme.NUMBER)
        self.text.tag_configure("operator", foreground=KanagawaTheme.OPERATOR)
        
        # Привязка событий
        self.text.bind("<KeyRelease>", self._on_text_change)
        self.text.bind("<ButtonRelease-1>", self._highlight_current_line)
        
        # Подсвечиваем текущую строку при запуске
        self._highlight_current_line()
    
    def _setup_key_bindings(self):
        """Настройка горячих клавиш"""
        # Основные сочетания клавиш для редактирования
        self.text.bind("<Control-a>", lambda e: self._select_all())
        self.text.bind("<Control-s>", lambda e: self.parent.save_file())
        self.text.bind("<Control-o>", lambda e: self.parent.open_file())
        self.text.bind("<Control-n>", lambda e: self.parent.new_file())
        
        # Отмена/повтор
        self.text.bind("<Control-z>", lambda e: self.text.edit_undo())
        self.text.bind("<Control-y>", lambda e: self.text.edit_redo())
        
        # Копирование/вставка/вырезание
        self.text.bind("<Control-c>", lambda e: self._copy())
        self.text.bind("<Control-v>", lambda e: self._paste())
        self.text.bind("<Control-x>", lambda e: self._cut())
        
        # Дополнительные функции
        self.text.bind("<Tab>", self._handle_tab)
        self.text.bind("<Shift-Tab>", self._handle_shift_tab)
    
    def _select_all(self):
        """Выделить весь текст"""
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, tk.END)
        return "break"  # Предотвращаем стандартное поведение Ctrl+A
    
    def _copy(self):
        """Копировать выделенный текст"""
        if self.text.tag_ranges(tk.SEL):
            self.text.event_generate("<<Copy>>")
        return "break"
    
    def _paste(self):
        """Вставить текст из буфера обмена"""
        self.text.event_generate("<<Paste>>")
        self._on_text_change(None)
        return "break"
    
    def _cut(self):
        """Вырезать выделенный текст"""
        if self.text.tag_ranges(tk.SEL):
            self.text.event_generate("<<Cut>>")
            self._on_text_change(None)
        return "break"
    
    def _handle_tab(self, event):
        """Обработка нажатия Tab - вставляет 4 пробела"""
        self.text.insert(tk.INSERT, "    ")
        return "break"  # Предотвращаем стандартное поведение Tab
    
    def _handle_shift_tab(self, event):
        """Обработка нажатия Shift+Tab - удаляет отступ"""
        # Получаем позицию курсора
        line_start = self.text.index(tk.INSERT + " linestart")
        line_text = self.text.get(line_start, line_start + " lineend")
        
        # Удаляем до 4 пробелов в начале строки
        if line_text.startswith("    "):
            self.text.delete(line_start, line_start + "+4c")
        elif line_text.startswith("   "):
            self.text.delete(line_start, line_start + "+3c")
        elif line_text.startswith("  "):
            self.text.delete(line_start, line_start + "+2c")
        elif line_text.startswith(" "):
            self.text.delete(line_start, line_start + "+1c")
        
        return "break"  # Предотвращаем стандартное поведение Shift+Tab
    
    def _on_text_change(self, event=None):
        """Обработчик изменения текста в редакторе"""
        self._update_line_numbers()
        self._highlight_syntax()
        self._highlight_current_line()
        self._update_cursor_position()
    
    def _highlight_current_line(self, event=None):
        """Подсвечивает текущую строку курсора"""
        self._update_cursor_position()
        
        # Удаляем предыдущую подсветку
        self.text.tag_remove("current_line", "1.0", tk.END)
        
        # Получаем текущую позицию курсора
        current_position = self.text.index(tk.INSERT)
        line = current_position.split('.')[0]
        
        # Подсвечиваем текущую строку
        self.text.tag_add("current_line", f"{line}.0", f"{line}.end+1c")
        self.text.tag_config("current_line", background=KanagawaTheme.LINE_HIGHLIGHT)
        
        # Обновляем активную строку в номерах строк
        if self.active_line != line:
            self.active_line = line
            self._update_line_numbers()
    
    def _update_cursor_position(self):
        """Обновляет информацию о позиции курсора"""
        current_position = self.text.index(tk.INSERT)
        line, col = current_position.split('.')
        # Обновляем статус в родительском приложении, если есть метод update_cursor_position
        if hasattr(self.parent, 'update_cursor_position'):
            self.parent.update_cursor_position()
    
    def _update_line_numbers(self):
        """Обновляет номера строк"""
        # Получаем текущий текст и считаем строки
        text_content = self.text.get("1.0", tk.END)
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
    
    def _on_scroll_y(self, *args):
        """Синхронизирует прокрутку редактора и номеров строк"""
        self.text.yview(*args)
        self.line_numbers.yview(*args)
    
    def _highlight_syntax(self):
        """Подсветка синтаксиса для кода"""
        # Удаляем все теги подсветки
        self.text.tag_remove("keyword", "1.0", tk.END)
        self.text.tag_remove("string", "1.0", tk.END)
        self.text.tag_remove("comment", "1.0", tk.END)
        self.text.tag_remove("function", "1.0", tk.END)
        self.text.tag_remove("class", "1.0", tk.END)
        self.text.tag_remove("number", "1.0", tk.END)
        self.text.tag_remove("operator", "1.0", tk.END)
        
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
                    start_pos = self.text.search(f"\\y{keyword}\\y", start_pos, tk.END, regexp=True)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(keyword)}c"
                    self.text.tag_add("keyword", start_pos, end_pos)
                    start_pos = end_pos
            
            # Операторы
            operators = ["+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "=", "+=", "-=", "*=", "/="]
            for op in operators:
                start_pos = "1.0"
                while True:
                    start_pos = self.text.search(f"{op}", start_pos, tk.END)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(op)}c"
                    self.text.tag_add("operator", start_pos, end_pos)
                    start_pos = end_pos
            
            # Числа
            start_pos = "1.0"
            while True:
                start_pos = self.text.search(r'\y\d+\y', start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                end_pos = self.text.search(r'\W', start_pos, tk.END, regexp=True)
                if not end_pos:
                    end_pos = tk.END
                self.text.tag_add("number", start_pos, end_pos)
                start_pos = end_pos
            
            # Строки
            for quote in ['"', "'"]:
                start_pos = "1.0"
                while True:
                    start_pos = self.text.search(f'{quote}', start_pos, tk.END)
                    if not start_pos:
                        break
                    end_pos = self.text.search(f'{quote}', f"{start_pos}+1c", tk.END)
                    if not end_pos:
                        break
                    end_pos = f"{end_pos}+1c"
                    self.text.tag_add("string", start_pos, end_pos)
                    start_pos = end_pos
            
            # Комментарии
            start_pos = "1.0"
            while True:
                start_pos = self.text.search('#', start_pos, tk.END)
                if not start_pos:
                    break
                line = int(float(start_pos))
                end_pos = f"{line}.end"
                self.text.tag_add("comment", start_pos, end_pos)
                start_pos = f"{line+1}.0"
            
            # Функции
            start_pos = "1.0"
            while True:
                start_pos = self.text.search('def ', start_pos, tk.END)
                if not start_pos:
                    break
                name_start = f"{start_pos}+4c"
                name_end = self.text.search('\\(', name_start, tk.END)
                if not name_end:
                    break
                self.text.tag_add("function", name_start, name_end)
                start_pos = name_end
            
            # Классы
            start_pos = "1.0"
            while True:
                start_pos = self.text.search('class ', start_pos, tk.END)
                if not start_pos:
                    break
                name_start = f"{start_pos}+6c"
                name_end = self.text.search('\\(|:', name_start, tk.END, regexp=True)
                if not name_end:
                    break
                self.text.tag_add("class", name_start, name_end)
                start_pos = name_end
    
    def get_text(self):
        """Получить весь текст из редактора"""
        return self.text.get("1.0", tk.END)
    
    def set_text(self, content):
        """Установить текст в редактор"""
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self._on_text_change()
    
    def set_current_file(self, file_path):
        """Устанавливает текущий файл"""
        self.current_file = file_path
        if file_path:
            _, ext = os.path.splitext(file_path)
            if ext:
                self.current_filetype = ext
        self._highlight_syntax()
    
    def apply_theme(self, theme):
        """
        Применяет тему к редактору кода.
        
        Args:
            theme: Объект темы с цветами
        """
        # Обновляем цвета редактора
        self.text.configure(
            bg=theme.BACKGROUND,
            fg=theme.FOREGROUND,
            insertbackground=theme.CURSOR,
            selectbackground=theme.SELECTION
        )
        
        # Обновляем цвета номеров строк
        self.line_numbers.configure(
            bg=theme.BACKGROUND,
            fg=theme.COMMENT
        )
        
        # Обновляем теги для подсветки синтаксиса
        self.text.tag_configure("keyword", foreground=theme.KEYWORD)
        self.text.tag_configure("string", foreground=theme.STRING)
        self.text.tag_configure("comment", foreground=theme.COMMENT)
        self.text.tag_configure("function", foreground=theme.FUNCTION)
        self.text.tag_configure("class", foreground=theme.CLASS)
        self.text.tag_configure("number", foreground=theme.NUMBER)
        self.text.tag_configure("operator", foreground=theme.OPERATOR)
        
        # Обновляем подсветку текущей строки
        self.text.tag_config("current_line", background=theme.LINE_HIGHLIGHT)
        
        # Применяем подсветку синтаксиса
        self._highlight_syntax()
        
        # Обновляем подсветку текущей строки
        self._highlight_current_line()
    
    def focus(self):
        """Устанавливает фокус на редактор"""
        self.text.focus_set()
    
    def insert(self, position, text):
        """Вставить текст в указанную позицию"""
        self.text.insert(position, text)
        self._on_text_change()
    
    def delete(self, start, end):
        """Удалить текст в указанном диапазоне"""
        self.text.delete(start, end)
        self._on_text_change()
    
    def insert_at_line(self, line_num, text):
        """Вставить текст на указанную строку"""
        # Проверяем валидность номера строки
        line_count = int(self.text.index(tk.END).split('.')[0])
        if line_num <= 0:
            line_num = 1
        if line_num > line_count:
            line_num = line_count
        
        # Создаем позицию вставки
        insert_position = f"{line_num}.0"
        self.text.insert(insert_position, text + "\n")
        self._on_text_change()
        
        return line_num
    
    def replace_lines(self, start_line, end_line, text):
        """Заменить указанный диапазон строк новым текстом"""
        # Проверяем валидность номеров строк
        line_count = int(self.text.index(tk.END).split('.')[0])
        if start_line <= 0:
            start_line = 1
        if end_line > line_count:
            end_line = line_count
        if start_line > end_line:
            start_line, end_line = end_line, start_line
        
        # Удаляем старые строки
        start_position = f"{start_line}.0"
        end_position = f"{end_line}.end+1c"  # +1c добавляет символ новой строки в конце
        self.text.delete(start_position, end_position)
        
        # Вставляем новый текст
        self.text.insert(start_position, text + "\n")
        self._on_text_change()
        
        return start_line 