# Компоненты UI из урока: адаптированы под flet 0.86 (Margin/Alignment вместо
# margin.only/alignment.*) и расширены LoginView для PIN-аутентификации (задание 2)

import flet as ft                  # Фреймворк для создания пользовательского интерфейса
from ui.styles import AppStyles    # Импорт стилей приложения
import asyncio                     # Библиотека для асинхронного программирования


class MessageBubble(ft.Container):
    """
    Компонент "пузырька" сообщения в чате.

    Наследуется от ft.Container для создания стилизованного контейнера сообщения.
    Отображает сообщения пользователя и AI с разными стилями и позиционированием.

    Args:
        message (str): Текст сообщения для отображения
        is_user (bool): Флаг, указывающий, является ли это сообщением пользователя
    """
    def __init__(self, message: str, is_user: bool):
        # Инициализация родительского класса Container
        super().__init__()

        # Настройка отступов внутри пузырька
        self.padding = 10

        # Настройка скругления углов пузырька
        self.border_radius = 10

        # Установка цвета фона в зависимости от отправителя:
        # - Синий для сообщений пользователя
        # - Серый для сообщений AI
        self.bgcolor = ft.Colors.BLUE_700 if is_user else ft.Colors.GREY_700

        # Установка выравнивания пузырька:
        # - Справа для сообщений пользователя
        # - Слева для сообщений AI
        # В flet 0.86 константы alignment.* заменены на Alignment(x, y)
        self.alignment = ft.Alignment(1.0, 0.0) if is_user else ft.Alignment(-1.0, 0.0)

        # Настройка внешних отступов для создания эффекта диалога:
        # - Отступ слева для сообщений пользователя
        # - Отступ справа для сообщений AI
        # - Небольшие отступы сверху и снизу для разделения сообщений
        # В flet 0.86 метод margin.only заменен на конструктор Margin
        self.margin = ft.Margin(
            left=50 if is_user else 0,      # Отступ слева
            right=0 if is_user else 50,      # Отступ справа
            top=5,                           # Отступ сверху
            bottom=5                         # Отступ снизу
        )

        # Создание содержимого пузырька
        self.content = ft.Column(
            controls=[
                # Текст сообщения с настройками отображения
                ft.Text(
                    value=message,                    # Текст сообщения
                    color=ft.Colors.WHITE,            # Белый цвет текста
                    size=16,                         # Размер шрифта
                    selectable=True,                 # Возможность выделения текста
                    weight=ft.FontWeight.W_400       # Нормальная толщина шрифта
                )
            ],
            tight=True  # Плотное расположение элементов в колонке
        )


class ModelSelector(ft.Dropdown):
    """
    Выпадающий список для выбора AI модели с функцией поиска.

    Наследуется от ft.Dropdown для создания кастомного выпадающего списка
    с дополнительным полем поиска для фильтрации моделей.

    Args:
        models (list): Список доступных моделей в формате:
                      [{"id": "model-id", "name": "Model Name"}, ...]
    """
    def __init__(self, models: list):
        # Инициализация родительского класса Dropdown
        super().__init__()

        # Применение стилей из конфигурации к компоненту
        for key, value in AppStyles.MODEL_DROPDOWN.items():
            setattr(self, key, value)

        # Настройка внешнего вида выпадающего списка
        self.label = None                    # Убираем текстовую метку
        self.hint_text = "Выбор модели"      # Текст-подсказка

        # Создание списка опций из предоставленных моделей
        self.options = [
            ft.dropdown.Option(
                key=model['id'],             # ID модели как ключ
                text=model['name']           # Название модели как отображаемый текст
            ) for model in models
        ]

        # Сохранение полного списка опций для фильтрации
        self.all_options = self.options.copy()

        # Установка начального значения (первая модель из списка)
        self.value = models[0]['id'] if models else None

        # Создание поля поиска для фильтрации моделей
        self.search_field = ft.TextField(
            on_change=self.filter_options,        # Функция обработки изменений
            hint_text="Поиск модели",            # Текст-подсказка в поле поиска
            **AppStyles.MODEL_SEARCH_FIELD       # Применение стилей из конфигурации
        )

    def filter_options(self, e):
        """
        Фильтрация списка моделей на основе введенного текста поиска.

        Args:
            e: Событие изменения текста в поле поиска
        """
        # Получение текста поиска в нижнем регистре
        search_text = self.search_field.value.lower() if self.search_field.value else ""

        # Если поле поиска пустое - показываем все модели
        if not search_text:
            self.options = self.all_options
        else:
            # Фильтрация моделей по тексту поиска
            # Ищем совпадения в названии или ID модели
            self.options = [
                opt for opt in self.all_options
                if search_text in opt.text.lower() or search_text in opt.key.lower()
            ]

        # Обновление интерфейса для отображения отфильтрованного списка
        e.page.update()


class LoginView(ft.Container):
    """
    Окно входа в приложение (задание 2).

    Работает в двух режимах:
    - Ввод ключа openRouter.ai (первый вход или после сброса):
      ключ проверяется через API, при валидном ключе и положительном
      балансе генерируется 4-значный PIN и выполняется вход
    - Ввод PIN (повторные входы): при верном PIN открывается чат,
      при неверном выводится ошибка

    Содержит кнопку сброса ключа для удобства пользователя.

    Args:
        cache: Кэш для хранения ключа и PIN (ChatCache)
        on_login: Колбэк успешного входа, принимает (api_key, page)
    """

    def __init__(self, cache, on_login):
        # Инициализация родительского класса Container
        super().__init__()

        # Сохраняем зависимости для колбэков
        self.cache = cache
        self.on_login = on_login

        # Применение стилей контейнера окна входа
        for key, value in AppStyles.LOGIN_CONTAINER.items():
            setattr(self, key, value)

        # Определяем режим: есть сохраненный PIN - вход по PIN
        _, self.saved_pin_hash = self.cache.get_auth()
        self.pin_mode = self.saved_pin_hash is not None

        # Поле ввода API ключа (для режима первого входа)
        self.key_field = ft.TextField(
            **AppStyles.LOGIN_KEY_FIELD,
            visible=not self.pin_mode
        )

        # Поле ввода PIN (для обоих режимов)
        self.pin_field = ft.TextField(
            **AppStyles.LOGIN_PIN_FIELD,
            visible=self.pin_mode,
            on_submit=self.handle_submit
        )

        # Текст сообщения об ошибке
        self.error_text = ft.Text(
            **AppStyles.LOGIN_ERROR_TEXT,
            visible=False
        )

        # Текст статуса (проверка ключа, генерация PIN и т.д.)
        self.status_text = ft.Text(
            **AppStyles.LOGIN_STATUS_TEXT,
            visible=False
        )

        # Кнопка входа - меняет назначение в зависимости от режима
        self.login_button = ft.Button(
            content="Войти по PIN" if self.pin_mode else "Войти по ключу",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
                padding=10,
            ),
            width=340,
            height=45,
            on_click=self.handle_submit
        )

        # Кнопка сброса ключа - видна только в режиме PIN
        self.reset_button = ft.Button(
            **AppStyles.RESET_BUTTON,
            visible=self.pin_mode,
            on_click=self.reset_key
        )

        # Заголовок меняется в зависимости от режима
        title_text = "Вход в приложение" if self.pin_mode else "Первый вход"

        # Собираем содержимое окна входа
        self.content = ft.Column(
            controls=[
                ft.Text(title_text, **AppStyles.LOGIN_TITLE),
                ft.Text(
                    "Введите PIN-код для входа" if self.pin_mode
                    else "Введите ключ авторизации openRouter.ai",
                    color=ft.Colors.GREY_400,
                    size=14
                ),
                self.key_field,
                self.pin_field,
                self.error_text,
                self.status_text,
                self.login_button,
                self.reset_button
            ],
            **AppStyles.LOGIN_COLUMN
        )

    def show_error(self, message: str):
        """
        Отображение сообщения об ошибке в окне входа.

        Args:
            message (str): Текст ошибки
        """
        self.error_text.value = message
        self.error_text.visible = True
        self.status_text.visible = False
        self.update()

    def show_status(self, message: str):
        """
        Отображение статусного сообщения (проверка ключа и т.д.).

        Args:
            message (str): Текст статуса
        """
        self.status_text.value = message
        self.status_text.visible = True
        self.error_text.visible = False
        self.update()

    async def handle_submit(self, e):
        """
        Обработка нажатия кнопки входа (асинхронный обработчик).

        В режиме PIN проверяет введенный код, в режиме ключа -
        валидирует ключ и генерирует PIN при положительном балансе.

        Args:
            e: Событие нажатия кнопки
        """
        # Сбрасываем предыдущие сообщения
        self.error_text.visible = False
        self.status_text.visible = False

        if self.pin_mode:
            await self.login_with_pin(e)
        else:
            await self.login_with_key(e)

    async def login_with_pin(self, e):
        """
        Вход по PIN-коду.

        При неверном PIN выводится ошибка, при верном -
        выполняется вход в приложение.

        Args:
            e: Событие нажатия кнопки
        """
        pin = self.pin_field.value or ""

        # Проверка формата PIN: 4 цифры
        if len(pin) != 4 or not pin.isdigit():
            self.show_error("PIN должен состоять из 4 цифр")
            return

        # Проверка PIN против сохраненного хэша
        if self.cache.check_pin(pin):
            api_key, _ = self.cache.get_auth()
            await self.on_login(api_key, e.page)
        else:
            self.show_error("Неверный PIN")

    async def login_with_key(self, e):
        """
        Вход по ключу openRouter.ai (первый вход).

        Проверяет ключ через API: если ключ валидный и баланс
        положительный - генерируется 4-значный PIN, ключ и хэш PIN
        сохраняются в базу, выполняется вход.

        По условию задания при неположительном балансе PIN не выдается.

        Args:
            e: Событие нажатия кнопки
        """
        api_key = (self.key_field.value or "").strip()
        pin = (self.pin_field.value or "").strip()

        # Проверка наличия ключа
        if not api_key:
            self.show_error("Введите ключ авторизации")
            return

        # Показываем статус проверки
        self.show_status("Проверка ключа и баланса...")
        self.login_button.disabled = True
        self.update()

        # Проверка ключа выполняется в отдельном потоке, чтобы не блокировать UI
        from api.openrouter import OpenRouterClient

        loop = asyncio.get_event_loop()
        try:
            client = await loop.run_in_executor(None, OpenRouterClient, api_key)
            validation = await loop.run_in_executor(None, client.validate_key)
        except ValueError:
            # Некорректный формат ключа - показываем ошибку и восстанавливаем кнопку
            self.login_button.disabled = False
            self.show_error("Ключ не найден или не валиден")
            return

        # Ключ невалиден
        if not validation["valid"]:
            self.login_button.disabled = False
            self.show_error("Ключ не найден или не валиден")
            return

        # Ключ валиден, но баланс неположительный - PIN не выдаем
        if not validation["balance_positive"]:
            self.login_button.disabled = False
            self.show_error(
                "Ключ валиден, но баланс не положительный "
                f"(${validation['balance']:.2f}). Пополните баланс - "
                "PIN выдается только при положительном балансе"
            )
            return

        # Генерируем PIN и сохраняем пару ключ + хэш PIN в базу
        pin = self.cache.generate_pin()
        self.cache.save_auth(api_key, pin)

        # Показываем сгенерированный PIN - его нужно запомнить
        self.show_status(f"Ваш PIN: {pin} - запомните его для следующего входа")
        await asyncio.sleep(3)

        # Выполняем вход
        await self.on_login(api_key, e.page)

    def reset_key(self, e):
        """
        Сброс сохраненного ключа и PIN (кнопка на окне входа).

        Переключает окно в режим ввода нового ключа.

        Args:
            e: Событие нажатия кнопки
        """
        # Удаляем пару ключ + PIN из базы
        self.cache.reset_auth()

        # Пересоздаем окно входа в режиме ключа
        page = e.page
        new_view = LoginView(self.cache, self.on_login)
        page.controls.clear()
        page.add(new_view)
        page.update()
