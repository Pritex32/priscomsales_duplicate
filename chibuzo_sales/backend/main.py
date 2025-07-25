from fastapi import FastAPI
from routers import sales, restock

app = FastAPI(title="ChibuSales API")

# Include Routers
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(restock.router, prefix="/api/restock", tags=["Restock"])

