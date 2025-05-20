"""
Модуль утилит для работы с кодом.
"""

import re
import os
import tempfile
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, Python3Lexer
from pygments.formatters import get_formatter_by_name

def get_language_from_file(file_path):
    """
    Определяет язык программирования по расширению файла.
    
    Args:
        file_path (str): Путь к файлу
        
    Returns:
        str: Название языка программирования
    """
    _, ext = os.path.splitext(file_path)
    
    # Словарь соответствия расширений и языков
    extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.cpp': 'C++',
        '.c': 'C',
        '.java': 'Java',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.go': 'Go',
        '.rs': 'Rust',
        '.sh': 'Bash',
        '.bat': 'Batch',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
    }
    
    return extensions.get(ext.lower(), 'Unknown')

def get_lexer_for_language(language):
    """
    Возвращает лексер Pygments для языка.
    
    Args:
        language (str): Название языка программирования
        
    Returns:
        Lexer: Лексер Pygments
    """
    language_map = {
        'Python': 'python',
        'JavaScript': 'javascript',
        'HTML': 'html',
        'CSS': 'css',
        'C++': 'cpp',
        'C': 'c',
        'Java': 'java',
        'Ruby': 'ruby',
        'PHP': 'php',
        'Go': 'go',
        'Rust': 'rust',
        'Bash': 'bash',
        'Batch': 'bat',
        'TypeScript': 'typescript',
    }
    
    if language in language_map:
        from pygments.lexers import get_lexer_by_name
        try:
            return get_lexer_by_name(language_map[language])
        except:
            return Python3Lexer()
    
    return Python3Lexer()

def highlight_syntax(code, file_extension='.py'):
    """
    Подсвечивает синтаксис кода.
    
    Args:
        code (str): Код для подсветки
        file_extension (str, optional): Расширение файла
        
    Returns:
        str: Подсвеченный код
    """
    try:
        if file_extension.lower() == '.py':
            lexer = Python3Lexer()
        else:
            lexer = get_lexer_for_filename(f"dummy{file_extension}")
        
        formatter = get_formatter_by_name('html')
        return highlight(code, lexer, formatter)
    except:
        # В случае ошибки просто возвращаем исходный код
        return code

def create_temp_file(content, extension='.py'):
    """
    Создает временный файл с указанным содержимым.
    
    Args:
        content (str): Содержимое файла
        extension (str, optional): Расширение файла
        
    Returns:
        str: Путь к временному файлу
    """
    fd, path = tempfile.mkstemp(suffix=extension)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
    except:
        # В случае ошибки удаляем файл и возвращаем None
        os.unlink(path)
        return None

def simulate_line_replacement(content, line_num, new_code):
    """
    Симулирует замену строки в тексте.
    
    Args:
        content (str): Исходный текст
        line_num (int): Номер строки для замены (начиная с 1)
        new_code (str): Новый код для замены
        
    Returns:
        tuple: (измененный текст, предварительный просмотр изменений)
    """
    lines = content.split('\n')
    
    if not lines or line_num > len(lines):
        return content, "Ошибка: указанный номер строки находится за пределами файла"
    
    # Сохраняем оригинальную строку для предварительного просмотра
    original_line = lines[line_num - 1]
    
    # Заменяем строку
    lines[line_num - 1] = new_code
    modified_content = '\n'.join(lines)
    
    # Создаем текст предварительного просмотра
    preview = f"Заменяемая строка {line_num}:\n{original_line}\n\nНовая строка {line_num}:\n{new_code}"
    
    return modified_content, preview

def simulate_range_replacement(content, start_line, end_line, new_code):
    """
    Симулирует замену диапазона строк в тексте.
    
    Args:
        content (str): Исходный текст
        start_line (int): Начальная строка диапазона (начиная с 1)
        end_line (int): Конечная строка диапазона (начиная с 1)
        new_code (str): Новый код для замены
        
    Returns:
        tuple: (измененный текст, предварительный просмотр изменений)
    """
    lines = content.split('\n')
    
    if not lines or start_line > len(lines) or end_line > len(lines):
        return content, "Ошибка: указанный диапазон строк находится за пределами файла"
    
    # Ensure start_line <= end_line
    if start_line > end_line:
        start_line, end_line = end_line, start_line
    
    # Сохраняем оригинальные строки для предварительного просмотра
    original_lines = lines[start_line - 1:end_line]
    original_text = '\n'.join(original_lines)
    
    # Заменяем строки
    new_lines = new_code.split('\n')
    lines[start_line - 1:end_line] = new_lines
    modified_content = '\n'.join(lines)
    
    # Создаем текст предварительного просмотра
    preview = f"Заменяемый диапазон (строки {start_line}-{end_line}):\n{original_text}\n\nНовый код:\n{new_code}"
    
    return modified_content, preview 