"""
FastAPI Application Entry Point

เทียบเท่า index.js ใน Express
- สร้าง FastAPI app instance
- ลงทะเบียน routers
- ตั้งค่า middleware (CORS, etc.)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, orders, products, reservations, tables, users

app = FastAPI(
    title="Cafe Inn API",
    description="Coffee Shop Backend API - Learning Project",
    version="0.1.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
def health_check():
    try:
        return {"status": "ok", "message": "Cafe Inn API is running"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Internal Server Error: {e}"},
        )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(tables.router, prefix="/tables", tags=["Tables"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])

