"""
Finkargo Automation Hub - FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.adapter.rest import legal_routes, operations_routes, auth_routes
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

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
    allow_origin_regex=r"https://.*\.vercel\.app"  # Support all Vercel preview URLs
)

# Include routers AFTER middleware
app.include_router(auth_routes.router, prefix="/api")
app.include_router(legal_routes.router)
app.include_router(operations_routes.router)

# Add exception handler to ensure CORS headers on all responses (including errors)
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that ensures CORS headers are always sent,
    even when errors occur before CORSMiddleware can process the response.
    """
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Create error response
    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', str(exc))

    response = JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )

    # Manually add CORS headers to error response
    origin = request.headers.get('origin')
    if origin:
        # Check if origin is allowed
        if origin in cors_origins or any(origin.endswith('.vercel.app') for _ in [1]):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"

    return response

from fastapi.exceptions import RequestValidationError, HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with CORS headers"""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

    # Add CORS headers
    origin = request.headers.get('origin')
    if origin:
        if origin in cors_origins or origin.endswith('.vercel.app'):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"

    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    response = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

    # Add CORS headers
    origin = request.headers.get('origin')
    if origin:
        if origin in cors_origins or origin.endswith('.vercel.app'):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"

    return response

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
            {"id": "hr", "name": "Recursos Humanos", "icon": "People"},
            {"id": "technology", "name": "Tecnología", "icon": "Code"},
            {"id": "customer-service", "name": "Atención al Cliente", "icon": "Support"},
            {"id": "legal", "name": "Legal", "icon": "Gavel"},
            {"id": "collections", "name": "Collections", "icon": "AccountBalance"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
