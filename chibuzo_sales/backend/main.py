from fastapi import FastAPI
from routers import sales, restock,expenses, payments

app = FastAPI(title="PriscomSales API")

# Include Routers
app.include_router(sales.router, prefix="/api/sales", tags=["sales"])
app.include_router(restock.router, prefix="/api/restock", tags=["restock"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])


