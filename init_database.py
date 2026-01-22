from database import GameDatabase

def initialize_database(db_path: str = "game_world.db"):
    """Инициализировать базу данных и создать все таблицы"""
    
    create_tables_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS Worlds (
        world_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        theme TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        settings_json TEXT DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS WorldConstants (
        constant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        constant_key TEXT NOT NULL,
        constant_value TEXT NOT NULL,
        data_type TEXT CHECK(data_type IN ('INTEGER', 'REAL', 'TEXT', 'BOOLEAN')),
        description TEXT,
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE,
        UNIQUE(world_id, constant_key)
    );

    CREATE TABLE IF NOT EXISTS Characters (
        character_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT CHECK(type IN ('player', 'npc', 'companion', 'enemy')),
        species TEXT,
        skills_json TEXT DEFAULT '{}',
        location_x REAL DEFAULT 0.0,
        location_y REAL DEFAULT 0.0,
        current_health REAL DEFAULT 100.0,
        max_health REAL DEFAULT 100.0,
        state_json TEXT DEFAULT '{}',
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Relationships (
        relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        character_a_id INTEGER NOT NULL,
        character_b_id INTEGER NOT NULL,
        relationship_type TEXT CHECK(relationship_type IN ('friendship', 'rivalry', 'love', 'hatred', 'allegiance')),
        score REAL DEFAULT 0.0,
        history_json TEXT DEFAULT '[]',
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE,
        FOREIGN KEY (character_a_id) REFERENCES Characters(character_id) ON DELETE CASCADE,
        FOREIGN KEY (character_b_id) REFERENCES Characters(character_id) ON DELETE CASCADE,
        CHECK(character_a_id != character_b_id),
        UNIQUE(world_id, character_a_id, character_b_id, relationship_type)
    );

    CREATE TABLE IF NOT EXISTS Items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT,
        base_properties_json TEXT DEFAULT '{}',
        is_unique BOOLEAN DEFAULT 0,
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ItemInstances (
        instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        custom_name TEXT,
        current_properties_json TEXT DEFAULT '{}',
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id INTEGER NOT NULL,
        item_instance_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        condition REAL DEFAULT 100.0,
        custom_properties_json TEXT DEFAULT '{}',
        FOREIGN KEY (character_id) REFERENCES Characters(character_id) ON DELETE CASCADE,
        FOREIGN KEY (item_instance_id) REFERENCES ItemInstances(instance_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Vehicles (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        world_id INTEGER NOT NULL,
        owner_id INTEGER,
        type TEXT CHECK(type IN ('mechanical', 'biological', 'magical')),
        name TEXT NOT NULL,
        components_json TEXT DEFAULT '{}',
        location_x REAL,
        location_y REAL,
        capacity INTEGER DEFAULT 1,
        current_health REAL,
        max_health REAL,
        FOREIGN KEY (world_id) REFERENCES Worlds(world_id) ON DELETE CASCADE,
        FOREIGN KEY (owner_id) REFERENCES Characters(character_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS VehicleInventory (
        vehicle_inv_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        item_instance_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        slot TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES Vehicles(vehicle_id) ON DELETE CASCADE,
        FOREIGN KEY (item_instance_id) REFERENCES ItemInstances(instance_id) ON DELETE CASCADE
    );

    -- Создаем индексы для ускорения часто используемых запросов
    CREATE INDEX IF NOT EXISTS idx_characters_world ON Characters(world_id);
    CREATE INDEX IF NOT EXISTS idx_characters_location ON Characters(world_id, location_x, location_y);
    CREATE INDEX IF NOT EXISTS idx_relationships_chars ON Relationships(character_a_id, character_b_id);
    CREATE INDEX IF NOT EXISTS idx_inventory_character ON Inventory(character_id);
    CREATE INDEX IF NOT EXISTS idx_items_world ON Items(world_id);
    """
    
    db = GameDatabase(db_path)
    
    try:
        # Разделяем SQL на отдельные команды
        commands = create_tables_sql.split(';')
        
        with db.transaction():
            for command in commands:
                command = command.strip()
                if command:
                    db.execute_query(command)
        
        print(f"База данных успешно инициализирована: {db_path}")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    initialize_database("game_world.db")