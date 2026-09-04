# Telegram-уведомления о низком балансе (задание 1)
# Токен берется из src/telegram_token.py (генерируется при сборке APK из GitHub Secrets)
# или из переменной окружения TELEGRAM_BOT_TOKEN (.env при локальном запуске)

import os
import time

import requests  # Библиотека для выполнения HTTP-запросов к Telegram Bot API

from utils.logger import AppLogger

# Интервал анти-спама: не чаще одного уведомления в 24 часа
NOTIFICATION_INTERVAL_SECONDS = 24 * 60 * 60


def _get_bot_token() -> str:
    """
    Получение токена Telegram-бота.

    Приоритет: переменная окружения, затем модуль telegram_token,
    который генерируется при сборке APK из GitHub Secrets.

    Returns:
        str: Токен бота или пустая строка, если токен не задан
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token:
        return token

    # Модуль появляется только при сборке APK (создает workflow)
    try:
        import telegram_token
        return getattr(telegram_token, "TELEGRAM_BOT_TOKEN", "")
    except ImportError:
        return ""


class TelegramNotifier:
    """
    Класс для отправки Telegram-уведомлений администратору приложения.

    Обеспечивает:
    - Автоматическое определение chat_id через getUpdates (пользователь
      отправляет боту /start, после чего chat_id сохраняется в базу)
    - Отправку сообщений о низком балансе
    - Анти-спам: не чаще одного уведомления в 24 часа
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
        self.bot_token = _get_bot_token()

        if self.bot_token:
            self.logger.info("TelegramNotifier initialized with bot token")
        else:
            self.logger.warning("Telegram bot token not found - notifications disabled")

    @property
    def is_configured(self) -> bool:
        """
        Проверка наличия токена бота.

        Returns:
            bool: True, если токен задан и уведомления доступны
        """
        return bool(self.bot_token)

    def _api_request(self, method: str, params: dict = None):
        """
        Выполнение запроса к Telegram Bot API.

        Args:
            method (str): Название метода API (getUpdates, sendMessage и т.д.)
            params (dict): Параметры запроса

        Returns:
            dict: Ответ API или None при ошибке
        """
        try:
            # Запрос к Bot API: формат адреса https://api.telegram.org/bot<token>/method
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/{method}",
                params=params,
                timeout=10
            )
            data = response.json()

            if not data.get("ok"):
                self.logger.error(f"Telegram API error in {method}: {data}")
                return None
            return data

        except Exception as e:
            self.logger.error(f"Telegram API request failed: {e}", exc_info=True)
            return None

    def discover_chat_id(self) -> bool:
        """
        Определение chat_id администратора через метод getUpdates.

        Пользователь отправляет боту команду /start, после чего
        chat_id извлекается из обновлений и сохраняется в базу.

        Returns:
            bool: True, если chat_id найден и сохранен
        """
        if not self.is_configured:
            return False

        data = self._api_request("getUpdates")
        if not data:
            return False

        # Ищем первое доступное обновление с сообщением от пользователя
        for update in data.get("result", []):
            message = update.get("message") or update.get("edited_message")
            if message and "chat" in message:
                chat_id = str(message["chat"]["id"])
                self.cache.set_setting("telegram_chat_id", chat_id)
                self.logger.info(f"Telegram chat_id discovered: {chat_id}")
                return True

        return False

    def send_message(self, text: str) -> bool:
        """
        Отправка сообщения администратору.

        Args:
            text (str): Текст сообщения

        Returns:
            bool: True при успешной отправке
        """
        if not self.is_configured:
            self.logger.warning("Cannot send notification - bot token not configured")
            return False

        chat_id = self.cache.get_setting("telegram_chat_id")

        # chat_id еще не определен - пробуем обнаружить через getUpdates
        if not chat_id:
            if not self.discover_chat_id():
                self.logger.warning(
                    "chat_id not found - user should send /start to the bot"
                )
                return False
            chat_id = self.cache.get_setting("telegram_chat_id")

        data = self._api_request("sendMessage", {
            "chat_id": chat_id,
            "text": text
        })

        if data:
            self.logger.info("Telegram notification sent successfully")
            return True
        return False

    def send_low_balance_notification(self, balance: str, threshold: float = 0.5) -> bool:
        """
        Отправка уведомления о низком балансе с защитой от спама.

        Уведомление отправляется не чаще одного раза в 24 часа -
        время последней отправки хранится в базе данных.

        Args:
            balance (str): Текущий баланс в виде строки, например '$0.12'
            threshold (float): Пороговый баланс для отправки уведомления

        Returns:
            bool: True, если уведомление отправлено
        """
        # Проверяем время последнего уведомления (анти-спам 24 часа)
        last_sent = self.cache.get_setting("last_balance_notification")
        if last_sent:
            try:
                elapsed = time.time() - float(last_sent)
                if elapsed < NOTIFICATION_INTERVAL_SECONDS:
                    self.logger.debug(
                        "Low balance notification skipped - sent recently "
                        f"({elapsed / 3600:.1f}h ago)"
                    )
                    return False
            except ValueError:
                # Некорректное значение - сбрасываем и отправляем заново
                pass

        text = (
            f"AI Chat: низкий баланс OpenRouter {balance}. "
            f"Пополните баланс, чтобы продолжить работу с платными моделями"
        )

        if self.send_message(text):
            # Сохраняем время успешной отправки для анти-спама
            self.cache.set_setting("last_balance_notification", str(time.time()))
            return True
        return False
