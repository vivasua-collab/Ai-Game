"""
Модуль ИИ API для текстовой RPG игры

ОПИСАНИЕ:
Этот модуль предоставляет API для работы с различными нейросетями, 
используемыми в качестве гейммастера в текстовой RPG игре. 
Модуль загружает выбранную нейросеть в память и держит её активной, 
принимает текстовые промпты от пользователей и возвращает сгенерированные ответы. 
Поддерживается работа с локальными и облачными ИИ сервисами через единый интерфейс.

НЕОБХОДИМЫЕ ЗАВИСИМОСТИ:
- torch>=1.9.0
- transformers>=4.21.0
- accelerate>=0.12.0
- numpy>=1.21.0
- requests>=2.25.0 (для API вызовов)

Установка зависимостей:
pip install torch transformers accelerate numpy requests

ФУНКЦИИ МОДУЛЯ:
- AI_API_Module.__init__(model_name, **kwargs) - инициализация модуля с указанием модели
- AI_API_Module.process_request(prompt, **options) - обработка текстового запроса
- AI_API_Module.clear_context() - очистка истории контекста
- AI_API_Module.restart_model(new_model_name) - перезапуск модели (смена модели)
- AI_API_Module.get_result(request_id) - получение результата асинхронного запроса
- AI_API_Module.set_temperature(temp_value) - установка температуры генерации
- AI_API_Module.set_max_tokens(max_tokens) - установка максимального количества токенов
- AI_API_Module.load_model(model_name) - загрузка новой модели
- AI_API_Module.unload_model() - выгрузка модели из памяти

КАК ПОЛЬЗОВАТЬСЯ:
1. Создайте экземпляр класса AI_API_Module, указав название модели:
   ai_module = AI_API_Module(model_name="gpt2")

2. Обработайте текстовый запрос:
   response = ai_module.process_request("Привет, расскажи анекдот!")

3. Для асинхронной обработки используйте request_id:
   ai_module.process_request("Как дела?", request_id="req_1")
   result = ai_module.get_result("req_1")

4. Управляйте контекстом:
   ai_module.clear_context()  # Очистить историю
   ai_module.restart_model("microsoft/DialoGPT-medium")  # Сменить модель

ПЕРЕМЕННЫЕ ОГРАНИЧЕНИЙ:
- MAX_CONTEXT_LENGTH - максимальная длина контекста (по умолчанию 2048 токенов)
- DEFAULT_MAX_TOKENS - максимальное количество токенов в ответе (по умолчанию 512)
- DEFAULT_TEMPERATURE - температура генерации (по умолчанию 0.7)
- DEFAULT_TOP_P - параметр top_p для nucleus sampling (по умолчанию 0.9)
- MEMORY_LIMIT - лимит оперативной памяти для модели (в GB)
- BATCH_SIZE - размер батча для обработки запросов (по умолчанию 1)

ПОДДЕРЖИВАЕМЫЕ НЕЙРОСЕТИ:
- Hugging Face Transformers модели (например, GPT-2, GPT-J, OPT, BLOOM)
- Локальные модели, совместимые с PyTorch
- API-совместимые облачные сервисы (OpenAI, Anthropic, и др.)
- Кастомные модели на базе PyTorch/Transformers

ФРЕЙМВОРКИ:
- PyTorch - основной фреймворк для работы с моделями
- Transformers (Hugging Face) - для загрузки и инференса
- Accelerate - для оптимизации работы с GPU
- Requests - для API вызовов
"""

import asyncio
import logging
import time
from queue import Queue
from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import requests  # Для API вызовов


class AI_API_Module:
    """
    Модуль ИИ API для текстовой RPG игры.
    Загружает нейросеть и держит её активной в памяти.
    Принимает промпты и возвращает результаты.
    """

    # Переменные ограничений
    MAX_CONTEXT_LENGTH = 4096  # Максимальная длина контекста (токены)
    DEFAULT_MAX_TOKENS = 2048  # Максимальное количество токенов в ответе
    DEFAULT_TEMPERATURE = 0.7  # Температура генерации
    DEFAULT_TOP_P = 0.9  # Параметр top_p для nucleus sampling
    MEMORY_LIMIT = 8  # Лимит оперативной памяти для модели (в GB)
    BATCH_SIZE = 1  # Размер батча для обработки запросов

    def __init__(self, model_name="gpt2", api_config=None):
        """
        Инициализация модуля ИИ.

        :param model_name: Название или путь к модели для загрузки
        :param api_config: Конфигурация для внешних ИИ сервисов (опционально)
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.context_history = []

        # Конфигурация внешних ИИ сервисов
        self.api_config = api_config or {}

        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Загрузка модели при инициализации
        self.load_model()

        # Очередь задач для асинхронной обработки
        self.task_queue = Queue()
        self.result_dict = {}

        # Запуск обработчика очереди в отдельном потоке
        self.thread = Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def load_model(self):
        """
        Загружает модель и токенизатор в память.
        """
        try:
            self.logger.info(f"Загрузка модели {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Устанавливаем pad_token, если он не определён
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

            self.logger.info("Модель успешно загружена")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке модели: {e}")
            # Если локальная модель не загрузилась, проверяем наличие API конфигурации
            if not self.api_config:
                raise e
            else:
                self.logger.info("Переход к использованию внешнего ИИ сервиса через API")

    def clear_context(self):
        """
        Очищает историю контекста.
        """
        self.context_history.clear()
        self.logger.info("Контекст очищен")

    def restart_model(self, new_model_name=None):
        """
        Перезапускает модель (опционально с новой моделью).

        :param new_model_name: Новое имя модели для загрузки (если нужно изменить)
        """
        try:
            # Очистка текущей модели из памяти
            if self.model is not None:
                del self.model
            if self.tokenizer is not None:
                del self.tokenizer

            # Если не указана новая модель, используем текущую
            model_to_load = new_model_name if new_model_name else self.model_name

            # Перезагрузка модели
            self.model_name = model_to_load
            self.load_model()

            # Очистка истории контекста
            self.clear_context()

            self.logger.info(f"Модель перезапущена с: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Ошибка при перезапуске модели: {e}")
            raise

    def _generate_response(self, prompt, max_length=512):
        """
        Генерирует ответ на основе промпта.
        Если локальная модель недоступна, использует внешний API.

        :param prompt: Текстовый промпт для генерации
        :param max_length: Максимальная длина генерируемого текста
        :return: Сгенерированный текст
        """
        # Если модель загружена, используем локальную генерацию
        if self.model is not None and self.tokenizer is not None:
            return self._generate_response_local(prompt, max_length)
        else:
            # Используем внешний API
            return self._generate_response_api(prompt, max_length)

    def _generate_response_local(self, prompt, max_length=512):
        """
        Генерирует ответ с использованием локальной модели.

        :param prompt: Текстовый промпт для генерации
        :param max_length: Максимальная длина генерируемого текста
        :return: Сгенерированный текст
        """
        try:
            # Подготовка входных данных
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")

            # Проверяем длину входа
            if inputs.shape[1] > self.MAX_CONTEXT_LENGTH:
                # Обрезаем, если слишком длинный
                inputs = inputs[:, -self.MAX_CONTEXT_LENGTH:]

            # Генерация ответа
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=min(inputs.shape[1] + max_length, self.MAX_CONTEXT_LENGTH),
                    num_return_sequences=1,
                    temperature=self.DEFAULT_TEMPERATURE,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    top_p=self.DEFAULT_TOP_P
                )

            # Декодирование результата
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Возвращаем только новую часть (без промпта)
            if len(response) > len(prompt) and response.startswith(prompt):
                response = response[len(prompt):].strip()

            return response
        except Exception as e:
            self.logger.error(f"Ошибка при локальной генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке запроса."

    def _generate_response_api(self, prompt, max_length=512):
        """
        Генерирует ответ с использованием внешнего API.
        Пример реализации для OpenAI API - может быть адаптирован для других сервисов.

        :param prompt: Текстовый промпт для генерации
        :param max_length: Максимальная длина генерируемого текста
        :return: Сгенерированный текст
        """
        # Проверяем, есть ли конфигурация для внешнего API
        if not self.api_config:
            return "Ошибка: нет конфигурации для внешнего ИИ сервиса."

        # Пример конфигурации:
        # {
        #     "service": "openai",
        #     "api_key": "your-api-key",
        #     "api_url": "https://api.openai.com/v1/chat/completions",
        #     "model": "gpt-3.5-turbo"
        # }

        service = self.api_config.get("service", "openai")
        api_key = self.api_config.get("api_key")
        api_url = self.api_config.get("api_url")
        model = self.api_config.get("model", "gpt-3.5-turbo")

        # Проверяем обязательные параметры
        if not api_key or not api_url:
            return "Ошибка: недостаточно данных для вызова внешнего API."

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            # Формируем payload в зависимости от сервиса
            if service == "openai":
                # Для OpenAI Chat Completions API
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Ты являешься гейммастером в текстовой RPG игре."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_length,
                    "temperature": self.DEFAULT_TEMPERATURE,
                    "top_p": self.DEFAULT_TOP_P
                }
            elif service == "custom":
                # Пример для кастомного API
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_length,
                    "temperature": self.DEFAULT_TEMPERATURE,
                    "top_p": self.DEFAULT_TOP_P
                }
            else:
                return f"Ошибка: неизвестный сервис {service}"

            # Выполняем запрос к API
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()

            # Обрабатываем ответ
            data = response.json()

            # Извлекаем текст в зависимости от сервиса
            if service == "openai":
                return data['choices'][0]['message']['content'].strip()
            elif service == "custom":
                # Адаптируйте под формат вашего API
                return data.get('response', 'Ответ не получен').strip()
            else:
                return "Ошибка: неизвестный формат ответа API"

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка при вызове внешнего API: {e}")
            return "Извините, произошла ошибка при обращении к внешнему ИИ сервису."
        except Exception as e:
            self.logger.error(f"Неизвестная ошибка при вызове внешнего API: {e}")
            return "Извините, произошла ошибка при обработке запроса через внешний ИИ сервис."

    def process_request(self, prompt, request_id=None, max_length=512):
        """
        Обрабатывает текстовый запрос (асинхронно через очередь).

        :param prompt: Текстовый промпт для генерации
        :param request_id: Уникальный ID запроса (для асинхронного получения результата)
        :param max_length: Максимальная длина генерируемого текста
        :return: Результат генерации (или None, если используется очередь)
        """
        # Добавляем в историю контекста
        self.context_history.append({"role": "user", "content": prompt})

        # Формируем полный промпт с историей
        full_prompt = self._build_context_prompt()

        # Если указан request_id, добавляем в очередь
        if request_id is not None:
            task = {
                "request_id": request_id,
                "prompt": full_prompt,
                "max_length": max_length
            }
            self.task_queue.put(task)
            return None
        else:
            # Прямая обработка без очереди
            response = self._generate_response(full_prompt, max_length)

            # Добавляем ответ в историю контекста
            self.context_history.append({"role": "assistant", "content": response})

            return response

    def get_result(self, request_id):
        """
        Получает результат асинхронного запроса по ID.

        :param request_id: Уникальный ID запроса
        :return: Результат или None, если ещё не готов
        """
        if request_id in self.result_dict:
            result = self.result_dict[request_id]
            # Удаляем результат после получения
            del self.result_dict[request_id]
            return result
        return None

    def _build_context_prompt(self):
        """
        Формирует полный промпт на основе истории контекста.

        :return: Полный текст промпта
        """
        # Для простоты объединяем все сообщения в один промпт
        # В реальном приложении может потребоваться более сложная логика ограничения длины
        context_parts = []
        for item in self.context_history[-10:]:  # Ограничиваем последние 10 сообщений
            role = item["role"]
            content = item["content"]
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def _process_queue(self):
        """
        Обрабатывает очередь задач в фоновом потоке.
        """
        while True:
            if not self.task_queue.empty():
                task = self.task_queue.get()

                response = self._generate_response(task["prompt"], task["max_length"])

                # Добавляем ответ в историю контекста
                self.context_history.append({"role": "assistant", "content": response})

                # Сохраняем результат с ID запроса
                self.result_dict[task["request_id"]] = response

            # Небольшая задержка, чтобы не перегружать CPU
            time.sleep(0.01)

    def set_temperature(self, temp_value):
        """
        Устанавливает температуру генерации.

        :param temp_value: Новое значение температуры (обычно от 0 до 1)
        """
        if 0 <= temp_value <= 1:
            self.DEFAULT_TEMPERATURE = temp_value
            self.logger.info(f"Температура генерации установлена: {temp_value}")
        else:
            self.logger.warning(f"Некорректное значение температуры: {temp_value}. Используйте значение от 0 до 1.")

    def set_max_tokens(self, max_tokens):
        """
        Устанавливает максимальное количество токенов в ответе.

        :param max_tokens: Новое максимальное количество токенов
        """
        if max_tokens > 0:
            self.DEFAULT_MAX_TOKENS = max_tokens
            self.logger.info(f"Максимальное количество токенов установлено: {max_tokens}")
        else:
            self.logger.warning(f"Некорректное значение max_tokens: {max_tokens}. Используйте положительное число.")

    def unload_model(self):
        """
        Выгружает модель из памяти.
        """
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.logger.info("Модель выгружена из памяти")


# Пример использования
if __name__ == "__main__":
    # Пример с локальной моделью
    ai_module = AI_API_Module(model_name="gpt2")

    # Пример запроса
    response = ai_module.process_request("Привет! Расскажи анекдот.")
    print(response)

    # Пример асинхронного запроса
    ai_module.process_request("Как дела?", request_id="req_1")
    result = ai_module.get_result("req_1")
    print(result)

    # Пример использования внешнего API (раскомментируйте для тестирования)
    # api_config = {
    #     "service": "openai",
    #     "api_key": "your-openai-api-key",
    #     "api_url": "https://api.openai.com/v1/chat/completions",
    #     "model": "gpt-3.5-turbo"
    # }
    # ai_module_api = AI_API_Module(api_config=api_config)
    # response_api = ai_module_api.process_request("Привет! Как дела?")
    # print(response_api)
