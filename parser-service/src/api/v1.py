from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time
from .. import schemas, crud
from ..deps import get_db
from ..dependencies import get_driver, driver_pool
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
n = '\n'

"""
----------- Производительность и ресурсы -----------
Создание и закрытие Chrome для каждого запроса — дорого. Для реального использования
можно использовать пул драйверов (внешняя очередь/брокер) — сложнее.
Использовать Selenium Grid / Селениум-узлы, чтобы несколько клиентов могли переиспользовать сессии.
Если вы делаете много автоматизации, подумайте об очереди задач (Celery/RQ) и воркерах, которые держат драйверы постоянно.
"""


router = APIRouter()

@router.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user_in)


@router.get("/district")
def use_driver(driver: WebDriver = Depends(get_driver)):
    info = {}
    try:
        driver.get("https://gorzdrav.spb.ru/service-free-schedule")
        wait = WebDriverWait(driver, 10)
        district_buttons = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '/html/body/div/div[1]/div[12]/div[3]/div[1]/div[2]/div[1]/div/div[1]/ul/li')
            )
        )
        total_districts = len(district_buttons)
        print(f'========> {total_districts}')

        for i in range(total_districts):
            try:
                # В КАЖДОЙ итерации заново находим все элементы
                district_buttons = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '/html/body/div/div[1]/div[12]/div[3]/div[1]/div[2]/div[1]/div/div[1]/ul/li')
                    )
                )

                if i < len(district_buttons):
                    district_name = district_buttons[i].text
                    print(f'========> {district_name}')

                    district_buttons[i].click()
                    clinic_list = wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//*[@id="serviceMoOutput"]/div'))
                    )

                    clinics = [clinic.text.split('\n', 1)[0] for clinic in clinic_list]
                    driver.back()
                    wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '/html/body/div/div[1]/div[12]/div[3]/div[1]/div[2]/div[1]/div/div[1]/ul')
                        )
                    )
                    if len(district_name) > 1:
                        info[district_name] = clinics
            except Exception as e:
                print(f"Ошибка при обработке района {i + 1}: {e}")
                driver.get("https://gorzdrav.spb.ru/service-free-schedule")
                continue

        return {"district_buttons": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/driver-pool")
async def get_driver_pool_stats():
    """Эндпоинт для проверки статуса пула драйверов"""
    return {
        "status": "ok",
        "pool_stats": driver_pool.get_stats(),
        "timestamp": time.time()
    }
