"""
Finkargo Automation Hub - FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.adapter.rest import legal_routes, operations_routes, auth_routes, finance_routes, tesoreria_routes
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
app.include_router(finance_routes.router)
app.include_router(tesoreria_routes.router)

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
            {"id": "hr", "name": "Recursos Humanos", "icon": "People"},
            {"id": "technology", "name": "Tecnología", "icon": "Code"},
            {"id": "customer-service", "name": "Atención al Cliente", "icon": "Support"},
            {"id": "legal", "name": "Legal", "icon": "Gavel"},
            {"id": "collections", "name": "Collections", "icon": "Settings"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
