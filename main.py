from fastapi import FastAPI
from routers.auth_proxy import router as auth_router
from routers.user_proxy import router as user_router
from routers.home_router import router as home_router

app = FastAPI(title="API Gateway")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(home_router)