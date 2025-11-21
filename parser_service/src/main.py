import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from .api.v1 import router as v1_router
from .dependencies import driver_pool
from logging.handlers import RotatingFileHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('parser_service.log', maxBytes=1024 * 1024, backupCount=3,  encoding='utf-8')
    ]
)
app = FastAPI(
    title="API Parser Service",
    description="API с пулом переиспользуемых Selenium драйверов",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения"""
    await driver_pool.initialize()
    print("🚀 FastAPI сервер запущен, пул драйверов инициализируется в фоне")

@app.on_event("shutdown")
async def shutdown_event():
    """Запускается при завершении приложения"""
    await driver_pool.close_all()
    print("🛑 Приложение завершено")

app.include_router(v1_router, prefix="/api/v1")


@app.get("/info")
async def info():
    try:
        base_dir = Path(__file__).parent.parent
        file_path = base_dir / "alembic" / "README.md"
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"message": content}
    except FileNotFoundError:
        return {"message": "README.md не найден"}
    except Exception as e:
        return {"message": f"Ошибка чтения файла: {str(e)}"}
