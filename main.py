from database import DatabaseManager
from ai_workspace import LocalModelGameMaster
from new_world import create_world as create_new_world
from character_creation import get_main_character_for_world, create_character_in_world

def display_worlds(worlds):
    """Отображение списка миров."""
    if not worlds:
        print("Миров пока нет.")
        return
    
    print("Доступные миры:")
    for world in worlds:
        print(f"ID: {world['id']}, Название: {world['name']}")

def select_world(db_manager: DatabaseManager):
    """Выбор мира пользователем."""
    worlds = db_manager.get_all_worlds()
    display_worlds(worlds)
    
    if not worlds:
        print("Нет доступных миров. Создайте новый мир.")
        return create_world(db_manager)
    
    while True:
        try:
            choice = int(input("Выберите мир (введите ID): "))
            selected_world = next((w for w in worlds if w["id"] == choice), None)
            if selected_world:
                print(f"Вы выбрали мир: {selected_world['name']}")
                return selected_world
            else:
                print("Неверный ID. Попробуйте снова.")
        except ValueError:
            print("Введите корректный номер.")

def create_world(db_manager: DatabaseManager):
    """Создание нового мира через модуль new_world."""
    # Вызов функции из модуля new_world для создания мира
    world_id = create_new_world(db_path=db_manager.db.db_path)
    # Получаем информацию о новом мире для возврата
    new_world = db_manager.get_all_worlds()
    selected_world = next((w for w in new_world if w["id"] == world_id), None)
    if selected_world:
        print(f"Мир '{selected_world['name']}' создан с ID {world_id}.")
        return selected_world
    else:
        # Если не удается найти мир сразу после создания, возвращаем базовую информацию
        world_info = db_manager.db.fetch_one("SELECT name FROM Worlds WHERE world_id = ?", (world_id,))
        name = world_info["name"] if world_info else "Новый мир"
        return {"id": world_id, "name": name}

def delete_world(db_manager: DatabaseManager):
    """Удаление мира."""
    worlds = db_manager.get_all_worlds()
    display_worlds(worlds)
    
    if not worlds:
        print("Нет миров для удаления.")
        return
    
    try:
        world_id = int(input("Введите ID мира для удаления: "))
        db_manager.delete_world(world_id)
        print(f"Мир с ID {world_id} удален.")
    except ValueError:
        print("Введите корректный номер.")

def edit_worlds_menu(db_manager: DatabaseManager):
    """Меню редактирования миров."""
    while True:
        print("\n--- Редактирование миров ---")
        print("1. Создать новый мир")
        print("2. Удалить мир")
        print("3. Назад")
        
        choice = input("Выберите действие: ")
        
        if choice == "1":
            create_world(db_manager)
        elif choice == "2":
            delete_world(db_manager)
        elif choice == "3":
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

def main_loop():
    """Основной цикл приложения."""
    db_manager = DatabaseManager("game.db")
    
    while True:
        print("\n--- Главное меню ---")
        print("1. Выбрать мир")
        print("2. Редактировать миры")
        print("3. Выйти")
        
        menu_choice = input("Выберите действие: ")
        
        if menu_choice == "1":
            selected_world = select_world(db_manager)
            if selected_world:
                print(f"Загружаем мир: {selected_world['name']}...")
                
                # Проверяем наличие главного персонажа в выбранном мире
                main_character = get_main_character_for_world(selected_world['id'], db_path=db_manager.db.db_path)
                
                if main_character:
                    print(f"Найден главный персонаж: {main_character['name']} (ID: {main_character['id']})")
                    print("Запуск симуляции мира...")
                    # Здесь будет логика запуска симуляции мира с главным персонажем
                    # Пока что просто выводим сообщение
                    print("Симуляция мира запущена. Для выхода в главное меню нажмите любую клавишу...")
                    input("Нажмите Enter для возврата в главное меню...")
                else:
                    print("В этом мире нет главного персонажа.")
                    create_char = input("Хотите создать главного персонажа? (y/n): ").lower()
                    if create_char in ['y', 'yes', 'да']:
                        try:
                            character_id = create_character_in_world(selected_world['id'], db_path=db_manager.db.db_path)
                            print(f"Главный персонаж создан с ID: {character_id}")
                            
                            # После создания персонажа, спрашиваем, хочет ли пользователь запустить симуляцию
                            start_sim = input("Хотите запустить симуляцию мира с новым персонажем? (y/n): ").lower()
                            if start_sim in ['y', 'yes', 'да']:
                                print("Запуск симуляции мира...")
                                # Здесь будет логика запуска симуляции мира с новым персонажем
                                print("Симуляция мира запущена. Для выхода в главное меню нажмите любую клавишу...")
                                input("Нажмите Enter для возврата в главное меню...")
                        except Exception as e:
                            print(f"Ошибка при создании персонажа: {e}")
                    else:
                        print("Возвращаемся в главное меню...")
        elif menu_choice == "2":
            edit_worlds_menu(db_manager)
        elif menu_choice == "3":
            print("Выход из игры.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main_loop()
