"""Модуль для работы с чатом ИИ в редакторе кода."""
import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, Frame, Scrollbar, Text, Button, Label, Menu, filedialog
import threading
import requests
import json
import re
import os
import time
import sys  # Add sys import for flush
import traceback  # Add traceback for better error reporting
import logging

from theme import KanagawaTheme
from ai_defaults import DEFAULT_AI_PROMPT, API_URL, DEFAULT_API_SETTINGS, CODE_BLOCK_PATTERN, READ_FILE_PATTERN, CODE_BLOCK_LINE_PATTERN, CODE_BLOCK_LINES_PATTERN, JSON_CODE_PATTERN, JSON_STOP_PATTERN, JSON_READ_FILE_PATTERN, JSON_EXECUTE_PATTERN

class AiChat:
    """Класс для работы с чатом ИИ"""
    
    def __init__(self, parent, frame):
        """
        Инициализация чата ИИ
        
        Args:
            parent: родительский экземпляр приложения
            frame: фрейм, в котором размещается чат
        """
        # Настраиваем логгирование
        self._setup_logging()
        
        # Debug - проверяем состояние stdout сразу при инициализации
        self.log_debug("=== ИНИЦИАЛИЗАЦИЯ AI CHAT ===")
        self.log_debug(f"Python version: {sys.version}")
        
        # Запускаем тест логирования
        self._test_debug_output()
        
        self.parent = parent
        self.frame = frame
        
        # История сообщений для контекста
        self.chat_messages = []
        
        # Флаг для отправки начальной инструкции
        self.is_first_message = True
        
        # Переменные для работы со стримингом
        self.response_active = False
        self.current_response = ""
        
        # Флаг для принудительной остановки генерации
        self.stop_generation = False
        
        # Загружаем настройки ИИ
        self.ai_settings = self._load_ai_settings()
        
        # Для отслеживания структуры проекта
        self.last_project_structure = ""
        
        self._setup_ui()
        
    
    def _setup_logging(self):
        """Настраивает логгирование в файл"""
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            log_file = os.path.join(log_dir, f"ai_chat_{time.strftime('%Y%m%d_%H%M%S')}.log")
            
            # Создаем логгер с именем модуля
            self.logger = logging.getLogger("ai_chat")
            self.logger.setLevel(logging.DEBUG)
            
            # Обработчик для файла
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Обработчик для консоли
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # Формат сообщений
            formatter = logging.Formatter('[%(asctime)s][%(threadName)s] %(levelname)s: %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Очищаем существующие обработчики
            if self.logger.handlers:
                self.logger.handlers.clear()
                
            # Добавляем обработчики к логгеру
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            # Предотвращаем передачу логов вверх к родительским логгерам
            self.logger.propagate = False
            
            # Выводим в консоль и в лог информацию о начале работы
            self.logger.info(f"Логгирование настроено. Лог файл: {log_file}")
            
        except Exception as e:
            print(f"Ошибка при настройке логгирования: {str(e)}")
            traceback.print_exc()
            self.logger = None
    
    def log_debug(self, message):
        """Логгирует отладочное сообщение"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.debug(message)
        
    def log_info(self, message):
        """Логгирует информационное сообщение"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(message)
        
    def log_error(self, message):
        """Логгирует сообщение об ошибке"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.error(message)
    
    def log_warning(self, message):
        """Логгирует предупреждение"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.warning(message)
    
    def _load_ai_settings(self):
        """Загружает настройки ИИ из файла"""
        ai_settings_file = "ai_settings.json"
        # Проверяем, существует ли основной файл настроек
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "ai_settings_file" in settings:
                        ai_settings_file = settings["ai_settings_file"]
            except:
                pass
        
        # Загружаем настройки ИИ
        default_settings = {
            "initial_prompt": DEFAULT_AI_PROMPT,
            "api_settings": DEFAULT_API_SETTINGS,
            "code_insertion_enabled": True,
            "auto_continue_enabled": True
        }
        
        if os.path.exists(ai_settings_file):
            try:
                with open(ai_settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    
                    # Проверяем, есть ли initial_prompt в загруженных настройках
                    # Если нет или пустой, используем значение по умолчанию
                    if "initial_prompt" not in loaded_settings or not loaded_settings["initial_prompt"]:
                        self.log_warning("Отсутствует initial_prompt в настройках ИИ, использую значение по умолчанию")
                        loaded_settings["initial_prompt"] = DEFAULT_AI_PROMPT
                    
                    # Добавляем auto_continue_enabled если его нет
                    if "auto_continue_enabled" not in loaded_settings:
                        loaded_settings["auto_continue_enabled"] = True
                    
                    return loaded_settings
            except Exception as e:
                self.log_error(f"Ошибка при загрузке настроек ИИ: {str(e)}")
                return default_settings
        else:
            # Создаем файл настроек ИИ, если он не существует
            try:
                with open(ai_settings_file, "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, indent=4)
            except:
                pass
            return default_settings
    
    def _setup_ui(self):
        """Настройка интерфейса чата ИИ"""
        # Заголовок чата
        ai_header = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.DARKER_BG, height=30)
        ai_header.pack(fill="x")
        
        ai_label = ctk.CTkLabel(ai_header, text="ИИ АССИСТЕНТ (DeepSeek-R1)", 
                               text_color=KanagawaTheme.FOREGROUND, font=("Arial", 10, "bold"))
        ai_label.pack(side="left", padx=10)
        
        # Добавляем кнопку очистки истории
        clear_btn = ctk.CTkButton(ai_header, text="🗑️", width=25, height=20, 
                                fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                text_color=KanagawaTheme.FOREGROUND, command=self.clear_history)
        clear_btn.pack(side="right", padx=5)
        
        # Кнопка настроек AI
        settings_btn = ctk.CTkButton(ai_header, text="⚙️", width=25, height=20, 
                                   fg_color="transparent", hover_color=KanagawaTheme.LIGHTER_BG,
                                   text_color=KanagawaTheme.FOREGROUND, 
                                   command=lambda: self.parent.show_settings_dialog("ai"))
        settings_btn.pack(side="right", padx=5)
        
        # Контейнер для чата
        chat_container = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.AI_BG)
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
            font=("Consolas", 10), 
            padx=5, 
            pady=5
        )
        self.chat_history.pack(fill="both", expand=True, side="top")
        self.chat_history.configure(state="disabled")
        
        # Теги для разных типов сообщений
        self.chat_history.tag_configure("user", foreground=KanagawaTheme.AI_USER_MSG)
        self.chat_history.tag_configure("bot", foreground=KanagawaTheme.AI_BOT_MSG)
        self.chat_history.tag_configure("system", foreground=KanagawaTheme.AI_ACCENT)
        self.chat_history.tag_configure("error", foreground=KanagawaTheme.CONSOLE_ERROR)
        self.chat_history.tag_configure("loading", foreground=KanagawaTheme.AI_BOT_MSG)
        self.chat_history.tag_configure("info", foreground=KanagawaTheme.CONSOLE_INFO)
        self.chat_history.tag_configure("code", foreground=KanagawaTheme.FUNCTION)
        self.chat_history.tag_configure("insert_button", foreground=KanagawaTheme.STRING)
        
        # Привязка для кнопок вставки кода
        self.chat_history.tag_bind("insert_button", "<Button-1>", self._on_insert_code_click)
        
        # Скроллбар для истории чата
        scrollbar = ctk.CTkScrollbar(chat_container, command=self.chat_history.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_history.config(yscrollcommand=scrollbar.set)
        
        # Контейнер для поля ввода
        input_container = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.DARKER_BG)
        input_container.pack(fill="x", pady=(0, 5), padx=5)
        
        # Поле ввода сообщения
        self.chat_input = tk.Text(
            input_container, 
            wrap="word", 
            height=3, 
            bd=0,
            bg=KanagawaTheme.BACKGROUND, 
            fg=KanagawaTheme.FOREGROUND,
            insertbackground=KanagawaTheme.CURSOR,
            font=("Consolas", 10), 
            padx=5, 
            pady=5
        )
        self.chat_input.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        # Подсказка для поля ввода
        self.chat_input.insert("1.0", "Введите ваш запрос к ИИ...")
        self.chat_input.bind("<FocusIn>", lambda e: self.chat_input.delete("1.0", tk.END) if self.chat_input.get("1.0", tk.END).strip() == "Введите ваш запрос к ИИ..." else None)
        self.chat_input.bind("<FocusOut>", lambda e: self.chat_input.insert("1.0", "Введите ваш запрос к ИИ...") if not self.chat_input.get("1.0", tk.END).strip() else None)
        
        # Привязка Enter для отправки сообщения
        self.chat_input.bind("<Return>", self._handle_enter)
        
        # Контейнер для кнопки отправки
        button_frame = ctk.CTkFrame(input_container, fg_color="transparent")
        button_frame.pack(side="right", padx=5, pady=10)
        
        # Кнопка остановки генерации (изначально скрыта)
        self.stop_button = ctk.CTkButton(
            button_frame, 
            text="⏹️", 
            width=40, 
            height=30,
            fg_color=KanagawaTheme.CONSOLE_ERROR,
            hover_color=KanagawaTheme.OPERATOR,
            text_color=KanagawaTheme.FOREGROUND,
            command=self.stop_response_generation
        )
        # Кнопка остановки изначально скрыта
        
        # Кнопка отправки сообщения
        self.send_button = ctk.CTkButton(
            button_frame, 
            text="▶", 
            width=40, 
            height=30,
            fg_color=KanagawaTheme.AI_ACCENT,
            hover_color=KanagawaTheme.BUTTON_HOVER,
            text_color=KanagawaTheme.FOREGROUND,
            command=self.send_message
        )
        self.send_button.pack(side="right")
        
        # Хранилище для блоков кода из ответов ИИ
        self.code_blocks = {}
        self.next_code_id = 1
        
        # Добавляем приветственное сообщение
        self.add_bot_message("Привет! Я ИИ-ассистент на основе DeepSeek-R1. Чтобы начать работу, введите свой вопрос или нажмите на иконку настроек, чтобы настроить API ключ.")
    
    def _handle_enter(self, event):
        """Обработка нажатия Enter в поле ввода"""
        # Если нажат Shift+Enter, добавляем перевод строки
        if event.state & 0x1:  # 0x1 - маска для Shift
            return
        
        # Иначе отправляем сообщение
        self.send_message()
        return "break"  # Предотвращаем стандартное поведение Enter
    
    def send_message(self):
        """Отправка сообщения в чат"""
        # Получаем текст сообщения
        message = self.chat_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Проверка, не идет ли уже генерация
        if self.response_active:
            return
            
        # Очищаем поле ввода
        self.chat_input.delete("1.0", tk.END)
        
        # Команда проверки структуры проекта
        if message.lower() == "проверка структуры":
            self.add_user_message(message)
            # Показываем начало ответа
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "Ассистент: ", "system")
            
            # Получаем структуру проекта напрямую для проверки
            try:
                current_dir = os.getcwd()
                structure = self._get_simple_project_structure(current_dir)
                
                debug_info = f"Проверка структуры проекта:\n\n"
                debug_info += f"Текущая директория: {current_dir}\n"
                debug_info += f"Структура получена: {'Да' if structure else 'Нет'}\n"
                debug_info += f"Размер структуры: {len(structure)} символов\n\n"
                debug_info += f"Первые 200 символов структуры:\n```\n{structure[:200]}...\n```\n\n"
                
                # Отправляем запрос к API и обрабатываем его
                response = self._send_request_with_retries(structure)
                if response is not None:
                    self.chat_history.insert(tk.END, response, "user")
                else:
                    self.chat_history.insert(tk.END, "Не удалось получить ответ от ассистента.", "error")
                
            except Exception as e:
                self.chat_history.insert(tk.END, f"Ошибка при получении структуры: {str(e)}", "error")
            finally:
                self.chat_history.configure(state="disabled")

    def _send_request_with_retries(self, data):
        """Отправка данных с повторными попытками при неудаче"""
        api_url = "YOUR_API_ENDPOINT"
        headers = {"Authorization": "Bearer YOUR_API_KEY"}
        retry_count = 0
        success = False

        while retry_count < 10:
            try:
                response = requests.post(api_url, headers=headers, json={"data": data})
                response.raise_for_status()  # Проверка статуса ответа
                return response.json()  # Возврат успешного ответа
            except requests.exceptions.RequestException as e:
                retry_count += 1
                wait_time = 2 ** retry_count  # Экспоненциальное время ожидания
                print(f"Ошибка: {str(e)}. Повторная попытка {retry_count}/10 через {wait_time} секунд.")
                time.sleep(wait_time)  # Ожидание перед повтором

        print("Ошибка: максимальное количество попыток исчерпано.")
        return None  # Возврат None в случае неудачи
    
    def _get_simple_project_structure(self, directory):
        """Получает простую структуру проекта без рекурсии"""
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
                # Показываем содержимое директорий
                try:
                    subdir = os.path.join(directory, d)
                    subitems = sorted(os.listdir(subdir))[:10]
                    for subitem in subitems:
                        if subitem.startswith('.'):
                            continue
                        if os.path.isdir(os.path.join(subdir, subitem)):
                            structure += f"  📁 {d}/{subitem}/\n"
                        else:
                            structure += f"  📄 {d}/{subitem}\n"
                except Exception as e:
                    structure += f"  ⚠️ Ошибка чтения директории: {str(e)}\n"
            
            # Выводим файлы в корневой директории
            for f in files:
                structure += f"📄 {f}\n"
                
        except Exception as e:
            print(f"Ошибка при получении простой структуры проекта: {str(e)}")
            structure = f"Ошибка: {str(e)}"
            
        return structure
    
    def _console_log(self, message):
        """Специальный метод для вывода в консоль с гарантированным flush"""
        self.log_debug(message)
    
    def _generate_response(self, message):
        """Генерирует ответ от нейросети"""
        # Проверяем наличие API ключа
        try:
            api_key = self.parent.settings.ai_api_key
            if not api_key:
                self._update_response(
                    "Ошибка: API ключ OpenRouter не настроен. Пожалуйста, нажмите на иконку ⚙️ и добавьте ключ в настройках.\n\n" +
                    "Чтобы получить API-ключ, зарегистрируйтесь на сайте https://openrouter.ai и создайте ключ в настройках аккаунта.", 
                    "error"
                )
                # Восстанавливаем кнопки
                self.stop_button.pack_forget()
                self.send_button.pack(side="right")
                return
        except Exception as e:
            self._update_response(f"Ошибка при проверке API ключа: {str(e)}", "error")
            # Восстанавливаем кнопки
            self.stop_button.pack_forget()
            self.send_button.pack(side="right")
            return
            
        # Подготавливаем сообщения для API
        messages = []
        
        # Всегда добавляем системную инструкцию для каждого запроса
        initial_prompt = self.ai_settings.get("initial_prompt", DEFAULT_AI_PROMPT)
        
        # Дополнительная проверка на случай, если начальная инструкция пуста
        if not initial_prompt or len(initial_prompt.strip()) == 0:
            self.log_warning("initial_prompt пуст, использую значение по умолчанию")
            initial_prompt = DEFAULT_AI_PROMPT
            
            # Сохраняем обновленные настройки на будущее
            self.ai_settings["initial_prompt"] = DEFAULT_AI_PROMPT
            try:
                with open("ai_settings.json", "w", encoding="utf-8") as f:
                    json.dump(self.ai_settings, f, indent=4)
            except Exception as e:
                self.log_error(f"Не удалось сохранить обновленные настройки ИИ: {str(e)}")
        
        # Добавляем системную инструкцию 
        messages.append({
            "role": "system",
            "content": initial_prompt
        })
        
        # Логируем для отладки
        self.log_debug(f"Используется начальная инструкция длиной {len(initial_prompt)} символов")
        
        # ВСЕГДА собираем свежую структуру проекта для каждого запроса
        try:
            # Собираем структуру проекта напрямую
            current_dir = os.getcwd()
            structure = ""
            
            files = []
            dirs = []
            
            # Получаем список файлов и директорий
            for item in os.listdir(current_dir):
                if item.startswith('.'):
                    continue
                full_path = os.path.join(current_dir, item)
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
                # Показываем содержимое директорий
                try:
                    subdir = os.path.join(current_dir, d)
                    subitems = sorted(os.listdir(subdir))[:10]
                    for subitem in subitems:
                        if subitem.startswith('.'):
                            continue
                        if os.path.isdir(os.path.join(subdir, subitem)):
                            structure += f"  📁 {d}/{subitem}/\n"
                        else:
                            structure += f"  📄 {d}/{subitem}\n"
                except Exception as e:
                    structure += f"  ⚠️ Ошибка чтения директории: {str(e)}\n"
            
            # Выводим файлы в корневой директории
            for f in files:
                structure += f"📄 {f}\n"
            
        except Exception as e:
            structure = f"Ошибка при сборе структуры проекта: {str(e)}"
            self.log_error(f"Ошибка при сборе структуры проекта: {str(e)}")
        
        # Всегда добавляем структуру проекта в каждый запрос
        if structure:
            structure_message = {
                "role": "system",
                "content": f"Текущая структура файловой системы проекта:\n{structure}"
            }
            messages.append(structure_message)
            # Сохраняем последнюю структуру
            self.last_project_structure = structure
        
        # Добавляем историю сообщений (максимум последние 10 для экономии токенов)
        messages.extend(self.chat_messages[-10:])
        
        try:
            # Устанавливаем флаг активного ответа
            self.response_active = True
            self.current_response = ""
            
            # Запускаем стриминговый запрос к API
            self._call_api_streaming(messages)
            
            # Проверяем наличие сигнала остановки
            if self.stop_generation:
                # Возвращаем кнопки в исходное состояние
                self.parent.after(0, lambda: self.stop_button.pack_forget())
                self.parent.after(0, lambda: self.send_button.pack(side="right"))
                return
            
            # Выводим полный ответ нейросети
            print("\n===== ПОЛНЫЙ ОТВЕТ ОТ НЕЙРОСЕТИ (ДО ОБРАБОТКИ) =====")
            print(self.current_response)
            print("===============================================\n")
            sys.stdout.flush()
            
            # Сохраняем ответ в историю сообщений
            self.chat_messages.append({"role": "assistant", "content": self.current_response})
            
            # Обрабатываем блоки кода в ответе
            processed_result = self._process_code_blocks(self.current_response)
            
            # Если обработчик вернул None, это означает, что он обнаружил запрос на чтение файла или
            # выполнение команды и уже запустил соответствующий процесс - завершаем обработку
            if processed_result is None:
                # Сбрасываем флаг активного ответа
                self.response_active = False
                return
            
            # Заменяем текущий ответ на обработанную версию, если они отличаются
            if processed_result != self.current_response:
                # Очищаем текущий ответ
                self.chat_history.configure(state="normal")
                # Определяем, где начинается текущий ответ
                last_assistant = self.chat_history.search("Ассистент: ", "end-1c linestart", backwards=True)
                if last_assistant:
                    # Удаляем текст после "Ассистент: "
                    start_pos = f"{last_assistant}+10c"  # 10 символов для "Ассистент: "
                    self.chat_history.delete(start_pos, "end-1c")
                    # Вставляем обработанное сообщение
                    self._format_final_response(processed_result)
                
                self.chat_history.configure(state="disabled")
                self.chat_history.see(tk.END)
            
            # Добавляем пустую строку в конце для отступа
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "\n\n")
            self.chat_history.configure(state="disabled")
            self.chat_history.see(tk.END)
            
        except Exception as e:
            error_message = str(e)
            
            # Логируем ошибку 
            print(f"ОШИБКА: {error_message}")
            sys.stdout.flush()
            
            # Логируем полный стек ошибки в файл
            try:
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                traceback_file = os.path.join(log_dir, "traceback.log")
                with open(traceback_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    traceback.print_exc(file=f)
            except:
                print("Не удалось записать стек ошибки в файл")
                sys.stdout.flush()
            
            # Добавляем справочную информацию для определенных ошибок
            if "недостаточно средств" in error_message.lower():
                error_message += "\n\nЧтобы пополнить баланс:\n1. Войдите в личный кабинет OpenRouter\n2. Перейдите в раздел Billing\n3. Следуйте инструкциям для пополнения счета"
            
            # Сообщаем пользователю об ошибке
            self._update_response(f"Произошла ошибка: {error_message}", "error")
        finally:
            # В любом случае скрываем кнопку остановки и показываем кнопку отправки
            self.parent.after(0, lambda: self.stop_button.pack_forget())
            self.parent.after(0, lambda: self.send_button.pack(side="right"))
            # Сбрасываем флаг активного ответа
            self.response_active = False
            # Убеждаемся, что данные выведены
            sys.stdout.flush()
    
    def _get_fresh_project_structure(self):
        """Получает актуальную структуру файловой системы проекта"""
        try:
            # Приоритеты директорий для сканирования:
            # 1. Открытый проект в интерфейсе (если есть)
            # 2. Текущая рабочая директория
            # 3. Директория запуска скрипта
            
            if hasattr(self.parent, "current_project") and self.parent.current_project:
                project_dir = self.parent.current_project
                print(f"Получаем структуру проекта из открытого проекта: {project_dir}")
            else:
                # Если нет текущего проекта, используем текущую директорию
                project_dir = os.getcwd()
                print(f"Используем текущую директорию как проект: {project_dir}")
            
            # Проверяем, что директория проекта существует
            if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
                print(f"ОШИБКА: Путь проекта не существует или не является директорией: {project_dir}")
                return f"Путь проекта не существует или не является директорией: {project_dir}"
                
            # НОВЫЙ СПОСОБ: Ручное построение структуры проекта
            # Этот подход более надёжен и прост, чем рекурсивный обход
            print(f"Собираем структуру проекта напрямую...")
            structure = ""
            
            items = sorted(os.listdir(project_dir))
            files = [item for item in items if os.path.isfile(os.path.join(project_dir, item)) and not item.startswith('.')]
            dirs = [item for item in items if os.path.isdir(os.path.join(project_dir, item)) and not item.startswith('.')]
            
            # Выводим сначала директории
            for d in dirs:
                dir_path = os.path.join(project_dir, d)
                structure += f"📁 {d}/\n"
                try:
                    # Показываем до 10 файлов в каждой директории
                    subitems = sorted(os.listdir(dir_path))[:10]
                    for subitem in subitems:
                        if subitem.startswith('.'):
                            continue
                        if os.path.isdir(os.path.join(dir_path, subitem)):
                            structure += f"  📁 {d}/{subitem}/\n"
                        else:
                            structure += f"  📄 {d}/{subitem}\n"
                    
                    # Если есть еще файлы, показываем счетчик
                    total_items = len(os.listdir(dir_path))
                    if total_items > 10:
                        structure += f"  ... и еще {total_items-10} элементов\n"
                except Exception as e:
                    structure += f"  ⚠️ Ошибка доступа к директории: {str(e)}\n"
            
            # Затем выводим файлы
            for f in files:
                structure += f"📄 {f}\n"
            
            if not structure:
                print("ВНИМАНИЕ: Структура проекта пуста.")
                return "Структура проекта пуста или нет доступных файлов"
            
            print(f"Успешно получена структура проекта ({len(structure)} символов)")
            # Выведем небольшой фрагмент для проверки
            preview = structure[:200] + "..." if len(structure) > 200 else structure
            print(f"Фрагмент структуры: {preview}")
            
            return structure
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА при получении структуры проекта: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Ошибка при получении структуры проекта: {str(e)}"
    
    def _handle_file_read_request(self, file_path):
        """Обрабатывает запрос на чтение файла от нейросети"""
        try:
            print(f"Обрабатываем запрос на чтение файла: {file_path}")
            # Нормализуем путь - проверяем абсолютный или относительный
            if not os.path.isabs(file_path):
                if hasattr(self.parent, "current_project") and self.parent.current_project:
                    file_path = os.path.join(self.parent.current_project, file_path)
                else:
                    # Если нет текущего проекта, используем каталог запуска
                    file_path = os.path.join(os.getcwd(), file_path)
            
            print(f"Полный путь к файлу: {file_path}")
            # Проверка существования файла
            if not os.path.exists(file_path):
                self._update_response(f"\nОшибка: Файл '{file_path}' не найден.", "error")
                return
            
            # Лимит на размер файла (например, 1 МБ)
            max_file_size = 1024 * 1024
            if os.path.getsize(file_path) > max_file_size:
                self._update_response(f"\nОшибка: Файл '{file_path}' слишком большой для чтения (> 1 МБ).", "error")
                return
            
            # Читаем содержимое файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    print(f"Файл успешно прочитан: {len(file_content)} символов")
            except UnicodeDecodeError:
                try:
                    # Пробуем другие кодировки
                    with open(file_path, 'r', encoding='latin-1') as f:
                        file_content = f.read()
                        print(f"Файл прочитан в кодировке latin-1: {len(file_content)} символов")
                except Exception as e:
                    # Если не удалось открыть как текстовый файл - сообщаем об ошибке
                    self._update_response(f"\nОшибка: Файл '{file_path}' не является текстовым файлом или использует нестандартную кодировку.", "error")
                    return
            
            # Добавляем сообщение о чтении файла
            self._update_response(f"Читаю файл: {os.path.basename(file_path)}\n", "info")
            
            # Формируем новый запрос с содержимым файла и структурой проекта
            message = f"""Содержимое файла '{file_path}':

```
{file_content}
```

ДЕЙСТВУЙ С ФАЙЛОМ: Теперь, когда ты видишь содержимое файла, продолжи выполнение запроса. НЕ нужно описывать содержимое файла, просто выполни нужные действия.
ПОМНИ:
1. Используй маркеры ###CODE_INSERT для вставки или изменения кода
2. Не используй выдуманные команды
3. НЕ нужно оборачивать маркеры ###CODE_INSERT в блоки ```."""
            
            # Сохраняем в историю чата
            self.chat_messages.append({"role": "user", "content": message})
            
            # НЕ показываем в интерфейсе, т.к. это внутренний запрос
            # self.add_user_message(message)
            
            # Запускаем новый запрос с содержимым файла
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "Анализирую файл...", "info")
            self.chat_history.configure(state="disabled")
            self.chat_history.see(tk.END)
            
            # Генерируем новый ответ с содержимым файла
            threading.Thread(target=self._generate_response, args=(message,)).start()
            
        except Exception as e:
            print(f"Ошибка при чтении файла: {str(e)}")
            self._update_response(f"\nОшибка чтения файла: {str(e)}", "error")
            
    def _process_code_blocks(self, message):
        """Обрабатывает блоки кода в сообщении"""
        processed_message = message
        
        # Сначала пробуем обработать JSON блоки
        json_result = self._process_json_code_blocks(processed_message)
        # Если JSON-обработчик вернул None, это означает, что он обнаружил запрос на чтение файла или
        # выполнение команды и уже запустил соответствующий процесс - прерываем дальнейшую обработку
        if json_result is None:
            return None
        
        # Иначе продолжаем с обработанным сообщением
        processed_message = json_result
        
        # Для обратной совместимости проверяем старые теги, но только если не было JSON-блоков
        # которые что-то изменили в сообщении
        if processed_message == message:
            # Логируем исходное сообщение перед обработкой для отладки
            print("\n===== ИСХОДНЫЙ ТЕКСТ С МАРКЕРАМИ ВСТАВКИ КОДА (ДО ОБРАБОТКИ) =====")
            print(message)
            print("================================================================\n")
            sys.stdout.flush()
            
            # Обработка устаревших тегов вставки кода с указанием строки
            line_matches = re.findall(CODE_BLOCK_LINE_PATTERN, message, re.DOTALL)
            if line_matches:
                for match_idx, (line_num, code_content) in enumerate(line_matches):
                    # Логируем найденный блок кода
                    print(f"\n=== НАЙДЕН БЛОК КОДА ДЛЯ СТРОКИ {line_num} (устаревший формат) ===")
                    print(f"Содержимое блока кода:\n{code_content}")
                    print("=======================================\n")
                    sys.stdout.flush()
                    
                    # Очищаем содержимое кода
                    code_content = code_content.strip()
                    
                    # Формируем тег для отображения кода с подсветкой синтаксиса
                    tag = f"```\n{code_content}\n```"
                    
                    # Готовим тег для замены
                    full_tag_pattern = r'###CODE_INSERT:' + re.escape(line_num) + r'\s*(.*?)###END_INSERT'
                    full_tag_match = re.search(full_tag_pattern, message, re.DOTALL)
                    
                    if full_tag_match:
                        original_tag = full_tag_match.group(0)
                        
                        # Сохраняем блок кода для возможной вставки
                        code_id = self.next_code_id
                        self.code_blocks[code_id] = {
                            'type': 'line',
                            'line': int(line_num),
                            'code': code_content,
                            'language': ""
                        }
                        self.next_code_id += 1
                        
                        # Заменяем тег в сообщении
                        insert_button = f"\n{tag}\n[Вставить код в редактор на строку {line_num}] (ID: {code_id})\n"
                        processed_message = processed_message.replace(original_tag, insert_button)
                        
                        # Если включена автоматическая вставка кода
                        if self.ai_settings.get("code_insertion_enabled", True):
                            # Проверяем, есть ли доступ к редактору
                            if hasattr(self.parent, '_insert_code_to_editor'):
                                self.parent._insert_code_to_editor(code_content, "line", int(line_num), None, None)
                                processed_message = processed_message.replace(insert_button, 
                                    f"\n{tag}\n\n*Код автоматически вставлен в строку {line_num}*\n")
            
            # Обработка тегов вставки кода с указанием диапазона строк
            lines_matches = re.findall(CODE_BLOCK_LINES_PATTERN, message, re.DOTALL)
            if lines_matches:
                for match_idx, (start_line, end_line, code_content) in enumerate(lines_matches):
                    # Логируем найденный блок кода
                    print(f"\n=== НАЙДЕН БЛОК КОДА ДЛЯ СТРОК {start_line}-{end_line} (устаревший формат) ===")
                    print(f"Содержимое блока кода:\n{code_content}")
                    print("=======================================\n")
                    sys.stdout.flush()
                    
                    # Очищаем содержимое кода
                    code_content = code_content.strip()
                    
                    # Формируем тег для отображения кода с подсветкой синтаксиса
                    tag = f"```\n{code_content}\n```"
                    
                    # Готовим тег для замены
                    full_tag_pattern = r'###CODE_INSERT:' + re.escape(start_line) + r'-' + re.escape(end_line) + r'\s*(.*?)###END_INSERT'
                    full_tag_match = re.search(full_tag_pattern, message, re.DOTALL)
                    
                    if full_tag_match:
                        original_tag = full_tag_match.group(0)
                        
                        # Сохраняем блок кода для возможной вставки
                        code_id = self.next_code_id
                        self.code_blocks[code_id] = {
                            'type': 'range',
                            'start_line': int(start_line),
                            'end_line': int(end_line),
                            'code': code_content,
                            'language': ""
                        }
                        self.next_code_id += 1
                        
                        # Заменяем тег в сообщении
                        insert_button = f"\n{tag}\n[Заменить строки {start_line}-{end_line} кодом] (ID: {code_id})\n"
                        processed_message = processed_message.replace(original_tag, insert_button)
                        
                        # Если включена автоматическая вставка кода
                        if self.ai_settings.get("code_insertion_enabled", True):
                            # Проверяем, есть ли доступ к редактору
                            if hasattr(self.parent, '_insert_code_to_editor'):
                                self.parent._insert_code_to_editor(code_content, "range", None, int(start_line), int(end_line))
                                processed_message = processed_message.replace(insert_button, 
                                    f"\n{tag}\n\n*Код автоматически заменил строки {start_line}-{end_line}*\n")
            
            # Обработка обычных тегов кода (без строки)
            standard_matches = re.findall(CODE_BLOCK_PATTERN, message, re.DOTALL)
            if standard_matches:
                for match_idx, code_content in enumerate(standard_matches):
                    # Логируем найденный стандартный блок кода
                    print(f"\n=== НАЙДЕН СТАНДАРТНЫЙ БЛОК КОДА (устаревший формат) ===")
                    print(f"Содержимое блока кода:\n{code_content}")
                    print("=======================================\n")
                    sys.stdout.flush()
                    
                    # Очищаем содержимое кода
                    code_content = code_content.strip()
                    
                    # Формируем тег для отображения кода с подсветкой синтаксиса
                    tag = f"```\n{code_content}\n```"
                    
                    # Готовим тег для замены
                    full_tag_pattern = r'###CODE_INSERT\s+(.*?)###END_INSERT'
                    full_tag_match = re.search(full_tag_pattern, message, re.DOTALL)
                    
                    if full_tag_match:
                        original_tag = full_tag_match.group(0)
                        
                        # Сохраняем блок кода для возможной вставки
                        code_id = self.next_code_id
                        self.code_blocks[code_id] = {
                            'type': 'standard',
                            'code': code_content,
                            'language': ""
                        }
                        self.next_code_id += 1
                        
                        # Заменяем тег в сообщении
                        insert_button = f"\n{tag}\n[Вставить код в редактор] (ID: {code_id})\n"
                        processed_message = processed_message.replace(original_tag, insert_button)
                        
                        # Если включена автоматическая вставка кода
                        if self.ai_settings.get("code_insertion_enabled", True):
                            # Проверяем, есть ли доступ к редактору
                            if hasattr(self.parent, '_insert_code_to_editor'):
                                self.parent._insert_code_to_editor(code_content, "standard", None, None, None)
                                processed_message = processed_message.replace(insert_button, 
                                    f"\n{tag}\n\n*Код автоматически вставлен в редактор*\n")
            
            # Обработка устаревшего тега чтения файла
            file_read_match = re.search(READ_FILE_PATTERN, message, re.DOTALL)
            if file_read_match:
                # Извлекаем путь к файлу
                file_path = file_read_match.group(1).strip()
                # Логируем найденный запрос на чтение файла
                print(f"\n=== НАЙДЕН ЗАПРОС НА ЧТЕНИЕ ФАЙЛА: {file_path} (устаревший формат) ===")
                sys.stdout.flush()
                
                # Останавливаем дальнейшую обработку и запускаем чтение файла
                # Сначала сохраняем исходное сообщение в истории для контекста
                self.chat_messages.append({"role": "assistant", "content": message})
                
                # Обновляем интерфейс
                self._update_response(f"\n*Чтение файла (устаревший формат): {file_path}*\n", "info")
                
                # Запускаем чтение файла в отдельном потоке
                threading.Thread(target=self._handle_file_read_request, args=(file_path,)).start()
                
                # Возвращаем None, что означает остановку дальнейшей обработки
                return None
        
        # После всех обработок, логируем обработанный текст
        print("\n===== ОБРАБОТАННЫЙ ТЕКСТ (ПОСЛЕ ОБРАБОТКИ КОДА) =====")
        print(processed_message)
        print("========================================================\n")
        sys.stdout.flush()
        
        return processed_message
    
    def _process_json_code_blocks(self, message):
        """Обрабатывает JSON блоки кода в сообщении"""
        import json
        processed_message = message
        
        # Логируем исходное сообщение перед обработкой JSON блоков
        print("\n===== ИСХОДНЫЙ ТЕКСТ С JSON БЛОКАМИ КОДА (ДО ОБРАБОТКИ) =====")
        print(message)
        print("================================================================\n")
        sys.stdout.flush()
        
        # Попробуем искать JSON объекты напрямую (на случай если они не в markdown-блоках)
        try:
            # Паттерн для поиска любых JSON-объектов, которые могут быть командами
            direct_json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
            direct_matches = re.findall(direct_json_pattern, message, re.DOTALL)
            
            for json_str in direct_matches:
                try:
                    # Проверяем, является ли это JSON объектом
                    json_obj = json.loads(json_str)
                    
                    # Если это JSON с полем type, то обрабатываем его
                    if isinstance(json_obj, dict) and "type" in json_obj:
                        json_type = json_obj.get("type")
                        
                        # Обработка команд чтения файла
                        if json_type == "read_file" and "path" in json_obj:
                            file_path = json_obj["path"]
                            print(f"\n=== НАЙДЕН ПРЯМОЙ JSON-ЗАПРОС НА ЧТЕНИЕ ФАЙЛА: {file_path} ===")
                            sys.stdout.flush()
                            
                            # Сохраняем сообщение и запускаем обработку
                            self.chat_messages.append({"role": "assistant", "content": message})
                            self._update_response(f"\n*Чтение файла: {file_path}*\n", "info")
                            threading.Thread(target=self._handle_json_file_read_request, args=(file_path,)).start()
                            return None
                            
                        # Обработка команд выполнения
                        elif json_type == "execute" and "command" in json_obj:
                            command = json_obj["command"]
                            print(f"\n=== НАЙДЕН ПРЯМОЙ JSON-ЗАПРОС НА ВЫПОЛНЕНИЕ КОМАНДЫ: {command} ===")
                            sys.stdout.flush()
                            
                            # Сохраняем сообщение и запускаем обработку
                            self.chat_messages.append({"role": "assistant", "content": message})
                            self._update_response(f"\n*Выполнение команды: {command}*\n", "info")
                            threading.Thread(target=self._handle_json_execute_request, args=(command,)).start()
                            return None
                            
                except json.JSONDecodeError:
                    # Пропускаем строки, которые не являются валидным JSON
                    pass
                except Exception as e:
                    print(f"Ошибка при прямой обработке JSON: {str(e)}")
        except Exception as e:
            print(f"Ошибка при поиске прямых JSON: {str(e)}")
        
        # Обработка JSON-запросов на чтение файлов
        read_file_matches = re.findall(JSON_READ_FILE_PATTERN, message, re.DOTALL)
        if read_file_matches:
            for json_str in read_file_matches:
                try:
                    # Парсим JSON содержимое
                    data = json.loads(json_str)
                    file_path = data.get("path", "")
                    
                    if not file_path:
                        continue
                        
                    # Нашли запрос на чтение файла в JSON-формате
                    print(f"\n=== НАЙДЕН JSON-ЗАПРОС НА ЧТЕНИЕ ФАЙЛА: {file_path} ===")
                    sys.stdout.flush()
                    
                    # Оригинальный блок для замены при необходимости
                    original_block = f"```json\n{json_str}\n```"
                    # Ищем точное вхождение в тексте, если не найдено, ищем без "json"
                    if original_block not in message:
                        original_block = f"```\n{json_str}\n```"
                        # Если и это не найдено, используем сам JSON
                        if original_block not in message:
                            original_block = json_str
                    
                    # Останавливаем дальнейшую обработку и запускаем чтение файла
                    # Сначала сохраняем исходное сообщение в истории для контекста
                    self.chat_messages.append({"role": "assistant", "content": message})
                    
                    # Обновляем интерфейс
                    self._update_response(f"\n*Чтение файла: {file_path}*\n", "info")
                    
                    # Запускаем чтение файла в отдельном потоке
                    threading.Thread(target=self._handle_json_file_read_request, args=(file_path,)).start()
                    
                    # Возвращаем None, что означает остановку дальнейшей обработки
                    return None
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON для чтения файла: {str(e)}")
                except Exception as e:
                    print(f"Ошибка при обработке JSON запроса на чтение файла: {str(e)}")
        
        # Обработка JSON-запросов на выполнение команд
        execute_matches = re.findall(JSON_EXECUTE_PATTERN, message, re.DOTALL)
        if execute_matches:
            for json_str in execute_matches:
                try:
                    # Парсим JSON содержимое
                    data = json.loads(json_str)
                    command = data.get("command", "")
                    
                    if not command:
                        continue
                    
                    # Нашли запрос на выполнение команды в JSON-формате
                    print(f"\n=== НАЙДЕН JSON-ЗАПРОС НА ВЫПОЛНЕНИЕ КОМАНДЫ: {command} ===")
                    sys.stdout.flush()
                    
                    # Оригинальный блок для замены при необходимости
                    original_block = f"```json\n{json_str}\n```"
                    # Ищем точное вхождение в тексте, если не найдено, ищем без "json"
                    if original_block not in message:
                        original_block = f"```\n{json_str}\n```"
                        # Если и это не найдено, используем сам JSON
                        if original_block not in message:
                            original_block = json_str
                    
                    # Останавливаем дальнейшую обработку и запускаем выполнение команды
                    # Сначала сохраняем исходное сообщение в истории для контекста
                    self.chat_messages.append({"role": "assistant", "content": message})
                    
                    # Обновляем интерфейс
                    self._update_response(f"\n*Выполнение команды: {command}*\n", "info")
                    
                    # Запускаем выполнение команды в отдельном потоке
                    threading.Thread(target=self._handle_json_execute_request, args=(command,)).start()
                    
                    # Возвращаем None, что означает остановку дальнейшей обработки
                    return None
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON для выполнения команды: {str(e)}")
                except Exception as e:
                    print(f"Ошибка при обработке JSON запроса на выполнение команды: {str(e)}")
        
        # Обработка JSON блоков кода
        json_matches = re.findall(JSON_CODE_PATTERN, message, re.DOTALL)
        if json_matches:
            for json_str in json_matches:
                try:
                    # Парсим JSON содержимое
                    code_data = json.loads(json_str)
                    
                    # Проверяем наличие необходимых полей
                    if "type" in code_data and code_data["type"] == "code_insert" and "code" in code_data:
                        code_content = code_data["code"].strip()
                        code_type = code_data.get("insert_type", "standard")
                        
                        # Формируем тег для отображения кода с подсветкой синтаксиса
                        tag = f"```\n{code_content}\n```"
                        
                        # Оригинальный блок для замены
                        original_block = f"```json\n{json_str}\n```"
                        # Ищем точное вхождение в тексте, если не найдено, ищем без "json"
                        if original_block not in message:
                            original_block = f"```\n{json_str}\n```"
                            # Если и это не найдено, используем сам JSON
                            if original_block not in message:
                                original_block = json_str
                        
                        # Сохраняем блок кода для возможной вставки
                        code_id = self.next_code_id
                        
                        # Определяем тип вставки и действуем соответственно
                        if code_type == "line" and "line" in code_data:
                            # Вставка на указанную строку
                            line_num = int(code_data["line"])
                            self.code_blocks[code_id] = {
                                'type': 'line',
                                'line': line_num,
                                'code': code_content,
                                'language': code_data.get("language", "")
                            }
                            
                            # Заменяем JSON блок в сообщении
                            insert_button = f"\n{tag}\n[Вставить код в редактор на строку {line_num}] (ID: {code_id})\n"
                            processed_message = processed_message.replace(original_block, insert_button)
                            
                            # Если включена автоматическая вставка кода
                            if self.ai_settings.get("code_insertion_enabled", True):
                                # Проверяем, есть ли доступ к редактору
                                if hasattr(self.parent, '_insert_code_to_editor'):
                                    self.parent._insert_code_to_editor(code_content, "line", line_num, None, None)
                                    processed_message = processed_message.replace(insert_button, 
                                        f"\n{tag}\n\n*Код автоматически вставлен в строку {line_num}*\n")
                            
                        elif code_type == "range" and "start_line" in code_data and "end_line" in code_data:
                            # Замена диапазона строк
                            start_line = int(code_data["start_line"])
                            end_line = int(code_data["end_line"])
                            self.code_blocks[code_id] = {
                                'type': 'range',
                                'start_line': start_line,
                                'end_line': end_line,
                                'code': code_content,
                                'language': code_data.get("language", "")
                            }
                            
                            # Заменяем JSON блок в сообщении
                            insert_button = f"\n{tag}\n[Заменить строки {start_line}-{end_line} кодом] (ID: {code_id})\n"
                            processed_message = processed_message.replace(original_block, insert_button)
                            
                            # Если включена автоматическая вставка кода
                            if self.ai_settings.get("code_insertion_enabled", True):
                                # Проверяем, есть ли доступ к редактору
                                if hasattr(self.parent, '_insert_code_to_editor'):
                                    self.parent._insert_code_to_editor(code_content, "range", None, start_line, end_line)
                                    processed_message = processed_message.replace(insert_button, 
                                        f"\n{tag}\n\n*Код автоматически заменил строки {start_line}-{end_line}*\n")
                        
                        else:
                            # Стандартная вставка в текущую позицию курсора
                            self.code_blocks[code_id] = {
                                'type': 'standard',
                                'code': code_content,
                                'language': code_data.get("language", "")
                            }
                            
                            # Заменяем JSON блок в сообщении
                            insert_button = f"\n{tag}\n[Вставить код в редактор] (ID: {code_id})\n"
                            processed_message = processed_message.replace(original_block, insert_button)
                            
                            # Если включена автоматическая вставка кода
                            if self.ai_settings.get("code_insertion_enabled", True):
                                # Проверяем, есть ли доступ к редактору
                                if hasattr(self.parent, '_insert_code_to_editor'):
                                    self.parent._insert_code_to_editor(code_content, "standard", None, None, None)
                                    processed_message = processed_message.replace(insert_button, 
                                        f"\n{tag}\n\n*Код автоматически вставлен в редактор*\n")
                        
                        self.next_code_id += 1
                        
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON: {str(e)}")
                    # В случае ошибки оставляем блок как есть
                except Exception as e:
                    print(f"Ошибка при обработке JSON блока кода: {str(e)}")
        
        # Обработка JSON Stop блоков
        stop_matches = re.findall(JSON_STOP_PATTERN, message, re.DOTALL)
        if stop_matches:
            for json_str in stop_matches:
                try:
                    # Парсим JSON содержимое
                    stop_data = json.loads(json_str)
                    message_text = stop_data.get("message", "Обработка кода завершена")
                    
                    # Формируем тег для замены
                    original_block = f"```json\n{json_str}\n```"
                    # Ищем точное вхождение в тексте, если не найдено, ищем без "json"
                    if original_block not in message:
                        original_block = f"```\n{json_str}\n```"
                        # Если и это не найдено, используем сам JSON
                        if original_block not in message:
                            original_block = json_str
                    
                    # Заменяем Stop блок информационным сообщением
                    processed_message = processed_message.replace(original_block, f"\n*{message_text}*\n")
                    
                    # Автоматическое продолжение процесса генерации
                    if self.ai_settings.get("auto_continue_enabled", True):
                        # Проверяем, что у родительского объекта есть метод для продолжения генерации
                        if hasattr(self.parent, '_generate_ai_response'):
                            # Запускаем генерацию в отдельном потоке после небольшой задержки
                            def continue_generation():
                                # Небольшая задержка для обновления UI
                                time.sleep(0.5)
                                # Продолжаем генерацию с сообщением о продолжении
                                if hasattr(self.parent, 'is_generating'):
                                    self.parent.is_generating = True
                                    threading.Thread(target=self.parent._generate_ai_response).start()
                            
                            # Запускаем продолжение в отдельном потоке
                            threading.Thread(target=continue_generation).start()
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON в stop блоке: {str(e)}")
                except Exception as e:
                    print(f"Ошибка при обработке JSON stop блока: {str(e)}")
        
        # После всех обработок, логируем обработанный текст
        print("\n===== ОБРАБОТАННЫЙ ТЕКСТ (ПОСЛЕ ОБРАБОТКИ JSON КОДА) =====")
        print(processed_message)
        print("========================================================\n")
        sys.stdout.flush()
        
        return processed_message
        
    def _handle_json_file_read_request(self, file_path):
        """Обрабатывает JSON-запрос на чтение файла"""
        try:
            print(f"Обрабатываем JSON-запрос на чтение файла: {file_path}")
            # Нормализуем путь - проверяем абсолютный или относительный
            if not os.path.isabs(file_path):
                if hasattr(self.parent, "current_project") and self.parent.current_project:
                    file_path = os.path.join(self.parent.current_project, file_path)
                else:
                    # Если нет текущего проекта, используем каталог запуска
                    file_path = os.path.join(os.getcwd(), file_path)
            
            print(f"Полный путь к файлу: {file_path}")
            # Проверка существования файла
            if not os.path.exists(file_path):
                self._update_response(f"\nОшибка: Файл '{file_path}' не найден.", "error")
                return
            
            # Лимит на размер файла (например, 1 МБ)
            max_file_size = 1024 * 1024
            if os.path.getsize(file_path) > max_file_size:
                self._update_response(f"\nОшибка: Файл '{file_path}' слишком большой для чтения (> 1 МБ).", "error")
                return
            
            # Читаем содержимое файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    print(f"Файл успешно прочитан: {len(file_content)} символов")
            except UnicodeDecodeError:
                try:
                    # Пробуем другие кодировки
                    with open(file_path, 'r', encoding='latin-1') as f:
                        file_content = f.read()
                        print(f"Файл прочитан в кодировке latin-1: {len(file_content)} символов")
                except Exception as e:
                    # Если не удалось открыть как текстовый файл - сообщаем об ошибке
                    self._update_response(f"\nОшибка: Файл '{file_path}' не является текстовым файлом или использует нестандартную кодировку.", "error")
                    return
            
            # Формируем новый запрос с содержимым файла
            message = f"""Содержимое файла '{file_path}':

```
{file_content}
```

Теперь, когда ты видишь содержимое файла, продолжи обработку задачи. Помни о JSON-формате для вставки кода и остановки."""
            
            # Сохраняем в историю чата
            self.chat_messages.append({"role": "user", "content": message})
            
            # Запускаем новый запрос с содержимым файла
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, "Анализирую файл...", "info")
            self.chat_history.configure(state="disabled")
            self.chat_history.see(tk.END)
            
            # Генерируем новый ответ с содержимым файла
            threading.Thread(target=self._generate_response, args=(message,)).start()
            
        except Exception as e:
            print(f"Ошибка при чтении файла: {str(e)}")
            self._update_response(f"\nОшибка чтения файла: {str(e)}", "error")
            
    def _handle_json_execute_request(self, command):
        """Обрабатывает JSON-запрос на выполнение команды"""
        try:
            print(f"Обрабатываем JSON-запрос на выполнение команды: {command}")
            
            # Проверяем безопасность команды (можно добавить дополнительные проверки)
            unsafe_commands = ["rm -rf", "format", "del /", "deltree"]
            if any(unsafe_cmd in command.lower() for unsafe_cmd in unsafe_commands):
                self._update_response(f"\nОшибка: Команда '{command}' заблокирована по соображениям безопасности.", "error")
                return
            
            # Выполняем команду
            import subprocess
            self._update_response(f"\nВыполнение команды: {command}\n", "info")
            
            try:
                # Выполняем команду и получаем вывод
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30  # Ограничиваем время выполнения 30 секундами
                )
                
                # Получаем результат выполнения
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
                
                # Формируем ответ
                output = f"Результат выполнения команды (код {exit_code}):\n\n"
                
                if stdout:
                    output += f"STDOUT:\n```\n{stdout}\n```\n\n"
                
                if stderr:
                    output += f"STDERR:\n```\n{stderr}\n```\n\n"
                
                if not stdout and not stderr:
                    output += "Команда выполнена без вывода.\n"
                
                # Формируем новый запрос с результатами выполнения команды
                message = f"""Результат выполнения команды '{command}':

{output}

Продолжи обработку задачи с учетом полученных результатов. Помни о JSON-формате для вставки кода и остановки."""
                
                # Сохраняем в историю чата
                self.chat_messages.append({"role": "user", "content": message})
                
                # Запускаем новый запрос с результатами команды
                self._update_response(output, "info")
                
                # Генерируем новый ответ
                threading.Thread(target=self._generate_response, args=(message,)).start()
                
            except subprocess.TimeoutExpired:
                self._update_response(f"\nОшибка: Выполнение команды '{command}' прервано по тайм-ауту (>30 сек).", "error")
            except Exception as e:
                self._update_response(f"\nОшибка при выполнении команды: {str(e)}", "error")
            
        except Exception as e:
            print(f"Ошибка при обработке запроса на выполнение команды: {str(e)}")
            self._update_response(f"\nОшибка: {str(e)}", "error")
    
    def _on_insert_code_click(self, event):
        """Обработчик клика по кнопке вставки кода"""
        # Получаем текст под курсором
        index = self.chat_history.index(f"@{event.x},{event.y}")
        line_start = self.chat_history.index(f"{index} linestart")
        line_end = self.chat_history.index(f"{index} lineend")
        line_text = self.chat_history.get(line_start, line_end)
        
        # Извлекаем ID блока кода
        match = re.search(r'ID: (\d+)', line_text)
        if match:
            code_id = int(match.group(1))
            if code_id in self.code_blocks:
                # Отладочный вывод содержимого кода
                print(f"DEBUG: Вставка кода ID={code_id}:")
                print(f"DEBUG: Тип вставки: {self.code_blocks[code_id].get('type', 'standard')}")
                if self.code_blocks[code_id].get('type') == 'line':
                    print(f"DEBUG: Строка: {self.code_blocks[code_id].get('line')}")
                elif self.code_blocks[code_id].get('type') == 'range':
                    print(f"DEBUG: Диапазон строк: {self.code_blocks[code_id].get('start_line')}-{self.code_blocks[code_id].get('end_line')}")
                print(f"DEBUG: Код для вставки:\n{self.code_blocks[code_id].get('code', '')}")
                
                # Вставляем код в редактор с учетом типа вставки
                self._insert_code_to_editor(self.code_blocks[code_id])
    
    def _insert_code_to_editor(self, code_info):
        """Вставляет код в текущий редактор с учетом указанных строк"""
        if not hasattr(self.parent, 'code_editor'):
            self.add_bot_message("Ошибка: не удалось найти редактор для вставки кода", "error")
            return
            
        try:
            code_type = code_info.get('type', 'standard')
            
            if code_type == 'standard':
                # Стандартная вставка в текущую позицию курсора
                code = code_info.get('code', '')
                self.parent.code_editor.insert(tk.INSERT, code)
                self.parent.status_text.configure(text="Код вставлен в редактор")
                
            elif code_type == 'line':
                # Вставка на указанную строку
                line_num = code_info.get('line', 1)
                code = code_info.get('code', '')
                
                # Получаем текущее содержимое редактора
                text = self.parent.code_editor.get("1.0", tk.END)
                lines = text.split("\n")
                
                # Проверяем валидность номера строки
                if line_num <= 0:
                    line_num = 1
                if line_num > len(lines):
                    line_num = len(lines) + 1
                
                # Вставляем код на указанную строку
                insert_position = f"{line_num}.0"
                self.parent.code_editor.insert(insert_position, code + "\n")
                self.parent.status_text.configure(text=f"Код вставлен в строку {line_num}")
                
            elif code_type == 'range':
                # Замена диапазона строк
                start_line = code_info.get('start_line', 1)
                end_line = code_info.get('end_line', 1)
                code = code_info.get('code', '')
                
                # Получаем текущее содержимое редактора
                text = self.parent.code_editor.get("1.0", tk.END)
                lines = text.split("\n")
                
                # Проверяем валидность номеров строк
                if start_line <= 0:
                    start_line = 1
                if end_line > len(lines):
                    end_line = len(lines)
                if start_line > end_line:
                    start_line, end_line = end_line, start_line
                
                # Удаляем старые строки и вставляем новый код
                start_position = f"{start_line}.0"
                end_position = f"{end_line}.end"
                self.parent.code_editor.delete(start_position, end_position)
                self.parent.code_editor.insert(start_position, code)
                self.parent.status_text.configure(text=f"Заменены строки {start_line}-{end_line}")
            
            # Обновляем номера строк и подсветку синтаксиса
            self.parent.update_line_numbers()
            self.parent.highlight_syntax()
            self.parent.highlight_current_line()
            
        except Exception as e:
            print(f"Ошибка при вставке кода: {str(e)}")
            self.add_bot_message(f"Ошибка при вставке кода: {str(e)}", "error")
    
    def _format_final_response(self, message):
        """Форматирует окончательный ответ с обработкой специальных тегов"""
        message_lines = message.split('\n')
        
        # Флаги для отслеживания текущего контекста
        in_code_block = False
        
        for line in message_lines:
            if line.startswith('```'):
                # Переключаем флаг кодового блока
                in_code_block = not in_code_block
                self.chat_history.insert(tk.END, f"{line}\n", "code")
            elif in_code_block:
                # Внутри блока кода
                self.chat_history.insert(tk.END, f"{line}\n", "code")
            elif line.strip().startswith('[Вставить код в редактор') or line.strip().startswith('[Заменить строки'):
                # Кнопка вставки кода
                self.chat_history.insert(tk.END, f"{line}\n", "insert_button")
            elif line.strip().startswith('*Код автоматически'):
                # Сообщение об автоматической вставке
                self.chat_history.insert(tk.END, f"{line}\n", "info")
            else:
                # Обычный текст
                self.chat_history.insert(tk.END, f"{line}\n", "bot")
        
        # Логируем итоговый ответ
        print("\n===== ИТОГОВЫЙ ОТФОРМАТИРОВАННЫЙ ОТВЕТ =====")
        print(message)
        print("=======================================\n")
        sys.stdout.flush()
    
    def _call_api_streaming(self, messages):
        """Вызывает OpenRouter API в режиме потоковой передачи"""
        api_key = self.parent.settings.ai_api_key
        api_url = API_URL
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Получаем настройки API из файла настроек
        api_settings = self.ai_settings.get("api_settings", DEFAULT_API_SETTINGS)
        
        # Дополнительная проверка перед отправкой: убедимся, что начальная инструкция присутствует
        system_message_exists = False
        default_system_message_index = -1
        
        # Проверяем наличие системного сообщения с инструкцией
        for i, msg in enumerate(messages):
            if msg.get('role') == 'system' and 'структура файловой системы' not in msg.get('content', '').lower():
                system_message_exists = True
                default_system_message_index = i
                break
        
        # Если системного сообщения нет, добавляем его
        if not system_message_exists:
            self.log_warning("В сообщениях отсутствует начальная инструкция, добавляю её")
            initial_prompt = self.ai_settings.get("initial_prompt", DEFAULT_AI_PROMPT)
            if not initial_prompt or len(initial_prompt.strip()) == 0:
                initial_prompt = DEFAULT_AI_PROMPT
            
            # Добавляем в начало списка сообщений
            messages.insert(0, {
                "role": "system",
                "content": initial_prompt
            })
        elif default_system_message_index >= 0:
            # Проверяем, что системное сообщение не пустое
            if not messages[default_system_message_index].get('content'):
                self.log_warning("Системное сообщение пусто, заменяю на значение по умолчанию")
                messages[default_system_message_index]['content'] = DEFAULT_AI_PROMPT
        
        # Системное сообщение с инструкцией уже добавлено, дополнительное не требуется
        
        data = {
            "model": api_settings.get("model", "deepseek/deepseek-r1"),
            "messages": messages,
            "temperature": api_settings.get("temperature", 0.7),
            "stream": True  # Обязательно включаем потоковую передачу
        }
        
        # Проверяем наличие структуры проекта в запросе
        has_project_structure = False
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # Проверка наличия структуры проекта в системных сообщениях
            if role == 'system' and 'структура файловой системы' in content.lower():
                has_project_structure = True
                
        # Если структуры проекта нет, добавляем её вручную
        if not has_project_structure:
            # Получаем структуру
            try:
                current_dir = os.getcwd()
                structure = self._get_simple_project_structure(current_dir)
                
                # Добавляем в сообщения
                if structure:
                    structure_message = {
                        "role": "system", 
                        "content": f"Текущая структура файловой системы проекта:\n{structure}"
                    }
                    messages.append(structure_message)
                    data["messages"] = messages  # Обновляем данные запроса
            except Exception as e:
                print(f"Ошибка при добавлении структуры проекта: {str(e)}")
                sys.stdout.flush()
        
        try:
            # Запрос к API
            with requests.post(api_url, headers=headers, json=data, stream=True) as response:
                if response.status_code != 200:
                    self._handle_api_error(response)
                    return
                
                # Проверяем наличие тега чтения файла в ответе
                read_file_tag_found = False
                
                # Обрабатываем потоковые данные
                chunk_counter = 0
                
                for line in response.iter_lines():
                    # Проверяем, не был ли получен сигнал остановки
                    if self.stop_generation:
                        return
                        
                    if not line:
                        continue
                    
                    # Декодируем строку и удаляем префикс 'data: '
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        line_text = line_text[6:]  # Удаляем 'data: '
                    
                    # Пропускаем служебные сообщения
                    if line_text == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(line_text)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                # Инкрементируем счетчик фрагментов
                                chunk_counter += 1
                                
                                # Проверяем, не начинается ли тег чтения файла
                                if "<read-file>" in (self.current_response + content):
                                    read_file_tag_found = True
                                
                                # Добавляем фрагмент к текущему ответу
                                self.current_response += content
                                
                                # Если найдено полное совпадение тега чтения файла, прерываем стрим
                                if read_file_tag_found and re.search(r'<read-file>\s*([^<\s][^<]*?)\s*</read-file>', self.current_response):
                                    # Добавляем последний фрагмент и выходим
                                    self._append_streaming_chunk(content)
                                    return
                                
                                # Обновляем интерфейс с новым фрагментом
                                self._append_streaming_chunk(content)
                                
                    except json.JSONDecodeError:
                        # Пропускаем строки, которые не являются JSON
                        pass
                
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при обращении к API: {str(e)}")
            sys.stdout.flush()
            raise Exception(f"Ошибка сети при обращении к API: {str(e)}")
        except Exception as e:
            # Проверяем, не была ли это остановка пользователем
            if not self.stop_generation:
                print(f"Ошибка в _call_api_streaming: {str(e)}")
                sys.stdout.flush()
                self._log_exception()
                raise Exception(f"Ошибка при обработке ответа API: {str(e)}")
    
    def _log_exception(self):
        """Логирует текущее исключение с полным стеком вызовов"""
        try:
            # Получаем информацию об исключении
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            
            # Форматируем стек вызовов для лога
            stack_trace = ''.join(lines)
            
            # Логируем стек вызовов
            self.log_error(f"Stack trace:\n{stack_trace}")
            
            # Также пишем в файл для надежности
            try:
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                    
                with open(os.path.join(log_dir, "exceptions.log"), "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    f.write(stack_trace)
            except:
                print("Не удалось записать стек ошибки в файл")
        except:
            # Если даже _log_exception дал сбой, записываем в стандартный вывод
            print("ERROR: Failed to log exception details")
            traceback.print_exc()
    
    def log_warning(self, message):
        """Логгирует предупреждение"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.warning(message)
        print(f"WARNING: {message}")
        sys.stdout.flush()
    
    def _append_streaming_chunk(self, chunk):
        """Добавляет фрагмент стримингового ответа в чат"""
        def update():
            try:
                self.chat_history.configure(state="normal")
                self.chat_history.insert(tk.END, chunk, "bot")
                self.chat_history.see(tk.END)
                self.chat_history.configure(state="disabled")
            except Exception as e:
                print(f"Ошибка обновления интерфейса: {str(e)}")
                sys.stdout.flush()
                self._log_exception()
        
        # Обновляем интерфейс в основном потоке
        self.parent.after(0, update)
    
    def _handle_api_error(self, response):
        """Обрабатывает ошибки API и возвращает понятное сообщение"""
        self.log_debug(f"_handle_api_error called with status code: {response.status_code}")
        
        try:
            error_json = response.json()
            error_info = error_json.get("error", {})
            error_message = error_info.get("message", "")
            self.log_debug(f"API returned error: {error_message}")
        except json.JSONDecodeError:
            error_json = {}
            error_info = {}
            error_message = response.text
            self.log_debug(f"Could not parse JSON from API error. Raw response: {response.text[:200]}")
        
        # Обработка конкретных ошибок по статус-коду
        if response.status_code == 401:
            error_text = "Ошибка авторизации: неверный API-ключ. Проверьте настройки API-ключа в разделе ИИ-ассистент."
            self._update_response(error_text, "error")
            self.log_debug(f"401 error: {error_text}")
            raise Exception(error_text)
        
        elif response.status_code == 402:
            if "Insufficient funds" in error_message or "Insufficient Balance" in error_message:
                error_text = "На вашем счету OpenRouter недостаточно средств. Пожалуйста, пополните баланс в личном кабинете."
                self._update_response(error_text, "error")
                self.log_debug(f"402 insufficient funds: {error_text}")
                raise Exception(error_text)
            error_text = "Ошибка оплаты API: недостаточно средств на счету OpenRouter."
            self._update_response(error_text, "error")
            self.log_debug(f"402 error: {error_text}")
            raise Exception(error_text)
        
        elif response.status_code == 403:
            error_text = "Доступ запрещен. У вас нет прав на использование этого API или модели."
            self._update_response(error_text, "error")
            self.log_debug(f"403 error: {error_text}")
            raise Exception(error_text)
        
        elif response.status_code == 404:
            error_text = "Запрашиваемый ресурс не найден. Возможно, указана неверная модель в настройках."
            self._update_response(error_text, "error")
            self.log_debug(f"404 error: {error_text}")
            raise Exception(error_text)
        
        elif response.status_code == 429:
            error_text = "Превышен лимит запросов к API. Пожалуйста, подождите некоторое время перед следующим запросом."
            self._update_response(error_text, "error")
            self.log_debug(f"429 error: {error_text}")
            raise Exception(error_text)
        
        elif response.status_code >= 500:
            error_text = f"Ошибка на сервере OpenRouter (код {response.status_code}). Пожалуйста, попробуйте позже."
            self._update_response(error_text, "error")
            self.log_debug(f"500+ error: {error_text}")
            raise Exception(error_text)
        
        # Общий случай для необработанных ошибок
        error_text = f"Ошибка API OpenRouter (код {response.status_code}): {error_message}"
        self._update_response(error_text, "error")
        self.log_debug(f"Unhandled API error: {error_text}")
        raise Exception(error_text)
    
    def show_api_help(self):
        """Показывает справочную информацию по работе с API"""
        help_text = """
Информация по работе с OpenRouter API:

1. Как получить API-ключ:
   - Зарегистрируйтесь на сайте https://openrouter.ai
   - Перейдите в настройки аккаунта → Settings → API Keys
   - Создайте новый API-ключ и скопируйте его

2. Часто возникающие ошибки:
   - Ошибка 401: Неверный API-ключ, проверьте настройки
   - Ошибка 402: Недостаточно средств, пополните баланс
   - Ошибка 429: Слишком много запросов, подождите перед следующим запросом

3. Настройки API:
   - В файле ai_settings.json можно настроить модель, температуру и другие параметры
   - Начальный промпт для ИИ также можно изменить через настройки

4. Как пополнить баланс:
   - Войдите в личный кабинет на сайте https://openrouter.ai
   - Перейдите в раздел Billing
   - Следуйте инструкциям для пополнения счета

5. О модели DeepSeek-R1:
   - DeepSeek-R1 - мощная языковая модель с широкими возможностями для программирования
   - Модель доступна через сервис OpenRouter, который агрегирует разные языковые модели

Если проблемы с API продолжаются, перезапустите редактор или обратитесь к документации OpenRouter.
"""
        # Показываем сообщение в чате
        self.add_bot_message(help_text, "info")
    
    def _update_response(self, message, tag="bot"):
        """Обновляет интерфейс чата с ответом от ИИ"""
        # Обновляем в основном потоке
        def update():
            self.chat_history.configure(state="normal")
            self.chat_history.insert(tk.END, message, tag)
            self.chat_history.insert(tk.END, "\n\n")
            self.chat_history.see(tk.END)
            self.chat_history.configure(state="disabled")
        
        # Запускаем обновление в главном потоке
        self.parent.after(0, update)
    
    def add_user_message(self, message):
        """Добавление сообщения пользователя в историю чата"""
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, "Вы: ", "system")
        self.chat_history.insert(tk.END, f"{message}\n\n", "user")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)
    
    def add_bot_message(self, message, tag="bot"):
        """Добавление сообщения бота в историю чата"""
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, "Ассистент: ", "system")
        self.chat_history.insert(tk.END, f"{message}\n\n", tag)
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)
    
    def clear_history(self):
        """Очищает историю чата и сбрасывает контекст"""
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state="disabled")
        self.chat_messages = []
        self.code_blocks = {}
        self.next_code_id = 1
        self.is_first_message = True
        
        # Добавляем приветственное сообщение
        self.add_bot_message("История чата очищена. Можно начинать с чистого листа!")
    
    def toggle(self):
        """For backwards compatibility - now handled directly in main app"""
        # Toggle is now handled by the main application
        pass
    
    def stop_response_generation(self):
        """Останавливает генерацию ответа"""
        if self.response_active:
            self.stop_generation = True
            # Удаляем кнопку остановки и показываем кнопку отправки
            self.stop_button.pack_forget()
            self.send_button.pack(side="right")
            # Добавляем сообщение о прерванной генерации
            self._update_response("\n\n*Генерация ответа остановлена пользователем*", "error") 
    
    def _test_debug_output(self):
        """Проверка работоспособности отладочного вывода"""
        self.log_debug("_test_debug_output started")
        
        if not hasattr(self, 'logger') or not self.logger:
            print("ВНИМАНИЕ: Логгер не настроен!")
            self.log_debug("WARNING: Logger not configured!")
            return
            
        try:
            # Запись в лог
            self.log_debug("=== ТЕСТ ОТЛАДОЧНОГО ВЫВОДА ===")
            self.log_info("Проверка INFO сообщения")
            self.log_debug("Проверка DEBUG сообщения")
            self.log_error("Проверка ERROR сообщения")
            
            self.log_debug("Standard logging test completed")
            
            # Проверка работы в отдельном потоке
            test_thread = threading.Thread(target=self._debug_test_thread)
            test_thread.daemon = True
            self.log_debug(f"Starting test thread {test_thread.name}")
            test_thread.start()
            test_thread.join(timeout=1.0)  # Ждем максимум 1 секунду
            self.log_debug("Test thread completed")
            
            self.log_debug("=== ТЕСТ ЗАВЕРШЕН ===")
            self.log_debug("_test_debug_output completed")
        except Exception as e:
            print(f"Ошибка при тестировании отладки: {str(e)}")
            self.log_debug(f"Error in _test_debug_output: {str(e)}")
            traceback.print_exc()
    
    def _debug_test_thread(self):
        """Тестовый поток для проверки работы логгера в многопоточном режиме"""
        thread_id = threading.get_ident()
