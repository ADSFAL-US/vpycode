#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый файл для практики редактирования нейросетью
Этот файл содержит несколько ошибок, которые нужно исправить
"""

# ОШИБКА 1: Опечатка в имени функции (prnt вместо print)
def hello_world():
    prnt("Hello, World!")  # Здесь опечатка
    return True

# ОШИБКА 2: Ошибка в формуле - должно быть умножение, а не сложение
def calculate_area(width, height):
    return width + height  # Неправильная формула - нужно умножение

# ОШИБКА 3: Бесконечный цикл - забыли увеличить счетчик
def countdown(start):
    counter = start
    while counter > 0:
        print(counter)
        # Здесь забыли уменьшить счетчик

# ОШИБКА 4: Фильтрация без возврата результата
def filter_even_numbers(numbers):
    # Не возвращаем результат
    [n for n in numbers if n % 2 == 0]

# ОШИБКА 5: Неправильная проверка в условии - нужно использовать == вместо =
def is_adult(age):
    if age = 18:  # Синтаксическая ошибка
        return True
    else:
        return False

# Тест для демонстрации работы
if __name__ == "__main__":
    hello_world()
    area = calculate_area(5, 10)
    print(f"Площадь: {area}")
    
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    even_numbers = filter_even_numbers(numbers)
    print(f"Четные числа: {even_numbers}")
    
    # Закомментированный вызов бесконечного цикла
    # countdown(5)
    
    adult = is_adult(20)
    print(f"Взрослый: {adult}") 