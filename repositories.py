from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
from models import *
from database import GameDatabase

class WorldRepository:
    """Репозиторий для работы с мирами"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
    
    def create_world(self, world: World) -> int:
        """Создать новый мир"""
        query = """
        INSERT INTO Worlds (name, theme, is_active, settings_json)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            world.name, world.theme, world.is_active, world.settings_json
        ))
        world.world_id = self.db.get_last_insert_id()
        return world.world_id
    
    def get_world(self, world_id: int) -> Optional[World]:
        """Получить мир по ID"""
        query = "SELECT * FROM Worlds WHERE world_id = ?"
        row = self.db.fetch_one(query, (world_id,))
        
        if row:
            return self._row_to_world(row)
        return None
    
    def get_all_worlds(self) -> List[World]:
        """Получить все миры"""
        query = "SELECT * FROM Worlds ORDER BY created_at DESC"
        rows = self.db.fetch_all(query)
        return [self._row_to_world(row) for row in rows]
    
    def update_world(self, world: World) -> bool:
        """Обновить мир"""
        query = """
        UPDATE Worlds 
        SET name = ?, theme = ?, is_active = ?, settings_json = ?
        WHERE world_id = ?
        """
        self.db.execute_query(query, (
            world.name, world.theme, world.is_active, 
            world.settings_json, world.world_id
        ))
        return True
    
    def delete_world(self, world_id: int) -> bool:
        """Удалить мир и все связанные данные (каскадное удаление)"""
        query = "DELETE FROM Worlds WHERE world_id = ?"
        self.db.execute_query(query, (world_id,))
        return True
    
    def activate_world(self, world_id: int):
        """Активировать мир"""
        query = "UPDATE Worlds SET is_active = 1 WHERE world_id = ?"
        self.db.execute_query(query, (world_id,))
    
    def deactivate_world(self, world_id: int):
        """Деактивировать мир"""
        query = "UPDATE Worlds SET is_active = 0 WHERE world_id = ?"
        self.db.execute_query(query, (world_id,))
    
    def _row_to_world(self, row: sqlite3.Row) -> World:
        """Конвертировать строку БД в объект World"""
        return World(
            world_id=row['world_id'],
            name=row['name'],
            theme=row['theme'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            is_active=bool(row['is_active']),
            settings_json=row['settings_json']
        )


class CharacterRepository:
    """Репозиторий для работы с персонажами"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
    
    def create_character(self, character: Character) -> int:
        """Создать персонажа"""
        query = """
        INSERT INTO Characters 
        (world_id, name, type, species, skills_json, location_x, location_y, 
         current_health, max_health, state_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            character.world_id, character.name, character.type, 
            character.species, character.skills_json,
            character.location_x, character.location_y,
            character.current_health, character.max_health,
            character.state_json
        ))
        character.character_id = self.db.get_last_insert_id()
        return character.character_id
    
    def get_character(self, character_id: int) -> Optional[Character]:
        """Получить персонажа по ID"""
        query = "SELECT * FROM Characters WHERE character_id = ?"
        row = self.db.fetch_one(query, (character_id,))
        
        if row:
            return self._row_to_character(row)
        return None
    
    def get_world_characters(self, world_id: int) -> List[Character]:
        """Получить всех персонажей мира"""
        query = "SELECT * FROM Characters WHERE world_id = ? ORDER BY name"
        rows = self.db.fetch_all(query, (world_id,))
        return [self._row_to_character(row) for row in rows]
    
    def get_characters_by_world_and_type(self, world_id: int, char_type: str) -> List[Character]:
        """Получить персонажей определенного типа в мире"""
        query = "SELECT * FROM Characters WHERE world_id = ? AND type = ? ORDER BY name"
        rows = self.db.fetch_all(query, (world_id, char_type))
        return [self._row_to_character(row) for row in rows]
    
    def get_characters_at_location(self, world_id: int, x: float, y: float, radius: float = 1.0) -> List[Character]:
        """Получить персонажей в радиусе от точки"""
        query = """
        SELECT * FROM Characters 
        WHERE world_id = ? 
        AND (location_x BETWEEN ? AND ?)
        AND (location_y BETWEEN ? AND ?)
        """
        rows = self.db.fetch_all(query, (
            world_id, x - radius, x + radius, y - radius, y + radius
        ))
        return [self._row_to_character(row) for row in rows]
    
    def update_character(self, character: Character) -> bool:
        """Обновить персонажа"""
        query = """
        UPDATE Characters 
        SET name = ?, type = ?, species = ?, skills_json = ?,
            location_x = ?, location_y = ?, current_health = ?,
            max_health = ?, state_json = ?
        WHERE character_id = ?
        """
        self.db.execute_query(query, (
            character.name, character.type, character.species,
            character.skills_json, character.location_x,
            character.location_y, character.current_health,
            character.max_health, character.state_json,
            character.character_id
        ))
        return True
    
    def move_character(self, character_id: int, x: float, y: float) -> bool:
        """Переместить персонажа"""
        query = """
        UPDATE Characters 
        SET location_x = ?, location_y = ?
        WHERE character_id = ?
        """
        self.db.execute_query(query, (x, y, character_id))
        return True
    
    def damage_character(self, character_id: int, damage: float) -> Optional[Character]:
        """Нанести урон персонажу"""
        character = self.get_character(character_id)
        if character:
            character.current_health = max(0, character.current_health - damage)
            self.update_character(character)
            return character
        return None
    
    def _row_to_character(self, row: sqlite3.Row) -> Character:
        """Конвертировать строку БД в объект Character"""
        return Character(
            character_id=row['character_id'],
            world_id=row['world_id'],
            name=row['name'],
            type=row['type'],
            species=row['species'],
            skills_json=row['skills_json'],
            location_x=row['location_x'],
            location_y=row['location_y'],
            current_health=row['current_health'],
            max_health=row['max_health'],
            state_json=row['state_json']
        )


class WorldConstantRepository:
    """Репозиторий для работы с мировыми константами"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
    
    def set_constant(self, constant: WorldConstant) -> int:
        """Установить или обновить константу"""
        # Проверяем, существует ли уже такая константа
        existing = self.get_constant(constant.world_id, constant.constant_key)
        
        if existing:
            # Обновляем существующую
            query = """
            UPDATE WorldConstants 
            SET constant_value = ?, data_type = ?, description = ?
            WHERE world_id = ? AND constant_key = ?
            """
            self.db.execute_query(query, (
                constant.constant_value, constant.data_type,
                constant.description, constant.world_id,
                constant.constant_key
            ))
            return existing.constant_id
        else:
            # Создаем новую
            query = """
            INSERT INTO WorldConstants 
            (world_id, constant_key, constant_value, data_type, description)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_query(query, (
                constant.world_id, constant.constant_key,
                constant.constant_value, constant.data_type,
                constant.description
            ))
            constant.constant_id = self.db.get_last_insert_id()
            return constant.constant_id
    
    def get_constant(self, world_id: int, key: str) -> Optional[WorldConstant]:
        """Получить константу по ключу"""
        query = """
        SELECT * FROM WorldConstants 
        WHERE world_id = ? AND constant_key = ?
        """
        row = self.db.fetch_one(query, (world_id, key))
        
        if row:
            return self._row_to_constant(row)
        return None
    
    def get_world_constants(self, world_id: int) -> Dict[str, Any]:
        """Получить все константы мира как словарь с правильными типами"""
        query = "SELECT * FROM WorldConstants WHERE world_id = ?"
        rows = self.db.fetch_all(query, (world_id,))
        
        constants = {}
        for row in rows:
            constant = self._row_to_constant(row)
            constants[constant.constant_key] = constant.get_typed_value()
        
        return constants
    
    def _row_to_constant(self, row: sqlite3.Row) -> WorldConstant:
        """Конвертировать строку БД в объект WorldConstant"""
        return WorldConstant(
            constant_id=row['constant_id'],
            world_id=row['world_id'],
            constant_key=row['constant_key'],
            constant_value=row['constant_value'],
            data_type=row['data_type'],
            description=row['description']
        )


class RelationshipRepository:
    """Репозиторий для работы с отношениями"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
    
    def create_relationship(self, relationship: Relationship) -> int:
        """Создать отношение между персонажами"""
        query = """
        INSERT INTO Relationships 
        (world_id, character_a_id, character_b_id, relationship_type, 
         score, history_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            relationship.world_id, relationship.character_a_id,
            relationship.character_b_id, relationship.relationship_type,
            relationship.score, relationship.history_json
        ))
        relationship.relationship_id = self.db.get_last_insert_id()
        return relationship.relationship_id
    
    def get_relationship(self, world_id: int, char_a_id: int, char_b_id: int, 
                        rel_type: str = None) -> Optional[Relationship]:
        """Получить отношение между персонажами"""
        if rel_type:
            query = """
            SELECT * FROM Relationships 
            WHERE world_id = ? AND character_a_id = ? 
            AND character_b_id = ? AND relationship_type = ?
            """
            params = (world_id, char_a_id, char_b_id, rel_type)
        else:
            query = """
            SELECT * FROM Relationships 
            WHERE world_id = ? AND character_a_id = ? 
            AND character_b_id = ?
            """
            params = (world_id, char_a_id, char_b_id)
        
        row = self.db.fetch_one(query, params)
        if row:
            return self._row_to_relationship(row)
        return None
    
    def update_relationship_score(self, relationship_id: int, delta: float):
        """Изменить оценку отношения"""
        query = """
        UPDATE Relationships 
        SET score = score + ?, last_updated = CURRENT_TIMESTAMP
        WHERE relationship_id = ?
        """
        self.db.execute_query(query, (delta, relationship_id))
    
    def add_interaction(self, relationship_id: int, interaction: Dict):
        """Добавить взаимодействие в историю отношения"""
        # Получаем текущее отношение
        query = "SELECT * FROM Relationships WHERE relationship_id = ?"
        row = self.db.fetch_one(query, (relationship_id,))
        
        if row:
            relationship = self._row_to_relationship(row)
            relationship.add_interaction(interaction)
            
            # Обновляем в БД
            update_query = """
            UPDATE Relationships 
            SET history_json = ?, last_updated = CURRENT_TIMESTAMP
            WHERE relationship_id = ?
            """
            self.db.execute_query(update_query, (
                relationship.history_json, relationship_id
            ))
    
    def get_character_relationships(self, character_id: int) -> List[Relationship]:
        """Получить все отношения персонажа"""
        query = """
        SELECT * FROM Relationships 
        WHERE character_a_id = ? OR character_b_id = ?
        ORDER BY last_updated DESC
        """
        rows = self.db.fetch_all(query, (character_id, character_id))
        return [self._row_to_relationship(row) for row in rows]
    
    def _row_to_relationship(self, row: sqlite3.Row) -> Relationship:
        """Конвертировать строку БД в объект Relationship"""
        return Relationship(
            relationship_id=row['relationship_id'],
            world_id=row['world_id'],
            character_a_id=row['character_a_id'],
            character_b_id=row['character_b_id'],
            relationship_type=row['relationship_type'],
            score=row['score'],
            history_json=row['history_json'],
            last_updated=datetime.fromisoformat(row['last_updated']) if row['last_updated'] else None
        )


class InventoryRepository:
    """Репозиторий для работы с инвентарем"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.item_repo = ItemRepository(db)
    
    def add_to_inventory(self, inventory: Inventory) -> int:
        """Добавить предмет в инвентарь"""
        query = """
        INSERT INTO Inventory 
        (character_id, item_instance_id, quantity, condition, custom_properties_json)
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            inventory.character_id, inventory.item_instance_id,
            inventory.quantity, inventory.condition,
            inventory.custom_properties_json
        ))
        inventory.inventory_id = self.db.get_last_insert_id()
        return inventory.inventory_id
    
    def get_character_inventory(self, character_id: int) -> List[Inventory]:
        """Получить инвентарь персонажа"""
        query = """
        SELECT i.*, ii.custom_name, it.name as item_name
        FROM Inventory i
        JOIN ItemInstances ii ON i.item_instance_id = ii.instance_id
        JOIN Items it ON ii.item_id = it.item_id
        WHERE i.character_id = ?
        ORDER BY it.name
        """
        rows = self.db.fetch_all(query, (character_id,))
        
        inventories = []
        for row in rows:
            inv = Inventory(
                inventory_id=row['inventory_id'],
                character_id=row['character_id'],
                item_instance_id=row['item_instance_id'],
                quantity=row['quantity'],
                condition=row['condition'],
                custom_properties_json=row['custom_properties_json']
            )
            # Добавляем дополнительную информацию
            inv.item_name = row['item_name']
            inv.custom_name = row['custom_name']
            inventories.append(inv)
        
        return inventories
    
    def remove_from_inventory(self, inventory_id: int) -> bool:
        """Удалить предмет из инвентаря"""
        query = "DELETE FROM Inventory WHERE inventory_id = ?"
        self.db.execute_query(query, (inventory_id,))
        return True
    
    def update_quantity(self, inventory_id: int, quantity: int):
        """Изменить количество предметов"""
        query = "UPDATE Inventory SET quantity = ? WHERE inventory_id = ?"
        self.db.execute_query(query, (quantity, inventory_id))


class ItemRepository:
    """Репозиторий для работы с предметами"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
    
    def create_item(self, item: Item) -> int:
        """Создать шаблон предмета"""
        query = """
        INSERT INTO Items 
        (world_id, name, description, type, base_properties_json, is_unique)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            item.world_id, item.name, item.description,
            item.type, item.base_properties_json, item.is_unique
        ))
        item.item_id = self.db.get_last_insert_id()
        return item.item_id
    
    def create_item_instance(self, instance: ItemInstance) -> int:
        """Создать экземпляр предмета"""
        query = """
        INSERT INTO ItemInstances 
        (world_id, item_id, custom_name, current_properties_json)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_query(query, (
            instance.world_id, instance.item_id,
            instance.custom_name, instance.current_properties_json
        ))
        instance.instance_id = self.db.get_last_insert_id()
        return instance.instance_id


class GameWorldManager:
    """Главный менеджер для работы со всеми компонентами мира"""
    
    def __init__(self, db_path: str = "game_world.db"):
        self.db = GameDatabase(db_path)
        self.worlds = WorldRepository(self.db)
        self.characters = CharacterRepository(self.db)
        self.constants = WorldConstantRepository(self.db)
        self.relationships = RelationshipRepository(self.db)
        self.inventory = InventoryRepository(self.db)
        self.items = ItemRepository(self.db)
    
    def get_world_context(self, world_id: int) -> Dict:
        """Получить полный контекст мира для ИИ-ГМ"""
        world = self.worlds.get_world(world_id)
        if not world:
            return None
        
        world_chars = self.characters.get_world_characters(world_id)
        world_constants = self.constants.get_world_constants(world_id)
        
        # Собираем отношения между персонажами
        relationships = []
        for char in world_chars:
            char_rels = self.relationships.get_character_relationships(char.character_id)
            relationships.extend(char_rels)
        
        # Собираем инвентари
        inventories = {}
        for char in world_chars:
            char_inv = self.inventory.get_character_inventory(char.character_id)
            if char_inv:
                inventories[char.character_id] = char_inv
        
        return {
            'world': world.to_dict(),
            'constants': world_constants,
            'characters': [char.__dict__ for char in world_chars],
            'relationships': [rel.__dict__ for rel in relationships],
            'inventories': {
                char_id: [inv.__dict__ for inv in inv_list]
                for char_id, inv_list in inventories.items()
            }
        }
    
    def save_world_state(self, world_id: int, state_data: Dict):
        """Сохранить состояние мира (для резервных копий)"""
        # Здесь можно реализовать сохранение снапшота состояния
        pass