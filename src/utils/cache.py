# Кэширование из урока: расширено таблицами auth (PIN, ключ) и settings
# (время последнего уведомления) для заданий 1 и 2

import sqlite3      # Библиотека для работы с SQLite базой данных
import hashlib      # Библиотека для хэширования PIN
import secrets      # Библиотека для генерации случайного PIN
import threading    # Библиотека для обеспечения потокобезопасности

from datetime import datetime  # Библиотека для работы с датой и временем
from utils.paths import get_db_path


class ChatCache:
    """
    Класс для кэширования истории чата в SQLite базе данных.

    Обеспечивает:
    - Потокобезопасное хранение истории сообщений
    - Сохранение метаданных (модель, токены, время)
    - Хранение ключа OpenRouter и PIN-кода (таблица auth)
    - Хранение времени последнего Telegram-уведомления (таблица settings)
    - Форматированный вывод истории
    - Очистку истории
    """

    def __init__(self):
        """
        Инициализация системы кэширования.

        Создает:
        - Файл базы данных SQLite в каталоге данных приложения
        - Потокобезопасное хранилище соединений
        - Необходимые таблицы в базе данных
        """
        # Имя файла SQLite базы данных - путь из модуля путей
        self.db_name = get_db_path()

        # Создание потокобезопасного хранилища соединений
        # Каждый поток будет иметь свое собственное соединение с базой
        self.local = threading.local()

        # Создание необходимых таблиц при инициализации
        self.create_tables()

    def get_connection(self):
        """
        Получение соединения с базой данных для текущего потока.

        Returns:
            sqlite3.Connection: Объект соединения с базой данных

        Note:
            Каждый поток получает свое собственное соединение,
            что обеспечивает потокобезопасность работы с базой.
        """
        # Проверяем, есть ли уже соединение в текущем потоке
        if not hasattr(self.local, 'connection'):
            # Если соединения нет - создаем новое
            self.local.connection = sqlite3.connect(self.db_name)
        return self.local.connection

    def create_tables(self):
        """
        Создание необходимых таблиц в базе данных.

        Создает таблицы:
        - messages: история сообщений чата
        - analytics_messages: данные аналитики использования
        - auth: ключ OpenRouter и хэш PIN-кода
        - settings: настройки (время последнего уведомления)
        """
        # Создаем новое соединение с базой
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # SQL запросы для создания таблиц
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID сообщения
                model TEXT,                           -- Идентификатор модели
                user_message TEXT,                    -- Текст от пользователя
                ai_response TEXT,                     -- Ответ от AI
                timestamp DATETIME,                   -- Время создания
                tokens_used INTEGER                   -- Использовано токенов
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model TEXT,
                message_length INTEGER,
                response_time FLOAT,
                tokens_used INTEGER
            )
        ''')

        # Таблица аутентификации: ключ OpenRouter и хэш PIN
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                api_key TEXT,
                pin_hash TEXT
            )
        ''')

        # Таблица настроек: время последнего отправленного уведомления
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()  # Сохранение изменений в базе
        conn.close()   # Закрытие соединения

    def save_message(self, model, user_message, ai_response, tokens_used):
        """
        Сохранение нового сообщения в базу данных.

        Args:
            model (str): Идентификатор использованной модели
            user_message (str): Текст сообщения пользователя
            ai_response (str): Ответ AI модели
            tokens_used (int): Количество использованных токенов
        """
        conn = self.get_connection()  # Получение соединения для текущего потока
        cursor = conn.cursor()

        # Вставка новой записи в таблицу messages
        cursor.execute('''
            INSERT INTO messages (model, user_message, ai_response, timestamp, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (model, user_message, ai_response, datetime.now(), tokens_used))
        conn.commit()  # Сохранение изменений

    def get_chat_history(self, limit=50):
        """
        Получение последних сообщений из истории чата.

        Args:
            limit (int): Максимальное количество возвращаемых сообщений

        Returns:
            list: Список кортежей с данными сообщений, отсортированных
                 по времени в обратном порядке (новые сначала)
        """
        conn = self.get_connection()  # Получение соединения для текущего потока
        cursor = conn.cursor()

        # Получение последних сообщений с ограничением по количеству
        cursor.execute('''
            SELECT * FROM messages
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()  # Возврат всех найденных записей

    def save_analytics(self, timestamp, model, message_length, response_time, tokens_used):
        """
        Сохранение данных аналитики в базу данных.

        Args:
            timestamp (datetime): Время создания записи
            model (str): Идентификатор использованной модели
            message_length (int): Длина сообщения
            response_time (float): Время ответа
            tokens_used (int): Количество использованных токенов
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO analytics_messages
            (timestamp, model, message_length, response_time, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, model, message_length, response_time, tokens_used))
        conn.commit()

    def get_analytics_history(self):
        """
        Получение всей истории аналитики.

        Returns:
            list: Список записей аналитики
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, model, message_length, response_time, tokens_used
            FROM analytics_messages
            ORDER BY timestamp ASC
        ''')
        return cursor.fetchall()

    def clear_history(self):
        """
        Очистка всей истории сообщений.

        Удаляет все записи из таблицы messages,
        эффективно очищая всю историю чата.
        """
        conn = self.get_connection()  # Получение соединения
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')  # Удаление всех записей
        conn.commit()  # Сохранение изменений

    def get_formatted_history(self):
        """
        Получение отформатированной истории диалога.

        Returns:
            list: Список словарей с данными сообщений
        """
        conn = self.get_connection()  # Получение соединения
        cursor = conn.cursor()

        # Получение всех сообщений, отсортированных по времени
        cursor.execute('''
            SELECT
                id,
                model,
                user_message,
                ai_response,
                timestamp,
                tokens_used
            FROM messages
            ORDER BY timestamp ASC
        ''')

        # Формирование списка словарей с данными сообщений
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row[0],              # ID сообщения
                "model": row[1],           # Использованная модель
                "user_message": row[2],    # Сообщение пользователя
                "ai_response": row[3],     # Ответ AI
                "timestamp": row[4],       # Временная метка
                "tokens_used": row[5]      # Использовано токенов
            })
        return history  # Возврат форматированной истории

    # Аутентификация: ключ OpenRouter и PIN (задание 2)

    def get_auth(self):
        """
        Получение сохраненного ключа OpenRouter и хэша PIN.

        Returns:
            tuple: (api_key, pin_hash) или (None, None), если вход еще не выполнен
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT api_key, pin_hash FROM auth WHERE id = 1')
        row = cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)

    def save_auth(self, api_key: str, pin: str):
        """
        Сохранение ключа OpenRouter и хэша PIN-кода.

        PIN хранится только в виде SHA-256 хэша - исходный код PIN
        не сохраняется нигде в приложении.

        Args:
            api_key (str): Ключ авторизации openRouter.ai
            pin (str): 4-значный PIN-код
        """
        # Хэшируем PIN перед сохранением в базу
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auth (id, api_key, pin_hash)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET api_key = ?, pin_hash = ?
        ''', (api_key, pin_hash, api_key, pin_hash))
        conn.commit()

    def check_pin(self, pin: str) -> bool:
        """
        Проверка введенного PIN-кода против сохраненного хэша.

        Args:
            pin (str): Введенный пользователем PIN

        Returns:
            bool: True, если PIN верный, иначе False
        """
        _, pin_hash = self.get_auth()
        if not pin_hash:
            return False
        # Сравниваем хэш введенного PIN с сохраненным
        return hashlib.sha256(pin.encode()).hexdigest() == pin_hash

    def reset_auth(self):
        """
        Сброс ключа и PIN - полный выход из приложения.

        Удаляет запись аутентификации, при следующем входе
        потребуется ввести новый ключ OpenRouter.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM auth WHERE id = 1')
        conn.commit()

    # Настройки: время последнего уведомления (задание 1)

    def get_setting(self, key: str):
        """
        Получение значения настройки по ключу.

        Args:
            key (str): Ключ настройки

        Returns:
            str: Значение настройки или None, если не задано
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_setting(self, key: str, value: str):
        """
        Сохранение значения настройки.

        Args:
            key (str): Ключ настройки
            value (str): Значение настройки
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
        ''', (key, value, value))
        conn.commit()

    @staticmethod
    def generate_pin() -> str:
        """
        Генерация случайного 4-значного PIN-кода.

        Используется криптографический генератор случайных чисел.

        Returns:
            str: PIN-код из 4 цифр в виде строки
        """
        return f"{secrets.randbelow(10000):04d}"
