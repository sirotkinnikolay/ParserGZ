from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.deps import get_db
from app.driver import get_driver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

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
    try:
        driver.get("https://gorzdrav.spb.ru/service-free-schedule")
        wait = WebDriverWait(driver, 10)
        district_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH,
                '/html/body/div/div[1]/div[12]/div[3]/div[1]/div[2]/div[1]/div/div[1]/ul/li'
            ))
        )
        district_buttons_texts = [btn.text for btn in district_buttons]
        return {"district_buttons": district_buttons_texts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
