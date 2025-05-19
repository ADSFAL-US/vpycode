#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Примеры правильного форматирования JSON-команд для ИИ
"""

# Пример 1: Чтение файла
READ_FILE_EXAMPLE = """```json
{
  "type": "read_file",
  "path": "demo.py"
}
```"""

# Пример 2: Вставка кода с настоящими переносами строк (правильно)
CODE_INSERT_CORRECT = """```json
{
  "type": "code_insert",
  "insert_type": "line",
  "line": 42,
  "language": "python",
  "code": "def example_function():
    print('Это правильный формат')
    for i in range(5):
        print(f'Число {i}')"
}
```"""

# Пример 3: Вставка кода с экранированными переносами строк (НЕПРАВИЛЬНО)
CODE_INSERT_WRONG = """```json
{
  "type": "code_insert",
  "insert_type": "line",
  "line": 42,
  "language": "python",
  "code": "def example_function():\\n    print('Это неправильный формат')\\n    for i in range(5):\\n        print(f'Число {i}')"
}
```"""

# Пример 4: Замена файла с правильным форматированием переносов строк
REPLACE_FILE_EXAMPLE = """```json
{
  "type": "replace_file",
  "path": "example.py",
  "content": "#!/usr/bin/env python
# -*- coding: utf-8 -*-

def main():
    print('Пример файла')
    
if __name__ == '__main__':
    main()"
}
```"""

# Пример 5: Выполнение команды
EXECUTE_COMMAND_EXAMPLE = """```json
{
  "type": "execute",
  "command": "python demo.py"
}
```"""

# Пример 6: Использование диапазона строк для замены
RANGE_REPLACE_EXAMPLE = """```json
{
  "type": "code_insert",
  "insert_type": "range",
  "start_line": 10,
  "end_line": 15,
  "language": "python",
  "code": "# Этот код заменит строки с 10 по 15
def new_function():
    return 'Новый код'"
}
```"""

if __name__ == "__main__":
    print("Это примеры правильного форматирования JSON для ИИ-ассистента")
    print("\nПример 1: Чтение файла")
    print(READ_FILE_EXAMPLE)
    
    print("\nПример 2: Правильная вставка кода (с настоящими переносами строк)")
    print(CODE_INSERT_CORRECT)
    
    print("\nПример 3: НЕПРАВИЛЬНАЯ вставка кода (с экранированными \\n)")
    print(CODE_INSERT_WRONG)
    
    print("\nПример 4: Замена содержимого файла")
    print(REPLACE_FILE_EXAMPLE)
    
    print("\nПример 5: Выполнение команды")
    print(EXECUTE_COMMAND_EXAMPLE)
    
    print("\nПример 6: Замена диапазона строк")
    print(RANGE_REPLACE_EXAMPLE) 