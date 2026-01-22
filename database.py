import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

class GameDatabase:
    """Основной класс для работы с базой данных игрового мира"""
    
    def __init__(self, db_path: str = "game_world.db"):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> sqlite3.Connection:
        """Установить соединение с базой данных"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # Для многопоточности
            )
            self.connection.row_factory = sqlite3.Row  # Для доступа по именам колонок
            # Включаем поддержку внешних ключей
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Включаем журналирование WAL для лучшей производительности
            self.connection.execute("PRAGMA journal_mode = WAL")
        
        return self.connection
    
    def disconnect(self):
        """Закрыть соединение с базой данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Выполнить SQL-запрос
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Курсор с результатами
        """
        conn = self.connect()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]):
        """
        Выполнить один запрос с несколькими наборами параметров
        
        Args:
            query: SQL-запрос
            params_list: Список кортежей с параметрами
        """
        conn = self.connect()
        try:
            conn.executemany(query, params_list)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            self.logger.error(f"Ошибка выполнения массового запроса: {e}")
            raise
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Получить одну запись
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Одна запись или None
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Получить все записи
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Список записей
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def get_last_insert_id(self) -> int:
        """Получить ID последней вставленной записи"""
        cursor = self.execute_query("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    
    def transaction(self):
        """Контекстный менеджер для транзакции"""
        return TransactionContext(self)
    
    def __enter__(self):
        """Контекстный менеджер для соединения"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие соединения при выходе из контекста"""
        self.disconnect()


class TransactionContext:
    """Контекстный менеджер для транзакций"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.conn = db.connect()
    
    def __enter__(self):
        self.conn.execute("BEGIN TRANSACTION")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
            self.db.logger.error(f"Транзакция отменена: {exc_val}")
        else:
            self.conn.commit()


class DatabaseManager:
    """Класс для управления базой данных игровых миров (совместимость с main.py)"""
    
    def __init__(self, db_path: str = "game_world.db"):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db = GameDatabase(db_path)
        
        # Используем инициализацию из init_database для полной совместимости
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Инициализация таблиц базы данных"""
        from init_database import initialize_database
        initialize_database(self.db.db_path)
    
    def get_all_worlds(self):
        """Получить список всех миров"""
        query = "SELECT world_id as id, name FROM Worlds ORDER BY world_id"
        rows = self.db.fetch_all(query)
        
        worlds = []
        for row in rows:
            worlds.append({
                "id": row["id"],
                "name": row["name"]
            })
        
        return worlds
    
    def create_world(self, name: str):
        """Создать новый мир
        
        Args:
            name: Название мира
            
        Returns:
            ID созданного мира
        """
        query = "INSERT INTO Worlds (name, theme) VALUES (?, ?)"
        self.db.execute_query(query, (name, "Default Theme"))
        return self.db.get_last_insert_id()
    
    def delete_world(self, world_id: int):
        """Удалить мир по ID
        
        Args:
            world_id: ID мира для удаления
        """
        query = "DELETE FROM Worlds WHERE world_id = ?"
        self.db.execute_query(query, (world_id,))