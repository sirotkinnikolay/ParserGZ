import os
import asyncio
import time
from contextlib import asynccontextmanager
from asyncio import Semaphore
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()


class AsyncDriverPool:
    """
    Асинхронный пул Selenium WebDriver для переиспользования драйверов
    """

    def __init__(self, pool_size: int = None):
        self.pool_size = pool_size or int(os.getenv("DRIVER_POOL_SIZE", "2"))
        self._drivers: List[Chrome] = []  # Список доступных драйверов
        self._semaphore = Semaphore(self.pool_size)  # Ограничивает одновременный доступ
        self._lock = asyncio.Lock()  # Защищает инициализацию от race conditions
        self._initialized = False
        self._initialization_task: Optional[asyncio.Task] = None  # Фоновая задача инициализации
        self._drivers_creation_tasks: List[asyncio.Task] = []  # Задачи создания драйверов

        self.selenium_remote = os.getenv("SELENIUM_REMOTE", "true").lower() in ("1", "true", "yes")
        self.selenium_url = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")
        # Кол-во попыток при создании одного драйвера (полезно при старте, когда selenium ещё поднимается)
        self._create_retries = int(os.getenv("DRIVER_CREATE_RETRIES", "10"))
        self._create_retry_delay = float(os.getenv("DRIVER_CREATE_RETRY_DELAY", "5.0"))

    async def initialize(self):
        """
        Асинхронная инициализация пула драйверов
        Вызывается при старте приложения - запускается в фоне и не блокирует старт сервера
        """
        if self._initialized or self._initialization_task:
            return

        # Запускаем инициализацию в фоне, не блокируя запуск приложения
        self._initialization_task = asyncio.create_task(self._initialize_background())
        print("🔄 Фоновая инициализация пула драйверов запущена...")

    async def _initialize_background(self):
        """Фоновая инициализация пула"""
        async with self._lock:
            if not self._initialized:
                print(f"🔄 Инициализация пула из {self.pool_size} драйверов в фоне...")

                # Ждем доступность Selenium если используем remote
                if self.selenium_remote:
                    await self._wait_for_selenium()

                # Запускаем создание всех драйверов параллельно
                await self._create_all_drivers_parallel()

                self._initialized = True
                print(f"✅ Пул драйверов инициализирован ({len(self._drivers)}/{self.pool_size} драйверов)")

    async def _create_all_drivers_parallel(self):
        """Создает все драйверы параллельно"""
        tasks = []
        for i in range(self.pool_size):
            task = asyncio.create_task(self._create_single_driver(i))
            tasks.append(task)
            # Небольшая задержка между запуском задач чтобы не перегрузить Selenium
            await asyncio.sleep(0.5)

        # Ждем завершения всех задач
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем результаты
        successful = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Не удалось создать драйвер {i + 1}: {result}")
            else:
                successful += 1

        print(f"✅ {successful}/{self.pool_size} драйверов создано")

    async def _create_single_driver(self, index: int):
        """Создает один драйвер"""
        try:
            driver = await asyncio.get_event_loop().run_in_executor(
                None, self._create_driver_with_retries
            )
            self._drivers.append(driver)
            print(f"✅ Создан драйвер {index + 1}/{self.pool_size}")
            return driver
        except Exception as e:
            print(f"❌ Ошибка создания драйвера {index + 1}: {e}")
            raise

    async def _wait_for_selenium(self, timeout: int = 60):
        """Ожидает пока Selenium станет доступен"""
        import requests
        from requests.exceptions import RequestException

        print("⏳ Ожидание доступности Selenium...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.selenium_url}/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('value', {}).get('ready', False):
                        print("✅ Selenium готов к работе")
                        return
            except RequestException:
                pass

            print("⏳ Selenium недоступен, повторная попытка через 3 секунды...")
            await asyncio.sleep(3)

        print("⚠️ Selenium не стал доступен в течение таймаута, продолжаем с ретраями...")

    def _create_driver_with_retries(self) -> Chrome:
        last_exc: Optional[Exception] = None
        for i in range(1, self._create_retries + 1):
            try:
                return self._create_driver()
            except Exception as e:
                last_exc = e
                print(f"⚠️ Попытка {i}/{self._create_retries} создать драйвер не удалась: {e}")
                if i < self._create_retries:
                    time.sleep(self._create_retry_delay)
        # если все ретраи не помогли — бросаем последнее исключение
        raise last_exc if last_exc is not None else RuntimeError("Unknown error creating driver")

    def _create_driver(self) -> Chrome:
        """
        Синхронное создание и настройка Chrome драйвера
        Выполняется в отдельном потоке
        """
        try:
            chrome_options = Options()
            # Базовые опции для headless режима
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--log-level=3")

            # Опции для скрытия автоматизации (частично)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            if self.selenium_remote:
                # Подключаемся к уже запущенному selenium/standalone-chrome (в другом контейнере)
                driver = webdriver.Remote(command_executor=self.selenium_url, options=chrome_options)
            else:
                # Локальный режим: автоматическое управление драйвером (ChromeDriverManager)
                service = Service(ChromeDriverManager().install())
                driver = Chrome(service=service, options=chrome_options)

            try:
                driver.set_window_size(1366, 768)
            except Exception:
                # Игнорируем ошибки установки размеров в headless окружении
                pass

            # Неявное ожидание (секунды)
            implicit_wait = int(os.getenv("DRIVER_IMPLICIT_WAIT", "5"))
            try:
                driver.implicitly_wait(implicit_wait)
            except Exception:
                pass

            # Скрытие WebDriver фактора, если возможно
            try:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception:
                # Игнорируем — в некоторых remote-серверных конфигурациях выполнение скрипта может быть недоступно до загрузки страницы
                pass

            return driver

        except Exception as e:
            # Более информативный лог
            print(f"❌ Ошибка создания драйвера: {e}")
            # Если в локальном режиме — вероятно отсутствует бинарь Chrome или зависимости => сообщаем
            if not self.selenium_remote:
                print(
                    "   -> Локальный режим включён (SELENIUM_REMOTE=false). Убедитесь, что в контейнере установлен Google Chrome и его зависимости.")
            else:
                print(
                    f"   -> Remote режим: пытались подключиться к {self.selenium_url}. Убедитесь, что selenium standalone доступен.")
            raise

    @asynccontextmanager
    async def get_driver(self):
        """
        Асинхронный контекстный менеджер для получения драйвера из пула
        """
        # Если пул еще не инициализирован, создаем драйвер по требованию
        if not self._initialized and not self._drivers:
            await self._create_driver_on_demand()

        # Запускаем фоновую инициализацию если еще не запущена
        if not self._initialization_task and not self._initialized:
            await self.initialize()

        # Ждем доступный драйвер (ограничено семафором)
        await self._semaphore.acquire()

        try:
            # Берем драйвер из пула или создаем новый если пул пустой
            if self._drivers:
                driver = self._drivers.pop()
            else:
                driver = await asyncio.get_event_loop().run_in_executor(
                    None, self._create_driver_with_retries
                )

            try:
                # Очищаем состояние драйвера перед использованием
                await self._clean_driver(driver)
                yield driver

            finally:
                # Возвращаем драйвер в пул
                self._drivers.append(driver)

        finally:
            # Освобождаем семафор
            self._semaphore.release()

    async def _create_driver_on_demand(self):
        """Создает драйвер по требованию если пул пустой"""
        try:
            driver = await asyncio.get_event_loop().run_in_executor(
                None, self._create_driver_with_retries
            )
            self._drivers.append(driver)
            print("✅ Создан драйвер по требованию")
        except Exception as e:
            print(f"❌ Не удалось создать драйвер по требованию: {e}")
            raise

    async def _clean_driver(self, driver: Chrome):
        """
        Очистка состояния драйвера перед повторным использованием
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_clean_driver, driver)
        except Exception as e:
            print(f"⚠️ Ошибка очистки драйвера: {e}")

    def _sync_clean_driver(self, driver: Chrome):
        """Синхронная очистка драйвера"""
        try:
            # Очищаем cookies
            try:
                driver.delete_all_cookies()
            except Exception:
                pass

            # Очищаем localStorage и sessionStorage
            try:
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
            except Exception:
                pass

            # Возвращаем на пустую страницу
            try:
                if getattr(driver, "current_url", None) and driver.current_url != "about:blank":
                    driver.get("about:blank")
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️ Ошибка при очистке драйвера: {e}")
            # Если драйвер сломан, заменяем его
            self._replace_broken_driver(driver)

    def _replace_broken_driver(self, broken_driver: Chrome):
        """Замена сломанного драйвера"""
        try:
            broken_driver.quit()
        except Exception:
            pass

        # Создаем новый драйвер (синхронно)
        try:
            new_driver = self._create_driver()
            self._drivers.append(new_driver)
            print("✅ Сломанный драйвер заменен")
        except Exception as e:
            print(f"❌ Не удалось заменить сломанный драйвер: {e}")

    async def close_all(self):
        """Закрытие всех драйверов при завершении приложения"""
        print("🔄 Закрытие пула драйверов...")

        # Отменяем задачу инициализации если она есть
        if self._initialization_task and not self._initialization_task.done():
            self._initialization_task.cancel()
            try:
                await self._initialization_task
            except asyncio.CancelledError:
                pass

        # Отменяем все задачи создания драйверов
        for task in self._drivers_creation_tasks:
            if not task.done():
                task.cancel()

        for driver in list(self._drivers):
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️ Ошибка закрытия драйвера: {e}")

        self._drivers.clear()
        self._initialized = False
        self._initialization_task = None
        self._drivers_creation_tasks.clear()
        print("✅ Пул драйверов закрыт")

    def get_stats(self):
        """Возвращает статистику пула"""
        return {
            "total_drivers": len(self._drivers),
            "pool_size": self.pool_size,
            "initialized": self._initialized,
            "available": self._semaphore._value
        }


# Глобальный экземпляр пула
driver_pool = AsyncDriverPool()


# FastAPI зависимость
async def get_driver():
    """
    Зависимость для внедрения драйвера в эндпоинты
    """
    async with driver_pool.get_driver() as driver:
        yield driver