# Telegram-уведомления о низком балансе (задание 1)
# Два канала связи с Bot API:
# 1) Мост-прокси (приоритет): src/tg_bridge.py с BRIDGE_URL и BRIDGE_SECRET -
#    генерируется при сборке APK из GitHub Secrets. Токен бота хранится
#    на стороне моста и не попадает в приложение
# 2) Прямой API (fallback для десктопа): токен из .env (TELEGRAM_BOT_TOKEN)

import os
import secrets

import requests  # Библиотека для выполнения HTTP-запросов

from utils.logger import AppLogger

# Таймаут запросов к Telegram
REQUEST_TIMEOUT = 15


def _get_bridge_config() -> tuple:
    """
    Получение конфигурации мост-прокси.

    При сборке APK workflow генерирует src/tg_bridge.py с адресом
    моста и секретом из GitHub Secrets.

    Returns:
        tuple: (bridge_url, bridge_secret) - пустые строки, если мост не задан
    """
    try:
        import tg_bridge
        return (
            getattr(tg_bridge, "BRIDGE_URL", "") or "",
            getattr(tg_bridge, "BRIDGE_SECRET", "") or ""
        )
    except ImportError:
        return "", ""


def _get_bot_token() -> str:
    """
    Получение токена Telegram-бота для прямого доступа (fallback).

    Приоритет: переменная окружения, затем модуль telegram_token
    (прошлая схема сборки).

    Returns:
        str: Токен бота или пустая строка, если токен не задан
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token:
        return token

    try:
        import telegram_token
        return getattr(telegram_token, "TELEGRAM_BOT_TOKEN", "")
    except ImportError:
        return ""


def generate_binding_code() -> str:
    """
    Генерация кода привязки Telegram-аккаунта.

    Код из 6 символов без похожих символов (без 0/O, 1/I) -
    пользователь отправляет его боту, приложение находит сообщение
    с этим кодом через getUpdates и привязывает chat_id.

    Returns:
        str: Код привязки, например 'K7X3Q2'
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


class TelegramNotifier:
    """
    Класс для отправки Telegram-уведомлений администратору приложения.

    Обеспечивает:
    - Работу через мост-прокси (приоритет) или прямой Bot API (fallback)
    - Привязку chat_id по коду подтверждения: пользователь отправляет
      боту сгенерированный код, приложение находит его в getUpdates -
      чужой chat_id привязаться не может
    - Ручной ввод chat_id (альтернативный способ привязки)
    - Отправку сообщений о низком балансе при каждой авторизации
    """

    def __init__(self, cache):
        """
        Инициализация отправителя уведомлений.

        Args:
            cache (ChatCache): Кэш для хранения chat_id и времени
                последнего уведомления
        """
        self.cache = cache
        self.logger = AppLogger()

        # Конфигурация каналов связи
        self.bridge_url, self.bridge_secret = _get_bridge_config()
        self.bot_token = _get_bot_token()

        if self.bridge_url and self.bridge_secret:
            self.logger.info("TelegramNotifier: bridge mode configured")
        elif self.bot_token:
            self.logger.info("TelegramNotifier: direct API mode configured")
        else:
            self.logger.warning("TelegramNotifier: no bridge and no bot token - notifications disabled")

    @property
    def is_configured(self) -> bool:
        """
        Проверка доступности канала отправки уведомлений.

        Returns:
            bool: True, если задан мост или токен бота
        """
        return bool((self.bridge_url and self.bridge_secret) or self.bot_token)

    @property
    def mode(self) -> str:
        """
        Текущий канал отправки уведомлений.

        Returns:
            str: 'bridge' (мост-прокси), 'direct' (прямой API) или 'none'
        """
        if self.bridge_url and self.bridge_secret:
            return "bridge"
        if self.bot_token:
            return "direct"
        return "none"

    def _bridge_updates(self) -> list:
        """
        Получение обновлений бота через мост-прокси.

        Returns:
            list: Список обновлений или пустой список при ошибке
        """
        try:
            response = requests.get(
                f"{self.bridge_url}/updates",
                params={"secret": self.bridge_secret},
                timeout=REQUEST_TIMEOUT
            )
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])

            self.logger.error(f"Bridge updates error: {data}")
            return []
        except Exception as e:
            self.logger.error(f"Bridge updates request failed: {e}", exc_info=True)
            return []

    def _bridge_send(self, chat_id: str, text: str) -> bool:
        """
        Отправка сообщения через мост-прокси.

        Args:
            chat_id (str): Идентификатор чата получателя
            text (str): Текст сообщения

        Returns:
            bool: True при успешной отправке
        """
        try:
            response = requests.post(
                f"{self.bridge_url}/send",
                headers={"X-Bridge-Secret": self.bridge_secret},
                json={"chat_id": chat_id, "text": text},
                timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if data.get("ok"):
                self.logger.info("Message sent via bridge")
                return True

            self.logger.error(f"Bridge send error: {data}")
            return False
        except Exception as e:
            self.logger.error(f"Bridge send request failed: {e}", exc_info=True)
            return False

    def _direct_request(self, method: str, params: dict = None):
        """
        Выполнение запроса к Telegram Bot API напрямую (fallback).

        Args:
            method (str): Название метода API (getUpdates, sendMessage)
            params (dict): Параметры запроса

        Returns:
            dict: Ответ API или None при ошибке
        """
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/{method}",
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if not data.get("ok"):
                self.logger.error(f"Telegram API error in {method}: {data}")
                return None
            return data

        except Exception as e:
            self.logger.error(f"Telegram API request failed: {e}", exc_info=True)
            return None

    def _get_updates(self) -> list:
        """
        Получение обновлений бота через активный канал.

        Returns:
            list: Список обновлений или пустой список при ошибке
        """
        if self.mode == "bridge":
            return self._bridge_updates()

        if self.mode == "direct":
            data = self._direct_request("getUpdates")
            return data.get("result", []) if data else []

        return []

    def _send_to_chat(self, chat_id: str, text: str) -> bool:
        """
        Отправка сообщения в конкретный чат через активный канал.

        Args:
            chat_id (str): Идентификатор чата получателя
            text (str): Текст сообщения

        Returns:
            bool: True при успешной отправке
        """
        if self.mode == "bridge":
            return self._bridge_send(chat_id, text)

        if self.mode == "direct":
            data = self._direct_request("sendMessage", {
                "chat_id": chat_id,
                "text": text
            })
            return data is not None

        return False

    def verify_binding_code(self, code: str) -> bool:
        """
        Привязка chat_id по коду подтверждения.

        Пользователь отправляет боту сообщение с кодом, приложение
        находит это сообщение через getUpdates - только владелец
        аккаунта, отправившего код, привязывается как получатель
        уведомлений.

        Args:
            code (str): Код, показанный приложением

        Returns:
            bool: True, если код найден и chat_id сохранен
        """
        code = (code or "").strip().upper()
        if not code:
            return False

        for update in self._get_updates():
            message = update.get("message") or update.get("edited_message")
            if not message or "chat" not in message:
                continue

            message_text = (message.get("text") or "").strip().upper()

            # Ищем код в сообщении: точное совпадение или /start CODE
            if message_text == code or message_text.endswith(f"START {code}"):
                chat_id = str(message["chat"]["id"])
                self.cache.set_setting("telegram_chat_id", chat_id)
                self.logger.info(f"Telegram chat_id bound via code: {chat_id}")
                return True

        return False

    def set_chat_id(self, chat_id: str):
        """
        Ручная привязка chat_id (альтернативный способ).

        Args:
            chat_id (str): Идентификатор чата из Telegram
        """
        self.cache.set_setting("telegram_chat_id", str(chat_id))
        self.logger.info(f"Telegram chat_id set manually: {chat_id}")

    def get_chat_id(self):
        """
        Получение сохраненного chat_id.

        Returns:
            str: chat_id или None, если не привязан
        """
        return self.cache.get_setting("telegram_chat_id")

    def send_message(self, text: str) -> bool:
        """
        Отправка сообщения администратору.

        Args:
            text (str): Текст сообщения

        Returns:
            bool: True при успешной отправке
        """
        if not self.is_configured:
            self.logger.warning("Cannot send notification - no bridge and no bot token")
            return False

        chat_id = self.get_chat_id()

        # chat_id не привязан - автоматическая попытка через /start
        if not chat_id:
            for update in self._get_updates():
                message = update.get("message") or update.get("edited_message")
                if message and "chat" in message:
                    chat_id = str(message["chat"]["id"])
                    self.set_chat_id(chat_id)
                    break

        if not chat_id:
            self.logger.warning(
                "chat_id not bound - user should bind via code or manual input"
            )
            return False

        return self._send_to_chat(chat_id, text)

    def send_low_balance_notification(self, balance: str, threshold: float = 0.5) -> bool:
        """
        Отправка уведомления о низком балансе.

        Вызывается при каждой авторизации в приложении - баланс
        проверяется при каждом запуске чата.

        Args:
            balance (str): Текущий баланс в виде строки, например '$0.12'
            threshold (float): Пороговый баланс для отправки уведомления

        Returns:
            bool: True, если уведомление отправлено
        """
        text = (
            f"AI Chat: низкий баланс OpenRouter {balance}. "
            f"Пополните баланс, чтобы продолжить работу с платными моделями"
        )

        return self.send_message(text)
