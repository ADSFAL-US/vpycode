#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Утилита для чтения файлов для ассистента
"""

def read_file_content(filename):
    """Читает содержимое файла и возвращает его как строку"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"Ошибка: Файл '{filename}' не найден."
    except Exception as e:
        return f"Ошибка при чтении файла: {str(e)}"

def process_read_file_tags(text):
    """
    Находит в тексте теги <read-file>filename</read-file> и заменяет их 
    содержимым указанных файлов
    """
    import re
    pattern = r'<read-file>(.*?)</read-file>'
    
    def replace_with_content(match):
        filename = match.group(1)
        return read_file_content(filename)
    
    return re.sub(pattern, replace_with_content, text)

# Пример использования
if __name__ == "__main__":
    # Пример текста с тегами для чтения файлов
    test_text = """
    Вот содержимое demo.py:
    <read-file>demo.py</read-file>
    
    А это был пример чтения файла через тег.
    """
    
    # Обработка тегов и вывод результата
    result = process_read_file_tags(test_text)
    print(result) 