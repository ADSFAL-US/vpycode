#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Пример правильного использования команд для редактирования конкретных строк файла
"""

print("ПРИМЕРЫ ПРАВИЛЬНОГО РЕДАКТИРОВАНИЯ СТРОК ФАЙЛА")
print("==============================================")

print("\n1. ЗАМЕНА ОДНОЙ СТРОКИ:")
print('Используйте JSON формат:')
print('{')
print('  "type": "code_insert",')
print('  "insert_type": "line",')
print('  "line": 42,')
print('  "code": "    return new_value  # исправленная строка"')
print('}')

print("\n2. ЗАМЕНА ДИАПАЗОНА СТРОК:")
print('Используйте JSON формат:')
print('{')
print('  "type": "code_insert",')
print('  "insert_type": "range",')
print('  "start_line": 15,')
print('  "end_line": 20,')
print('  "code": "def new_function():')
print('    # Этот код заменит строки с 15 по 20')
print('    value = calculate()')
print('    return value"')
print('}')

print("\n3. ВСТАВКА В ТЕКУЩУЮ ПОЗИЦИЮ КУРСОРА:")
print('Используйте JSON формат:')
print('{')
print('  "type": "code_insert",')
print('  "code": "# Этот код будет вставлен там, где находится курсор"')
print('}')

print("\nОЧЕНЬ ВАЖНО!!!")
print("==============")
print("1. В поле 'code' используйте РЕАЛЬНЫЕ переносы строк, а не \\n")
print("2. Сохраняйте правильную табуляцию/отступы в редактируемом коде")
print("3. Команды выполняются немедленно - не нужно спрашивать разрешения")
print("4. Никогда не показывайте полный код файла - используйте только JSON-команды")

print("\nПРИМЕР НЕПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ (НЕ ДЕЛАЙТЕ ТАК!):")
print('НЕ используйте экранированные переносы строк:')
print('{')
print('  "type": "code_insert",')
print('  "insert_type": "line",')
print('  "line": 5,')
print('  "code": "def bad_function():\\n    print(\'Неправильный формат\')\\n    return None"')
print('}')

print("\nПРИМЕР НЕПРАВИЛЬНОГО ПОДХОДА (НЕ ДЕЛАЙТЕ ТАК!):")
print('Вот как я бы исправил файл:')
print('')
print('def fixed_function():')
print('    # Не показывайте код вне JSON-команд!')
print('    return correct_value')
print('')
print('Хотите, чтобы я применил это исправление?')

print("\nРАБОТАЙТЕ ТАК:")
print("1. Прочитайте файл: отправьте JSON-команду read_file")
print("2. Отредактируйте файл: сразу отправьте JSON-команду code_insert или replace_file")
print("3. Объясняйте ПОСЛЕ редактирования, а не до") 