from fastapi import FastAPI
from routers.auth_proxy import router as auth_router

app = FastAPI(title="API Gateway")

app.include_router(auth_router)