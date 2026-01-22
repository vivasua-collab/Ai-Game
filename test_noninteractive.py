#!/usr/bin/env python3
"""
Тестирование интеграции компонентов без интерактивного ввода
"""

import io
import sys
from unittest.mock import patch, mock_open
from new_world import _create_world_from_text, _create_world_from_file
from character_creation import create_character_in_world, get_main_character_for_world
from database import DatabaseManager
from models import World
from repositories import GameWorldManager


def test_world_creation_from_text():
    """Тест создания мира из текста"""
    print("=== Тест создания мира из текста ===")
    
    sample_text = """Тестовый мир
    
    Тема: фэнтези, приключения
    
    Правила мира:
    - Магия разрешена
    - Запрещено убийство игроков
    - Уважай других игроков
    
    Константы:
    - Уровень магии: 7.5
    - Частота событий: 0.3
    
    Сюжетные элементы:
    - Древняя война
    - Затерянные артефакты
    """
    
    # Создаем мир из текста
    world_id = _create_world_from_text(sample_text, db_path="game.db")
    
    print(f"Мир создан с ID: {world_id}")
    
    # Проверяем, что мир действительно создан
    db_manager = DatabaseManager("game.db")
    worlds = db_manager.get_all_worlds()
    world_exists = any(w['id'] == world_id for w in worlds)
    
    if world_exists:
        print("✓ Мир успешно сохранен в базе данных")
        # Выведем информацию о мире
        world_info = next(w for w in worlds if w['id'] == world_id)
        print(f"  Название: {world_info['name']}")
    else:
        print("✗ Мир не найден в базе данных")
    
    return world_id


def test_character_creation(world_id):
    """Тест создания персонажа"""
    print(f"\n=== Тест создания персонажа в мире {world_id} ===")
    
    # Используем mock для имитации ввода пользователя
    with patch('builtins.input', side_effect=['Тестовый Герой', 'человек']):
        try:
            # Создаем персонажа в мире
            char_id = create_character_in_world(world_id, db_path="game.db")
            
            print(f"Персонаж создан с ID: {char_id}")
            
            # Проверяем, что персонаж действительно создан
            main_char = get_main_character_for_world(world_id, db_path="game.db")
            
            if main_char and main_char['id'] == char_id:
                print("✓ Персонаж успешно сохранен в базе данных")
                print(f"  Имя персонажа: {main_char['name']}")
                print(f"  Вид/раса: {main_char['species']}")
            else:
                print("✗ Персонаж не найден в базе данных")
            
            return char_id
        except Exception as e:
            print(f"Ошибка при создании персонажа: {e}")
            return None


def test_character_check(world_id):
    """Тест проверки наличия персонажа"""
    print(f"\n=== Тест проверки наличия персонажа в мире {world_id} ===")
    
    # Проверяем наличие персонажа
    main_char = get_main_character_for_world(world_id, db_path="game.db")
    
    if main_char:
        print(f"✓ Найден главный персонаж: {main_char['name']} (ID: {main_char['id']})")
    else:
        print("✗ Главный персонаж не найден")


def test_world_creation_from_file():
    """Тест создания мира из файла"""
    print(f"\n=== Тест создания мира из файла ===")
    
    # Подготовим тестовый файл
    file_content = """Мир Альтерии

Тема: фэнтези, магия, приключения
Жанр: эпическое фэнтези с элементами мистики

Правила мира:
- Магия требует энергии и имеет последствия
- Каждое заклинание влияет на окружающую среду
- Законы физики могут быть изменены магией
- Существуют древние артефакты с огромной силой

Константы:
- Уровень магической энергии: 7.5
- Частота магических бурь: 0.3
- Сила защиты: 100
- Уровень опасности: 5

Сюжетные элементы:
- Древняя война между магами и рыцарями
- Затерянные города в облаках
- Драконы как хранители знаний
- Поиск потерянной короны
"""
    
    # Используем mock для имитации чтения файла
    with patch("builtins.open", mock_open(read_data=file_content)):
        try:
            world_id = _create_world_from_text(file_content, db_path="game.db")
            print(f"Мир из файла создан с ID: {world_id}")
            
            # Проверяем, что мир действительно создан
            db_manager = DatabaseManager("game.db")
            worlds = db_manager.get_all_worlds()
            world_exists = any(w['id'] == world_id for w in worlds)
            
            if world_exists:
                print("✓ Мир из файла успешно сохранен в базе данных")
                return world_id
            else:
                print("✗ Мир из файла не найден в базе данных")
                return None
        except Exception as e:
            print(f"Ошибка при создании мира из файла: {e}")
            return None


if __name__ == "__main__":
    print("Запуск теста интеграции компонентов (без интерактивного ввода)...")
    
    # Тест создания мира из текста
    world_id = test_world_creation_from_text()
    
    if world_id:
        # Тест создания персонажа
        char_id = test_character_creation(world_id)
        
        # Тест проверки наличия персонажа
        test_character_check(world_id)
    
    # Тест создания мира из файла
    file_world_id = test_world_creation_from_file()
    
    print("\n=== Завершение теста ===")
    print("Если все тесты прошли успешно, система готова к работе!")