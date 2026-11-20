import time                         # подключаю time чтобы паузы делать и время в логах показывать
import traceback                    # это на случай если что-то совсем сломается, чтоб стек ошибки увидеть
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# ставлю алиас для TimeoutError чтобы не путался со встроенным питоновским

# цвета для терминала чтобы красным выделять проблемные города, обычный ANSI код
RED = "\033[91m"      # красный цвет текста
GREEN = "\033[92m"    # зелёный, для городов где всё ок (на всякий, пригодится)
RESET = "\033[0m"     # сброс цвета обратно в обычный

# тут все города которые надо проверить, взял из прошлого скрипта, ничего не менял
ALL_CITIES = [
    "Абакан", "Анапа", "Аша", "Барнаул", "Благовещенск", "Бузулук",
    "Волжск", "Вязники", "Вятские Поляны", "Геленджик", "Георгиевск", "Глазов",
    "Гуково", "Гусь-Хрустальный", "Ейск", "Екатеринбург", "Ессентуки", "Златоуст",
    "Иваново", "Ижевск", "Ипатово", "Ирбит", "Иркутск", "Искитим", "Казань",
    "Каменск-Уральский", "Каменск-Шахтинский", "Камышин", "Каневская", "Карталы",
    "Кемерово", "Кимовск", "Киров", "Кирово-Чепецк", "Ковров", "Кольчугино",
    "Комсомольск-на-Амуре", "Кореновск", "Краснодар", "Красноярск", "Кузнецк",
    "Кумертау", "Курган", "Курганск", "Лабинск", "Ленинск-Кузнецкий",
    "Лесосибирск", "Магнитогорск", "Майкоп", "Маркс", "Междуреченск", "Миасс",
    "Минеральные Воды", "Михайловск", "Можга", "Москва", "Набережные Челны",
    "Нагайбак", "Находка", "Невинномысск", "Нефтекамск", "Нижневартовск",
    "Нижнекамск", "Нижний Тагил", "Новокузнецк", "Новосибирск", "Новошахтинск",
    "Омск", "Оренбург", "Орск", "Отрадный", "Партизанск", "Пермь", "Рыбинск",
    "Рычск", "Рязань", "Салават", "Самара", "Санкт-Петербург", "Сарапул",
    "Сатка", "Саяногорск", "Светлоград", "Севастополь", "Североуральск",
    "Северская", "Сердобск", "Славянск-на-Кубани", "Советский", "Соликамск",
    "Сосновка", "Спасск-Дальний", "Стерлитамак", "Сургут", "Сходня", "Сыктывкар",
    "Таганрог", "Тамбов", "Ташкент", "Темрюк", "Томск", "Туймазы", "Тулун",
    "Тюмень", "Улан-Удэ", "Уссурийск", "Усть-Лабинск", "Уфа", "Чайковский",
    "Чебаркуль", "Чебоксары", "Челябинск", "Череповец", "Чусовой", "Шилово",
    "Южноуральск"
]

# сюда буду складывать результаты проверки, потом из этого отчёт соберу
report = []

# простая функция логирования, чтоб каждое сообщение с временем было
def log_message(message):
    # печатаю время и само сообщение
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

# функция выбора города, взял из старого скрипта почти без изменений, она рабочая
def select_city(page, city_name):
    try:
        # ищу кнопку открытия списка городов, селекторов несколько на случай если вёрстка поменяется
        city_button = page.locator(
            "button[class*='FirstLevelMenu_button__'], "
            "button[class*='city'], "
            "button:has-text('Москва'), "
            "button:has-text('Абакан')"
        ).first
        # прокручиваю к кнопке чтоб точно видно было
        city_button.scroll_into_view_if_needed()
        # небольшая пауза, а то иногда клик не срабатывает
        page.wait_for_timeout(500)
        # кликаю чтоб модалка открылась
        city_button.click()
        # жду 2 сек пока модалка прогрузится
        page.wait_for_timeout(2000)

        # жду пока в модалке появятся кнопки городов
        page.wait_for_selector(".CitiesModal_cityName__W4Od4", timeout=8000)

        # беру все кнопки городов
        buttons = page.locator(".CitiesModal_cityName__W4Od4").all()
        # сначала ищу точное совпадение названия
        for button in buttons:
            if button.inner_text().strip() == city_name:
                button.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                button.click()
                # жду 3 сек чтоб данные под город перезагрузились
                page.wait_for_timeout(3000)
                return True

        # если точного нет, пробую частичное совпадение (вдруг там пробелы лишние)
        for button in buttons:
            if city_name in button.inner_text():
                button.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                button.click()
                page.wait_for_timeout(3000)
                return True

        # если не нашли город, пишу в лог
        log_message(f"⚠️ Город {city_name} не найден в списке")
        # закрываю модалку чтоб не мешала
        page.keyboard.press("Escape")
        return False

    except Exception as e:
        # если что-то пошло не так, ловлю ошибку
        log_message(f"Ошибка при выборе города {city_name}: {e}")
        # пытаюсь закрыть модалку, вдруг она осталась висеть
        try:
            page.keyboard.press("Escape")
        except:
            pass
        return False

# вот эта функция новая — она заходит в раздел акций и вытаскивает количество из заголовка
def get_actions_count(page):
    # пробую открыть страницу акций, жду загрузку dom
    try:
        page.goto("https://www.leran.pro/actions/", wait_until="domcontentloaded")
    except Exception as e:
        # если не открылось — пишу ошибку и возвращаю None
        log_message(f"Не смог открыть страницу акций: {e}")
        return None

    # даю странице 4 секунды, чтоб всё подгрузилось, а то акции часто подгружаются ajax-ом
    page.wait_for_timeout(4000)

    # тут буду искать заголовок с количеством акций
    # пробую несколько вариантов селекторов, вдруг у них классы поменяются
    possible_selectors = [
        "h1",                                  # часто заголовок это h1
        "h2",                                  # или h2
        "div[class*='title']",                 # или див с классом содержащим title
        "div[class*='Title']",                 # с большой буквы тоже пробую
        "span[class*='count']",                # может счётчик отдельным элементом
        "span[class*='Count']"
    ]

    # перебираю селекторы по очереди
    for selector in possible_selectors:
        try:
            # беру все элементы по селектору
            elements = page.locator(selector).all()
            # прохожу по каждому
            for el in elements:
                try:
                    # беру текст элемента
                    text = el.inner_text()
                except:
                    # если текст не читается — пропускаю
                    continue
                # если в тексте есть слово "акци" (акция/акции/акций)
                if text and "акци" in text.lower():
                    # пробую вытащить из текста число
                    # ищу цифры в строке
                    import re
                    numbers = re.findall(r"\d+", text)
                    # если нашли хоть одно число
                    if numbers:
                        # беру первое и возвращаю как int
                        return int(numbers[0])
        except Exception:
            # если селектор битый — просто иду дальше
            continue

    # если по заголовкам не нашли, пробую другой вариант — искать по всему body
    try:
        body_text = page.locator("body").inner_text()
        import re
        # ищу паттерны вида "акций: 5", "акции (5)", "5 акций" и т.п.
        patterns = [
            r"акци[ийя][^\d]{0,30}(\d+)",       # акций ... 5
            r"(\d+)\s*акци",                     # 5 акций
        ]
        for pat in patterns:
            m = re.search(pat, body_text.lower())
            if m:
                return int(m.group(1))
    except Exception:
        pass

    # если вообще ничего не нашли — возвращаю None
    return None

# главная функция
def main():
    # запускаю playwright синхронно
    with sync_playwright() as p:
        # открываю хром, headless=False чтоб глазами видеть что происходит
        browser = p.chromium.launch(
            headless=False,
            # отключаю флаг автоматизации чтоб сайт не спалил бота
            args=["--disable-blink-features=AutomationControlled"],
        )
        # создаю контекст как будто инкогнито
        context = browser.new_context(
            # подставляю юзер-агент обычного хрома
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            # разрешение как у обычного пользователя
            viewport={"width": 1920, "height": 1080},
        )
        # новая страница
        page = context.new_page()
        # скрываю navigator.webdriver чтоб сайт не понял что это автоматизация
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # основной try/finally чтоб браузер точно закрылся
        try:
            # пишу что стартуем
            log_message("🚀 ЗАПУСК СКРИПТА ПРОВЕРКИ АКЦИЙ")

            # открываю главную страницу
            page.goto("https://www.leran.pro/", wait_until="domcontentloaded")
            # жду 3 сек
            page.wait_for_timeout(3000)

            # иду по всем городам
            log_message(f"Начинаю проверку городов, всего {len(ALL_CITIES)} шт.")

            # enumerate с 1 чтоб номер города был человеческий
            for idx, city in enumerate(ALL_CITIES, 1):
                # пишу какой сейчас город и какой по счёту
                log_message(f"\n--- {idx}/{len(ALL_CITIES)}: {city} ---")

                # для каждого города (даже первого) вызываю select_city
                # потому что мы теперь каждый раз ходим на главную и выбираем заново
                # сначала открываю главную чтоб кнопка города точно была
                try:
                    page.goto("https://www.leran.pro/", wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                except Exception as e:
                    log_message(f"Не открылась главная: {e}")
                    report.append(f"{city} - не удалось открыть главную")
                    continue

                # выбираю город
                if not select_city(page, city):
                    # если не получилось — в отчёт и дальше
                    report.append(f"{city} - не удалось выбрать город")
                    continue

                # теперь захожу в раздел акций и смотрю сколько их
                count = get_actions_count(page)

                # если None — значит не смогли распарсить
                if count is None:
                    # пишу в отчёт что не смогли определить
                    log_message(f"  ⚠️ {city} - не удалось определить количество акций")
                    report.append(f"{city} - не удалось определить количество акций")
                    continue

                # если акций 0 — это плохо, выделяю красным
                if count == 0:
                    # красным в консоль
                    log_message(f"{RED}  ❌ {city} - АКЦИЙ НЕТ (0){RESET}")
                    # в отчёт тоже добавлю пометку что 0
                    report.append(f"{city} - 0 акций")
                else:
                    # если акции есть — просто пишу сколько
                    log_message(f"  ✅ {city} - акций: {count}")

            # тут вывожу итоговый отчёт
            log_message("\n" + "=" * 60)
            log_message("📊 ИТОГОВЫЙ ОТЧЁТ ПО АКЦИЯМ:")
            log_message("=" * 60)

            # если в отчёте что-то есть
            if report:
                # печатаю каждую строку, но строки где "0 акций" выделяю красным
                for line in report:
                    if "0 акций" in line:
                        # красным выделяю
                        log_message(f"{RED}  • {line}{RESET}")
                    else:
                        # остальное обычным
                        log_message(f"  • {line}")
            else:
                # если пусто — значит всё ок
                log_message("  Во всех городах есть акции!")

            log_message("=" * 60)

        except Exception as e:
            # если критическая ошибка — ловлю, пишу и печатаю стек
            log_message(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            traceback.print_exc()
        finally:
            # тут всегда закрываю браузер
            log_message("🛑 Завершение работы")
            # пауза 3 сек чтоб успеть увидеть результат
            page.wait_for_timeout(3000)
            # закрываю контекст
            context.close()
            # закрываю браузер
            browser.close()

# если скрипт запущен напрямую — вызываю main
if __name__ == "__main__":
    main()
    