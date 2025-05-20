"""
Модуль для работы с терминалом внутри редактора кода.
Обеспечивает функциональность командной строки.
"""

import os
import sys
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import customtkinter as ctk

from theme import KanagawaTheme

class Terminal:
    """Класс для работы с встроенным терминалом"""
    
    def __init__(self, parent, frame):
        """
        Инициализация терминала
        
        Args:
            parent: родительский экземпляр приложения
            frame: фрейм, в котором размещается терминал
        """
        self.parent = parent
        self.frame = frame
        self.shell_process = None
        self.command_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        self._setup_ui()
        self.start_shell()
    
    def _setup_ui(self):
        """Настройка интерфейса терминала"""
        # Заголовок консоли
        console_header = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.DARKER_BG, height=25)
        console_header.pack(fill="x")
        
        console_label = ctk.CTkLabel(console_header, text="ТЕРМИНАЛ", 
                                  text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        console_label.pack(side="left", padx=10)
        
        # Кнопки управления консолью
        clear_btn = ctk.CTkButton(console_header, text="🗑️", width=25, height=20, 
                               fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                               text_color=KanagawaTheme.FOREGROUND, command=self.clear)
        clear_btn.pack(side="right", padx=5)
        
        # Контейнер для консоли
        console_container = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.CONSOLE_BG)
        console_container.pack(fill="both", expand=True)
        console_container.grid_rowconfigure(0, weight=1)
        console_container.grid_columnconfigure(0, weight=1)
        
        # Текстовое поле консоли с возможностью ввода
        self.output = scrolledtext.ScrolledText(
            console_container, 
            wrap="word", 
            bd=0,
            bg=KanagawaTheme.CONSOLE_BG, 
            fg=KanagawaTheme.CONSOLE_FG,
            insertbackground=KanagawaTheme.CURSOR,
            font=("Consolas", 10), 
            padx=5, 
            pady=5
        )
        self.output.pack(fill="both", expand=True)
        
        # Устанавливаем теги для разных типов вывода
        self.output.tag_configure("error", foreground=KanagawaTheme.CONSOLE_ERROR)
        self.output.tag_configure("success", foreground=KanagawaTheme.CONSOLE_SUCCESS)
        self.output.tag_configure("info", foreground=KanagawaTheme.CONSOLE_INFO)
        self.output.tag_configure("prompt", foreground=KanagawaTheme.FUNCTION)
        
        # Добавляем привязки для обработки ввода в консоли и фокуса
        self.output.bind("<Return>", self._handle_input)
        self.output.bind("<FocusIn>", self._on_focus_in)
    
    def _on_focus_in(self, event=None):
        """Обработчик получения фокуса терминалом"""
        # Прокручиваем до конца и устанавливаем курсор в конец
        self.output.see(tk.END)
        self.output.mark_set(tk.INSERT, tk.END)
    
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
            self.write("Терминал готов к работе. Введите команду и нажмите Enter.\n", "info")
            self.write("$ ", "prompt")
        except Exception as e:
            print(f"Ошибка запуска командной оболочки: {e}")
    
    def _read_shell_output(self):
        """Читает вывод из оболочки и отправляет его в консоль"""
        if not self.shell_process:
            return
            
        while self.shell_process is not None and self.shell_process.poll() is None:
            try:
                line = self.shell_process.stdout.readline()
                if line:
                    self.output_queue.put(line)
                    # Обновляем консоль в основном потоке
                    self.parent.after(10, self._update_console_from_queue)
            except Exception:
                if self.shell_process is not None:
                    continue
                else:
                    break
    
    def _send_shell_commands(self):
        """Отправляет команды в оболочку из очереди"""
        if not self.shell_process:
            return
            
        while self.shell_process is not None and self.shell_process.poll() is None:
            try:
                if not self.command_queue.empty():
                    cmd = self.command_queue.get()
                    self.shell_process.stdin.write(f"{cmd}\n")
                    self.shell_process.stdin.flush()
            except Exception:
                if self.shell_process is not None:
                    continue
                else:
                    break
            # Небольшая задержка, чтобы не нагружать CPU
            time.sleep(0.05)
    
    def _update_console_from_queue(self):
        """Обновляет консоль выводом из очереди"""
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()
                self.write(line)
                
            # Добавляем новый промпт после вывода
            if not self.output_queue.empty():
                # Если в очереди еще есть данные, продолжаем обработку
                self.parent.after(10, self._update_console_from_queue)
            else:
                # Если очередь пуста, добавляем промпт
                # Сохраним текущее состояние readonly
                state = self.output.cget("state")
                self.output.configure(state="normal")
                self.output.insert(tk.END, "$ ", "prompt")
                # Прокручиваем до конца и устанавливаем курсор в конец
                self.output.see(tk.END)
                self.output.mark_set(tk.INSERT, tk.END)
                # Возвращаем исходное состояние
                self.output.configure(state=state)
        except Exception as e:
            print(f"Ошибка обновления консоли: {e}")
    
    def _handle_input(self, event):
        """Обрабатывает ввод в консоли"""
        try:
            # Получаем последнюю строку (текущий ввод)
            input_start = self.output.index("insert linestart")
            input_end = self.output.index("insert")
            input_text = self.output.get(input_start, input_end)
            
            # Проверяем, что ввод начинается с промпта ($)
            if input_text.startswith("$ "):
                # Извлекаем команду (убираем промпт)
                command = input_text[2:].strip()
                
                # Добавляем новую строку после ввода
                self.output.insert("insert", "\n")
                
                # Отправляем команду в оболочку
                self.command_queue.put(command)
                
                # Предотвращаем стандартное поведение клавиши Enter
                return "break"
        except Exception as e:
            print(f"Ошибка обработки ввода: {e}")
    
    def write(self, text, tag=None):
        """
        Записывает текст в консоль с опциональным тегом
        
        Args:
            text: текст для записи
            tag: опциональный тег для форматирования (error, success, info, prompt)
        """
        self.output.configure(state="normal")
        if tag:
            self.output.insert(tk.END, text, tag)
        else:
            self.output.insert(tk.END, text)
        # Прокручиваем до конца и устанавливаем курсор в конец
        self.output.see(tk.END)
        self.output.mark_set(tk.INSERT, tk.END)
        self.output.configure(state="normal")  # Оставляем редактируемым, чтобы можно было вводить команды
    
    def clear(self):
        """Очистка содержимого консоли"""
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.configure(state="normal")
        self.write("$ ", "prompt")
    
    def toggle(self):
        """Переключает видимость консоли"""
        if self.frame.winfo_viewable():
            self.frame.pack_forget()
        else:
            self.frame.pack(fill="both", side="bottom", padx=0, pady=0, expand=False, height=150)
            # Устанавливаем фокус на консоль при отображении
            self.output.focus_set()
    
    def terminate(self):
        """Завершение процесса оболочки при закрытии приложения"""
        if self.shell_process and self.shell_process.poll() is None:
            try:
                self.shell_process.terminate()
            except:
                pass
        self.shell_process = None 