"""
Модуль системных утилит для редактора кода.
"""

import os
import sys
import subprocess
import threading
import io
import tempfile
import ctypes
from contextlib import redirect_stdout, redirect_stderr

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

def setup_dpi_awareness():
    """Настройка DPI для Windows"""
    if os.name == 'nt':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(True)
        except:
            pass

def maximize_window(hwnd):
    """Максимизирует окно Windows"""
    if os.name == 'nt':
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

def minimize_window(hwnd):
    """Минимизирует окно Windows"""
    if os.name == 'nt':
        user32.ShowWindow(hwnd, SW_MINIMIZE)

def restore_window(hwnd):
    """Восстанавливает окно Windows"""
    if os.name == 'nt':
        user32.ShowWindow(hwnd, SW_RESTORE)

def get_window_state(hwnd):
    """Получает состояние окна Windows"""
    if os.name == 'nt':
        placement = wintypes.WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(placement)
        user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
        return placement.showCmd
    return None

def is_window_maximized(hwnd):
    """Проверяет, максимизировано ли окно Windows"""
    if os.name == 'nt':
        return get_window_state(hwnd) == SW_MAXIMIZE
    return False

def execute_code(cmd, work_dir=None, shell=True, output_callback=None):
    """
    Выполняет код в отдельном процессе и возвращает результат.
    
    Args:
        cmd (str): Команда для выполнения
        work_dir (str, optional): Рабочая директория
        shell (bool, optional): Использовать ли shell
        output_callback (callable, optional): Функция обратного вызова для вывода
        
    Returns:
        tuple: (код возврата, stdout, stderr)
    """
    process = None
    try:
        # Создаем процесс
        process = subprocess.Popen(
            cmd,
            cwd=work_dir,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
            bufsize=1
        )
        
        # Буферы для stdout и stderr
        stdout_buffer = []
        stderr_buffer = []
        
        # Создаем функцию для чтения вывода
        def read_output(pipe, buffer, is_stderr=False):
            for line in iter(pipe.readline, ''):
                buffer.append(line)
                if output_callback:
                    output_callback(line, is_stderr)
            pipe.close()
        
        # Запускаем потоки для чтения вывода
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_buffer))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_buffer, True))
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Ждем завершения процесса
        return_code = process.wait()
        
        # Ждем завершения потоков
        stdout_thread.join()
        stderr_thread.join()
        
        # Возвращаем результат
        return return_code, ''.join(stdout_buffer), ''.join(stderr_buffer)
    
    except Exception as e:
        # В случае ошибки, убедимся, что процесс завершен
        if process and process.poll() is None:
            process.kill()
        
        return 1, '', f"Ошибка выполнения: {str(e)}" 