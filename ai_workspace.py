"""
API для управления сессиями ИИ моделей.

Этот модуль предоставляет интерфейс для запуска и взаимодействия с двумя моделями ИИ.
Он принимает команды и данные для обработки, а также возвращает результаты генерации.
Работает только с входом и выходом данных — не выполняет сторонние операции.

Поддерживаемые модели:
- Модель 1 (основная): тяжелая модель генерации повествования, запускается на первом графическом ускорителе.
- Модель 2 (легковесная): вторичная модель для вспомогательных задач, работает на CPU или втором графическом адаптере при наличии.

Функционал:
- Команда START-1 или START-2 запускает одну или две модели соответственно.
- После старта все входные сообщения должны начинаться с префикса INPUT-* (где * — номер модели).
- При запуске одной модели маршрутация игнорируется: весь поток идет через модель 1.
- Контекстное окно задается отдельно для каждой модели.
- Поддерживается динамическая маршрутизация запросов по модели.

Пример использования:
  - Вход: "START-2"
  - Вход: "INPUT-1: Привет, расскажи историю..."
  - Вход: "INPUT-2: Сократи этот текст: ..."
  - Выход: ответ от соответствующей модели.

Конфигурация контекстных окон и устройств должна быть задана в конфигурационном файле или в коде.

Для получения ответа сторонним модулем:
- Вызовите await api.process_input(message), где message — входное сообщение.
- Результат будет возвращён в переменной response.
"""

import asyncio
import logging
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIWorkspaceAPI:
    def __init__(self):
        self.models = {}
        self.context_windows = {
            1: 4096,  # Основная модель
            2: 1024   # Легковесная модель
        }
        self.device_mapping = {
            1: "cuda:0",  # Первый графический ускоритель
            2: "cuda:1"   # Второй графический ускоритель или "cpu"
        }

    async def start_models(self, count: int) -> bool:
        """Запускает указанное количество моделей."""
        if count not in [1, 2]:
            logger.error("Недопустимое количество моделей. Допустимо: 1 или 2.")
            return False

        for model_id in range(1, count + 1):
            try:
                # Имитация загрузки модели
                self.models[model_id] = f"Model_{model_id}_loaded_on_{self.device_mapping[model_id]}"
                logger.info(f"Модель {model_id} запущена на {self.device_mapping[model_id]}")
            except Exception as e:
                logger.error(f"Ошибка запуска модели {model_id}: {e}")
                return False

        logger.info(f"Успешно запущены {count} модели(ей)")
        return True

    async def process_input(self, message: str) -> str:
        """Обрабатывает входное сообщение с маршрутизацией по модели."""
        if not message.startswith("INPUT-"):
            return "Ошибка: сообщение должно начинаться с INPUT-*"

        parts = message.split(":", 1)
        if len(parts) < 2:
            return "Ошибка: неверный формат сообщения"

        model_id_str = parts[0][5:]  # извлекаем число после INPUT-
        try:
            model_id = int(model_id_str)
        except ValueError:
            return "Ошибка: неверный номер модели"

        if model_id not in self.models:
            return f"Ошибка: модель {model_id} не запущена"

        # Если запущена только одна модель — все идет через неё
        if len(self.models) == 1 and 1 in self.models:
            model_id = 1

        # Имитация генерации
        response = f"Ответ от модели {model_id}: {parts[1].strip()[:50]}... (генерация завершена)"
        return response

    async def stop_all(self):
        """Останавливает все модели."""
        for model_id in self.models:
            logger.info(f"Модель {model_id} остановлена")
        self.models.clear()
        logger.info("Все модели остановлены")


# Глобальный экземпляр API
api = AIWorkspaceAPI()

# Асинхронная точка входа
async def main():
    print("AI Workspace API запущен. Ожидаю команды...")
    while True:
        try:
            command = input("Введите команду (например, 'START-2' или 'INPUT-1: ...'): ").strip()
            if command.startswith("START-"):
                _, count_str = command.split("-", 1)
                try:
                    count = int(count_str)
                    success = await api.start_models(count)
                    if not success:
                        print("Не удалось запустить модели.")
                except ValueError:
                    print("Неверный формат команды. Используйте: START-1 или START-2")
            elif command.startswith("INPUT-"):
                result = await api.process_input(command)
                print(result)
            else:
                print("Неизвестная команда. Доступны: START-1, START-2, INPUT-*")
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
            await api.stop_all()
            break


if __name__ == "__main__":
    asyncio.run(main())
