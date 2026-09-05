# Точка входа приложения из урока: расширена окном входа (PIN-аутентификация,
# задание 2), Telegram-уведомлениями о низком балансе (задание 1) и мобильной
# адаптацией путей и платформ (задание 3)

# Импорт необходимых библиотек и модулей
import flet as ft                                  # Фреймворк для создания кроссплатформенных приложений с современным UI
from api.openrouter import OpenRouterClient        # Клиент для взаимодействия с AI API через OpenRouter
from ui.styles import AppStyles                    # Модуль с настройками стилей интерфейса
from ui.components import MessageBubble, ModelSelector, LoginView  # Компоненты пользовательского интерфейса
from utils.cache import ChatCache                  # Модуль для кэширования истории чата
from utils.logger import AppLogger                 # Модуль для логирования работы приложения
from utils.analytics import Analytics              # Модуль для сбора и анализа статистики использования
from utils.monitor import PerformanceMonitor       # Модуль для мониторинга производительности
from utils.notifications import TelegramNotifier, generate_binding_code  # Telegram-уведомления о низком балансе
from utils.paths import get_exports_dir            # Кроссплатформенные пути для экспорта
import asyncio                                     # Библиотека для асинхронного программирования
import time                                        # Библиотека для работы с временными метками
import json                                        # Библиотека для работы с JSON-данными
from datetime import datetime                      # Класс для работы с датой и временем
import sys                                         # Библиотека для работы с интерпретатором Python
import os                                          # Библиотека для работы с операционной системой

# Порог низкого баланса для отправки уведомления (задание 1)
LOW_BALANCE_THRESHOLD = 0.5

# Добавляем каталог src в путь поиска модулей при прямом запуске файла
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ChatApp:
    """
    Основной класс приложения чата.
    Управляет всей логикой работы приложения, включая UI и взаимодействие с API.
    """

    def __init__(self, api_key: str, proxy_url: str = None):
        """
        Инициализация основных компонентов приложения:
        - API клиент для связи с языковой моделью
        - Система кэширования для сохранения истории
        - Система логирования для отслеживания работы
        - Система аналитики для сбора статистики
        - Система мониторинга для отслеживания производительности
        - Система уведомлений о низком балансе

        Args:
            api_key (str): Ключ авторизации openRouter.ai, полученный при входе
            proxy_url (str): Адрес прокси из окна входа (опционально)
        """
        # Инициализация основных компонентов
        # Клиент создается с прокси: openrouter.ai может быть заблокирован
        self.api_client = OpenRouterClient(api_key, proxy_url=proxy_url or None)
        self.cache = ChatCache()                   # Инициализация системы кэширования
        self.logger = AppLogger()                  # Инициализация системы логирования
        self.analytics = Analytics(self.cache)     # Инициализация системы аналитики с передачей кэша
        self.monitor = PerformanceMonitor()        # Инициализация системы мониторинга
        self.notifier = TelegramNotifier(self.cache)  # Инициализация Telegram-уведомлений

        # Создание компонента для отображения баланса API
        self.balance_text = ft.Text(
            "Баланс: Загрузка...",                # Начальный текст до загрузки реального баланса
            **AppStyles.BALANCE_TEXT               # Применение стилей из конфигурации
        )

        # Кроссплатформенный путь к директории экспорта истории чата (задание 3)
        self.exports_dir = get_exports_dir()

    def load_chat_history(self):
        """
        Загрузка истории чата из кэша и отображение её в интерфейсе.
        Сообщения добавляются в обратном порядке для правильной хронологии.
        """
        try:
            history = self.cache.get_chat_history()    # Получение истории из кэша
            for msg in reversed(history):              # Перебор сообщений в обратном порядке
                # Распаковка данных сообщения в отдельные переменные
                _, model, user_message, ai_response, timestamp, tokens = msg
                # Добавление пары сообщений (пользователь + AI) в интерфейс
                self.chat_history.controls.extend([
                    MessageBubble(                     # Создание пузырька сообщения пользователя
                        message=user_message,
                        is_user=True
                    ),
                    MessageBubble(                     # Создание пузырька ответа AI
                        message=ai_response,
                        is_user=False
                    )
                ])
        except Exception as e:
            # Логирование ошибки при загрузке истории
            self.logger.error(f"Ошибка загрузки истории чата: {e}")

    def update_balance(self):
        """
        Обновление отображения баланса API в интерфейсе.
        При успешном получении баланса показывает его зеленым цветом,
        при ошибке - красным с текстом 'н/д' (не доступен).

        Также проверяет низкий баланс и отправляет Telegram-уведомление
        (не чаще одного раза в 24 часа).
        """
        try:
            balance = self.api_client.get_balance()         # Запрос баланса через API
            self.balance_text.value = f"Баланс: {balance}"  # Обновление текста с балансом
            self.balance_text.color = ft.Colors.GREEN_400   # Установка зеленого цвета для успешного получения

            # Уведомление о низком балансе через Telegram (задание 1)
            self.check_low_balance(balance)
        except Exception as e:
            # Обработка ошибки получения баланса
            self.balance_text.value = "Баланс: н/д"         # Установка текста ошибки
            self.balance_text.color = ft.Colors.RED_400     # Установка красного цвета для ошибки
            self.logger.error(f"Ошибка обновления баланса: {e}")

    def check_low_balance(self, balance: str):
        """
        Проверка баланса на предмет низкого значения.

        При балансе ниже порога отправляет Telegram-уведомление
        администратору с анти-спамом в 24 часа.

        Args:
            balance (str): Строка баланса в формате '$X.XX'
        """
        try:
            # Извлекаем числовое значение из строки вида '$1.23'
            numeric_balance = float(balance.replace("$", "").replace(",", "."))

            if numeric_balance <= LOW_BALANCE_THRESHOLD:
                # Отправляем уведомление (анти-спам внутри метода)
                sent = self.notifier.send_low_balance_notification(
                    balance, LOW_BALANCE_THRESHOLD
                )
                if sent:
                    self.logger.info("Low balance notification sent")
        except ValueError:
            # Баланс в неожиданном формате (например 'Ошибка') - пропускаем
            self.logger.warning(f"Cannot parse balance for notification: {balance}")

    def _notifications_status_text(self) -> str:
        """
        Формирование стартового статуса для диалога уведомлений.

        Returns:
            str: Описание текущего состояния привязки и канала
        """
        if not self.notifier.is_configured:
            return "Уведомления не настроены: нет канала отправки"

        chat_id = self.notifier.get_chat_id()
        mode_names = {"bridge": "мост", "direct": "прямой API"}
        mode_name = mode_names.get(self.notifier.mode, self.notifier.mode)

        if chat_id:
            return f"Канал: {mode_name}. Привязан chat_id {chat_id}"
        return f"Канал: {mode_name}. chat_id не привязан - используй код ниже"

    async def main(self, page: ft.Page):
        """
        Основная функция инициализации интерфейса приложения.
        Создает все элементы UI и настраивает их взаимодействие.

        Args:
            page (ft.Page): Объект страницы Flet для размещения элементов интерфейса
        """
        # Применение базовых настроек страницы из конфигурации стилей
        for key, value in AppStyles.PAGE_SETTINGS.items():
            setattr(page, key, value)

        # Установка размеров окна только на десктопе (задание 3)
        AppStyles.set_window_size(page)

        # Инициализация выпадающего списка для выбора модели AI
        models = self.api_client.available_models
        self.model_dropdown = ModelSelector(models)
        self.model_dropdown.value = models[0]['id'] if models else None

        async def send_message_click(e):
            """
            Асинхронная функция отправки сообщения.
            """
            if not self.message_input.value:
                return

            try:
                # Визуальная индикация процесса
                self.message_input.border_color = ft.Colors.BLUE_400
                page.update()

                # Сохранение данных сообщения
                start_time = time.time()
                user_message = self.message_input.value
                self.message_input.value = ""
                page.update()

                # Добавление сообщения пользователя
                self.chat_history.controls.append(
                    MessageBubble(message=user_message, is_user=True)
                )

                # Индикатор загрузки
                loading = ft.ProgressRing()
                self.chat_history.controls.append(loading)
                page.update()

                # Асинхронная отправка запроса
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.api_client.send_message(
                        user_message,
                        self.model_dropdown.value
                    )
                )

                # Удаление индикатора загрузки
                self.chat_history.controls.remove(loading)

                # Обработка ответа
                if "error" in response:
                    response_text = f"Ошибка: {response['error']}"
                    tokens_used = 0
                    self.logger.error(f"Ошибка API: {response['error']}")
                else:
                    response_text = response["choices"][0]["message"]["content"]
                    tokens_used = response.get("usage", {}).get("total_tokens", 0)

                # Сохранение в кэш
                self.cache.save_message(
                    model=self.model_dropdown.value,
                    user_message=user_message,
                    ai_response=response_text,
                    tokens_used=tokens_used
                )

                # Добавление ответа в чат
                self.chat_history.controls.append(
                    MessageBubble(message=response_text, is_user=False)
                )

                # Обновление аналитики
                response_time = time.time() - start_time
                self.analytics.track_message(
                    model=self.model_dropdown.value,
                    message_length=len(user_message),
                    response_time=response_time,
                    tokens_used=tokens_used
                )

                # Логирование метрик
                self.monitor.log_metrics(self.logger)
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения: {e}")
                self.message_input.border_color = ft.Colors.RED_500

                # Показ уведомления об ошибке
                page.show_dialog(
                    ft.AlertDialog(
                        content=ft.Text(str(e), color=ft.Colors.RED_500),
                        actions=[
                            ft.TextButton("Закрыть", on_click=lambda e: page.pop_dialog())
                        ]
                    )
                )

        async def show_analytics(e):
            """Показ статистики использования"""
            stats = self.analytics.get_statistics()    # Получение статистики

            # Создание диалога статистики
            dialog = ft.AlertDialog(
                title=ft.Text("Аналитика"),
                content=ft.Column([
                    ft.Text(f"Всего сообщений: {stats['total_messages']}"),
                    ft.Text(f"Всего токенов: {stats['total_tokens']}"),
                    ft.Text(f"Среднее токенов/сообщение: {stats['tokens_per_message']:.2f}"),
                    ft.Text(f"Сообщений в минуту: {stats['messages_per_minute']:.2f}")
                ], tight=True),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda e: page.pop_dialog()),
                ],
            )

            page.show_dialog(dialog)                  # Открытие диалога

        async def clear_history(e):
            """
            Очистка истории чата.
            """
            try:
                self.cache.clear_history()          # Очистка кэша
                self.analytics.clear_data()         # Очистка аналитики
                self.chat_history.controls.clear()  # Очистка истории чата
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка очистки истории: {e}")
                page.show_dialog(
                    ft.AlertDialog(
                        content=ft.Text(f"Ошибка очистки истории: {e}"),
                        actions=[
                            ft.TextButton("Закрыть", on_click=lambda e: page.pop_dialog())
                        ]
                    )
                )

        async def confirm_clear_history(e):
            """Подтверждение очистки истории"""
            # Создание диалога подтверждения
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Подтверждение удаления"),
                content=ft.Text("Вы уверены? Это действие нельзя отменить!"),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
                    ft.TextButton("Очистить", on_click=handle_clear_confirmed),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.show_dialog(dialog)

        async def handle_clear_confirmed(e):
            """Подтверждение очистки: закрываем диалог и очищаем"""
            page.pop_dialog()
            await clear_history(e)

        async def show_notifications_dialog(e):
            """
            Диалог настройки Telegram-уведомлений (задание 1).

            Два способа привязки chat_id:
            - Код подтверждения: приложение показывает код и копирует его
              в буфер, пользователь отправляет боту сообщение с кодом -
              привязывается именно его аккаунт
            - Ручной ввод chat_id (узнать: /start у бота @userinfobot)

            Кнопка теста отправляет сообщение мгновенно, не дожидаясь
            низкого баланса.
            """
            # Генерируем код привязки и копируем в буфер обмена
            binding_code = generate_binding_code()

            # Статус привязки внутри диалога
            tg_status = ft.Text(
                self._notifications_status_text(),
                size=13,
                color=ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER,
            )

            chat_id_field = ft.TextField(
                **AppStyles.TG_CHAT_ID_FIELD,
                value=self.notifier.get_chat_id() or "",
            )

            async def copy_code(ev):
                # Копируем код в буфер обмена
                try:
                    await page.clipboard.set(binding_code)
                    tg_status.value = f"Код {binding_code} скопирован в буфер обмена"
                    tg_status.color = ft.Colors.GREEN_400
                    page.update()
                except Exception as err:
                    self.logger.error(f"Clipboard copy failed: {err}")

            async def verify_code(ev):
                # Ищем код среди сообщений боту через getUpdates
                tg_status.value = "Поиск кода среди сообщений боту..."
                tg_status.color = ft.Colors.GREY_400
                page.update()

                loop = asyncio.get_event_loop()
                found = await loop.run_in_executor(
                    None, self.notifier.verify_binding_code, binding_code
                )

                if found:
                    tg_status.value = (
                        f"Привязано: chat_id {self.notifier.get_chat_id()}"
                    )
                    tg_status.color = ft.Colors.GREEN_400
                else:
                    tg_status.value = (
                        "Код не найден. Отправьте боту сообщение "
                        f"{binding_code} и повторите"
                    )
                    tg_status.color = ft.Colors.RED_400
                page.update()

            async def save_chat_id(ev):
                # Ручное сохранение chat_id из поля
                value = (chat_id_field.value or "").strip()
                if not value.isdigit():
                    tg_status.value = "chat_id должен быть числом"
                    tg_status.color = ft.Colors.RED_400
                    page.update()
                    return

                self.notifier.set_chat_id(value)
                tg_status.value = f"chat_id {value} сохранен"
                tg_status.color = ft.Colors.GREEN_400
                page.update()

            async def send_test(ev):
                # Тестовая отправка без ожидания низкого баланса
                tg_status.value = "Отправка теста..."
                tg_status.color = ft.Colors.GREY_400
                page.update()

                loop = asyncio.get_event_loop()
                sent = await loop.run_in_executor(
                    None, self.notifier.send_message,
                    "AI Chat: тестовое уведомление - связка работает"
                )

                if sent:
                    tg_status.value = "Тест отправлен - проверь Telegram"
                    tg_status.color = ft.Colors.GREEN_400
                else:
                    tg_status.value = (
                        "Не отправлено. Сначала привяжи chat_id "
                        "кодом или вручную"
                    )
                    tg_status.color = ft.Colors.RED_400
                page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Telegram-уведомления"),
                content=ft.Column(
                    [
                        tg_status,
                        ft.Container(height=4),
                        ft.Text(
                            "Способ 1 - код подтверждения:",
                            size=13, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            binding_code,
                            **AppStyles.TG_CODE_TEXT,
                        ),
                        ft.Text(
                            "Скопируй код и отправь его сообщением "
                            "твоему боту, затем нажми Проверить",
                            size=12,
                            color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.Button(
                                    content="Скопировать",
                                    icon=ft.Icons.CONTENT_COPY,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.BLUE_700,
                                        padding=10,
                                    ),
                                    expand=1,
                                    height=42,
                                    on_click=copy_code,
                                ),
                                ft.Button(
                                    **AppStyles.TG_VERIFY_BUTTON,
                                    on_click=verify_code,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            "Способ 2 - chat_id вручную (узнать: /start "
                            "у @userinfobot):",
                            size=13, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        chat_id_field,
                        ft.Button(
                            **AppStyles.TG_SAVE_CHAT_BUTTON,
                            on_click=save_chat_id,
                        ),
                        ft.Container(height=4),
                        ft.Button(
                            **AppStyles.TG_TEST_BUTTON,
                            on_click=send_test,
                        ),
                    ],
                    **AppStyles.TG_DIALOG_COLUMN,
                ),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda ev: page.pop_dialog()),
                ],
            )

            page.show_dialog(dialog)

            # Копируем код в буфер сразу при открытии диалога
            try:
                await page.clipboard.set(binding_code)
                tg_status.value = (
                    f"Код {binding_code} уже скопирован в буфер обмена - "
                    "отправь его боту и нажми Проверить"
                )
                page.update()
            except Exception as err:
                self.logger.error(f"Clipboard copy failed: {err}")

        async def save_dialog(e):
            """
            Сохранение истории диалога в JSON файл.
            """
            try:
                # Получение истории из кэша
                history = self.cache.get_chat_history()

                # Форматирование данных для сохранения
                dialog_data = []
                for msg in history:
                    dialog_data.append({
                        "timestamp": str(msg[4]),
                        "model": msg[1],
                        "user_message": msg[2],
                        "ai_response": msg[3],
                        "tokens_used": msg[5]
                    })

                # Создание имени файла
                filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.exports_dir, filename)

                # Сохранение в JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialog_data, f, ensure_ascii=False, indent=2, default=str)

                # Создание диалога успешного сохранения
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Диалог сохранен"),
                    content=ft.Column([
                        ft.Text("Путь сохранения:"),
                        ft.Text(filepath, selectable=True, weight=ft.FontWeight.BOLD),
                    ], tight=True),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: page.pop_dialog()),
                    ],
                )

                page.show_dialog(dialog)

            except Exception as e:
                self.logger.error(f"Ошибка сохранения: {e}")
                page.show_dialog(
                    ft.AlertDialog(
                        content=ft.Text(f"Ошибка сохранения: {e}"),
                        actions=[
                            ft.TextButton("Закрыть", on_click=lambda e: page.pop_dialog())
                        ]
                    )
                )

        def close_dialog(dialog):
            """Закрытие диалогового окна"""
            page.pop_dialog()

        # Создание компонентов интерфейса
        self.message_input = ft.TextField(**AppStyles.MESSAGE_INPUT)  # Поле ввода
        self.chat_history = ft.ListView(**AppStyles.CHAT_HISTORY)    # История чата

        # Загрузка существующей истории
        self.load_chat_history()

        # Создание кнопок управления
        save_button = ft.Button(
            on_click=save_dialog,           # Привязка функции сохранения
            **AppStyles.SAVE_BUTTON         # Применение стилей
        )

        clear_button = ft.Button(
            on_click=confirm_clear_history, # Привязка функции очистки
            **AppStyles.CLEAR_BUTTON        # Применение стилей
        )

        send_button = ft.Button(
            on_click=send_message_click,    # Привязка функции отправки
            **AppStyles.SEND_BUTTON         # Применение стилей
        )

        analytics_button = ft.Button(
            on_click=show_analytics,        # Привязка функции аналитики
            **AppStyles.ANALYTICS_BUTTON    # Применение стилей
        )

        notifications_button = ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS,    # Иконка уведомлений
            icon_color=ft.Colors.AMBER_400, # Янтарный цвет для акцента
            tooltip="Настройки Telegram-уведомлений",
            on_click=show_notifications_dialog  # Привязка диалога уведомлений
        )

        # Создание layout компонентов

        # Строка 1: поле ввода + кнопка отправки
        input_row = ft.Row(
            controls=[                      # Размещение элементов ввода
                self.message_input,
                send_button
            ],
            spacing=10,                     # Отступ между элементами
        )

        # Строка 2: Сохранить + Аналитика (равномерное растягивание)
        buttons_row_1 = ft.Row(
            controls=[
                save_button,
                analytics_button
            ],
            spacing=10,                     # Отступ между кнопками
        )

        # Строка 3: Очистить + кнопка Telegram-уведомлений
        buttons_row_2 = ft.Row(
            controls=[
                clear_button,
                notifications_button
            ],
            spacing=10,                     # Отступ между кнопками
        )

        # Создание колонки для элементов управления
        controls_column = ft.Column(
            controls=[                      # Размещение элементов управления
                input_row,
                buttons_row_1,
                buttons_row_2
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # Растягивание по ширине
            spacing=10,                     # Отступ между строками
        )

        # Создание контейнера для баланса
        balance_container = ft.Container(
            content=self.balance_text,            # Размещение текста баланса
            **AppStyles.BALANCE_CONTAINER        # Применение стилей к контейнеру
        )

        # Создание колонки выбора модели
        model_selection = ft.Column(
            controls=[                            # Размещение элементов выбора модели
                self.model_dropdown.search_field,
                self.model_dropdown,
                balance_container
            ],
            **AppStyles.MODEL_SELECTION_COLUMN   # Применение стилей к колонке
        )

        # Создание основной колонки приложения
        self.main_column = ft.Column(
            controls=[                            # Размещение основных элементов
                model_selection,
                self.chat_history,
                controls_column
            ],
            **AppStyles.MAIN_COLUMN               # Применение стилей к главной колонке
        )

        # Добавление основной колонки на страницу
        page.add(self.main_column)

        # Обновляем баланс и проверяем низкий баланс (задание 1)
        self.update_balance()

        # Запуск монитора
        self.monitor.get_metrics()

        # Логирование запуска
        self.logger.info("Приложение запущено")


def main(page: ft.Page):
    """
    Точка входа: сначала показывается окно входа (PIN или ключ),
    после успешной аутентификации открывается чат (задание 2).
    """
    # Кэш нужен до создания приложения - для проверки PIN
    cache = ChatCache()

    async def handle_login(api_key: str, proxy_url: str, page: ft.Page):
        """
        Колбэк успешного входа: заменяет окно входа на чат.

        Args:
            api_key (str): Ключ авторизации openRouter.ai
            proxy_url (str): Адрес прокси из окна входа (пустая строка - напрямую)
            page (ft.Page): Объект страницы приложения
        """
        # Создаем приложение чата с проверенным ключом и прокси
        app = ChatApp(api_key, proxy_url=proxy_url)

        # Заменяем содержимое страницы на чат
        page.controls.clear()
        await app.main(page)

    # Настройка страницы до отображения окна входа
    for key, value in AppStyles.PAGE_SETTINGS.items():
        setattr(page, key, value)
    AppStyles.set_window_size(page)

    # Показываем окно входа
    page.add(LoginView(cache, handle_login))


# Точка входа в приложение
if __name__ == "__main__":
    # В flet 0.86 ft.app заменен на ft.run
    ft.run(main)
