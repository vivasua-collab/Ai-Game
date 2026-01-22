from typing import Dict, List, Optional
import json
from repositories import GameWorldManager
from models import *
import random


class LocalModelGameMaster:
    """Локальный ИИ-мастер игры, эмулирующий поведение ИИ для автономной работы игры"""
    
    def __init__(self, model_name: str = "local-llm-emulator"):
        """
        Инициализация локального ИИ-мастера
        
        Args:
            model_name: Название модели (для совместимости с будущей ИИ-реализацией)
        """
        self.model_name = model_name
        self.world_manager = GameWorldManager("game.db")  # Указываем тот же файл базы данных, что и DatabaseManager
        self.conversation_history = {}
        print(f"Локальный ИИ-мастер инициализирован с моделью: {model_name}")
    
    def generate_response(self, world_id: int, player_input: str, character_id: int = None) -> str:
        """
        Генерация ответа от ИИ-мастера на основе текущего состояния мира и ввода игрока
        
        Args:
            world_id: ID игрового мира
            player_input: Ввод игрока
            character_id: ID персонажа игрока (если применимо)
            
        Returns:
            Текст ответа от ИИ-мастера
        """
        # Получаем контекст мира
        world_context = self.world_manager.get_world_context(world_id)
        
        if not world_context:
            return "Мир не найден. Пожалуйста, выберите существующий игровой мир."
        
        # Эмуляция обработки запроса игрока
        response = self._simulate_ai_response(world_context, player_input, character_id)
        
        # Сохраняем в историю
        if world_id not in self.conversation_history:
            self.conversation_history[world_id] = []
        
        self.conversation_history[world_id].append({
            "player_input": player_input,
            "ai_response": response,
            "timestamp": len(self.conversation_history[world_id])
        })
        
        return response
    
    def _simulate_ai_response(self, world_context: Dict, player_input: str, character_id: int = None) -> str:
        """
        Симуляция ИИ-ответа на основе контекста мира и ввода игрока
        
        Args:
            world_context: Контекст игрового мира
            player_input: Ввод игрока
            character_id: ID персонажа игрока
            
        Returns:
            Сгенерированный ответ
        """
        # Простая логика для симуляции ИИ-ответа
        world_name = world_context['world']['name']
        
        # Определяем тип действия игрока
        player_input_lower = player_input.lower()
        
        if any(word in player_input_lower for word in ['привет', 'здравствуй', 'здравствуйте', 'hello']):
            return f"Приветствуем вас в мире '{world_name}'! Что бы вы хотели сделать?"
        
        elif any(word in player_input_lower for word in ['осмотреться', 'смотреть', 'вокруг', 'окрестности', 'look']):
            # Описание окружения на основе персонажей в мире
            characters = world_context.get('characters', [])
            if characters:
                char_names = [char['name'] for char in characters[:3]]  # Только первые 3 персонажа
                return f"Вы осматриваетесь в мире '{world_name}'. Видите: {', '.join(char_names)}."
            else:
                return f"Вы находитесь в пустом пространстве мира '{world_name}'."
        
        elif any(word in player_input_lower for word in ['переместиться', 'идти', 'двигаться', 'move', 'go']):
            return f"Вы перемещаетесь по миру '{world_name}'. Куда именно вы хотите идти?"
        
        elif any(word in player_input_lower for word in ['инвентарь', 'вещи', 'предметы', 'inventory']):
            # Показываем инвентарь персонажа, если известен
            if character_id and character_id in world_context.get('inventories', {}):
                inventory = world_context['inventories'][character_id]
                if inventory:
                    items = [inv.get('item_name', 'неизвестный предмет') for inv in inventory]
                    return f"Ваш инвентарь: {', '.join(items)}"
                else:
                    return "Ваш инвентарь пуст."
            else:
                return "Инвентарь недоступен."
        
        else:
            # Общий случай - генерируем общий ответ
            actions = [
                f"В мире '{world_name}' происходит что-то интересное.",
                f"Вы чувствуете атмосферу мира '{world_name}'.",
                f"Что-то привлекает ваше внимание в '{world_name}'.",
                f"Воздух в '{world_name}' наполнен загадками.",
                f"Ваши действия в '{world_name}' имеют последствия."
            ]
            
            return random.choice(actions)
    
    def update_world_state(self, world_id: int, action_result: Dict) -> bool:
        """
        Обновление состояния мира на основе действий игрока
        
        Args:
            world_id: ID игрового мира
            action_result: Результат действия игрока
            
        Returns:
            Успешность обновления
        """
        try:
            # В реальной реализации здесь будет логика обновления мира
            # на основе действий игрока с использованием ИИ
            print(f"Состояние мира {world_id} обновлено: {action_result}")
            return True
        except Exception as e:
            print(f"Ошибка обновления мира: {e}")
            return False
    
    def get_world_status(self, world_id: int) -> Dict:
        """
        Получение текущего статуса мира
        
        Args:
            world_id: ID игрового мира
            
        Returns:
            Статус мира
        """
        world_context = self.world_manager.get_world_context(world_id)
        
        if not world_context:
            return {"error": "Мир не найден"}
        
        return {
            "world_info": world_context['world'],
            "character_count": len(world_context.get('characters', [])),
            "active_relations": len(world_context.get('relationships', [])),
            "has_inventory": bool(world_context.get('inventories'))
        }