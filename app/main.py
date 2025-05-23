# File: app/main.py
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
import msgpack
import redis
import time
from typing import Callable, List

from app.core.config import settings
from app.api.routes import auth, events, collaboration, history, changelog
from app.db.base import Base, engine
from app.api.deps import get_db

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Collaborative Event Management System API",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None,
    openapi_version="3.0.2",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Setup Redis connection for rate limiting
USE_REDIS = True
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=1,  # Short timeout to fail fast
    )
    # Test connection
    redis_client.ping()
    print("Redis connection successful. Rate limiting enabled.")
except (redis.ConnectionError, redis.exceptions.TimeoutError):
    print("Warning: Redis connection failed. Rate limiting will be disabled.")
    USE_REDIS = False


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for rate limiting
    """
    # Skip rate limiting if Redis is not available
    if not USE_REDIS:
        return await call_next(request)
        
    # Skip rate limiting for docs
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host
    
    # Check if rate limit exceeded
    minute_key = f"rate_limit:{client_ip}:{int(time.time()) // 60}"
    
    try:
        # Increment and check counter
        current = redis_client.incr(minute_key)
        
        # Set expiry if first request
        if current == 1:
            redis_client.expire(minute_key, 60)
        
        # Check if limit exceeded
        if current > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
    except:
        # If Redis fails, just continue without rate limiting
        pass
    
    # Continue processing request
    return await call_next(request)


# Content negotiation middleware
@app.middleware("http")
async def content_negotiation_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for content negotiation
    """
    response = await call_next(request)
    
    # Check Accept header
    accept = request.headers.get("Accept", "")
    
    # If client accepts MessagePack and response is JSON, convert to MessagePack
    if "application/x-msgpack" in accept and response.headers.get("content-type") == "application/json":
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Parse JSON and encode to MessagePack
        import json
        try:
            data = json.loads(response_body)
            msgpack_data = msgpack.packb(data)
            
            # Create new response
            return Response(
                content=msgpack_data,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/x-msgpack"
            )
        except:
            # If conversion fails, return original response
            pass
    
    return response


# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)
app.include_router(
    events.router,
    prefix=f"{settings.API_V1_STR}/events",
    tags=["events"]
)
app.include_router(
    collaboration.router,
    prefix=f"{settings.API_V1_STR}/events",
    tags=["collaboration"]
)
app.include_router(
    history.router,
    prefix=f"{settings.API_V1_STR}/events",
    tags=["version history"]
)
app.include_router(
    changelog.router,
    prefix=f"{settings.API_V1_STR}/events",
    tags=["changelog"]
)


# Custom API docs
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui-bundle.min.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.css",
    )




@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint() -> JSONResponse:
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME, 
        version="1.0.0", 
        description="Collaborative Event Management System API",
        routes=app.routes,
        openapi_version="3.0.2"
    )
    return JSONResponse(openapi_schema)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)