
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


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


USE_REDIS = True
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=1, 
    )
 
    redis_client.ping()
    print("Redis connection successful. Rate limiting enabled.")
except (redis.ConnectionError, redis.exceptions.TimeoutError):
    print("Warning: Redis connection failed. Rate limiting will be disabled.")
    USE_REDIS = False



@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for rate limiting
    """
   
    if not USE_REDIS:
        return await call_next(request)
        
  
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
        return await call_next(request)
    
  
    client_ip = request.client.host
    

    minute_key = f"rate_limit:{client_ip}:{int(time.time()) // 60}"
    
    try:
     
        current = redis_client.incr(minute_key)
        
   
        if current == 1:
            redis_client.expire(minute_key, 60)
        
       
        if current > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
    except:

        pass
    
    return await call_next(request)



@app.middleware("http")
async def content_negotiation_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for content negotiation
    """
    response = await call_next(request)
    
    
    accept = request.headers.get("Accept", "")
    
    
    if "application/x-msgpack" in accept and response.headers.get("content-type") == "application/json":
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
     
        import json
        try:
            data = json.loads(response_body)
            msgpack_data = msgpack.packb(data)
            
        
            return Response(
                content=msgpack_data,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/x-msgpack"
            )
        except:
 
            pass
    
    return response



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



@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)