from database import DatabaseManager
from ai_workspace import api
from new_world import create_world as create_new_world
from character_creation import get_main_character_for_world, create_character_in_world
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

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

def start_models_with_timeout():
    """Запускает модели с таймаутом 10 секунд, после чего продолжает выполнение."""
    def get_user_choice():
        print("Выберите количество моделей для запуска:")
        print("1 - Запустить одну модель")
        print("2 - Запустить две модели")
        choice = input("Ваш выбор (1 или 2, по умолчанию 1): ").strip()
        if choice == "2":
            return 2
        else:
            return 1
    
    # Запускаем ввод пользователя в отдельном потоке
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(get_user_choice)
    
    # Ждем ввод в течение 10 секунд
    try:
        choice = future.result(timeout=10)
    except:
        print("\nВремя ожидания истекло. Продолжаем с одной моделью.")
        choice = 1
    
    # Запускаем модели
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(api.start_models(choice))
    loop.close()
    
    return success

def chat_simulation(selected_world, main_character):
    """Симуляция мира с чатом и взаимодействием с ИИ."""
    print("Запуск симуляции мира...")
    
    # Отправляем первый запрос в API ИИ для старта мира
    initial_prompt = f"Создай начальный сценарий для мира '{selected_world['name']}' с главным героем '{main_character['name']}'. Опиши начальную ситуацию, локацию и возможные действия."
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    initial_response = loop.run_until_complete(api.process_input(f"INPUT-1: {initial_prompt}"))
    loop.close()
    
    print("\n--- НАЧАЛО ИГРЫ ---")
    print(initial_response)
    
    # Основной цикл чата
    while True:
        user_input = input("\nВаше действие или вопрос: ")
        if user_input.lower() in ['exit', 'quit', 'выйти', 'выход']:
            break
            
        # Формируем запрос с учетом состояния ГГ
        prompt = f"Как главный герой '{main_character['name']}' должен отреагировать на это действие: '{user_input}'? Опиши развитие событий в мире '{selected_world['name']}'."
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(api.process_input(f"INPUT-1: {prompt}"))
        loop.close()
        
        print(response)

def main_loop():
    """Основной цикл приложения."""
    # Сначала запускаем стартовую процедуру для загрузки моделей
    print("Запуск стартовой процедуры загрузки моделей...")
    models_started = start_models_with_timeout()
    
    if not models_started:
        print("Не удалось запустить модели. Завершение программы.")
        return
    
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
                    # Запускаем симуляцию с чатом
                    chat_simulation(selected_world, main_character)
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
                                # Получаем информацию о созданном персонаже для симуляции
                                main_character = get_main_character_for_world(selected_world['id'], db_path=db_manager.db.db_path)
                                chat_simulation(selected_world, main_character)
                        except Exception as e:
                            print(f"Ошибка при создании персонажа: {e}")
                    else:
                        print("Возвращаемся в главное меню...")
        elif menu_choice == "2":
            edit_worlds_menu(db_manager)
        elif menu_choice == "3":
            print("Остановка всех моделей...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(api.stop_all())
            loop.close()
            
            print("Выход из игры.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main_loop()
