
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import climate, health, farms, observations, rotations
from app.config import settings
from app.database.connection import Base, engine
from app.models import farm

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AgroSphere AI API",
    description="Backend API for AgroSphere AI",
    version="0.1.0",
    lifespan=lifespan
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    fields = {}

    for error in exc.errors():
        location = [
            str(part)
            for part in error["loc"]
            if part != "body"
        ]
        fields[".".join(location) or "body"] = error["msg"]

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data.",
                "fields": fields
            }
        }
    )


app.include_router(
    health.router,
    prefix="/api/v1"
)

app.include_router(
    farms.router,
    prefix="/api/v1"
)

app.include_router(observations.router, prefix="/api/v1")
app.include_router(observations.snapshot_router, prefix="/api/v1")
app.include_router(climate.router, prefix="/api/v1")
app.include_router(rotations.router, prefix="/api/v1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)
