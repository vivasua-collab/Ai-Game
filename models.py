import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any

@dataclass
class World:
    """Модель игрового мира"""
    world_id: int = None
    name: str = ""
    theme: str = ""
    created_at: datetime = None
    is_active: bool = True
    settings_json: str = "{}"
    
    @property
    def settings(self) -> Dict:
        """Получить настройки как словарь"""
        return json.loads(self.settings_json) if self.settings_json else {}
    
    @settings.setter
    def settings(self, value: Dict):
        """Установить настройки из словаря"""
        self.settings_json = json.dumps(value, ensure_ascii=False)
    
    def to_dict(self) -> Dict:
        """Конвертировать в словарь (для JSON)"""
        data = asdict(self)
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        return data

@dataclass
class WorldConstant:
    """Модель мировой константы"""
    constant_id: int = None
    world_id: int = None
    constant_key: str = ""
    constant_value: str = ""
    data_type: str = "TEXT"
    description: str = ""
    
    def get_typed_value(self):
        """Получить значение с правильным типом"""
        if self.data_type == "INTEGER":
            return int(self.constant_value)
        elif self.data_type == "REAL":
            return float(self.constant_value)
        elif self.data_type == "BOOLEAN":
            return self.constant_value.lower() == "true"
        else:
            return self.constant_value

@dataclass
class Character:
    """Модель персонажа"""
    character_id: int = None
    world_id: int = None
    name: str = ""
    type: str = "npc"  # player, npc, companion, enemy
    species: str = ""
    skills_json: str = "{}"
    location_x: float = 0.0
    location_y: float = 0.0
    current_health: float = 100.0
    max_health: float = 100.0
    state_json: str = "{}"
    
    @property
    def skills(self) -> Dict:
        return json.loads(self.skills_json) if self.skills_json else {}
    
    @skills.setter
    def skills(self, value: Dict):
        self.skills_json = json.dumps(value, ensure_ascii=False)
    
    @property
    def state(self) -> Dict:
        return json.loads(self.state_json) if self.state_json else {}
    
    @state.setter
    def state(self, value: Dict):
        self.state_json = json.dumps(value, ensure_ascii=False)
    
    def get_location(self) -> tuple:
        return (self.location_x, self.location_y)
    
    def set_location(self, x: float, y: float):
        self.location_x = x
        self.location_y = y

@dataclass
class Relationship:
    """Модель отношений между персонажами"""
    relationship_id: int = None
    world_id: int = None
    character_a_id: int = None
    character_b_id: int = None
    relationship_type: str = ""  # friendship, rivalry, love, hatred, allegiance
    score: float = 0.0
    history_json: str = "[]"
    last_updated: datetime = None
    
    @property
    def history(self) -> List:
        return json.loads(self.history_json) if self.history_json else []
    
    @history.setter
    def history(self, value: List):
        self.history_json = json.dumps(value, ensure_ascii=False)
    
    def add_interaction(self, interaction: Dict):
        """Добавить взаимодействие в историю"""
        history = self.history
        interaction['timestamp'] = datetime.now().isoformat()
        history.append(interaction)
        # Ограничим историю последними 50 событиями
        if len(history) > 50:
            history = history[-50:]
        self.history = history
        self.last_updated = datetime.now()

@dataclass
class Item:
    """Модель предмета (шаблон)"""
    item_id: int = None
    world_id: int = None
    name: str = ""
    description: str = ""
    type: str = ""  # weapon, potion, key, resource
    base_properties_json: str = "{}"
    is_unique: bool = False
    
    @property
    def base_properties(self) -> Dict:
        return json.loads(self.base_properties_json) if self.base_properties_json else {}
    
    @base_properties.setter
    def base_properties(self, value: Dict):
        self.base_properties_json = json.dumps(value, ensure_ascii=False)

@dataclass
class ItemInstance:
    """Модель экземпляра предмета"""
    instance_id: int = None
    world_id: int = None
    item_id: int = None
    created_at: datetime = None
    custom_name: str = ""
    current_properties_json: str = "{}"
    
    @property
    def current_properties(self) -> Dict:
        return json.loads(self.current_properties_json) if self.current_properties_json else {}
    
    @current_properties.setter
    def current_properties(self, value: Dict):
        self.current_properties_json = json.dumps(value, ensure_ascii=False)

@dataclass
class Inventory:
    """Модель записи инвентаря персонажа"""
    inventory_id: int = None
    character_id: int = None
    item_instance_id: int = None
    quantity: int = 1
    condition: float = 100.0
    custom_properties_json: str = "{}"
    
    @property
    def custom_properties(self) -> Dict:
        return json.loads(self.custom_properties_json) if self.custom_properties_json else {}
    
    @custom_properties.setter
    def custom_properties(self, value: Dict):
        self.custom_properties_json = json.dumps(value, ensure_ascii=False)

@dataclass
class Vehicle:
    """Модель транспорта"""
    vehicle_id: int = None
    world_id: int = None
    owner_id: Optional[int] = None
    type: str = ""  # mechanical, biological, magical
    name: str = ""
    components_json: str = "{}"
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    capacity: int = 1
    current_health: Optional[float] = None
    max_health: Optional[float] = None
    
    @property
    def components(self) -> Dict:
        return json.loads(self.components_json) if self.components_json else {}
    
    @components.setter
    def components(self, value: Dict):
        self.components_json = json.dumps(value, ensure_ascii=False)
    
    def get_location(self) -> Optional[tuple]:
        if self.location_x is not None and self.location_y is not None:
            return (self.location_x, self.location_y)
        return None
    
    def set_location(self, x: float, y: float):
        self.location_x = x
        self.location_y = y

@dataclass
class VehicleInventory:
    """Модель инвентаря транспорта"""
    vehicle_inv_id: int = None
    vehicle_id: int = None
    item_instance_id: int = None
    quantity: int = 1
    slot: Optional[str] = None