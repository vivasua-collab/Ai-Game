from init_database import initialize_database
from repositories import GameWorldManager

def quick_start():
    """Быстрый старт работы с базой данных"""
    
    # 1. Инициализация
    initialize_database()
    
    # 2. Создание менеджера
    manager = GameWorldManager()
    
    # 3. Основные операции
    # Создать мир
    from models import World
    import time
    world_name = f"Нова_{int(time.time())}"
    new_world = World(name=world_name, theme="Фэнтези")
    world_id = manager.worlds.create_world(new_world)
    
    # Добавить персонажа
    from models import Character
    import json
    hero = Character(
        world_id=world_id,
        name="Косой",
        type="player",
        skills_json=json.dumps({"атака": 80, "защита": 70}, ensure_ascii=False)
    )
    hero_id = manager.characters.create_character(hero)
    
    # Получить контекст для ИИ
    context = manager.get_world_context(world_id)
    
    # Сохранить состояние (например, после игровой сессии)
    # ...
    
    print(f"Мир '{new_world.name}' готов к использованию!")
    print(f"ID мира: {world_id}")
    print(f"ID главного героя: {hero_id}")
    
    return manager, world_id

if __name__ == "__main__":
    quick_start()
