import uvicorn
from fastapi import FastAPI
from app.api.v1_jobs import router as jobs_router

def create_platform_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise AI Platform",
        version="1.0.0",
        description="Production-grade asynchronous distributed core."
    )

    # Mount our modular API components
    app.include_router(jobs_router)

    return app

app = create_platform_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)