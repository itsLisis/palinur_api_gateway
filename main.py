from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth_proxy import router as auth_router
from routers.user_proxy import router as user_router
from routers.home_router import router as home_router
from routers.matching_proxy import router as matching_router
from routers.chat_proxy import router as chat_router

app = FastAPI(title="API Gateway")

# CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(home_router)
app.include_router(matching_router)
app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api_gateway"}