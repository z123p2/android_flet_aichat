import flet as ft  # Импортируем фреймворк Flet для создания пользовательского интерфейса


class AppStyles:
    """
    Класс для централизованного хранения всех стилей приложения.

    Содержит константы и конфигурации для всех визуальных элементов интерфейса:
    - Настройки страницы
    - Стили компонентов чата
    - Настройки кнопок
    - Параметры полей ввода
    - Конфигурации layout элементов
    - Стили окна входа (PIN-аутентификация, задание 2)
    """

    # Основные настройки страницы приложения
    PAGE_SETTINGS = {
        "title": "AI Chat",                                    # Заголовок окна приложения
        "vertical_alignment": ft.MainAxisAlignment.CENTER,     # Вертикальное выравнивание содержимого по центру
        "horizontal_alignment": ft.CrossAxisAlignment.CENTER,  # Горизонтальное выравнивание содержимого по центру
        "padding": 20,                                        # Отступы от краев окна
        "bgcolor": ft.Colors.GREY_900,                        # Темно-серый цвет фона для темной темы
        "theme_mode": ft.ThemeMode.DARK,                      # Использование темной темы оформления
    }

    # Настройки области истории чата
    CHAT_HISTORY = {
        "expand": True,       # Разрешаем расширение на все доступное пространство
        "spacing": 10,        # Отступ между сообщениями в пикселях
        "auto_scroll": True,  # Автоматическая прокрутка к новым сообщениям
        "padding": 20,        # Внутренние отступы области чата
    }

    # Настройки поля ввода сообщений
    MESSAGE_INPUT = {
        "expand": 7,                         # 3.5/4 ширины строки ввода
        "height": 50,                        # Высота поля ввода в пикселях
        "multiline": False,                  # Запрет многострочного ввода
        "text_size": 16,                     # Размер шрифта текста
        "color": ft.Colors.WHITE,            # Цвет вводимого текста
        "bgcolor": ft.Colors.GREY_800,       # Цвет фона поля ввода
        "border_color": ft.Colors.BLUE_400,  # Цвет границы поля
        "cursor_color": ft.Colors.WHITE,     # Цвет курсора ввода
        "content_padding": 10,               # Внутренние отступы текста
        "border_radius": 8,                  # Радиус скругления углов
        "hint_text": "Введите сообщение здесь...",  # Текст-подсказка в пустом поле
        "shift_enter": True,                 # Включение отправки по Shift+Enter
    }

    # Настройки кнопки сохранения диалога
    SAVE_BUTTON = {
        "content": "Сохранить",              # Текст на кнопке
        "icon": ft.Icons.SAVE,               # Иконка сохранения
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.DEEP_PURPLE_700,  # Темно-фиолетовый цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "tooltip": "Сохранить диалог в файл", # Всплывающая подсказка
        "expand": 1,                         # Растягивание на половину строки
        "height": 40,                        # Высота кнопки
    }

    # Настройки кнопки очистки истории
    CLEAR_BUTTON = {
        "content": "Очистить",               # Текст на кнопке
        "icon": ft.Icons.DELETE,             # Иконка удаления
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.RED_700,       # Красный цвет фона для предупреждения
            padding=10,                      # Внутренние отступы
        ),
        "tooltip": "Очистить историю чата",   # Всплывающая подсказка
        "expand": 1,                         # Растягивание на половину строки
        "height": 40,                        # Высота кнопки
    }

    # Настройки кнопки показа аналитики
    ANALYTICS_BUTTON = {
        "content": "Аналитика",              # Текст на кнопке
        "icon": ft.Icons.ANALYTICS,          # Иконка аналитики
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.GREEN_700,     # Зеленый цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "tooltip": "Показать аналитику",     # Всплывающая подсказка
        "expand": 1,                         # Растягивание на половину строки
        "height": 40,                        # Высота кнопки
    }

    # Настройки кнопки отправки сообщения: только иконка треугольника
    SEND_BUTTON = {
        "icon": ft.Icons.SEND,               # Иконка отправки без текста
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет иконки
            bgcolor=ft.Colors.BLUE_700,      # Цвет фона кнопки
            padding=10,                      # Внутренние отступы
        ),
        "tooltip": "Отправить сообщение",    # Всплывающая подсказка при наведении
        "expand": 1,                         # 0.5/4 ширины в строке с полем ввода
        "height": 50,                        # Высота кнопки на уровне поля ввода
    }

    # Настройки строки с полем ввода и кнопкой отправки
    INPUT_ROW = {
        "spacing": 10,                                    # Отступ между элементами
        "alignment": ft.MainAxisAlignment.SPACE_BETWEEN,  # Распределение пространства между элементами
    }

    # Настройки строки с кнопками управления
    CONTROL_BUTTONS_ROW = {
        "spacing": 20,                            # Отступ между кнопками
        "alignment": ft.MainAxisAlignment.CENTER,  # Выравнивание кнопок по центру
    }

    # Настройки колонки с элементами управления
    CONTROLS_COLUMN = {
        "spacing": 20,                                    # Отступ между элементами
        "horizontal_alignment": ft.CrossAxisAlignment.CENTER,  # Выравнивание по центру по горизонтали
    }

    # Настройки главной колонки приложения
    MAIN_COLUMN = {
        "expand": True,                                   # Разрешение расширения
        "spacing": 20,                                    # Отступ между элементами
        "alignment": ft.MainAxisAlignment.CENTER,         # Вертикальное выравнивание по центру
        "horizontal_alignment": ft.CrossAxisAlignment.CENTER,  # Горизонтальное выравнивание по центру
    }

    # Настройки поля поиска модели
    MODEL_SEARCH_FIELD = {
        "expand": 1,                         # Половина ширины строки с балансом
        "height": 45,                        # Высота поля
        "border_radius": 8,                  # Радиус скругления углов
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона поля
        "border_color": ft.Colors.GREY_700,  # Цвет границы в обычном состоянии
        "color": ft.Colors.WHITE,            # Цвет текста
        "content_padding": 10,               # Внутренние отступы
        "cursor_color": ft.Colors.WHITE,     # Цвет курсора
        "focused_border_color": ft.Colors.BLUE_400,  # Цвет границы при фокусе
        "hint_style": ft.TextStyle(          # Стиль текста-подсказки
            color=ft.Colors.GREY_400,        # Цвет текста-подсказки
            size=14,                         # Размер шрифта подсказки
        ),
        "prefix_icon": ft.Icons.SEARCH,      # Иконка поиска слева от поля
    }

    # Настройки выпадающего списка выбора модели
    MODEL_DROPDOWN = {
        "height": 45,                        # Высота в закрытом состоянии
        "border_radius": 8,                  # Радиус скругления углов
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона
        "border_color": ft.Colors.GREY_700,  # Цвет границы
        "color": ft.Colors.WHITE,            # Цвет текста
        "content_padding": 10,               # Внутренние отступы
        "focused_border_color": ft.Colors.BLUE_400,  # Цвет границы при фокусе
    }

    # Настройки колонки с элементами выбора модели
    MODEL_SELECTION_COLUMN = {
        "spacing": 10,                       # Отступ между элементами
    }

    # Настройки строки поиска модели с балансом
    SEARCH_BALANCE_ROW = {
        "spacing": 10,                       # Отступ между элементами
    }

    # Настройки текста отображения баланса
    BALANCE_TEXT = {
        "size": 14,                          # Размер шрифта (компактно для узкого контейнера)
        "color": ft.Colors.GREEN_400,        # Зеленый цвет для позитивного восприятия
        "weight": ft.FontWeight.BOLD,        # Жирное начертание для акцента
        "no_wrap": True,                     # Без переноса строки
        "max_lines": 1,                      # Одна строка
    }

    # Настройки контейнера для отображения баланса
    BALANCE_CONTAINER = {
        "expand": 1,                         # 1/4 ширины строки с поиском
        "alignment": ft.Alignment(0.0, 0.0),  # Центрирование текста баланса
        "padding": 10,                       # Внутренние отступы
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона
        "border_radius": 8,                  # Радиус скругления углов
        "border": ft.Border.all(1, ft.Colors.GREY_700),  # Тонкая серая граница
    }

    # Стили окна входа (задание 2)

    # Настройки главного контейнера окна входа
    LOGIN_CONTAINER = {
        "width": 400,                        # Ширина контейнера
        "padding": 30,                       # Внутренние отступы
        "bgcolor": ft.Colors.GREY_800,       # Цвет фона
        "border_radius": 12,                 # Радиус скругления углов
    }

    # Настройки колонки окна входа
    LOGIN_COLUMN = {
        "spacing": 15,                                    # Отступ между элементами
        "horizontal_alignment": ft.CrossAxisAlignment.CENTER,  # Выравнивание по центру
    }

    # Настройки заголовка окна входа
    LOGIN_TITLE = {
        "size": 22,                          # Размер шрифта
        "weight": ft.FontWeight.BOLD,        # Жирное начертание
        "color": ft.Colors.WHITE,            # Цвет текста
    }

    # Настройки поля ввода API ключа
    LOGIN_KEY_FIELD = {
        "width": 340,                        # Ширина поля
        "password": True,                    # Скрытие ключа при вводе
        "can_reveal_password": True,         # Возможность показать ключ
        "multiline": False,                  # Однострочный ввод
        "text_size": 14,                     # Размер шрифта
        "color": ft.Colors.WHITE,            # Цвет текста
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона
        "border_color": ft.Colors.GREY_700,  # Цвет границы
        "cursor_color": ft.Colors.WHITE,     # Цвет курсора
        "content_padding": 10,               # Внутренние отступы
        "border_radius": 8,                  # Радиус скругления углов
        "prefix_icon": ft.Icons.KEY,         # Иконка ключа слева
        "hint_text": "Ключ авторизации openRouter.ai",  # Подсказка
    }

    # Настройки поля ввода PIN
    LOGIN_PIN_FIELD = {
        "width": 340,                        # Ширина поля
        "password": True,                    # Скрытие PIN при вводе
        "max_length": 4,                     # Максимум 4 цифры
        "keyboard_type": ft.KeyboardType.NUMBER,  # Цифровая клавиатура
        "text_size": 24,                     # Крупный шрифт для PIN
        "color": ft.Colors.WHITE,            # Цвет текста
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона
        "border_color": ft.Colors.GREY_700,  # Цвет границы
        "cursor_color": ft.Colors.WHITE,     # Цвет курсора
        "content_padding": 10,               # Внутренние отступы
        "border_radius": 8,                  # Радиус скругления углов
        "prefix_icon": ft.Icons.LOCK,        # Иконка замка слева
        "hint_text": "PIN",                  # Подсказка
        "text_align": ft.TextAlign.CENTER,   # Центрирование текста
    }

    # Настройки кнопки входа
    LOGIN_BUTTON = {
        "content": "Войти",                  # Текст на кнопке
        "icon": ft.Icons.LOGIN,              # Иконка входа
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.BLUE_700,      # Цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "width": 340,                        # Ширина кнопки
        "height": 45,                        # Высота кнопки
    }

    # Настройки кнопки сброса ключа
    RESET_BUTTON = {
        "content": "Сбросить ключ",          # Текст на кнопке
        "icon": ft.Icons.REFRESH,            # Иконка сброса
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.RED_700,       # Красный цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "width": 340,                        # Ширина кнопки
        "height": 45,                        # Высота кнопки
    }

    # Настройки текста сообщения об ошибке входа
    LOGIN_ERROR_TEXT = {
        "size": 14,                          # Размер шрифта
        "color": ft.Colors.RED_400,          # Красный цвет ошибки
        "text_align": ft.TextAlign.CENTER,   # Центрирование текста
    }

    # Настройки текста статуса (проверка ключа и т.п.)
    LOGIN_STATUS_TEXT = {
        "size": 14,                          # Размер шрифта
        "color": ft.Colors.GREY_400,         # Серый цвет статуса
        "text_align": ft.TextAlign.CENTER,   # Центрирование текста
    }

    # Стили диалога Telegram-уведомлений

    # Настройки колонки диалога уведомлений
    TG_DIALOG_COLUMN = {
        "spacing": 12,                       # Отступ между элементами
        "width": 360,                        # Ширина диалога
        "tight": True,                       # Плотное расположение
    }

    # Настройки текста кода привязки
    TG_CODE_TEXT = {
        "size": 32,                          # Крупный шрифт для кода
        "weight": ft.FontWeight.BOLD,        # Жирное начертание
        "color": ft.Colors.AMBER_400,        # Янтарный цвет для акцента
        "text_align": ft.TextAlign.CENTER,   # Центрирование
    }

    # Настройки поля ручного ввода chat_id
    TG_CHAT_ID_FIELD = {
        "text_size": 14,                     # Размер шрифта
        "color": ft.Colors.WHITE,            # Цвет текста
        "bgcolor": ft.Colors.GREY_900,       # Цвет фона
        "border_color": ft.Colors.GREY_700,  # Цвет границы
        "cursor_color": ft.Colors.WHITE,     # Цвет курсора
        "content_padding": 10,               # Внутренние отступы
        "border_radius": 8,                  # Радиус скругления углов
        "prefix_icon": ft.Icons.TAG,         # Иконка идентификатора
        "hint_text": "chat_id из Telegram",  # Подсказка
    }

    # Настройки кнопки копирования кода привязки
    TG_COPY_BUTTON = {
        "content": "Скопировать",            # Текст на кнопке
        "icon": ft.Icons.CONTENT_COPY,       # Иконка копирования
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.BLUE_700,      # Цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "expand": 1,                         # Растягивание в строке
        "height": 42,                        # Высота кнопки
    }

    # Настройки кнопки проверки кода привязки
    TG_VERIFY_BUTTON = {
        "content": "Проверить код",          # Текст на кнопке
        "icon": ft.Icons.CHECK_CIRCLE,       # Иконка проверки
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.GREEN_700,     # Зеленый цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "expand": 1,                         # Растягивание в строке
        "height": 42,                        # Высота кнопки
    }

    # Настройки кнопки отправки тестового уведомления
    TG_TEST_BUTTON = {
        "content": "Отправить тест",         # Текст на кнопке
        "icon": ft.Icons.SEND,               # Иконка отправки
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.BLUE_700,      # Цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "expand": 1,                         # Растягивание в строке
        "height": 42,                        # Высота кнопки
    }

    # Настройки кнопки сохранения chat_id вручную
    TG_SAVE_CHAT_BUTTON = {
        "content": "Сохранить",              # Текст на кнопке
        "icon": ft.Icons.SAVE,               # Иконка сохранения
        "style": ft.ButtonStyle(             # Стиль оформления кнопки
            color=ft.Colors.WHITE,           # Цвет текста
            bgcolor=ft.Colors.DEEP_PURPLE_700,  # Темно-фиолетовый цвет фона
            padding=10,                      # Внутренние отступы
        ),
        "expand": 1,                         # Растягивание в строке
        "height": 42,                        # Высота кнопки
    }

    @staticmethod
    def set_window_size(page: ft.Page):
        """
        Установка фиксированного размера окна приложения.

        Вызывается только на десктопных платформах - на мобильных
        у страницы нет свойства window (задание 3).

        Args:
            page (ft.Page): Объект страницы приложения
        """
        # Проверяем платформу: window есть только на десктопе
        desktop_platforms = (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX)
        if page.platform in desktop_platforms:
            page.window.width = 600              # Фиксированная ширина окна
            page.window.height = 800             # Фиксированная высота окна
            page.window.resizable = False        # Запрет изменения размера пользователем
