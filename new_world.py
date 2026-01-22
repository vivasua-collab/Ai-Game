"""
Модуль для создания нового игрового мира.
Предоставляет возможность выбора между чтением из файла и вводом в текстовое поле.
"""

import json
import re
from typing import Dict, List, Any, Tuple
from repositories import GameWorldManager
from models import World, WorldConstant
import random


def create_world(db_path: str = "game.db") -> int:
    """
    Создание нового мира с возможностью выбора источника данных.
    
    Args:
        db_path: Путь к файлу базы данных
        
    Returns:
        ID созданного мира
    """
    print("\n--- Создание нового мира ---")
    print("1. Создать мир из файла")
    print("2. Ввести описание мира вручную")
    
    while True:
        choice = input("Выберите вариант (1 или 2): ").strip()
        if choice == "1":
            return _create_world_from_file(db_path)
        elif choice == "2":
            return _create_world_from_text_input(db_path)
        else:
            print("Неверный выбор. Пожалуйста, введите 1 или 2.")


def _create_world_from_file(db_path: str = "game.db") -> int:
    """
    Создание мира из локального файла.
    
    Args:
        db_path: Путь к файлу базы данных
        
    Returns:
        ID созданного мира
    """
    file_path = input("Введите путь к файлу с описанием мира: ").strip()
    
    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Создаем мир на основе содержимого файла
        world_id = _create_world_from_text(content, db_path)
        print(f"Мир успешно создан из файла: {file_path}")
        return world_id
    except FileNotFoundError:
        print(f"Файл не найден: {file_path}")
        raise
    except Exception as e:
        print(f"Ошибка при создании мира из файла: {e}")
        raise


def _create_world_from_text_input(db_path: str = "game.db") -> int:
    """
    Создание мира на основе ввода пользователя.
    
    Args:
        db_path: Путь к файлу базы данных
        
    Returns:
        ID созданного мира
    """
    print("Введите описание мира (для завершения ввода введите пустую строку):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    content = "\n".join(lines)
    if not content.strip():
        print("Описание мира не может быть пустым.")
        raise ValueError("Пустое описание мира")
    
    world_id = _create_world_from_text(content, db_path)
    print("Мир успешно создан на основе введенного описания.")
    return world_id


def _create_world_from_text(text: str, db_path: str = "game.db") -> int:
    """
    Создание мира на основе текстового описания.
    
    Args:
        text: Текстовое описание мира
        db_path: Путь к файлу базы данных
        
    Returns:
        ID созданного мира
    """
    # Анализируем текст для извлечения параметров
    world_params = _extract_world_parameters_from_text(text)
    
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
    world_manager = GameWorldManager(db_path)
    world_id = world_manager.worlds.create_world(world)
    
    # Создаем мировые константы, если они есть
    _save_world_constants(world_id, world_params, world_manager)
    
    print(f"Мир '{world.name}' успешно создан с ID: {world_id}")
    return world_id


def _extract_world_parameters_from_text(content: str) -> Dict[str, Any]:
    """
    Извлечение параметров мира из текстового описания.
    
    Args:
        content: Текстовое описание мира
        
    Returns:
        Словарь с параметрами мира
    """
    # Определяем шаблоны для поиска различных элементов
    patterns = {
        'name': r'(?:мир|мировой|игровой)?\s*([А-Яа-яЁё][а-яё]*\w*)',
        'theme': r'(?:тема|стиль|атмосфера|жанр):\s*(.+?)(?:\.|\n|$)',
        'rules': r'(?:правила|законы|ограничения):\s*(.+?)(?:\.|\n|$)',
        'constants': r'(?:константа|постоянная|параметр):\s*(.+?)(?:\.|\n|$)',
        'story_elements': r'(?:сюжет|история|повествование):\s*(.+?)(?:\.|\n|$)'
    }
    
    # Извлекаем данные из текста
    extracted_data = {}
    
    # Извлекаем название мира
    name_match = re.search(patterns['name'], content, re.IGNORECASE)
    if name_match:
        extracted_data['name'] = name_match.group(1).strip()
    else:
        # Если не нашли явное название, генерируем его
        extracted_data['name'] = _generate_world_name(content)
    
    # Извлекаем тему
    theme_matches = re.findall(r'(?:тема|стиль|атмосфера|жанр)[\s:,-]+([^.\\n]+)', content, re.IGNORECASE)
    if theme_matches:
        extracted_data['theme'] = ', '.join(theme_matches).strip()
    else:
        # Если тема не указана, определяем на основе ключевых слов
        extracted_data['theme'] = _infer_theme(content)
    
    # Извлекаем правила мира
    rules_matches = re.findall(r'(?:правила?|законы?|ограничения?|запреты?)\W+(.+?)(?:\.|\n|(?=правила?|законы?|ограничения?|,\s*[А-Яа-я]))', content, re.IGNORECASE | re.DOTALL)
    extracted_data['rules'] = [rule.strip() for rule in rules_matches if rule.strip()]
    
    # Извлекаем константы мира
    constants_matches = re.findall(r'(?:константа|постоянная|параметр|значение)\W+([^.!\n?]+)', content, re.IGNORECASE)
    extracted_data['constants'] = [const.strip() for const in constants_matches if const.strip()]
    
    # Извлекаем элементы повествования
    story_matches = re.findall(r'(?:сюжет|история|повествование|мир|вселенная)\W+([^.!\n?]+)', content, re.IGNORECASE)
    extracted_data['story_elements'] = [story.strip() for story in story_matches if story.strip()]
    
    # Дополнительно анализируем текст для извлечения конкретных значений
    extracted_data.update(_extract_specific_values(content))
    
    return extracted_data


def _generate_world_name(content: str) -> str:
    """Генерация названия мира на основе содержимого текста"""
    # Находим наиболее часто встречающиеся существительные или слова, которые могут быть названием
    words = re.findall(r'[А-Яа-яЁё][а-яё]+', content)
    
    # Убираем слишком короткие слова и выбираем потенциальные названия
    potential_names = [word for word in words if len(word) > 3 and word.lower() not in ['мир', 'это', 'что', 'как', 'так', 'все']]
    
    if potential_names:
        # Перемещаем наиболее часто встречающееся слово или просто первое подходящее
        return potential_names[0]
    else:
        # Если не удалось определить, генерируем случайное имя
        prefixes = ["Темный", "Светлый", "Забытый", "Загадочный", "Новый", "Древний"]
        suffixes = ["Мир", "Простор", "Край", "Царство", "Королевство", "Земля"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"


def _infer_theme(content: str) -> str:
    """Определение темы мира на основе ключевых слов в тексте"""
    content_lower = content.lower()
    
    themes = {
        "фэнтези": ["магия", "волшебник", "замок", "дракон", "эльф", "гном", "королевство"],
        "научная фантастика": ["технология", "космос", "робот", "корабль", "планета", "алгоритм", "искусственный интеллект"],
        "мистика": ["призрак", "дух", "тайна", "загадка", "паранормальный", "оккультный"],
        "вестерн": ["ковбой", "пистолет", "сараи", "шериф", "городок", "дикое запад"],
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


def _extract_specific_values(content: str) -> Dict[str, Any]:
    """Извлечение конкретных числовых и текстовых значений из текста"""
    values = {}
    
    # Ищем числовые константы
    numbers = re.findall(r'(\d+(?:\.\d+)?)', content)
    if numbers:
        values['numeric_constants'] = [float(num) for num in numbers[:5]]  # Перем первые 5 чисел
    
    # Ищем названия персонажей
    character_names = re.findall(r'(?:герой|персонаж|имя):\s*([А-Яа-яЁё][а-яё]*)', content, re.IGNORECASE)
    if character_names:
        values['character_names'] = character_names
    
    # Ищем названия мест
    location_names = re.findall(r'(?:место|локация|страна|город):\s*([А-Яа-яЁё][а-яё]*)', content, re.IGNORECASE)
    if location_names:
        values['locations'] = location_names
    
    # Ищем ключевые характеристики
    characteristics = re.findall(r'(?:характеристика|атрибут|свойство):\s*([^.!\n?]+)', content, re.IGNORECASE)
    if characteristics:
        values['characteristics'] = [char.strip() for char in characteristics]
    
    return values


def _save_world_constants(world_id: int, world_params: Dict[str, Any], world_manager: GameWorldManager):
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
        world_manager.constants.set_constant(constant)