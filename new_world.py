"""
Модуль для генерации нового игрового мира на основе текстового описания
с использованием локальной нейросети.
"""

import json
import re
from typing import Dict, List, Any, Tuple
from repositories import GameWorldManager
from models import World, WorldConstant
import random


class WorldGenerator:
    """Класс для генерации мира на основе текстового описания и локальной нейросети"""
    
    def __init__(self, db_path: str = "game.db"):
        """
        Инициализация генератора мира
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.world_manager = GameWorldManager(db_path)
        print("Генератор мира инициализирован")
    
    def extract_world_parameters(self, text_file_path: str) -> Dict[str, Any]:
        """
        Извлечение параметров мира из текстового файла с помощью локальной нейросети
        
        Args:
            text_file_path: Путь к текстовому файлу с описанием мира
            
        Returns:
            Словарь с параметрами мира
        """
        # Читаем текстовый файл
        with open(text_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Симулируем работу локальной нейросети для извлечения параметров
        return self._simulate_local_llm_processing(content)
    
    def _simulate_local_llm_processing(self, content: str) -> Dict[str, Any]:
        """
        Симуляция обработки текста с помощью локальной нейросети
        
        Args:
            content: Текстовое описание мира
            
        Returns:
            Словарь с извлеченными параметрами мира
        """
        # Определяем шаблоны для поиска различных элементов
        patterns = {
            'name': r'(?:мир|мировой|игровой)?\s*([А-ЯЁ][а-яё]*\w*)',
            'theme': r'(?:тема|стиль|атмосфера|жанр):\s*(.+?)(?:\.|\n|$)',
            'rules': r'(?:правила|законы|ограничения):\s*(.+?)(?:\.|\n|$)',
            'constants': r'(?:константа|постоянная|параметр):\s*(.+?)(?:\.|\n|$)',
            'story_elements': r'(?:сюжет|история|повествование):\s*(.+?)(?:\.|\n|$)'
        }
        
        # Извлекаем информацию из текста
        extracted_data = {}
        
        # Извлекаем название мира
        name_match = re.search(patterns['name'], content, re.IGNORECASE)
        if name_match:
            extracted_data['name'] = name_match.group(1).strip()
        else:
            # Если не нашли явное название, генерируем его
            extracted_data['name'] = self._generate_world_name(content)
        
        # Извлекаем тему
        theme_matches = re.findall(r'(?:тема|стиль|атмосфера|жанр)[\s:,-]+([^.\n]+)', content, re.IGNORECASE)
        if theme_matches:
            extracted_data['theme'] = ', '.join(theme_matches).strip()
        else:
            # Если тема не указана, определяем на основе ключевых слов
            extracted_data['theme'] = self._infer_theme(content)
        
        # Извлекаем правила мира
        rules_matches = re.findall(r'(?:правила?|законы?|ограничения?|запреты?)\W+(.+?)(?:\.|\n|(?=правила?|законы?|ограничения?|,\s*[А-ЯЁ]))', content, re.IGNORECASE | re.DOTALL)
        extracted_data['rules'] = [rule.strip() for rule in rules_matches if rule.strip()]
        
        # Извлекаем константы мира
        constants_matches = re.findall(r'(?:константа|постоянная|параметр|значение)\W+([^.!\n?]+)', content, re.IGNORECASE)
        extracted_data['constants'] = [const.strip() for const in constants_matches if const.strip()]
        
        # Извлекаем элементы повествования
        story_matches = re.findall(r'(?:сюжет|история|повествование|мир|вселенная)\W+([^.!\n?]+)', content, re.IGNORECASE)
        extracted_data['story_elements'] = [story.strip() for story in story_matches if story.strip()]
        
        # Дополнительно анализируем текст для извлечения конкретных значений
        extracted_data.update(self._extract_specific_values(content))
        
        return extracted_data
    
    def _generate_world_name(self, content: str) -> str:
        """Генерация названия мира на основе содержимого текста"""
        # Находим наиболее часто встречающиеся существительные или слова, которые могут быть названием
        words = re.findall(r'[А-ЯЁ][а-яё]+', content)
        
        # Убираем слишком короткие слова и выбираем потенциальные названия
        potential_names = [word for word in words if len(word) > 3 and word.lower() not in ['мир', 'это', 'что', 'как', 'так', 'все']]
        
        if potential_names:
            # Берем наиболее часто встречающееся слово или просто первое подходящее
            return potential_names[0]
        else:
            # Если не удалось определить, генерируем случайное имя
            prefixes = ["Темный", "Светлый", "Забытый", "Загадочный", "Новый", "Древний"]
            suffixes = ["Мир", "Простор", "Край", "Царство", "Королевство", "Земля"]
            return f"{random.choice(prefixes)} {random.choice(suffixes)}"
    
    def _infer_theme(self, content: str) -> str:
        """Определение темы мира на основе ключевых слов в тексте"""
        content_lower = content.lower()
        
        themes = {
            "фэнтези": ["магия", "волшебник", "замок", "дракон", "эльф", "гном", "колдовство"],
            "научная фантастика": ["технология", "космос", "робот", "корабль", "планета", "алгоритм", "искусственный интеллект"],
            "мистика": ["призрак", "дух", "загадка", "тайна", "паранормальный", "оккультный"],
            "вестерн": ["ковбой", "пистолет", "сарай", "шериф", "городок", "дикое запад"],
            "стимпанк": ["паровой", "механизм", "часы", "бронза", "пар", "инженерия"],
            "биопанк": ["биология", "генетика", "органика", "трансформация", "эволюция", "мутация"]
        }
        
        found_themes = []
        for theme, keywords in themes.items():
            if any(keyword in content_lower for keyword in keywords):
                found_themes.append(theme)
        
        if found_themes:
            return ", ".join(found_themes)
        else:
            return "универсальный"
    
    def _extract_specific_values(self, content: str) -> Dict[str, Any]:
        """Извлечение конкретных числовых и текстовых значений из текста"""
        values = {}
        
        # Ищем числовые константы
        numbers = re.findall(r'(\d+(?:\.\d+)?)', content)
        if numbers:
            values['numeric_constants'] = [float(num) for num in numbers[:5]]  # Берем первые 5 чисел
        
        # Ищем названия персонажей
        character_names = re.findall(r'(?:герой|персонаж|имя):\s*([А-ЯЁ][а-яё]*)', content, re.IGNORECASE)
        if character_names:
            values['character_names'] = character_names
        
        # Ищем названия мест
        location_names = re.findall(r'(?:место|локация|страна|город):\s*([А-ЯЁ][а-яё]*)', content, re.IGNORECASE)
        if location_names:
            values['locations'] = location_names
        
        # Ищем ключевые характеристики
        characteristics = re.findall(r'(?:характеристика|атрибут|свойство):\s*([^.!\n?]+)', content, re.IGNORECASE)
        if characteristics:
            values['characteristics'] = [char.strip() for char in characteristics]
        
        return values
    
    def create_world_from_text(self, text_file_path: str) -> int:
        """
        Создание нового мира на основе текстового файла
        
        Args:
            text_file_path: Путь к текстовому файлу с описанием мира
            
        Returns:
            ID созданного мира
        """
        # Извлекаем параметры мира из текста
        world_params = self.extract_world_parameters(text_file_path)
        
        # Создаем объект мира
        world = World(
            name=world_params.get('name', 'Новый Мир'),
            theme=world_params.get('theme', 'Неопределенный'),
            is_active=True
        )
        
        # Устанавливаем дополнительные настройки мира
        settings = {
            'rules': world_params.get('rules', []),
            'story_elements': world_params.get('story_elements', []),
            'constants': world_params.get('constants', []),
            'numeric_constants': world_params.get('numeric_constants', []),
            'character_names': world_params.get('character_names', []),
            'locations': world_params.get('locations', []),
            'characteristics': world_params.get('characteristics', [])
        }
        world.settings = settings
        
        # Сохраняем мир в базу данных
        world_id = self.world_manager.worlds.create_world(world)
        
        # Создаем мировые константы, если они есть
        self._save_world_constants(world_id, world_params)
        
        print(f"Мир '{world.name}' успешно создан с ID: {world_id}")
        return world_id
    
    def _save_world_constants(self, world_id: int, world_params: Dict[str, Any]):
        """Сохранение мировых констант в базу данных"""
        constants_data = [
            ('world_theme', world_params.get('theme', 'default'), 'TEXT', 'Тема мира'),
            ('creation_date', str(world_params.get('name', 'unknown')), 'TEXT', 'Название мира')
        ]
        
        # Добавляем числовые константы, если они есть
        numeric_constants = world_params.get('numeric_constants', [])
        for i, const_val in enumerate(numeric_constants[:10]):  # Ограничиваем до 10 констант
            const_key = f'constant_{i+1}'
            constants_data.append((const_key, str(const_val), 'REAL', f'Числовая константа {i+1}'))
        
        # Сохраняем константы в базу данных
        for key, value, data_type, description in constants_data:
            constant = WorldConstant(
                world_id=world_id,
                constant_key=key,
                constant_value=value,
                data_type=data_type,
                description=description
            )
            self.world_manager.constants.set_constant(constant)


def generate_world_from_file(file_path: str, db_path: str = "game.db") -> int:
    """
    Функция для генерации мира из текстового файла
    
    Args:
        file_path: Путь к текстовому файлу с описанием мира
        db_path: Путь к файлу базы данных
        
    Returns:
        ID созданного мира
    """
    generator = WorldGenerator(db_path)
    return generator.create_world_from_text(file_path)


if __name__ == "__main__":
    # Пример использования
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        world_id = generate_world_from_file(file_path)
        print(f"Создан мир с ID: {world_id}")
    else:
        print("Укажите путь к текстовому файлу с описанием мира")