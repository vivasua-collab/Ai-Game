"""
Модуль для создания персонажа в соответствии с правилами мира.
"""

import json
from models import Character
from repositories import GameWorldManager
from typing import Dict, Any


def create_character_in_world(world_id: int, db_path: str = "game.db") -> int:
    """
    Создание персонажа в указанном мире.

    Args:
        world_id: ID мира, в котором создается персонаж
        db_path: Путь к файлу базы данных

    Returns:
        ID созданного персонажа
    """
    print(f"\n--- Создание персонажа в мире ID: {world_id} ---")
    
    # Запрашиваем данные персонажа у пользователя
    name = input("Введите имя персонажа: ").strip()
    
    # Определяем тип персонажа (игрок или NPC)
    char_type = "player"  # Для главного персонажа всегда устанавливаем тип "player"
    
    # Запрашиваем вид/расу персонажа
    species = input("Введите расу/вид персонажа (например, человек, эльф, гном и т.д.): ").strip()
    
    # Инициализируем пустой словарь для навыков
    skills = {}
    skills_json = json.dumps(skills, ensure_ascii=False)
    
    # Создаем объект персонажа
    character = Character(
        world_id=world_id,
        name=name,
        type=char_type,
        species=species,
        skills_json=skills_json,
        current_health=100.0,
        max_health=100.0
    )
    
    # Сохраняем персонажа в базе данных
    world_manager = GameWorldManager(db_path)
    character_id = world_manager.characters.create_character(character)
    
    print(f"Персонаж '{name}' успешно создан с ID: {character_id}")
    
    return character_id


def get_main_character_for_world(world_id: int, db_path: str = "game.db") -> Dict[str, Any]:
    """
    Получить главного персонажа (игрока) для указанного мира.

    Args:
        world_id: ID мира
        db_path: Путь к файлу базы данных

    Returns:
        Словарь с информацией о персонаже или None, если персонаж не найден
    """
    world_manager = GameWorldManager(db_path)
    characters = world_manager.characters.get_characters_by_world_and_type(world_id, "player")
    
    if characters:
        # Возвращаем первого попавшегося игрока (главного персонажа)
        character = characters[0]
        return {
            "id": character.character_id,
            "name": character.name,
            "species": character.species
        }
    
    return None