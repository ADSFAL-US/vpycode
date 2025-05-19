#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Демонстрационный файл с ошибками для тестирования ассистента
"""

# Функция с исправленной скобкой
def hello(name="мир"):
    """Приветствует пользователя или мир"""
    return f"Привет, {name}!"

# Класс с исправленными двоеточиями
class Calculator:
    """Простой калькулятор"""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        """Добавляет значение"""
        self.result += value
        return self.result
    
    def subtract(self, value):
        """Вычитает значение"""
        self.result -= value
        return self.result
    
    def multiply(self, value):
        """Умножает на значение"""
        self.result *= value
        return self.result
    
    def divide(self, value):
        """Делит на значение"""
        if value == 0:
            raise ZeroDivisionError("Деление на ноль невозможно!")
        self.result /= value
        return self.result

# Пример использования с исправлениями
if __name__ == "__main__":
    import sys
    try:
        print(hello("тестирование"))
        
        calc = Calculator()
        print(f"Начальное значение: {calc.result}")
        print(f"После добавления 5: {calc.add(5)}")
        print(f"После вычитания 2: {calc.subtract(2)}")
        print(f"После умножения на 3: {calc.multiply(3)}")
        print(f"После деления на 2: {calc.divide(2)}")
    except Exception as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)
