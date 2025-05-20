"""
Менеджер плагинов для загрузки, активации и деактивации плагинов.
"""
import os
import sys
import importlib
import inspect
import traceback
from typing import Dict, List, Any, Type

from plugins.base import Plugin

class PluginManager:
    """Класс для управления плагинами приложения."""
    
    def __init__(self, app):
        """
        Инициализация менеджера плагинов.
        
        Args:
            app: Экземпляр основного приложения
        """
        self.app = app
        self.plugins: Dict[str, Plugin] = {}
        self.active_plugins: Dict[str, Plugin] = {}
        self.plugin_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),  # Встроенные плагины
            os.path.join(os.path.expanduser("~"), ".vpycode", "plugins")  # Пользовательские плагины
        ]
    
    def discover_plugins(self) -> List[Type[Plugin]]:
        """
        Обнаруживает все доступные плагины.
        
        Returns:
            Список классов плагинов
        """
        discovered_plugins = []
        
        # Добавляем каталог плагинов в sys.path, если его там нет
        for plugin_dir in self.plugin_dirs:
            if os.path.exists(plugin_dir) and plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
        
        # Сканируем все директории плагинов
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
                
            # Перебираем все файлы в каталоге плагинов
            for item in os.listdir(plugin_dir):
                if item.startswith('__') or not item.endswith('.py'):
                    continue
                    
                module_name = item[:-3]  # Убираем расширение .py
                try:
                    # Формируем полный путь к модулю
                    if plugin_dir.endswith('plugins'):
                        # Для встроенных плагинов используем формат "plugins.module_name"
                        full_module_name = f"plugins.{module_name}"
                    else:
                        # Для пользовательских плагинов просто имя модуля
                        full_module_name = module_name
                        
                    # Загружаем модуль плагина
                    module = importlib.import_module(full_module_name)
                    
                    # Ищем в модуле классы, наследующие от Plugin
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, Plugin) and obj != Plugin:
                            discovered_plugins.append(obj)
                            print(f"Обнаружен плагин: {name} в {full_module_name}")
                            
                except Exception as e:
                    print(f"Ошибка при обнаружении плагина {module_name}: {e}")
                    traceback.print_exc()
        
        return discovered_plugins
    
    def load_plugins(self):
        """
        Загружает и инициализирует все доступные плагины.
        """
        # Обнаружение плагинов
        plugin_classes = self.discover_plugins()
        
        # Загрузка каждого плагина
        for plugin_class in plugin_classes:
            try:
                # Создаем экземпляр плагина
                plugin_instance = plugin_class(self.app)
                
                # Сохраняем экземпляр плагина
                self.plugins[plugin_instance.name] = plugin_instance
                
                print(f"Плагин загружен: {plugin_instance.name} v{plugin_instance.version}")
                
            except Exception as e:
                print(f"Ошибка при загрузке плагина {plugin_class.__name__}: {e}")
                traceback.print_exc()
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Активирует указанный плагин.
        
        Args:
            plugin_name: Имя плагина для активации
            
        Returns:
            True если активация успешна, иначе False
        """
        print(f"[DEBUG] Попытка активации плагина {plugin_name}")
        if plugin_name not in self.plugins:
            print(f"[ERROR] Плагин не найден: {plugin_name}")
            return False
            
        if plugin_name in self.active_plugins:
            print(f"[DEBUG] Плагин уже активен: {plugin_name}")
            return True
            
        try:
            print(f"[DEBUG] Вызов метода activate() для плагина {plugin_name}")
            # Активируем плагин
            self.plugins[plugin_name].activate()
            
            # Добавляем в список активных плагинов
            self.active_plugins[plugin_name] = self.plugins[plugin_name]
            
            print(f"[DEBUG] Плагин успешно активирован: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при активации плагина {plugin_name}: {e}")
            traceback.print_exc()
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Деактивирует указанный плагин.
        
        Args:
            plugin_name: Имя плагина для деактивации
            
        Returns:
            True если деактивация успешна, иначе False
        """
        if plugin_name not in self.active_plugins:
            print(f"Плагин не активен: {plugin_name}")
            return False
            
        try:
            # Деактивируем плагин
            self.active_plugins[plugin_name].deactivate()
            
            # Удаляем из списка активных плагинов
            del self.active_plugins[plugin_name]
            
            print(f"Плагин деактивирован: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"Ошибка при деактивации плагина {plugin_name}: {e}")
            traceback.print_exc()
            return False
    
    def activate_all(self):
        """Активирует все загруженные плагины."""
        for plugin_name in list(self.plugins.keys()):
            self.activate_plugin(plugin_name)
    
    def deactivate_all(self):
        """Деактивирует все активные плагины."""
        for plugin_name in list(self.active_plugins.keys()):
            self.deactivate_plugin(plugin_name)
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о всех загруженных плагинах.
        
        Returns:
            Список словарей с информацией о плагинах
        """
        plugin_info = []
        
        for name, plugin in self.plugins.items():
            plugin_info.append({
                "name": name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "active": name in self.active_plugins
            })
        
        return plugin_info
    
    def get_all_plugins(self):
        """
        Возвращает все загруженные плагины.
        
        Returns:
            Список экземпляров плагинов
        """
        return list(self.plugins.values())
    
    def get_plugin_by_name(self, name):
        """
        Возвращает плагин по его имени.
        
        Args:
            name (str): Имя плагина
            
        Returns:
            Plugin: Экземпляр плагина или None, если плагин не найден
        """
        return self.plugins.get(name)
    
    def get_plugins_for_extension(self, extension):
        """
        Возвращает список плагинов, поддерживающих указанное расширение файла.
        
        Args:
            extension (str): Расширение файла (например, '.py')
            
        Returns:
            List[Plugin]: Список плагинов
        """
        supported_plugins = []
        
        for plugin in self.plugins.values():
            if hasattr(plugin, 'supported_extensions') and extension in plugin.supported_extensions:
                supported_plugins.append(plugin)
                
        return supported_plugins
    
    def activate_plugins(self, app):
        """
        Активирует все плагины.
        
        Args:
            app: Экземпляр приложения
        """
        for plugin_name in list(self.plugins.keys()):
            self.activate_plugin(plugin_name)