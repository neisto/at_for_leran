import time  # подключаю time чтоб паузы делать и время в логах показывать
import traceback  # это если что-то совсем сломается, чтоб стек ошибки увидеть
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError  # импортирую плейрайт, а то у него ТаймаутЕррор конфликтует с питоновским, переименовал

# тут все города которые надо проверить, взял со скрина и отсортировал по алфавиту
ALL_CITIES = [  # начинаю список городов
    "Абакан", "Анапа", "Аша",  # города на А
    "Барнаул", "Благовещенск", "Бузулук",  # города на Б
    "Волжск", "Вязники", "Вятские Поляны",  # города на В
    "Геленджик", "Георгиевск", "Глазов", "Гуково", "Гусь-Хрустальный",  # города на Г
    "Ейск", "Екатеринбург", "Ессентуки",  # города на Е
    "Златоуст",  # города на З
    "Иваново", "Ижевск", "Ипатово", "Ирбит", "Иркутск", "Искитим",  # города на И
    "Казань", "Каменск-Уральский", "Каменск-Шахтинский", "Камышин", "Каневская",  # города на К (часть 1)
    "Карталы", "Кемерово", "Кимовск", "Киров", "Кирово-Чепецк", "Ковров",  # города на К (часть 2)
    "Кольчугино", "Комсомольск-на-Амуре", "Кореновск", "Краснодар", "Красноярск",  # города на К (часть 3)
    "Кузнецк", "Кумертау", "Курган", "Курганск",  # города на К (часть 4)
    "Лабинск", "Ленинск-Кузнецкий", "Лесосибирск",  # города на Л
    "Магнитогорск", "Майкоп", "Маркс", "Междуреченск", "Миасс", "Минеральные Воды",  # города на М (часть 1)
    "Михайловск", "Можга", "Москва",  # города на М (часть 2)
    "Набережные Челны", "Нагайбак", "Находка", "Невинномысск", "Нефтекамск",  # города на Н (часть 1)
    "Нижневартовск", "Нижнекамск", "Нижний Тагил", "Новокузнецк", "Новосибирск",  # города на Н (часть 2)
    "Новошахтинск",  # города на Н (часть 3)
    "Омск", "Оренбург", "Орск", "Отрадный",  # города на О
    "Партизанск", "Пермь",  # города на П
    "Рыбинск", "Рычск", "Рязань",  # города на Р
    "Салават", "Самара", "Санкт-Петербург", "Сарапул", "Сатка", "Саяногорск",  # города на С (часть 1)
    "Светлоград", "Севастополь", "Североуральск", "Северская", "Сердобск",  # города на С (часть 2)
    "Славянск-на-Кубани", "Советский", "Соликамск", "Сосновка", "Спасск-Дальний",  # города на С (часть 3)
    "Стерлитамак", "Сургут", "Сходня", "Сыктывкар",  # города на С (часть 4)
    "Таганрог", "Тамбов", "Ташкент", "Темрюк", "Томск", "Туймазы", "Тулун", "Тюмень",  # города на Т
    "Улан-Удэ", "Уссурийск", "Усть-Лабинск", "Уфа",  # города на У
    "Чайковский", "Чебаркуль", "Чебоксары", "Челябинск", "Череповец", "Чусовой",  # города на Ч
    "Шилово",  # города на Ш
    "Южноуральск"  # города на Ю
]  # конец списка городов

report = []  # сюда буду складывать результаты проверки, потом из этого отчёт соберу
processed_cities = set()  # сетка для уже обработанных городов, чтоб два раза не гонять один и тот же


def log_message(message):  # простая функция чтоб красиво в консоль писать
    print(f"[{time.strftime('%H:%M:%S')}] {message}")  # время в скобках и само сообщение


def open_city_selector(page):  # функция чтоб открыть модалку выбора города
    """Открываем список городов"""  # описание функции
    try:  # пробуем, вдруг чё пойдёт не так
        city_button = page.locator(  # ищу кнопку которая открывает список городов
            "button[class*='FirstLevelMenu_button__']"  # селектор по куску класса, обычно работает
        ).first  # беру первую найденную
        city_button.scroll_into_view_if_needed()  # прокручиваю к кнопке чтоб точно видно было
        page.wait_for_timeout(500)  # жду полсекунды, а то иногда не кликается
        city_button.click()  # кликаю, модалка открывается
        log_message("✅ Селектор городов открыт")  # пишу что всё ок
        page.wait_for_timeout(2000)  # жду 2 сек пока модалка прогрузится
        return True  # верну тру, значит всё получилось
    except Exception as e:  # если кнопку не нашел или ещё чё
        log_message(f"❌ Не удалось открыть селектор городов: {e}")  # пишу ошибку
        return False  # верну фолс


def select_city(page, city_name):  # функция выбора конкретного города
    """Выбор города по имени из списка ALL_CITIES"""  # описание
    try:  # пробуем
        # 1. сначала открываю модалку
        if not open_city_selector(page):  # если не открылась
            return False  # то дальше смысла нет

        # 2. жду пока в модалке появятся города
        try:  # вложенный трай, чтоб если чё не сломать всё
            page.wait_for_selector(  # жду элемент с классом города
                ".CitiesModal_cityName__W4Od4", timeout=10000  # максимум 10 секунд жду
            )
        except PlaywrightTimeoutError:  # если за 10 сек не дождался
            log_message("⚠️ Модальное окно с городами не загрузилось")  # пишу предупреждение
            return False  # возвращаю фолс

        # 3. теперь ищу сам город
        log_message(f"Ищем город: {city_name}")  # пишу какой ищу

        # способ 1: по классу, самый надёжный
        try:  # пробую
            city_buttons = page.locator(".CitiesModal_cityName__W4Od4").all()  # беру все кнопки городов
            for button in city_buttons:  # перебираю каждую
                if button.inner_text().strip() == city_name:  # если текст совпал точь-в-точь
                    button.scroll_into_view_if_needed()  # прокручиваю
                    page.wait_for_timeout(500)  # жду
                    button.click()  # кликаю
                    log_message(f"✅ Город {city_name} выбран")  # пишу что выбрал
                    page.wait_for_timeout(2000)  # жду пока страница обновится
                    return True  # всё ок
        except Exception:  # если ошибка
            pass  # молча идём дальше

        # способ 2: через XPath, если первый не сработал
        try:  # пробую
            xpath = (  # собираю xpath
                f"//button[contains(@class, 'CitiesModal_cityName__') "  # кнопка с нужным классом
                f"and text()='{city_name}']"  # и точным текстом
            )
            button = page.locator(f"xpath={xpath}").first  # беру первую
            button.wait_for(state="visible", timeout=5000)  # жду чтоб стала видимой
            button.scroll_into_view_if_needed()  # прокручиваю
            page.wait_for_timeout(500)  # жду
            button.click()  # кликаю
            log_message(f"✅ Город {city_name} выбран через XPath")  # пишу
            page.wait_for_timeout(2000)  # жду
            return True  # ок
        except Exception:  # если ошибка
            pass  # дальше

        # способ 3: частичное совпадение, вдруг там пробелы лишние
        try:  # пробую
            city_buttons = page.locator(  # ищу все кнопки городов
                "button[class*='CitiesModal_cityName__']"
            ).all()
            for button in city_buttons:  # перебираю
                if city_name in button.inner_text():  # если название города входит в текст кнопки
                    button.scroll_into_view_if_needed()  # прокручиваю
                    page.wait_for_timeout(500)  # жду
                    button.click()  # кликаю
                    log_message(  # пишу
                        f"✅ Город {city_name} выбран (частичное совпадение)"
                    )
                    page.wait_for_timeout(2000)  # жду
                    return True  # ок
        except Exception:  # если ошибка
            pass  # дальше

        log_message(f"⚠️ Город {city_name} не найден в списке")  # если ни один способ не сработал
        return False  # фолс

    except Exception as e:  # если ошибка на уровне всей функции
        log_message(f"Ошибка при выборе города {city_name}: {e}")  # пишу
        return False  # фолс


def clear_basket_force(page):  # функция чтоб принудительно очистить корзину
    """Принудительная очистка корзины"""  # описание
    log_message("Очистка корзины...")  # пишу что начал

    try:  # пробуем
        page.goto("https://www.leran.pro/basket/", wait_until="domcontentloaded")  # иду в корзину
        page.wait_for_timeout(5000)  # жду 5 сек загрузки

        delete_count = 0  # счётчик удалённых товаров
        max_attempts = 30  # максимум попыток, чтоб не зациклиться

        while delete_count < max_attempts:  # пока не удалил всё или не кончились попытки
            try:  # пробуем
                deleted = False  # флаг, удалил ли товар в этой итерации

                # способ 1: через иконку мусорки
                try:  # пробую
                    delete_icon = page.locator(  # ищу svg с ссылкой на trash
                        "use[href*='trash']"
                    ).first
                    if delete_icon.count() > 0:  # если нашел
                        delete_button = delete_icon.locator(  # ищу родительскую кнопку
                            "xpath=./ancestor::button"
                        ).first
                        delete_button.scroll_into_view_if_needed()  # прокручиваю
                        page.wait_for_timeout(500)  # жду
                        delete_button.click()  # кликаю, товар удаляется
                        deleted = True  # флаг что удалил
                        log_message(  # пишу
                            f"Удален товар #{delete_count + 1}"
                        )
                except Exception:  # если ошибка
                    pass  # дальше

                # способ 2: через JS, если первый не сработал
                if not deleted:  # если товар ещё не удалён
                    js_delete = """  # пишу js скрипт который ищет и кликает
                    () => {
                        const svg = document.querySelector('use[href*="trash"]');  // ищу иконку
                        if (svg) {  // если нашел
                            const btn = svg.closest('button');  // ищу родительскую кнопку
                            if (btn) {  // если кнопка есть
                                btn.click();  // кликаю
                                return true;  // вернул успех
                            }
                        }
                        return false;  // если ничего не нашел
                    }
                    """
                    if page.evaluate(js_delete):  # выполняю js
                        deleted = True  # флаг
                        log_message(f"Удален товар #{delete_count + 1}")  # пишу

                if deleted:  # если товар удалился
                    delete_count += 1  # плюсую счётчик
                    page.wait_for_timeout(1500)  # жду полторы сек перед следующим
                else:  # если не удалился, может корзина пуста
                    # проверяю не пустая ли корзина
                    try:  # пробую
                        empty_check = page.locator(  # ищу текст про пустую корзину
                            "text=/Корзина пуста|пуста/"
                        ).all()
                        if empty_check:  # если нашел
                            log_message("✅ Корзина пуста")  # пишу
                            break  # выхожу из цикла
                    except Exception:  # если ошибка
                        pass  # дальше

                    log_message("✅ Корзина очищена")  # пишу что очищена
                    break  # выхожу

            except Exception as e:  # если ошибка в итерации
                log_message(f"Ошибка при удалении: {e}")  # пишу
                break  # выхожу

        if delete_count == 0:  # если ничё не удалил
            log_message("⚠️ Не удалось удалить товары")  # пишу предупреждение

        return delete_count  # возвращаю сколько удалил

    except Exception as e:  # если ошибка на уровне всей функции
        log_message(f"Ошибка очистки корзины: {e}")  # пишу
        return 0  # верну 0


def add_product_to_cart(page):  # функция чтоб добавить один товар в корзину
    """Добавление товара в корзину"""  # описание
    try:  # пробую
        page.wait_for_selector(  # жду пока появятся карточки товаров
            "div[class*='ProductLineCard']", timeout=10000  # максимум 10 сек
        )

        js = """  # js скрипт для добавления
        () => {
            const product = document.querySelector('div[class*="ProductLineCard"]');  // ищу первую карточку
            if (product) {  // если есть
                const btn = product.querySelector('span[class*="basketText"]');  // ищу кнопку В корзину
                if (btn && btn.textContent.includes('В корзину')) {  // если нашел и текст подходит
                    btn.click();  // кликаю
                    return true;  // успех
                }
                const buttons = product.querySelectorAll('button');  // если span не нашел, ищу кнопки
                for (let b of buttons) {  // перебираю
                    if (b.textContent.includes('В корзину')) {  // если текст подходит
                        b.click();  // кликаю
                        return true;  // успех
                    }
                }
            }
            return false;  // ничего не нашел
        }
        """

        if page.evaluate(js):  # выполняю js
            log_message("✅ Товар добавлен в корзину")  # пишу что добавил
            return True  # ок

        return False  # не получилось

    except Exception as e:  # если ошибка
        log_message(f"Ошибка при добавлении товара: {e}")  # пишу
        return False  # фолс


def process_city(page, city_name):  # функция обработки одного города, тут вся основная логика
    """Обработка одного города"""  # описание
    if city_name in processed_cities:  # если город уже обработан
        return  # выхожу

    log_message(f"\n{'='*50}")  # рисую разделитель
    log_message(f"Обработка города: {city_name}")  # пишу какой город

    try:  # пробую
        # 1. открываю главную
        page.goto("https://www.leran.pro/", wait_until="domcontentloaded")  # иду на главную
        page.wait_for_timeout(3000)  # жду 3 сек

        # 2. выбираю город
        if not select_city(page, city_name):  # если не получилось выбрать
            log_message(f"⚠️ Пропускаем город {city_name}")  # пишу что пропускаю
            return  # выхожу

        # 3. иду в категорию пылесосов
        log_message("Переход в категорию пылесосов...")  # пишу
        page.goto(  # перехожу
            "https://www.leran.pro/cat/tehnika_dlya_doma/pylesosy/",
            wait_until="domcontentloaded",
        )
        page.wait_for_timeout(5000)  # жду 5 сек

        # 4. добавляю товар в корзину
        if not add_product_to_cart(page):  # если не добавился
            log_message("❌ Не удалось добавить товар, пропускаем город")  # пишу
            return  # выхожу

        page.wait_for_timeout(3000)  # жду 3 сек

        # 5. иду в корзину
        log_message("Переход в корзину...")  # пишу
        page.goto("https://www.leran.pro/basket/", wait_until="domcontentloaded")  # перехожу
        page.wait_for_timeout(5000)  # жду 5 сек

        # 6. оформляю заказ
        log_message("Оформление заказа...")  # пишу
        checkout_found = False  # флаг, нашел ли кнопку

        js = """  # js чтоб найти и кликнуть по кнопке оформления
        () => {
            const btns = document.querySelectorAll('button');  // беру все кнопки
            for (let btn of btns) {  // перебираю
                if (btn.textContent.includes('Оформить заказ') ||  // если текст про оформление
                    btn.textContent.includes('Перейти к оформлению')) {  // или про переход
                    btn.click();  // кликаю
                    return true;  // успех
                }
            }
            return false;  // не нашел
        }
        """

        if page.evaluate(js):  # выполняю js
            checkout_found = True  # флаг
            log_message("✅ Кнопка оформления найдена через JS")  # пишу

        if not checkout_found:  # если js не сработал, пробую через плейрайт
            try:  # пробую
                checkout_buttons = page.locator(  # ищу кнопки с текстом
                    "button:has-text('Оформить'), button:has-text('Перейти')"
                ).all()
                for btn in checkout_buttons:  # перебираю
                    txt = btn.inner_text()  # беру текст
                    if "Оформить" in txt or "Перейти" in txt:  # если подходит
                        btn.scroll_into_view_if_needed()  # прокручиваю
                        page.wait_for_timeout(500)  # жду
                        btn.click()  # кликаю
                        checkout_found = True  # флаг
                        log_message("✅ Кнопка оформления найдена")  # пишу
                        break  # выхожу
            except Exception:  # если ошибка
                pass  # дальше

        if not checkout_found:  # если кнопку так и не нашел
            log_message("⚠️ Кнопка оформления не найдена")  # пишу
            page.screenshot(path=f"checkout_error_{city_name}.png")  # делаю скрин для отладки

        page.wait_for_timeout(5000)  # жду 5 сек после оформления

        # 7. проверяю доставку
        log_message("Проверка доставки...")  # пишу
        found_free = False  # флаг, нашел ли бесплатную

        try:  # пробую
            delivery_elements = page.locator("label[class*='Delivery']").all()  # ищу элементы с инфой о доставке

            for el in delivery_elements:  # перебираю
                text = el.inner_text()  # беру текст
                if "Бесплатно" in text:  # если есть слово Бесплатно
                    found_free = True  # флаг
                    break  # выхожу

            if found_free:  # если нашел бесплатную
                report.append(  # добавляю в отчет
                    f"{city_name} - обнаружена бесплатная доставка"
                )
                log_message(f"✅ {city_name} - БЕСПЛАТНАЯ ДОСТАВКА!")  # пишу
            else:  # если нет
                report.append(  # добавляю в отчет
                    f"{city_name} - бесплатная доставка не обнаружена"
                )
                log_message(  # пишу
                    f"❌ {city_name} - бесплатная доставка НЕ обнаружена"
                )

        except Exception as e:  # если ошибка при проверке
            log_message(f"Ошибка проверки доставки: {e}")  # пишу
            report.append(f"{city_name} - ошибка проверки доставки")  # в отчет

        # 8. чищу корзину
        clear_basket_force(page)  # вызываю функцию очистки

        # 9. возвращаюсь на главную
        log_message("Возврат на главную...")  # пишу
        page.goto("https://www.leran.pro/", wait_until="domcontentloaded")  # иду на главную
        page.wait_for_timeout(3000)  # жду 3 сек

        processed_cities.add(city_name)  # отмечаю город как обработанный
        log_message(f"✅ Город {city_name} обработан")  # пишу что всё ок

    except Exception as e:  # если критическая ошибка при обработке города
        log_message(f"❌ ОШИБКА при обработке {city_name}:")  # пишу
        log_message(str(e))  # текст ошибки
        try:  # пробую сделать скрин
            page.screenshot(path=f"error_{city_name}.png")
        except Exception:  # если не получилось
            pass  # дальше


# основной код
def main():  # главная функция, запускает весь процесс
    with sync_playwright() as p:  # запускаю плейрайт синхронно
        browser = p.chromium.launch(  # открываю хром
            headless=False,  # headless=False чтоб глазами видеть что происходит
            args=[  # аргументы
                "--disable-blink-features=AutomationControlled",  # отключаю флаг автоматизации чтоб сайт не спалил бота
            ],
        )
        context = browser.new_context(  # создаю контекст как инкогнито
            user_agent=(  # подставляю юзер-агент обычного хрома
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},  # разрешение экрана
        )
        page = context.new_page()  # новая страница

        # скрываю webdriver флаг
        page.add_init_script(  # скрипт который выполняется до загрузки страницы
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"  # прячу navigator.webdriver
        )

        try:  # пробую
            log_message("🚀 ЗАПУСК СКРИПТА")  # пишу что стартую
            log_message(  # пишу сколько городов
                f"Всего городов для обработки: {len(ALL_CITIES)}"
            )

            # обрабатываю города по алфавиту
            for i, city in enumerate(ALL_CITIES, 1):  # перебираю с индексом с 1
                log_message(f"\n--- Город {i}/{len(ALL_CITIES)} ---")  # пишу номер и название
                process_city(page, city)  # обрабатываю город
                page.wait_for_timeout(3000)  # жду 3 сек перед следующим

            # отчет
            log_message("\n" + "=" * 60)  # разделитель
            log_message("📊 ОТЧЕТ ПО ГОРОДАМ:")  # заголовок
            log_message("=" * 60)  # разделитель
            if report:  # если отчет не пустой
                for line in report:  # перебираю строки
                    log_message(f"  • {line}")  # пишу каждую
            else:  # если пусто
                log_message("  Нет данных для отчета")  # пишу
            log_message("=" * 60)  # разделитель

        except Exception as e:  # если критическая ошибка
            log_message(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")  # пишу
            traceback.print_exc()  # вывожу стек
        finally:  # выполняется всегда
            log_message("🛑 ЗАВЕРШЕНИЕ РАБОТЫ")  # пишу
            page.wait_for_timeout(3000)  # жду 3 сек чтоб успеть увидеть
            context.close()  # закрываю контекст
            browser.close()  # закрываю браузер


if __name__ == "__main__":  # если скрипт запущен напрямую
    main()  # вызываю главную функцию


    # Короче этот скрипт — это бот-тестировщик для сайта leran.pro. Он проверяет, есть ли бесплатная доставка для каждого города из списка при оформлении заказа.