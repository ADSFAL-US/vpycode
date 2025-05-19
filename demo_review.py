#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Демонстрационный файл для тестирования функции code review
"""

import tkinter as tk
import code_review

def show_demo_review():
    # Создаем простое окно для демонстрации
    root = tk.Tk()
    root.title("Code Review Demo")
    root.geometry("400x200")
    
    # Создаем старый и новый текст для сравнения
    old_code = """def calculate_sum(a, b):
    # Сложение двух чисел
    return a + b
    
def multiply(x, y):
    # Умножение двух чисел
    return x * y
    
# Пример использования
result = calculate_sum(5, 3)
print(f"Сумма: {result}")"""

    new_code = """def calculate_sum(a, b):
    # Сложение двух чисел
    return a + b

def multiply(x, y):
    # Умножение двух чисел
    return x * y
    
def divide(x, y):
    # Деление двух чисел
    if y == 0:
        raise ZeroDivisionError("Деление на ноль невозможно!")
    return x / y
    
# Пример использования
result = calculate_sum(5, 3)
print(f"Сумма: {result}")
product = multiply(4, 2)
print(f"Произведение: {product}")"""
    
    # Функции обратного вызова
    def on_accept(content):
        print("Изменения приняты!")
        root.title("Изменения приняты")
        
    def on_reject():
        print("Изменения отклонены!")
        root.title("Изменения отклонены")
    
    # Создаем кнопку для запуска предпросмотра
    button = tk.Button(
        root, 
        text="Запустить предпросмотр изменений", 
        command=lambda: code_review.show_code_review(
            root, 
            "example.py", 
            old_code, 
            new_code, 
            line_num=8, 
            on_accept=on_accept, 
            on_reject=on_reject
        )
    )
    button.pack(pady=80)
    
    # Запускаем главный цикл
    root.mainloop()

if __name__ == "__main__":
    show_demo_review() 