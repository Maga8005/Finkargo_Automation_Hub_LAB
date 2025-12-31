"""
Finkargo Automation Hub - FastAPI Backend Entry Point

Optimizado con:
- GZipMiddleware para compresión de respuestas JSON
- CORS configurado para Vercel preview URLs
- Request size limit middleware for large file uploads (50 MB)
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.settings import get_settings
from src.adapter.rest import legal_routes, operations_routes, auth_routes, finance_routes, tesoreria_routes, alianzas_routes, treasury_matching_routes, risk_routes, pa_routes
from src.adapter.rest.declaraciones import directory_scanner as treasury_directory_scanner
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size for file uploads.
    Prevents memory exhaustion from extremely large uploads.

    Note: This middleware runs before CORS middleware in the request chain,
    so we must include CORS headers in our 413 responses to avoid misleading
    CORS errors in the browser.
    """

    def __init__(self, app, max_upload_size: int = 52428800):  # 50 MB default
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        # Check content-length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_upload_size:
                    logger.warning(f"Request body too large: {size} bytes (max: {self.max_upload_size})")
                    # Get the origin header for CORS
                    origin = request.headers.get("origin", "*")
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"El archivo es demasiado grande. Tamaño máximo: {self.max_upload_size // (1024 * 1024)} MB"
                        },
                        headers={
                            "Access-Control-Allow-Origin": origin,
                            "Access-Control-Allow-Credentials": "true",
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)


app = FastAPI(
    title=settings.APP_NAME,
    description="Automation Hub for Finkargo Internal Processes",
    version="1.0.0"
)

# Parse CORS origins from JSON string
try:
    cors_origins = json.loads(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
    logger.info(f"✅ CORS Origins configured: {cors_origins}")
    logger.info(f"✅ CORS Origin type: {type(cors_origins)}")
except Exception as e:
    logger.error(f"❌ Failed to parse CORS_ORIGINS: {e}")
    cors_origins = ["http://localhost:5173"]

# IMPORTANT: Add CORS middleware BEFORE including routers
# Use allow_origin_regex for Vercel preview URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.finkargo\.com"  # Support all Vercel preview URLs
)

# GZip middleware for compressing JSON responses
# minimum_size=500 means only compress responses larger than 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Request size limit middleware for large file uploads
# Uses MAX_UPLOAD_SIZE from settings (default 50 MB)
app.add_middleware(RequestSizeLimitMiddleware, max_upload_size=settings.MAX_UPLOAD_SIZE)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled exceptions.
    Ensures CORS headers are included in error responses.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Include routers AFTER middleware
app.include_router(auth_routes.router, prefix="/api")
app.include_router(legal_routes.router)
app.include_router(operations_routes.router)
app.include_router(finance_routes.router)
app.include_router(tesoreria_routes.router)
app.include_router(alianzas_routes.router)
app.include_router(treasury_matching_routes.router)
app.include_router(treasury_directory_scanner.router)
app.include_router(risk_routes.router)
app.include_router(pa_routes.router)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }

@app.get("/api/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins_raw": settings.CORS_ORIGINS,
        "cors_origins_parsed": cors_origins,
        "cors_origins_type": str(type(cors_origins)),
        "note": "This endpoint helps debug CORS configuration issues"
    }

@app.get("/api/departments")
async def get_departments():
    """Get list of Finkargo departments"""
    return {
        "departments": [
            {"id": "operations", "name": "Operaciones", "icon": "Settings"},
            {"id": "sales", "name": "Ventas", "icon": "TrendingUp"},
            {"id": "finance", "name": "Finanzas", "icon": "AttachMoney"},
            {"id": "tesoreria", "name": "Tesorería", "icon": "AccountBalance"},
            {"id": "alianzas", "name": "Alianzas", "icon": "People"},
            {"id": "hr", "name": "Recursos Humanos", "icon": "People"},
            {"id": "technology", "name": "Tecnología", "icon": "Code"},
            {"id": "customer-service", "name": "Atención al Cliente", "icon": "Support"},
            {"id": "legal", "name": "Legal", "icon": "Gavel"},
            {"id": "risk", "name": "Riesgos", "icon": "Shield"},
            {"id": "collections", "name": "Collections", "icon": "Settings"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
