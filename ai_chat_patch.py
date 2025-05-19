#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Патч для класса AiChat, исправляющий обработку запросов на чтение файлов
"""

import re
from read_file_handler import process_read_file_tags

def apply_patch(ai_chat_instance):
    """
    Применяет патч к экземпляру класса AiChat
    
    Args:
        ai_chat_instance: экземпляр класса AiChat, который нужно пропатчить
    """
    # Сохраняем оригинальный метод _process_code_blocks
    original_process_code_blocks = ai_chat_instance._process_code_blocks
    
    # Определяем новую функцию для обработки кода и тегов чтения файлов
    def patched_process_code_blocks(message):
        # Сначала обработаем все теги чтения файлов
        message_with_files = process_read_file_tags(message)
        
        # Затем вызываем оригинальный метод для обработки блоков кода
        return original_process_code_blocks(message_with_files)
    
    # Заменяем оригинальный метод на наш пропатченный
    ai_chat_instance._process_code_blocks = patched_process_code_blocks
    
    print("Патч для чтения файлов успешно применён!")
    return ai_chat_instance

# Пример использования:
# from ai_chat import AiChat
# import ai_chat_patch
# 
# # ... создание экземпляра AiChat ...
# ai_chat = AiChat(parent, frame)
# 
# # Применение патча
# ai_chat_patch.apply_patch(ai_chat) 