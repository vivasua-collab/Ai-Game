#!/usr/bin/env python3
"""
Тестирование интеграции всех компонентов системы
"""

from new_world import create_world
from character_creation import create_character_in_world, get_main_character_for_world
from database import DatabaseManager

def test_world_creation():
    """Тест создания мира"""
    print("=== Тест создания мира ===")
    
    # Создаем тестовый мир
    db_manager = DatabaseManager("game.db")
    world_id = create_world(db_path="game.db")
    
    print(f"Мир создан с ID: {world_id}")
    
    # Проверяем, что мир действительно создан
    worlds = db_manager.get_all_worlds()
    world_exists = any(w['id'] == world_id for w in worlds)
    
    if world_exists:
        print("✓ Мир успешно сохранен в базе данных")
    else:
        print("✗ Мир не найден в базе данных")
    
    return world_id

def test_character_creation(world_id):
    """Тест создания персонажа"""
    print(f"\n=== Тест создания персонажа в мире {world_id} ===")
    
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

def test_character_check(world_id):
    """Тест проверки наличия персонажа"""
    print(f"\n=== Тест проверки наличия персонажа в мире {world_id} ===")
    
    # Проверяем наличие персонажа
    main_char = get_main_character_for_world(world_id, db_path="game.db")
    
    if main_char:
        print(f"✓ Найден главный персонаж: {main_char['name']} (ID: {main_char['id']})")
    else:
        print("✗ Главный персонаж не найден")

if __name__ == "__main__":
    print("Запуск теста интеграции компонентов...")
    
    # Тест создания мира
    world_id = test_world_creation()
    
    # Тест создания персонажа
    char_id = test_character_creation(world_id)
    
    # Тест проверки наличия персонажа
    test_character_check(world_id)
    
    print("\n=== Завершение теста ===")
    print("Если все тесты прошли успешно, система готова к работе!")