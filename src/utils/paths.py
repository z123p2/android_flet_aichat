# Кроссплатформенные пути приложения: на мобильных платформах используется
# каталог данных Flet (FLET_APP_STORAGE_DATA), на десктопе - рабочая директория

import os


def get_app_data_dir() -> str:
    """
    Возвращает каталог данных приложения для текущей платформы.

    Returns:
        str: Путь к каталогу, доступному для записи на любой платформе
    """
    storage_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)
        return storage_dir
    return os.getcwd()


def get_db_path() -> str:
    """
    Возвращает путь к файлу базы данных SQLite.

    Returns:
        str: Путь к chat_cache.db внутри каталога данных приложения
    """
    return os.path.join(get_app_data_dir(), "chat_cache.db")


def get_logs_dir() -> str:
    """
    Возвращает путь к каталогу логов, создавая его при необходимости.

    Returns:
        str: Путь к каталогу logs внутри каталога данных приложения
    """
    logs_dir = os.path.join(get_app_data_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_exports_dir() -> str:
    """
    Возвращает путь к каталогу экспорта истории чата, создавая его при необходимости.

    Returns:
        str: Путь к каталогу exports внутри каталога данных приложения
    """
    exports_dir = os.path.join(get_app_data_dir(), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    return exports_dir
