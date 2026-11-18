import time  # Импортируем модуль time для работы с задержками (wait_for_timeout) и форматирования времени в логах
import traceback  # Импортируем traceback для вывода подробного стека ошибок при критических сбоях
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError  # Импортируем Playwright (синхронная версия) и переименовываем TimeoutError для избежания конфликта

# ПОЛНЫЙ СПИСОК ГОРОДОВ (строго по скриншоту, отсортирован по алфавиту)
ALL_CITIES = [  # Начинаем объявление списка городов
    "Абакан", "Анапа", "Аша",  # Города на А
    "Барнаул", "Благовещенск", "Бузулук",  # Города на Б
    "Волжск", "Вязники", "Вятские Поляны",  # Города на В
    "Геленджик", "Георгиевск", "Глазов", "Гуково", "Гусь-Хрустальный",  # Города на Г
    "Ейск", "Екатеринбург", "Ессентуки",  # Города на Е
    "Златоуст",  # Города на З
    "Иваново", "Ижевск", "Ипатово", "Ирбит", "Иркутск", "Искитим",  # Города на И
    "Казань", "Каменск-Уральский", "Каменск-Шахтинский", "Камышин", "Каневская",  # Города на К (часть 1)
    "Карталы", "Кемерово", "Кимовск", "Киров", "Кирово-Чепецк", "Ковров",  # Города на К (часть 2)
    "Кольчугино", "Комсомольск-на-Амуре", "Кореновск", "Краснодар", "Красноярск",  # Города на К (часть 3)
    "Кузнецк", "Кумертау", "Курган", "Курганск",  # Города на К (часть 4)
    "Лабинск", "Ленинск-Кузнецкий", "Лесосибирск",  # Города на Л
    "Магнитогорск", "Майкоп", "Маркс", "Междуреченск", "Миасс", "Минеральные Воды",  # Города на М (часть 1)
    "Михайловск", "Можга", "Москва",  # Города на М (часть 2)
    "Набережные Челны", "Нагайбак", "Находка", "Невинномысск", "Нефтекамск",  # Города на Н (часть 1)
    "Нижневартовск", "Нижнекамск", "Нижний Тагил", "Новокузнецк", "Новосибирск",  # Города на Н (часть 2)
    "Новошахтинск",  # Города на Н (часть 3)
    "Омск", "Оренбург", "Орск", "Отрадный",  # Города на О
    "Партизанск", "Пермь",  # Города на П
    "Рыбинск", "Рычск", "Рязань",  # Города на Р
    "Салават", "Самара", "Санкт-Петербург", "Сарапул", "Сатка", "Саяногорск",  # Города на С (часть 1)
    "Светлоград", "Севастополь", "Североуральск", "Северская", "Сердобск",  # Города на С (часть 2)
    "Славянск-на-Кубани", "Советский", "Соликамск", "Сосновка", "Спасск-Дальний",  # Города на С (часть 3)
    "Стерлитамак", "Сургут", "Сходня", "Сыктывкар",  # Города на С (часть 4)
    "Таганрог", "Тамбов", "Ташкент", "Темрюк", "Томск", "Туймазы", "Тулун", "Тюмень",  # Города на Т
    "Улан-Удэ", "Уссурийск", "Усть-Лабинск", "Уфа",  # Города на У
    "Чайковский", "Чебаркуль", "Чебоксары", "Челябинск", "Череповец", "Чусовой",  # Города на Ч
    "Шилово",  # Города на Ш
    "Южноуральск"  # Города на Ю
]  # Конец списка городов

report = []  # Глобальный список для сбора итогового отчета (например, "город - обнаружена бесплатная доставка")
processed_cities = set()  # Множество (set) для хранения уже обработанных городов, чтобы избежать повторной работы


def log_message(message):  # Вспомогательная функция для красивого вывода сообщений в консоль
    print(f"[{time.strftime('%H:%M:%S')}] {message}")  # Печатаем текущее время в квадратных скобках и само сообщение


def open_city_selector(page):  # Функция для открытия модального окна выбора города
    """Открываем список городов"""  # Докстринг (описание функции)
    try:  # Начинаем блок обработки исключений
        city_button = page.locator(  # Ищем кнопку, открывающую список городов
            "button[class*='FirstLevelMenu_button__']"  # Используем CSS-селектор: кнопка, в классе которой есть эта строка
        ).first  # Берем первый найденный элемент (если их несколько)
        city_button.scroll_into_view_if_needed()  # Прокручиваем страницу к этой кнопке, чтобы она была видна
        page.wait_for_timeout(500)  # Ждем полсекунды для стабильности
        city_button.click()  # Кликаем по кнопке, открывая модалку
        log_message("✅ Селектор городов открыт")  # Логируем успех
        page.wait_for_timeout(2000)  # Ждем 2 секунды, чтобы модалка успела прогрузиться
        return True  # Возвращаем True, если все прошло успешно
    except Exception as e:  # Если произошла ошибка (например, кнопка не найдена)
        log_message(f"❌ Не удалось открыть селектор городов: {e}")  # Логируем ошибку
        return False  # Возвращаем False


def select_city(page, city_name):  # Функция для выбора конкретного города из списка
    """Выбор города по имени из списка ALL_CITIES"""  # Докстринг
    try:  # Блок обработки исключений
        # 1. Открываем селектор городов
        if not open_city_selector(page):  # Вызываем функцию открытия модалки
            return False  # Если не удалось открыть, возвращаем False

        # 2. Ждем загрузки модального окна с городами
        try:  # Вложенный try для ожидания элементов модалки
            page.wait_for_selector(  # Ждем, пока на странице появится хотя бы один элемент с классом города
                ".CitiesModal_cityName__W4Od4", timeout=10000  # Таймаут 10 секунд
            )
        except PlaywrightTimeoutError:  # Если за 10 секунд не дождались
            log_message("⚠️ Модальное окно с городами не загрузилось")  # Логируем предупреждение
            return False  # Возвращаем False

        # 3. Ищем город в модальном окне
        log_message(f"Ищем город: {city_name}")  # Логируем начало поиска

        # Способ 1: через класс CitiesModal_cityName__W4Od4 (самый надежный)
        try:  # Пытаемся найти точное совпадение по тексту
            city_buttons = page.locator(".CitiesModal_cityName__W4Od4").all()  # Получаем список всех кнопок с городами
            for button in city_buttons:  # Перебираем каждую кнопку
                if button.inner_text().strip() == city_name:  # Если текст кнопки (очищенный от пробелов) совпадает с искомым
                    button.scroll_into_view_if_needed()  # Прокручиваем к ней
                    page.wait_for_timeout(500)  # Ждем
                    button.click()  # Кликаем
                    log_message(f"✅ Город {city_name} выбран")  # Логируем успех
                    page.wait_for_timeout(2000)  # Ждем обновления страницы
                    return True  # Возвращаем True
        except Exception:  # Если возникла ошибка
            pass  # Игнорируем и переходим к следующему способу

        # Способ 2: через XPath с классом (если первый способ не сработал)
        try:  # Пытаемся найти через XPath
            xpath = (  # Формируем XPath-запрос
                f"//button[contains(@class, 'CitiesModal_cityName__') "  # Ищем кнопку, в классе которой есть нужная строка
                f"and text()='{city_name}']"  # И текст которой точно равен названию города
            )
            button = page.locator(f"xpath={xpath}").first  # Берем первый элемент по XPath
            button.wait_for(state="visible", timeout=5000)  # Ждем, пока он станет видимым (5 сек)
            button.scroll_into_view_if_needed()  # Прокручиваем
            page.wait_for_timeout(500)  # Ждем
            button.click()  # Кликаем
            log_message(f"✅ Город {city_name} выбран через XPath")  # Логируем
            page.wait_for_timeout(2000)  # Ждем
            return True  # Возвращаем True
        except Exception:  # Если ошибка
            pass  # Игнорируем

        # Способ 3: через частичное совпадение (если в названии есть лишние символы)
        try:  # Пытаемся найти по вхождению подстроки
            city_buttons = page.locator(  # Ищем все кнопки с классом города
                "button[class*='CitiesModal_cityName__']"
            ).all()
            for button in city_buttons:  # Перебираем
                if city_name in button.inner_text():  # Если название города является частью текста кнопки
                    button.scroll_into_view_if_needed()  # Прокручиваем
                    page.wait_for_timeout(500)  # Ждем
                    button.click()  # Кликаем
                    log_message(  # Логируем
                        f"✅ Город {city_name} выбран (частичное совпадение)"
                    )
                    page.wait_for_timeout(2000)  # Ждем
                    return True  # Возвращаем True
        except Exception:  # Если ошибка
            pass  # Игнорируем

        log_message(f"⚠️ Город {city_name} не найден в списке")  # Если ни один способ не сработал
        return False  # Возвращаем False

    except Exception as e:  # Если произошла ошибка на уровне всей функции
        log_message(f"Ошибка при выборе города {city_name}: {e}")  # Логируем
        return False  # Возвращаем False


def clear_basket_force(page):  # Функция для принудительной очистки корзины (удаления всех товаров)
    """Принудительная очистка корзины"""  # Докстринг
    log_message("Очистка корзины...")  # Логируем начало

    try:  # Блок обработки исключений
        page.goto("https://www.leran.pro/basket/", wait_until="domcontentloaded")  # Переходим на страницу корзины
        page.wait_for_timeout(5000)  # Ждем 5 секунд загрузки

        delete_count = 0  # Счетчик удаленных товаров
        max_attempts = 30  # Максимальное количество попыток удаления (защита от бесконечного цикла)

        while delete_count < max_attempts:  # Пока не удалили максимум или не очистили корзину
            try:  # Вложенный try для каждой попытки
                deleted = False  # Флаг: удалось ли удалить товар в этой итерации

                # Способ 1: через use[href*="trash"]
                try:  # Пытаемся найти иконку корзины (мусорку)
                    delete_icon = page.locator(  # Ищем SVG-иконку с ссылкой на "trash"
                        "use[href*='trash']"
                    ).first
                    if delete_icon.count() > 0:  # Если такая иконка есть на странице
                        delete_button = delete_icon.locator(  # Находим родительскую кнопку для этой иконки
                            "xpath=./ancestor::button"
                        ).first
                        delete_button.scroll_into_view_if_needed()  # Прокручиваем к кнопке
                        page.wait_for_timeout(500)  # Ждем
                        delete_button.click()  # Кликаем (удаляем товар)
                        deleted = True  # Флаг успеха
                        log_message(  # Логируем
                            f"Удален товар #{delete_count + 1}"
                        )
                except Exception:  # Если ошибка
                    pass  # Игнорируем

                # Способ 2: через JavaScript (если первый способ не сработал)
                if not deleted:  # Если товар еще не удален
                    js_delete = """  # Пишем JS-скрипт для поиска и клика по кнопке удаления
                    () => {
                        const svg = document.querySelector('use[href*="trash"]');  // Ищем иконку
                        if (svg) {  // Если нашли
                            const btn = svg.closest('button');  // Находим родительскую кнопку
                            if (btn) {  // Если кнопка есть
                                btn.click();  // Кликаем
                                return true;  // Возвращаем успех
                            }
                        }
                        return false;  // Если ничего не нашли
                    }
                    """
                    if page.evaluate(js_delete):  # Выполняем JS на странице
                        deleted = True  # Флаг успеха
                        log_message(f"Удален товар #{delete_count + 1}")  # Логируем

                if deleted:  # Если товар был удален
                    delete_count += 1  # Увеличиваем счетчик
                    page.wait_for_timeout(1500)  # Ждем 1.5 секунды перед следующей попыткой
                else:  # Если товар не удален (возможно, корзина пуста)
                    # Проверяем, пуста ли корзина
                    try:  # Ищем текст "Корзина пуста"
                        empty_check = page.locator(
                            "text=/Корзина пуста|пуста/"
                        ).all()
                        if empty_check:  # Если нашли
                            log_message("✅ Корзина пуста")  # Логируем
                            break  # Выходим из цикла
                    except Exception:  # Если ошибка
                        pass  # Игнорируем

                    log_message("✅ Корзина очищена")  # Логируем, что очищена
                    break  # Выходим из цикла

            except Exception as e:  # Если ошибка в итерации
                log_message(f"Ошибка при удалении: {e}")  # Логируем
                break  # Выходим из цикла

        if delete_count == 0:  # Если не удалили ни одного товара
            log_message("⚠️ Не удалось удалить товары")  # Логируем предупреждение

        return delete_count  # Возвращаем количество удаленных товаров

    except Exception as e:  # Если ошибка на уровне всей функции
        log_message(f"Ошибка очистки корзины: {e}")  # Логируем
        return 0  # Возвращаем 0


def add_product_to_cart(page):  # Функция для добавления одного товара в корзину
    """Добавление товара в корзину"""  # Докстринг
    try:  # Блок обработки исключений
        page.wait_for_selector(  # Ждем, пока на странице появятся карточки товаров
            "div[class*='ProductLineCard']", timeout=10000  # Таймаут 10 секунд
        )

        js = """  # Пишем JS-скрипт для добавления товара
        () => {
            const product = document.querySelector('div[class*="ProductLineCard"]');  // Находим первую карточку товара
            if (product) {  // Если карточка есть
                const btn = product.querySelector('span[class*="basketText"]');  // Ищем кнопку "В корзину" внутри карточки
                if (btn && btn.textContent.includes('В корзину')) {  // Если кнопка найдена и содержит нужный текст
                    btn.click();  // Кликаем
                    return true;  // Возвращаем успех
                }
                const buttons = product.querySelectorAll('button');  // Если span не нашли, ищем все кнопки внутри карточки
                for (let b of buttons) {  // Перебираем кнопки
                    if (b.textContent.includes('В корзину')) {  // Если текст кнопки подходит
                        b.click();  // Кликаем
                        return true;  // Возвращаем успех
                    }
                }
            }
            return false;  // Если ничего не нашли
        }
        """

        if page.evaluate(js):  # Выполняем JS на странице
            log_message("✅ Товар добавлен в корзину")  # Логируем успех
            return True  # Возвращаем True

        return False  # Если не удалось, возвращаем False

    except Exception as e:  # Если ошибка
        log_message(f"Ошибка при добавлении товара: {e}")  # Логируем
        return False  # Возвращаем False


def process_city(page, city_name):  # Функция для обработки одного города (основная логика)
    """Обработка одного города"""  # Докстринг
    if city_name in processed_cities:  # Если город уже обработан
        return  # Выходим из функции

    log_message(f"\n{'='*50}")  # Логируем разделитель
    log_message(f"Обработка города: {city_name}")  # Логируем название города

    try:  # Блок обработки исключений
        # 1. Открываем главную
        page.goto("https://www.leran.pro/", wait_until="domcontentloaded")  # Переходим на главную страницу
        page.wait_for_timeout(3000)  # Ждем 3 секунды

        # 2. Выбираем город
        if not select_city(page, city_name):  # Вызываем функцию выбора города
            log_message(f"⚠️ Пропускаем город {city_name}")  # Если не удалось выбрать, логируем
            return  # Выходим из функции (пропускаем город)

        # 3. Переходим в категорию пылесосов
        log_message("Переход в категорию пылесосов...")  # Логируем
        page.goto(  # Переходим на страницу категории
            "https://www.leran.pro/cat/tehnika_dlya_doma/pylesosy/",
            wait_until="domcontentloaded",
        )
        page.wait_for_timeout(5000)  # Ждем 5 секунд загрузки

        # 4. Добавляем товар в корзину
        if not add_product_to_cart(page):  # Вызываем функцию добавления товара
            log_message("❌ Не удалось добавить товар, пропускаем город")  # Если не удалось, логируем
            return  # Выходим

        page.wait_for_timeout(3000)  # Ждем 3 секунды

        # 5. Переходим в корзину
        log_message("Переход в корзину...")  # Логируем
        page.goto("https://www.leran.pro/basket/", wait_until="domcontentloaded")  # Переходим в корзину
        page.wait_for_timeout(5000)  # Ждем 5 секунд

        # 6. Оформляем заказ
        log_message("Оформление заказа...")  # Логируем
        checkout_found = False  # Флаг: найдена ли кнопка оформления

        js = """  # JS-скрипт для поиска и клика по кнопке оформления заказа
        () => {
            const btns = document.querySelectorAll('button');  // Находим все кнопки
            for (let btn of btns) {  // Перебираем
                if (btn.textContent.includes('Оформить заказ') ||  // Если текст содержит "Оформить заказ"
                    btn.textContent.includes('Перейти к оформлению')) {  // Или "Перейти к оформлению"
                    btn.click();  // Кликаем
                    return true;  // Возвращаем успех
                }
            }
            return false;  // Если не нашли
        }
        """

        if page.evaluate(js):  # Выполняем JS
            checkout_found = True  # Устанавливаем флаг
            log_message("✅ Кнопка оформления найдена через JS")  # Логируем

        if not checkout_found:  # Если JS не сработал, пробуем через Playwright
            try:  # Пытаемся найти кнопку
                checkout_buttons = page.locator(  # Ищем кнопки с текстом
                    "button:has-text('Оформить'), button:has-text('Перейти')"
                ).all()
                for btn in checkout_buttons:  # Перебираем
                    txt = btn.inner_text()  # Получаем текст
                    if "Оформить" in txt or "Перейти" in txt:  # Если текст подходит
                        btn.scroll_into_view_if_needed()  # Прокручиваем
                        page.wait_for_timeout(500)  # Ждем
                        btn.click()  # Кликаем
                        checkout_found = True  # Устанавливаем флаг
                        log_message("✅ Кнопка оформления найдена")  # Логируем
                        break  # Выходим из цикла
            except Exception:  # Если ошибка
                pass  # Игнорируем

        if not checkout_found:  # Если кнопка так и не найдена
            log_message("⚠️ Кнопка оформления не найдена")  # Логируем
            page.screenshot(path=f"checkout_error_{city_name}.png")  # Делаем скриншот для отладки

        page.wait_for_timeout(5000)  # Ждем 5 секунд после оформления

        # 7. Проверяем доставку
        log_message("Проверка доставки...")  # Логируем
        found_free = False  # Флаг: найдена ли бесплатная доставка

        try:  # Пытаемся найти информацию о доставке
            delivery_elements = page.locator("label[class*='Delivery']").all()  # Ищем все элементы с классом Delivery

            for el in delivery_elements:  # Перебираем
                text = el.inner_text()  # Получаем текст
                if "Бесплатно" in text:  # Если есть слово "Бесплатно"
                    found_free = True  # Устанавливаем флаг
                    break  # Выходим

            if found_free:  # Если нашли бесплатную доставку
                report.append(  # Добавляем в отчет
                    f"{city_name} - обнаружена бесплатная доставка"
                )
                log_message(f"✅ {city_name} - БЕСПЛАТНАЯ ДОСТАВКА!")  # Логируем
            else:  # Если не нашли
                report.append(  # Добавляем в отчет
                    f"{city_name} - бесплатная доставка не обнаружена"
                )
                log_message(  # Логируем
                    f"❌ {city_name} - бесплатная доставка НЕ обнаружена"
                )

        except Exception as e:  # Если ошибка при проверке
            log_message(f"Ошибка проверки доставки: {e}")  # Логируем
            report.append(f"{city_name} - ошибка проверки доставки")  # Добавляем в отчет

        # 8. Очищаем корзину
        clear_basket_force(page)  # Вызываем функцию очистки корзины

        # 9. Возвращаемся на главную
        log_message("Возврат на главную...")  # Логируем
        page.goto("https://www.leran.pro/", wait_until="domcontentloaded")  # Переходим на главную
        page.wait_for_timeout(3000)  # Ждем 3 секунды

        processed_cities.add(city_name)  # Добавляем город в множество обработанных
        log_message(f"✅ Город {city_name} обработан")  # Логируем успех

    except Exception as e:  # Если произошла критическая ошибка при обработке города
        log_message(f"❌ ОШИБКА при обработке {city_name}:")  # Логируем
        log_message(str(e))  # Логируем текст ошибки
        try:  # Пытаемся сделать скриншот
            page.screenshot(path=f"error_{city_name}.png")
        except Exception:  # Если не удалось
            pass  # Игнорируем


# Основной код
def main():  # Главная функция, запускающая весь процесс
    with sync_playwright() as p:  # Запускаем Playwright в синхронном режиме
        browser = p.chromium.launch(  # Запускаем браузер Chromium
            headless=False,  # headless=False означает, что мы видим окно браузера (удобно для отладки)
            args=[  # Аргументы запуска
                "--disable-blink-features=AutomationControlled",  # Отключаем флаг автоматизации (чтобы сайт не понял, что это бот)
            ],
        )
        context = browser.new_context(  # Создаем новый контекст браузера (как новое окно инкогнито)
            user_agent=(  # Подменяем User-Agent на обычный браузер Chrome
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},  # Устанавливаем разрешение экрана
        )
        page = context.new_page()  # Создаем новую страницу в контексте

        # Скрываем webdriver-флаг
        page.add_init_script(  # Добавляем скрипт, который выполняется до загрузки страницы
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"  # Скрываем флаг navigator.webdriver
        )

        try:  # Блок обработки исключений
            log_message("🚀 ЗАПУСК СКРИПТА")  # Логируем начало
            log_message(  # Логируем количество городов
                f"Всего городов для обработки: {len(ALL_CITIES)}"
            )

            # Обрабатываем города по алфавиту
            for i, city in enumerate(ALL_CITIES, 1):  # Перебираем все города с индексом (начиная с 1)
                log_message(f"\n--- Город {i}/{len(ALL_CITIES)} ---")  # Логируем номер и название города
                process_city(page, city)  # Вызываем функцию обработки города
                page.wait_for_timeout(3000)  # Ждем 3 секунды перед следующим городом

            # Отчет
            log_message("\n" + "=" * 60)  # Логируем разделитель
            log_message("📊 ОТЧЕТ ПО ГОРОДАМ:")  # Логируем заголовок отчета
            log_message("=" * 60)  # Логируем разделитель
            if report:  # Если отчет не пуст
                for line in report:  # Перебираем строки отчета
                    log_message(f"  • {line}")  # Логируем каждую строку
            else:  # Если отчет пуст
                log_message("  Нет данных для отчета")  # Логируем
            log_message("=" * 60)  # Логируем разделитель

        except Exception as e:  # Если произошла критическая ошибка
            log_message(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")  # Логируем
            traceback.print_exc()  # Выводим полный стек ошибки
        finally:  # Блок, который выполняется всегда (даже если была ошибка)
            log_message("🛑 ЗАВЕРШЕНИЕ РАБОТЫ")  # Логируем завершение
            page.wait_for_timeout(3000)  # Ждем 3 секунды, чтобы вы увидели результат
            context.close()  # Закрываем контекст браузера
            browser.close()  # Закрываем сам браузер


if __name__ == "__main__":  # Если скрипт запущен напрямую (а не импортирован как модуль)
    main()  # Вызываем главную функцию



    # Этот скрипт представляет собой автоматизированного бота-тестировщика для интернет-магазина leran.pro. Его основная задача — проверить, доступна ли бесплатная доставка для каждого города из заданного списка при оформлении заказа.