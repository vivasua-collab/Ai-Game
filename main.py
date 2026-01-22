from database import DatabaseManager
from ai_workspace import LocalModelGameMaster

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
    """Создание нового мира."""
    name = input("Введите название нового мира: ")
    world_id = db_manager.create_world(name)
    print(f"Мир '{name}' создан с ID {world_id}.")
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
    ai_master = LocalModelGameMaster()

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
                # Здесь будет логика игры
        elif menu_choice == "2":
            edit_worlds_menu(db_manager)
        elif menu_choice == "3":
            print("Выход из игры.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main_loop()
