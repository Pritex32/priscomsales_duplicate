from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import supabase_client

router = APIRouter()

# Define request model for creating a sale
class SaleRequest(BaseModel):
    user_id: int
    employee_id: int
    customer_name: str
    customer_phone: str
    item_id: int
    item_name: str
    quantity: int
    unit_price: float
    total_amount: float
    amount_paid: float
    amount_balance: float
    payment_method: str
    payment_status: str
    sale_date: str  # Format: YYYY-MM-DD
    due_date: str | None = None
    notes: str | None = None

# ✅ Create a new sale
@router.post("/sales")
def create_sale(sale: SaleRequest):
    try:
        # Insert sale into Supabase
        data = {
            "user_id": sale.user_id,
            "employee_id": sale.employee_id,
            "customer_name": sale.customer_name,
            "customer_phone": sale.customer_phone,
            "item_id": sale.item_id,
            "item_name": sale.item_name,
            "quantity": sale.quantity,
            "unit_price": sale.unit_price,
            "total_amount": sale.total_amount,
            "amount_paid": sale.amount_paid,
            "amount_balance": sale.amount_balance,
            "payment_method": sale.payment_method,
            "payment_status": sale.payment_status,
            "sale_date": sale.sale_date,
            "due_date": sale.due_date,
            "notes": sale.notes,
        }

        response = supabase_client.table("sales_master_history").insert(data).execute()

        if response.data:
            return {"status": "success", "data": response.data}
        else:
            raise HTTPException(status_code=400, detail="Failed to insert sale")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Get all sales for a user
@router.get("/sales/{user_id}")
def get_sales(user_id: int):
    try:
        response = supabase_client.table("sales_master_history").select("*").eq("user_id", user_id).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
