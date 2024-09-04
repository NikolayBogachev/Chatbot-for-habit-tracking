import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter


from api.handlers import router, logger

from database.db import init_db

app = FastAPI(title="Chat-Bot")


@app.on_event("startup")
async def startup_event():

    init_db()

    logger.info("Приложение успешно запущено")


main_api_router = APIRouter()

main_api_router.include_router(router)

app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
