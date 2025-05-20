"""
Модуль проводника файлов для редактора кода.
"""

import os
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk

from theme import KanagawaTheme

class FileExplorer:
    """Класс проводника файлов"""
    
    def __init__(self, parent, frame):
        """
        Инициализация проводника файлов
        
        Args:
            parent: родительский экземпляр приложения
            frame: фрейм, в котором размещается проводник
        """
        self.parent = parent
        self.frame = frame
        self.current_path = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса проводника файлов"""
        # Заголовок проводника
        explorer_header = ctk.CTkFrame(self.frame, fg_color=KanagawaTheme.DARKER_BG, height=30)
        explorer_header.pack(fill="x")
        
        explorer_label = ctk.CTkLabel(
            explorer_header, 
            text="ПРОВОДНИК", 
            text_color=KanagawaTheme.FOREGROUND, 
            font=("Arial", 10, "bold")
        )
        explorer_label.pack(side="left", padx=10)
        
        # Кнопка открытия проекта
        open_project_btn = ctk.CTkButton(
            explorer_header, 
            text="📂", 
            width=25, 
            height=20, 
            fg_color="transparent", 
            hover_color=KanagawaTheme.LIGHTER_BG,
            text_color=KanagawaTheme.FOREGROUND, 
            command=self.parent.open_project
        )
        open_project_btn.pack(side="right", padx=5)
        
        # Дерево файлов
        self.tree_style = ttk.Style()
        self.tree_style.configure(
            "Treeview", 
            background=KanagawaTheme.BACKGROUND, 
            foreground=KanagawaTheme.FOREGROUND, 
            fieldbackground=KanagawaTheme.BACKGROUND, 
            borderwidth=0,
            rowheight=22
        )
        self.tree_style.map("Treeview", background=[("selected", KanagawaTheme.SELECTION)])
        
        self.tree_style.configure(
            "Treeview.Heading", 
            background=KanagawaTheme.DARKER_BG, 
            foreground=KanagawaTheme.FOREGROUND, 
            borderwidth=0
        )
        
        self.tree = ttk.Treeview(self.frame, style="Treeview", show="tree")
        self.tree.pack(fill="both", expand=True)
        
        # Полоса прокрутки
        tree_scrollbar = ctk.CTkScrollbar(
            self.frame, 
            command=self.tree.yview,
            button_color=KanagawaTheme.SCROLLBAR,
            button_hover_color=KanagawaTheme.FOREGROUND
        )
        tree_scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Привязка событий
        self.tree.bind("<Double-1>", self._on_item_double_click)
    
    def _on_item_double_click(self, event):
        """Обрабатывает двойной щелчок по элементу дерева"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            item_dict = self._get_item_path(item_id)
            if item_dict and os.path.isfile(item_dict["path"]):
                self.parent.load_file(item_dict["path"])
    
    def _get_item_path(self, item_id):
        """
        Получает путь к элементу дерева
        
        Args:
            item_id: идентификатор элемента
            
        Returns:
            dict: словарь с информацией об элементе (path, type)
        """
        if not hasattr(self.tree, 'items_dict'):
            return None
        
        return self.tree.items_dict.get(item_id)
    
    def update_tree(self, path):
        """
        Обновляет дерево файлов для указанной директории
        
        Args:
            path (str): Путь к директории
        """
        # Проверяем, что путь существует
        if not os.path.exists(path):
            return
        
        # Сохраняем текущий путь
        self.current_path = path
        
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Инициализируем словарь для хранения путей
        self.tree.items_dict = {}
        
        # Добавляем корневую директорию
        root_text = os.path.basename(path) or path
        root = self.tree.insert("", "end", text=f" {root_text}")
        self.tree.items_dict[root] = {"path": path, "type": "directory"}
        
        # Рекурсивно добавляем все файлы и директории
        self._add_directory_to_tree(path, root)
    
    def _add_directory_to_tree(self, path, parent):
        """
        Рекурсивно добавляет директорию в дерево
        
        Args:
            path (str): Путь к директории
            parent: родительский элемент в дереве
        """
        try:
            # Получаем список файлов и директорий
            items = sorted(os.listdir(path))
            
            # Сначала добавляем директории
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    item_id = self.tree.insert(parent, "end", text=f" 📁 {item}")
                    self.tree.items_dict[item_id] = {"path": item_path, "type": "directory"}
                    # Рекурсивно добавляем содержимое директории
                    self._add_directory_to_tree(item_path, item_id)
            
            # Затем добавляем файлы
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) and not item.startswith('.'):
                    # Определяем иконку для файла
                    icon = self._get_file_icon(item_path)
                    item_id = self.tree.insert(parent, "end", text=f" {icon} {item}")
                    self.tree.items_dict[item_id] = {"path": item_path, "type": "file"}
        except:
            pass
    
    def _get_file_icon(self, file_path):
        """
        Возвращает иконку для файла в зависимости от его расширения
        
        Args:
            file_path (str): Путь к файлу
            
        Returns:
            str: Иконка файла
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Словарь соответствия расширений и иконок
        icons = {
            '.py': '🐍',
            '.js': '📝',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📘',
            '.txt': '📄',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.mp3': '🎵',
            '.mp4': '🎬',
            '.pdf': '📑',
            '.zip': '📦',
            '.rar': '📦',
            '.exe': '⚙️',
            '.sh': '⚙️',
            '.bat': '⚙️',
        }
        
        return icons.get(ext, '📄')
    
    def refresh(self):
        """Обновляет дерево файлов для текущей директории"""
        if self.current_path:
            self.update_tree(self.current_path)
    
    def focus(self):
        """Устанавливает фокус на дерево файлов"""
        self.tree.focus_set()
    
    def toggle(self):
        """For backwards compatibility - now handled directly in main app"""
        # Toggle is now handled by the main application
        pass 