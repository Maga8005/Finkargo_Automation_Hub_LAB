"""
Finkargo Automation Hub - FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.adapter.rest import legal_routes, operations_routes, auth_routes
import json

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Automation Hub for Finkargo Internal Processes",
    version="1.0.0"
)

# Parse CORS origins from JSON string
cors_origins = json.loads(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS

print(f"CORS Origins configured: {cors_origins}")

# IMPORTANT: Add CORS middleware BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers AFTER middleware
app.include_router(auth_routes.router, prefix="/api")
app.include_router(legal_routes.router)
app.include_router(operations_routes.router)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
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
