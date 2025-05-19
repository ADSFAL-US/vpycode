#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Демонстрационный скрипт для AI-ассистента, показывающий
правильную последовательность действий при редактировании файлов
"""

import json
import sys

def print_separator():
    print("\n" + "=" * 70 + "\n")

def print_step(step_number, description):
    print(f"\n--- ШАГ {step_number}: {description} ---\n")

print("ДЕМОНСТРАЦИЯ ПРАВИЛЬНОГО ИСПОЛЬЗОВАНИЯ JSON-КОМАНД ДЛЯ AI-АССИСТЕНТА")
print("=================================================================")
print("Это пример правильной последовательности действий для редактирования файла.")
print_separator()

print_step(1, "Чтение файла")
print("AI должен отправить команду read_file БЕЗ объяснений и ожидания подтверждения:")
print("""
```json
{
  "type": "read_file",
  "path": "demo.py"
}
```
""")

print_step(2, "Система отвечает содержимым файла")
print("Система отправляет ответ с содержимым файла.")
print("AI получает содержимое и видит, что нужно удалить комментарий в строке 52.")

print_step(3, "Непосредственное редактирование файла")
print("AI должен СРАЗУ отправить команду для исправления файла:")
print("""
```json
{
  "type": "replace_file",
  "path": "demo.py",
  "content": "#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"""
Демонстрационный файл для тестирования ассистента
\"""

# Простая функция для проверки
def hello(name=\"мир\"):
    \"""Приветствует пользователя или мир\"""
    return f\"Привет, {name}!\"

# Класс для демонстрации
class Calculator:
    \"""Простой калькулятор\"""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        \"""Добавляет значение\"""
        self.result += value
        return self.result
    
    def subtract(self, value):
        \"""Вычитает значение\"""
        self.result -= value
        return self.result
    
    def multiply(self, value):
        \"""Умножает на значение\"""
        self.result *= value
        return self.result
    
    def divide(self, value):
        \"""Делит на значение\"""
        if value == 0:
            raise ValueError(\"Деление на ноль невозможно!\")
        self.result /= value
        return self.result

# Пример использования
if __name__ == \"__main__\":
    print(hello(\"тестирование\"))
    
    calc = Calculator()
    print(f\"Начальное значение: {calc.result}\")
    print(f\"После добавления 5: {calc.add(5)}\")
    print(f\"После вычитания 2: {calc.subtract(2)}\")
    print(f\"После умножения на 3: {calc.multiply(3)}\")
    print(f\"После деления на 2: {calc.divide(2)}\")"
}
```
""")

print_step(4, "Система подтверждает выполнение")
print("Система отвечает сообщением о том, что файл был успешно обновлен.")

print_step(5, "AI объясняет изменения")
print("ТОЛЬКО ПОСЛЕ выполнения команды редактирования AI может объяснить, что было сделано:")
print("""
Я удалил лишний комментарий `#надо убрать вот этот комментарий` из последней строки файла.
""")

print_separator()
print("ВАЖНЫЕ ЗАМЕЧАНИЯ:")
print("1. AI НИКОГДА не должен спрашивать разрешение на выполнение команд")
print("2. AI НИКОГДА не должен показывать код в обычных блоках - только в JSON-командах")
print("3. AI должен СРАЗУ применять исправления после прочтения файла")
print("4. Объяснения должны даваться ТОЛЬКО ПОСЛЕ выполнения команд")
print_separator()

if __name__ == "__main__":
    print("Запустите этот файл для просмотра примера правильного поведения AI-ассистента.")
    print("python ai_test_runner.py") 