from init_database import initialize_database
from models import *
from repositories import GameWorldManager

def test_database():
    """Тестирование работы базы данных"""
    
    # 1. Инициализируем базу данных
    print("Инициализация базы данных...")
    initialize_database("test_world.db")
    
    # 2. Создаем менеджер мира
    print("\nСоздание менеджера мира...")
    manager = GameWorldManager("test_world.db")
    
    # 3. Создаем новый мир
    print("\nСоздание нового мира...")
    new_world = World(
        name="Элиндор",
        theme="Фэнтези с магией камня",
        settings={
            "magic_system": "rune_based",
            "gravity": 9.8,
            "allow_technology": False
        }
    )
    
    world_id = manager.worlds.create_world(new_world)
    print(f"Мир создан с ID: {world_id}")
    
    # 4. Добавляем мировые константы
    print("\nДобавление мировых констант...")
    gravity = WorldConstant(
        world_id=world_id,
        constant_key="GRAVITY",
        constant_value="9.78",
        data_type="REAL",
        description="Ускорение свободного падения"
    )
    
    magic_power = WorldConstant(
        world_id=world_id,
        constant_key="MAGIC_POWER",
        constant_value="100",
        data_type="INTEGER",
        description="Базовая сила магии"
    )
    
    manager.constants.set_constant(gravity)
    manager.constants.set_constant(magic_power)
    
    # 5. Создаем персонажей
    print("\nСоздание персонажей...")
    
    player = Character(
        world_id=world_id,
        name="Артан",
        type="player",
        species="человек",
        skills={"меч": 75, "магия": 40, "красноречие": 60},
        location_x=10.5,
        location_y=20.3,
        current_health=100,
        max_health=100
    )
    
    npc = Character(
        world_id=world_id,
        name="Лиана",
        type="npc",
        species="эльф",
        skills={"стрельба из лука": 90, "скрытность": 85, "травничество": 70},
        location_x=12.0,
        location_y=21.0,
        current_health=85,
        max_health=85
    )
    
    player_id = manager.characters.create_character(player)
    npc_id = manager.characters.create_character(npc)
    print(f"Персонажи созданы: ID игрока={player_id}, ID NPC={npc_id}")
    
    # 6. Создаем отношения между персонажами
    print("\nСоздание отношений...")
    relationship = Relationship(
        world_id=world_id,
        character_a_id=player_id,
        character_b_id=npc_id,
        relationship_type="friendship",
        score=30.0
    )
    
    rel_id = manager.relationships.create_relationship(relationship)
    print(f"Отношение создано с ID: {rel_id}")
    
    # 7. Добавляем предметы
    print("\nСоздание предметов...")
    
    # Шаблон меча
    sword_item = Item(
        world_id=world_id,
        name="Стальной меч",
        description="Прочный стальной меч",
        type="weapon",
        base_properties={"damage": 15, "weight": 3.5, "durability": 100}
    )
    
    item_id = manager.items.create_item(sword_item)
    
    # Экземпляр меча
    sword_instance = ItemInstance(
        world_id=world_id,
        item_id=item_id,
        custom_name="Меч Артана",
        current_properties={"damage": 18, "enchantment": "fire"}
    )
    
    instance_id = manager.items.create_item_instance(sword_instance)
    
    # Добавляем в инвентарь игрока
    inventory = Inventory(
        character_id=player_id,
        item_instance_id=instance_id,
        quantity=1,
        condition=95.0,
        custom_properties={"owner": "Артан", "acquired": "2024-01-15"}
    )
    
    inv_id = manager.inventory.add_to_inventory(inventory)
    print(f"Предмет добавлен в инвентарь с ID: {inv_id}")
    
    # 8. Получаем контекст мира для ИИ
    print("\nПолучение контекста мира...")
    context = manager.get_world_context(world_id)
    
    if context:
        print(f"Мир: {context['world']['name']}")
        print(f"Персонажей в мире: {len(context['characters'])}")
        print(f"Констант: {len(context['constants'])}")
        print(f"Отношений: {len(context['relationships'])}")
        
        # Показываем инвентарь игрока
        if player_id in context['inventories']:
            print(f"\nИнвентарь игрока:")
            for item in context['inventories'][player_id]:
                print(f"  - {item.get('item_name', 'Предмет')}")
    
    # 9. Тестируем обновление состояний
    print("\nТестирование обновления состояний...")
    
    # Перемещаем персонажа
    manager.characters.move_character(player_id, 15.0, 25.0)
    
    # Обновляем отношение
    manager.relationships.update_relationship_score(rel_id, 10.0)
    
    # Добавляем взаимодействие
    interaction = {
        "type": "conversation",
        "topic": "квест",
        "mood": "friendly",
        "summary": "Обсудили задание по поиску артефакта"
    }
    manager.relationships.add_interaction(rel_id, interaction)
    
    # 10. Получаем обновленный контекст
    print("\nОбновленный контекст мира:")
    updated_context = manager.get_world_context(world_id)
    
    player_data = next(c for c in updated_context['characters'] if c['character_id'] == player_id)
    print(f"Новая позиция игрока: {player_data['location_x']}, {player_data['location_y']}")
    
    # 11. Тестируем каскадное удаление
    print("\nТестирование каскадного удаления мира...")
    manager.worlds.delete_world(world_id)
    
    # Проверяем, что данные удалились
    remaining_chars = manager.characters.get_world_characters(world_id)
    print(f"Персонажей осталось после удаления мира: {len(remaining_chars)}")
    
    print("\nТестирование завершено успешно!")

if __name__ == "__main__":
    test_database()