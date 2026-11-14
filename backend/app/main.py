
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import health, farms, observations, rotations, scenarios, plans, assistant
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
    unsupported_language = request.url.path == "/api/v1/assistant/messages" and any(
        error["loc"] == ("body", "language") and error["type"] == "literal_error"
        for error in exc.errors()
    )

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
                "code": "UNSUPPORTED_LANGUAGE" if unsupported_language else "VALIDATION_ERROR",
                "message": "Only English ('en') is supported by the assistant." if unsupported_language else "Invalid request data.",
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
app.include_router(rotations.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)
