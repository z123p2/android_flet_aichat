# Клиент OpenRouter API из урока: расширено методами validate_key()
# и get_bot_chat_id() для заданий 1 и 2; load_dotenv защищен try/except -
# на Android поиск .env через обход файловой системы приводит к сбою
# (ключ вводится через UI задания 2, токен бота вшит при сборке APK)

import requests  # Библиотека для выполнения HTTP-запросов к API
import os       # Библиотека для работы с операционной системой и переменными окружения
from dotenv import load_dotenv  # Библиотека для загрузки переменных окружения из .env файла
from utils.logger import AppLogger  # Импорт собственного логгера для отслеживания работы

try:
    # Загрузка переменных окружения из .env файла при импорте модуля
    # .env существует только при локальном запуске на десктопе
    load_dotenv()
except Exception:
    # На мобильных платформах обход директорий в поиске .env невозможен -
    # пропускаем загрузку без ошибок
    pass


class OpenRouterClient:
    """
    Клиент для взаимодействия с OpenRouter API.

    OpenRouter - это сервис, предоставляющий унифицированный доступ к различным
    языковым моделям (GPT, Claude и др.) через единый API интерфейс.

    Поддерживает работу через HTTP/HTTPS/SOCKS5 прокси - если openrouter.ai
    недоступен с устройства напрямую (блокировка провайдером или регионом).
    """

    # Таймаут всех запросов к API в секундах
    REQUEST_TIMEOUT = 15

    def __init__(self, api_key: str = None, proxy_url: str = None):
        """
        Инициализация клиента OpenRouter.

        Настраивает:
        - Систему логирования
        - API ключ и базовый URL из переменных окружения или аргумента
        - Заголовки для HTTP запросов
        - Прокси (если задан) для всех запросов
        - Список доступных моделей

        Args:
            api_key (str): Ключ авторизации openRouter.ai. Если не задан,
                берется из переменной окружения OPENROUTER_API_KEY
            proxy_url (str): Адрес прокси в формате http://host:port или
                socks5://host:port. Если не задан - запросы идут напрямую

        Raises:
            ValueError: Если API ключ не найден
        """
        # Инициализация логгера для отслеживания работы клиента
        self.logger = AppLogger()

        # Получение необходимых параметров из окружения или аргумента
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")  # API ключ для авторизации
        self.base_url = os.getenv("BASE_URL") or "https://openrouter.ai/api/v1"  # Базовый URL API

        # Проверка наличия API ключа
        if not self.api_key:
            # Логирование критической ошибки
            self.logger.error("OpenRouter API key not found in .env")
            # Выбрасывание исключения с понятным сообщением
            raise ValueError("OpenRouter API key not found in .env")

        # Создаем сессию с прокси для всех запросов клиента
        self.session = self._build_session(proxy_url)

        # Настройка заголовков для всех API запросов
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",  # Токен для авторизации запросов
            "Content-Type": "application/json"          # Указание формата данных
        }

        # Логирование успешной инициализации клиента
        self.logger.info("OpenRouterClient initialized successfully")

        # Загрузка списка доступных моделей при инициализации
        self.available_models = self.get_models()

    def _build_session(self, proxy_url: str = None):
        """
        Создание HTTP-сессии, при необходимости с прокси.

        Args:
            proxy_url (str): Адрес прокси или None для прямых запросов

        Returns:
            requests.Session: Настроенная сессия
        """
        session = requests.Session()

        if proxy_url:
            # requests принимает словарь прокси: один адрес для http и https
            session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            self.logger.info(f"HTTP session configured with proxy: {proxy_url}")

        return session

    @staticmethod
    def classify_error(e: Exception) -> str:
        """
        Классификация исключения requests для понятных сообщений пользователю.

        Args:
            e (Exception): Исключение из запроса к API

        Returns:
            str: Тип ошибки: 'network' (нет соединения/таймаут),
                'auth' (невалидный ключ), 'http' (прочие коды HTTP)
        """
        import requests.exceptions

        # Сетевые проблемы: нет интернета, DNS, таймаут, отказ прокси
        if isinstance(e, (requests.exceptions.ConnectionError,
                          requests.exceptions.Timeout,
                          requests.exceptions.ProxyError)):
            return "network"
        # Прочие ошибки считаем http-проблемами
        return "http"

    def get_models(self):
        """
        Получение списка доступных языковых моделей.

        Returns:
            list: Список словарей с информацией о моделях:
                 [{"id": "model-id", "name": "Model Name"}, ...]

        Note:
            При ошибке запроса возвращает список базовых моделей по умолчанию
        """
        # Логирование начала запроса списка моделей
        self.logger.debug("Fetching available models")

        try:
            # Выполнение GET запроса к API для получения списка моделей
            response = self.session.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )
            # Преобразование ответа из JSON в словарь Python
            models_data = response.json()

            # Логирование успешного получения списка моделей
            self.logger.info(f"Retrieved {len(models_data['data'])} models")

            # Преобразование данных в нужный формат
            return [
                {
                    "id": model["id"],     # Идентификатор модели для API
                    "name": model["name"]   # Человекочитаемое название модели
                }
                for model in models_data["data"]
            ]
        except Exception as e:
            # Список моделей по умолчанию при ошибке API
            models_default = [
                {"id": "deepseek-coder", "name": "DeepSeek"},
                {"id": "claude-3-sonnet", "name": "Claude 3.5 Sonnet"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
            ]
            # Логирование ошибки и возврата списка по умолчанию
            self.logger.info(f"Retrieved {len(models_default)} models with Error: {e}")
            return models_default

    def send_message(self, message: str, model: str):
        """
        Отправка сообщения выбранной языковой модели.

        Args:
            message (str): Текст сообщения для отправки
            model (str): Идентификатор выбранной модели

        Returns:
            dict: Ответ от API, содержащий либо ответ модели, либо информацию об ошибке
        """
        # Логирование отправки сообщения
        self.logger.debug(f"Sending message to model: {model}")

        # Формирование данных для отправки в API
        data = {
            "model": model,  # Идентификатор выбранной модели
            "messages": [{"role": "user", "content": message}]  # Сообщение в формате API
        }

        try:
            # Логирование начала выполнения запроса
            self.logger.debug("Making API request")

            # Отправка POST запроса к API
            response = self.session.post(
                f"{self.base_url}/chat/completions",  # Эндпоинт для чата
                headers=self.headers,                 # Заголовки с авторизацией
                json=data,                            # Данные запроса
                timeout=self.REQUEST_TIMEOUT          # Таймаут для стабильной работы на мобильных
            )

            # Проверка на ошибки HTTP
            response.raise_for_status()

            # Логирование успешного получения ответа
            self.logger.info("Successfully received response from API")

            # Возврат данных ответа
            return response.json()

        except Exception as e:
            # Формирование информативного сообщения об ошибке
            error_msg = f"API request failed: {str(e)}"
            # Логирование ошибки с полным стектрейсом для отладки
            self.logger.error(error_msg, exc_info=True)
            # Возврат сообщения об ошибке в формате ответа API
            return {"error": str(e)}

    def get_balance(self):
        """
        Получение текущего баланса аккаунта.

        Returns:
            str: Строка с балансом в формате '$X.XX' или 'Ошибка' при неудаче
        """
        try:
            # Запрос баланса через API
            response = self.session.get(
                f"{self.base_url}/credits",  # Эндпоинт для проверки баланса
                headers=self.headers,        # Заголовки с авторизацией
                timeout=self.REQUEST_TIMEOUT
            )
            # Получение данных из ответа
            data = response.json()
            if data:
                data = data.get('data')
                # Вычисление доступного баланса (всего кредитов минус использовано)
                return f"${(data.get('total_credits', 0) - data.get('total_usage', 0)):.2f}"
            return "Ошибка"
        except Exception as e:
            # Формирование сообщения об ошибке
            error_msg = f"API request failed: {str(e)}"
            # Логирование ошибки с полным стектрейсом
            self.logger.error(error_msg, exc_info=True)
            # Возврат сообщения об ошибке
            return "Ошибка"

    def validate_key(self) -> dict:
        """
        Проверка валидности ключа и получение числового баланса (задание 2).

        По условию задания PIN генерируется только если ключ валидный
        и баланс положительный.

        Returns:
            dict: Словарь вида:
                - valid: bool - валиден ли ключ
                - balance_positive: bool - положительный ли баланс
                - balance: float - числовое значение баланса
                - error_type: 'ok' | 'auth' | 'network' | 'http' - причина
                    отказа для точного сообщения в UI
                - error_detail: str - технические детали ошибки (для отладки)
        """
        try:
            # Запрос данных о кредитах - при невалидном ключе API вернет ошибку
            response = self.session.get(
                f"{self.base_url}/credits",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )

            # Код 401/403 означает невалидный ключ
            if response.status_code in (401, 403):
                self.logger.warning(
                    f"OpenRouter key validation failed: HTTP {response.status_code}"
                )
                return {
                    "valid": False,
                    "balance_positive": False,
                    "balance": 0.0,
                    "error_type": "auth",
                    "error_detail": f"HTTP {response.status_code}: {response.text[:120]}"
                }

            # Прочие коды ошибки (5xx, 429 и т.д.) - проблема на стороне API
            if response.status_code != 200:
                self.logger.warning(
                    f"OpenRouter key validation: unexpected HTTP {response.status_code}"
                )
                return {
                    "valid": False,
                    "balance_positive": False,
                    "balance": 0.0,
                    "error_type": "http",
                    "error_detail": f"HTTP {response.status_code}: {response.text[:120]}"
                }

            data = response.json().get("data")

            if data is None:
                return {
                    "valid": False,
                    "balance_positive": False,
                    "balance": 0.0,
                    "error_type": "http",
                    "error_detail": f"Unexpected response: {str(response.json())[:120]}"
                }

            # Доступный баланс: всего кредитов минус использовано
            balance = data.get("total_credits", 0) - data.get("total_usage", 0)
            self.logger.info(f"Key validated, balance: {balance:.2f}")

            return {
                "valid": True,
                "balance_positive": balance > 0,
                "balance": balance,
                "error_type": "ok",
                "error_detail": ""
            }

        except Exception as e:
            # Разделяем сетевые ошибки (нет интернета/прокси недоступен)
            # и прочие - чтобы UI показывал точную причину
            error_type = self.classify_error(e)
            self.logger.error(
                f"Key validation failed ({error_type}): {e}", exc_info=True
            )
            return {
                "valid": False,
                "balance_positive": False,
                "balance": 0.0,
                "error_type": error_type,
                "error_detail": str(e)[:160]
            }
