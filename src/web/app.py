"""
FastAPI Main Web Application for Modern Educational Complex SMS.
Aggregates REST APIs, static assets, templates, and security middleware.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from src.web.routes.auth_routes import router as auth_router
from src.web.routes.dashboard_routes import router as dashboard_router
from src.web.routes.student_routes import router as student_router
from src.web.routes.attendance_routes import router as attendance_router
from src.web.routes.fee_routes import router as fee_router
from src.web.routes.staff_routes import router as staff_router
from src.web.routes.exam_routes import router as exam_router
from src.web.routes.system_routes import router as system_router

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.SCHOOL_NAME,
    description="Online Web Portal for School Administrators, Teachers, and Staff.",
    version="2.0.0"
)

# CORS Middleware (permits LAN and online access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Exports Directory for receipts and PDFs
if settings.EXPORTS_DIR.exists():
    app.mount("/exports", StaticFiles(directory=str(settings.EXPORTS_DIR)), name="exports")

# Mount Official School Assets
if settings.ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(settings.ASSETS_DIR)), name="assets")

# Template Engine
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(student_router)
app.include_router(attendance_router)
app.include_router(fee_router)
app.include_router(staff_router)
app.include_router(exam_router)
app.include_router(system_router)


@app.get("/", response_class=HTMLResponse)
async def serve_home_portal(request: Request):
    """Serves the main single-page application."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "school_name": settings.SCHOOL_NAME,
            "school_tagline": settings.SCHOOL_TAGLINE,
            "school_phone": settings.SCHOOL_PHONE,
            "school_email": settings.SCHOOL_EMAIL
        }
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ModernEduComplex-SMS-Web", "db_type": settings.DB_TYPE}
