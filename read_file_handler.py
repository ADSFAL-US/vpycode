#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для обработки запросов чтения файлов в ассистенте
"""

import os
import re

# Регулярное выражение для поиска тегов <read-file>
READ_FILE_PATTERN = r'<read-file>(.*?)</read-file>'

def read_file_content(file_path, max_size=1024*1024):
    """
    Читает содержимое файла и возвращает его как строку.
    Поддерживает ограничение на размер файла.
    
    Args:
        file_path (str): Путь к файлу
        max_size (int): Максимальный размер файла в байтах
        
    Returns:
        str: Содержимое файла или сообщение об ошибке
    """
    try:
        # Нормализуем путь
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            
        # Проверяем существование файла
        if not os.path.exists(file_path):
            return f"Ошибка: Файл '{file_path}' не найден."
            
        # Проверяем размер файла
        if os.path.getsize(file_path) > max_size:
            return f"Ошибка: Файл '{file_path}' слишком большой для чтения (> {max_size//1024} КБ)."
            
        # Пытаемся прочитать файл в разных кодировках
        encodings = ['utf-8', 'latin-1', 'cp1251']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content
            except UnicodeDecodeError:
                continue
                
        return f"Ошибка: Не удалось прочитать файл '{file_path}'. Возможно, он имеет бинарный формат."
                
    except Exception as e:
        return f"Ошибка при чтении файла: {str(e)}"

def process_read_file_tags(text):
    """
    Находит в тексте теги <read-file>filename</read-file> и заменяет их 
    содержимым указанных файлов
    
    Args:
        text (str): Текст с тегами чтения файлов
        
    Returns:
        str: Текст с заменёнными тегами на содержимое файлов
    """
    def replace_with_content(match):
        filename = match.group(1).strip()
        content = read_file_content(filename)
        
        # Форматируем ответ в зависимости от расширения файла
        ext = os.path.splitext(filename)[1].lower()
        
        # Если это исходный код, добавляем подсветку синтаксиса
        code_extensions = ['.py', '.js', '.html', '.css', '.cpp', '.c', '.h', '.java', '.php']
        if ext in code_extensions:
            return f"```{ext[1:]}\n{content}\n```"
        else:
            return content
    
    return re.sub(READ_FILE_PATTERN, replace_with_content, text)

# Пример использования
if __name__ == "__main__":
    test_text = """
    Вот содержимое файла:
    <read-file>demo.py</read-file>
    
    А это был пример чтения файла через тег.
    """
    
    result = process_read_file_tags(test_text)
    print(result) 