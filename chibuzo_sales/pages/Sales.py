import streamlit as st
# to hide streamlit features
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    footer:after {content:'';}
    header {visibility: hidden;}
    .css-164nlkn.egzxvld1 {visibility: hidden;}  /* Streamlit footer class */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
import bcrypt
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime,date
import json
import time

from PIL import Image
import io
import os
import numpy as np
from storage3.exceptions import StorageApiError
import uuid

from fpdf import FPDF
import base64
import jwt
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
# 🔐 Same secret key must be used across all pages




# to show spiner rotating when the app is laoding
 #Only show spinner on first load
if "loaded" not in st.session_state:
    st.markdown("""
        <style>
        .loader {
          border: 6px solid #f3f3f3;
          border-top: 6px solid #00FFC6;
          border-radius: 50%;
          width: 50px;
          height: 50px;
          animation: spin 1s linear infinite;
          margin: auto;
          position: relative;
          top: 50px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        </style>

        <div class="loader"></div>
        <h5 style="text-align:center;">Loading PriscomSales App...</h5>
    """, unsafe_allow_html=True)
    
    time.sleep(2)  # Simulate loading time
    st.session_state.loaded = True
    st.rerun()  # 🔁 Rerun app to remove loader and show main content

jwt_SECRET_KEY = "4606"  # Use env vars in production
ALGORITHM = "HS256"

#Decode function
def generate_jwt(user_id, username, role,plan="free", is_active=False, email=None):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
         "plan": plan,
        "is_active": is_active,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, jwt_SECRET_KEY, algorithm=ALGORITHM)
    return token
def decode_jwt(token):
    try:
        return jwt.decode(token, jwt_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        st.warning("Token expired.")
    except jwt.InvalidTokenError:
        st.error("Invalid token.")
    return None

# Restore login from browser localStorage

# === Restore Login from JWT ===
def restore_login_from_jwt():
    if not st.session_state.get("logged_in"):
        token = st_javascript("""localStorage.getItem("login_token");""")
        if token and token != "null":
            user_data = decode_jwt(token)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_id = int(user_data["user_id"])
                st.session_state.username = user_data["username"]
                st.session_state.role = user_data["role"]
                st.session_state.role = user_data["role"]
                st.session_state.plan = user_data.get("plan", "free")
                st.session_state.is_active = user_data.get("is_active", False)
                st.session_state.user_email = user_data.get("email", "")

# Run this first
restore_login_from_jwt()

# === Session Validation ===
if not st.session_state.get("logged_in"):
    st.warning("⏳ Waiting for session to restore from browser...")
    st.warning('Login Again')
    st.stop()

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("❌ No valid user ID in session. Please log in again.")
    st.stop()

try:
    user_id = int(user_id)
except Exception:
    st.error("❌ User ID is not a valid integer.")
    st.stop()


# validate user





if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    st.warning("Please log in first.")
    st.stop()

# Main content # this shows you are currently logged in
if st.session_state.get("logged_in"):
    st.title(f"Welcome, {st.session_state.username}")
else:
    st.warning("Please log in first.")


from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database









def restore_subscription_info():
    user_id = st.session_state.get("user_id")
    try:
        response = supabase.table("subscription")\
            .select("plan, is_active")\
            .eq("user_id", user_id)\
            .order("started_at", desc=True)\
            .limit(1)\
            .execute()
        sub = response.data[0] if response.data else {}
        st.session_state.plan = sub.get("plan", "free")
        st.session_state.is_active = sub.get("is_active", False)
    except Exception as e:
        st.session_state.plan = "free"
        st.session_state.is_active = False
        st.warning(f"⚠️ Could not fetch subscription info: {e}")


if "plan" not in st.session_state or "is_active" not in st.session_state:
    restore_subscription_info()


user_id = st.session_state.get("user_id")

   

 





# this will show if the person has paid or not

# ---------- PLAN ENFORCEMENT ---------- #
def fetch_subscription_data(user_id):
    try:
        response = supabase.table("subscription").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching subscription data: {e}")
        return pd.DataFrame()


# to prevent usage after plan expired on employee
def block_if_subscription_expired():
    plan = st.session_state.get("plan", "free")
    is_active = st.session_state.get("is_active", False)
    user_id = st.session_state.get("user_id")

    if plan == "free" or not is_active:
        # Check row count (example: from 'sales' table)
        response1 = supabase.table("sales_master_log").select("sale_id", count="exact").eq("user_id", user_id).execute()
        row_count1 = response1.count or 0
        response2 = supabase.table("sales_master_history").select("sale_id", count="exact").eq("user_id", user_id).execute()
        row_count2 = response2.count or 0

        # ✅ Block if either exceeds 10
        if row_count1 > 10 or row_count2 > 10:
            st.error("🚫 Free plan limit reached (max 10 entries in sales or purchases). Please upgrade to continue.")
            st.stop()

def show_plan_status():
    if st.session_state.plan == "free" and not st.session_state.is_active:
        st.info("🆓 You are currently on the **Free Plan**. Limited to 10 transactions.")
    elif st.session_state.plan == "pro" and st.session_state.is_active:
        st.success("💼 You are on the **Pro Plan**. Enjoy unlimited access!")
    else:
        st.warning("⚠️ Your subscription status is unclear. Please contact support.")



def handle_subscription_expiration(user_id):
    try:
        # 🔁 Fetch latest subscription data
        response = supabase.table("subscription").select("*").eq("user_id", user_id).order("expires_at", desc=True).limit(1).execute()
        data = response.data

        if not data:
            return  # No subscription record yet

        sub = data[0]
        expires_at_str = sub.get("expires_at")
        plan = sub.get("plan", "free")
        is_active = sub.get("is_active", False)
        today = date.today()

        # 🧮 Check if expired
        if expires_at_str and date.fromisoformat(expires_at_str) < today and is_active:
            # ❌ Subscription expired – downgrade to free
            supabase.table("subscription").update({
                "plan": "free",
                "is_active": False
            }).eq("user_id", user_id).execute()

            # 🔄 Update session
            st.session_state.plan = "free"
            st.session_state.is_active = False

            # 🔁 Re-generate token with downgraded plan
            username = st.session_state.get("username", "")
            role = st.session_state.get("role", "user")
            email = st.session_state.get("user_email", "")

            token = generate_jwt(user_id, username, role, plan="free", is_active=False, email=email)
            st.session_state.jwt_token = token
            st.markdown(f"""<script>
                          localStorage.setItem("login_token", "{token}");
                           </script>""", unsafe_allow_html=True)

            # ⚠️ Notify user
            st.warning("🔔 Your Pro subscription has expired. You've been downgraded to the Free Plan.")

    except Exception as e:
        st.error(f"Subscription check failed: {e}")
if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    block_if_subscription_expired()
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    show_plan_status()



# -------- Helper Functions --------
import tempfile
import mimetypes


def upload_invoice(file, folder, filename,user_id):
    bucket = "salesinvoices"  # Make sure the bucket name matches your Supabase Storage bucket
    path_in_bucket = f"{folder}/{filename}"

    # Determine MIME type dynamically
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name

    try:
        # Upload the file to Supabase with the correct MIME type
        with open(tmp_file_path, "rb") as f:
            supabase.storage.from_(bucket).upload(path_in_bucket, f, {"content-type": mime_type})

        # Remove the temporary file
        os.remove(tmp_file_path)

        # Return the public URL of the uploaded file
        return supabase.storage.from_(bucket).get_public_url(path_in_bucket)

    except StorageApiError as e:
        os.remove(tmp_file_path)

        error_info = e.args[0]  # Could be dict or string
        if isinstance(error_info, dict):
            if error_info.get("statusCode") == 409:
                st.error("⚠️ This invoice already exists. Please rename the file or upload a different one.")
            else:
                st.error(f"❌ Failed to upload invoice: {error_info.get('message', str(e))}")
        else:  # error_info is a string, just display it
            st.error(f"❌ Failed to upload invoice: {error_info}")

    return None



import re





# to get employee names when logged in and put it in the table along side the record the person inputs , not manually
@st.cache_data(ttl=7200)
def get_employee_dict(user_id):
    # Assuming 'user_id' exists in the 'employees' table
    employees = supabase.table("employees").select("employee_id, name").eq("user_id", user_id).execute()
    return {emp["name"]: emp["employee_id"] for emp in employees.data}
    


# -------- Tabs --------
st.title("**💼 Sales & Expenses Management**")
tab1, tab2 ,tab3, tab4 ,tab5= st.tabs(["➕ Add Sale", "Payments","💸 Add Expense","Delete",'Report'])

# ========== ADD SALE ==========

@st.cache_data(ttl=7200)
def fetch_inventory_items(user_id):
    if not user_id or str(user_id) == "None":
        raise ValueError("Invalid user_id passed to fetch_inventory_items")

    response = supabase.table("inventory_master_log")\
        .select("item_id, item_name")\
        .eq("user_id", user_id)\
        .execute()

    items = response.data or []
    return {item["item_name"]: item["item_id"] for item in items}

 
# Check if user is logged in and fetch user_id
# Get the authenticated user ID (from auth)
@st.cache_data(ttl=7200)
def fetch_goods_bought_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('goods_bought_history').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data
    

@st.cache_data(ttl=7200)
def fetch_sales_data(user_id, limit=10):
    
    response = supabase.table("sales_master_history").select("*") \
                .eq("user_id", user_id) \
                .order("sale_date", desc=True) \
                .limit(limit) \
                .execute()
    
    data = response.data or []
    
    # Convert the fetched data to a DataFrame
    sales_df = pd.DataFrame(data)
    
    if not sales_df.empty:
        return sales_df
    else:
        print("No sales data found or an error occurred.")
        return pd.DataFrame()

@st.cache_data(ttl=7200)
def fetch_expenses_master_data(user_id):
    response = supabase.table("expenses_master").select("*").eq("user_id", user_id).execute()
    data = response.data or []
    
    expenses_df = pd.DataFrame(data)
    
    if not expenses_df.empty:
        return expenses_df
    else:
        print("No data found or an error occurred.")

# Fetch and display the payment data
@st.cache_data(ttl=7200) # cache data for 2 hrs
def fetch_payment_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('payments').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame() 
    
restock_df=fetch_goods_bought_history(user_id)
sales_df= fetch_sales_data(user_id)
expenses_df = fetch_expenses_master_data(user_id)
payment_df=fetch_payment_history(user_id)


# function to serach through all tables and get information
def search_transactions(search_query, sales_df, expenses_df, restock_df, payment_df):
    search_query_lower = search_query.strip().lower()
    
    # Filter Sales Data
    filtered_sales = sales_df[sales_df.apply(lambda row: row.astype(str).str.contains(search_query_lower).any(), axis=1)]
    
    # Filter Expenses Data
    filtered_expenses = expenses_df[expenses_df.apply(lambda row: row.astype(str).str.contains(search_query_lower).any(), axis=1)]
    
    # Filter Restock Data
    filtered_restock = restock_df[restock_df.apply(lambda row: row.astype(str).str.contains(search_query_lower).any(), axis=1)]
    
    # Filter Payment Data
    filtered_payment = payment_df[payment_df.apply(lambda row: row.astype(str).str.contains(search_query_lower).any(), axis=1)]
    
    # Combine filtered data
    combined_filtered_data = pd.concat([filtered_sales, filtered_expenses, filtered_restock, filtered_payment])
    
    return combined_filtered_data







# Fetch logged-in user's name and id regardless of role
user_name = st.session_state.get("username", "Unknown User")
user_id = st.session_state.get("user_id")

if not user_id:
    st.error("❌ No valid user ID found. Please log in again.")
    st.stop()

try:
    user_id = int(user_id)
except:
    st.error("❌ Invalid user ID format.")
    st.stop()


# getting the employee id
employee_lookup = supabase.table("employees").select("employee_id").eq("user_id", user_id).eq("name", user_name).limit(1).execute()

if not employee_lookup.data:
    st.error("❌ This employee is not registered.")
    st.stop()

employee_id = employee_lookup.data[0]["employee_id"]

# Initialize session state keys if not set
if "invoice_uploaded" not in st.session_state:
    st.session_state["invoice_uploaded"] = False
if "invoice_file_url" not in st.session_state:
    st.session_state["invoice_file_url"] = None

with tab1:     
    col7,col9=st.columns([3,1])
    with col7:
        st.header("🛒 Record a New Sale")
    with col9:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()  # ✅ Clear cached data
            st.rerun() 
    
   
    employee_name=st.text_input("Employee name",value= user_name, disabled=True,key="employee_name_input")

    employee_id=st.text_input("Employee id",value= employee_id, disabled=True,key="employee_name_input_2")

    # Item selection with default placeholder
    item_dict = fetch_inventory_items(user_id)
    item_options = ["Select an item"] + list(item_dict.keys())
    item_name = st.selectbox("Select Item", item_options, key="item_selectbox")
    item_id = item_dict.get(item_name, None)
    # Quantity input
    quantity = st.number_input("Quantity Sold", min_value=1, step=1, key="quantity")

    # Unit price input
    unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01, key="unit_price")

    # Auto-calculate total amount
    total_amount = quantity * unit_price
    st.info(f"💰 Total Amount: ₦{total_amount:,.2f}")

    # Sale info
    sale_date = st.date_input("Sale Date", value=date.today(), key="sale_date")
    customer_name = st.text_input("Customer Name", key="customer_name")
    customer_phone = st.text_input("Customer Phone Number", key="customer_phone")

    payment_method = st.selectbox("Payment Method", ["cash", "card", "transfer"], key="payment_method")
    payment_status = st.selectbox("Payment Status", ["paid", "credit", "partial"], key="payment_status")
    due_date = st.date_input("Due Date", value=date.today(), key="due_date") if payment_status != "paid" else None
    invoice_number = st.text_input("Invoice Number (optional)", key="invoice_number")
    notes = st.text_area("Notes", key="notes")

    # Upload invoice
    invoice_file_url = None
    invoice_file = st.file_uploader("Upload Invoice (PDF/Image)", type=["pdf", "jpg", "jpeg", "png"], key="invoice_upload")
    invoice_name = st.text_input("Enter desired invoice name (without extension)", value=f"invoice_{employee_id}_{date.today().isoformat()}", key='sale_key_invoice')
   
    # Partial payment
    partial_payment_amount = None
    partial_payment_date = None
    partial_payment_note = None
    if payment_status == "partial":
        st.subheader("💰 Enter Partial Payment Details")
        partial_payment_amount = st.number_input("Partial Payment Amount", min_value=0.0, max_value=total_amount, value=0.0, key="partial_amount")
        partial_payment_date = st.date_input("Partial Payment Date", value=date.today(), key="partial_date")
        partial_payment_note = st.text_area("Partial Payment Notes (optional)", key="partial_notes")

    # Upload logic (only once)
    if not st.session_state.get("invoice_uploaded"):
        if invoice_file and st.button("📤 Upload Invoice"):
            try:
                extension = os.path.splitext(invoice_file.name)[1]
                # Use user-entered name, or fallback if blank
                # Prepare fallback item name
                fallback_item_name = item_name.strip().replace(" ", "_") if item_name and item_name != "Select an item" else "no_item"
                # Build default filename if invoice_name is empty
                default_name = f"invoice_{user_id}_{fallback_item_name}_{sale_date}"
                final_invoice_name = invoice_name.strip() or default_name
               
                # Sanitize to remove invalid characters
                final_invoice_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', final_invoice_name)
                unique_id = str(uuid.uuid4())[:8]
                filename = f"{final_invoice_name}_{unique_id}{extension}"
                invoice_file_url = upload_invoice(invoice_file, "salesinvoices", filename, user_id)
                st.session_state["invoice_uploaded"] = True
                st.session_state["invoice_file_url"] = invoice_file_url
                st.success(f"✅ Invoice uploaded successfully as '{filename}'.")
            except Exception as e:
                st.error(f"❌ Upload failed: {e}")
                st.session_state["invoice_uploaded"] = False

    # Optional preview button
    if invoice_file and st.session_state.get("invoice_uploaded"):
        if st.button("🖼️ Preview Invoice"):
            extension = os.path.splitext(invoice_file.name)[1]
            if extension.lower() in [".jpg", ".jpeg", ".png"]:
                st.image(invoice_file, use_container_width=True)
            elif extension.lower() == ".pdf":
                st.download_button("📥 Download PDF for Preview", invoice_file, file_name=invoice_file.name)
                st.info("👆 Click the button above to preview the PDF file.")

     # Optional re-upload
    if st.session_state.get("invoice_uploaded"):
        if st.button("🔁 Re-upload Invoice"):
            st.session_state["invoice_uploaded"] = False
            st.session_state["invoice_file_url"] = None
            st.warning("⚠️ You can now upload a new invoice.")

    # Save Sale
    if st.button("💾 Save Sale", key="save_sale_btn"):
        if payment_status in ["credit", "partial"] and not customer_phone:
            st.warning("📞 It's highly recommended to collect the customer's phone number for credit or partial payments.")

        if not st.session_state.get("invoice_uploaded"):
            st.error("❌ Please upload an invoice before saving the sale.")
            st.stop()
        invoice_file_url = st.session_state.get("invoice_file_url")      
        if not item_id or item_name == "Select an item":
            st.error("❌ Please select a valid item before saving.")
            st.stop()
              
                 
        amount_paid = 0.0
        amount_balance = total_amount

        if payment_status == "paid":
            amount_paid = total_amount
            amount_balance = 0.0
        elif payment_status == "partial":
            if partial_payment_amount is None or partial_payment_amount <= 0:
                st.error("❌ Please enter a valid partial payment amount.")
                st.stop()
            else:
                amount_paid = partial_payment_amount
                amount_balance = total_amount - partial_payment_amount
        elif payment_status == "credit":
            amount_paid = 0.0
            amount_balance = total_amount

        if invoice_file is None:
            st.error("❌ Please upload an invoice or proof of payment before saving.")
            st.stop()
        


        sale_data = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "user_id": user_id,
            "sale_date": str(sale_date),
            "customer_name": customer_name,
            'customer_phone': customer_phone if customer_phone else None,
            "item_id": item_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "amount_paid": amount_paid,
            "amount_balance": amount_balance,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "due_date": str(due_date) if due_date else None,
            "invoice_number": invoice_number,
            "invoice_file_url": invoice_file_url,
            "notes": notes,
        }

        try:
            result = supabase.table("sales_master_log").insert(sale_data).execute()
            new_sale_id = result.data[0]["sale_id"]
            st.success("✅ Sale recorded successfully!")
            
            # Insert payment record if paid or partial
            if payment_status in ["paid", "partial", "credit"]:
                st.subheader("💳 Recording Payment...")

        # Determine payment data based on status
            if payment_status == "paid":
                pay_amount = total_amount
                pay_date = date.today()
                pay_note = ""
            elif payment_status == "partial":
                pay_amount = partial_payment_amount
                pay_date = partial_payment_date
                pay_note = partial_payment_note
            else:  # credit
                pay_amount = 0
                pay_date = date.today()
                pay_note = "Credit sale"
        
        # Prepare payment record with reference to sales_master_log
            payment_data = {
            "sale_log_id": new_sale_id,  # FK to sales_master_log
            "payment_date": str(pay_date),
            "amount": pay_amount,
            "payment_method": payment_method if payment_status != "credit" else "none",
            "notes": pay_note    }

        # Insert payment record once
            payment_result = supabase.table("payments").insert(payment_data).execute()
            payment_id = payment_result.data[0]["payment_id"]
            st.success(f"💸 Payment recorded successfully.")
            
        # Update sale record with payment info and status
            update_data = {"payment_id": payment_id}

            if payment_status == "paid" or amount_balance == 0.0:
                update_data["payment_status"] = "paid"
                st.success("✅ Sale status updated to PAID.")
            elif payment_status == "partial":
                update_data["payment_status"] = "partial"
                st.success("⚠️ Partial payment recorded, balance remains.")
            elif payment_status == "credit":
                update_data["amount_paid"] = 0
                update_data["payment_status"] = "credit"
                st.success("📝 Credit sale recorded without payment.")
             
            supabase.table("sales_master_log").update(update_data).eq("sale_id", new_sale_id).execute()
            # ✅ Clear form values before rerun
            for key in [
                "item_selectbox",
                "quantity",
                "unit_price",
                "sale_date",
                "customer_name",
                "customer_phone",
                "payment_method",
                "payment_status",
                "due_date",
                "invoice_number",
                "notes",
                "invoice_upload",
                "sale_key_invoice",
                "partial_amount",
                "partial_date",
                "partial_notes"
            ]:
                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()
            
        except Exception as e:
              st.error(f"❌ Failed to update sales record with payment: {e}")

   



# to get the user name of the owner and then use it to customize the receipt
def safe_text(text): # to convert the naira text to be downloadable
    return str(text).replace("₦", "NGN")

user_info = supabase.table("users").select("username").eq("user_id", user_id).single().execute()
tenant_name = user_info.data["username"] if user_info.data else "Sales"
# function to generate receipt

st.divider()
with tab1:
    col1,col2=st.columns(2)               
    with col1:
        st.subheader("📄 Generate Sales Receipt")
    

    # 🔁 Step 1: Fetch sales for the logged-in user
        try:
            sales_result = supabase.table("sales_master_history").select("*").eq("user_id", user_id).order("sale_date", desc=True).limit(50).execute()
            sales = sales_result.data

            if not sales:
                st.warning("No sales found for this user.")
            else: # 🔁 Step 2: Extract available sale dates
                available_dates = sorted({s["sale_date"] for s in sales}, reverse=True)

            # Convert strings to date objects
                date_options = [datetime.strptime(d, "%Y-%m-%d").date() for d in available_dates]
                selected_date = st.date_input("Select Sale Date", value=date_options[0])

            # 🔁 Step 3: Filter sales by selected date
                sales_for_date = [s for s in sales if s["sale_date"] == selected_date.strftime("%Y-%m-%d")]

                if not sales_for_date:
                    st.warning(f"No sales on {selected_date.strftime('%Y-%m-%d')}.")
                else:
                    sale_options = {   f"{s['item_name']} (₦{s['total_amount']:,.2f}) [#{s['sale_id']}]": s for s in sales_for_date
                }
                selected_sale_label = st.selectbox("Select a sale to generate receipt", list(sale_options.keys()))
                selected_sale = sale_options[selected_sale_label]

                # Optional: edit the date if needed
                
            # 🔁 Step 3: Show Receipt Details
                if st.button(" Show Receipt", key="show_receipt_btn"):
                    st.markdown(f"""   
                    ###  Sales Receipt
                    - **Sale ID:** {selected_sale['sale_id']}
                    - **Employee Name:** {selected_sale.get('employee_name', 'N/A')}
                    - **Sale Date:** {selected_sale['sale_date']}
                    - **Customer:** {selected_sale['customer_name']}
                    - **Item:** {selected_sale['item_name']}
                    - **Quantity:** {selected_sale['quantity']}
                    - **Unit Price:** ₦{selected_sale['unit_price']:,.2f}
                    - **Total Amount:** ₦{selected_sale['total_amount']:,.2f}
                    - **Amount Paid:** ₦{selected_sale.get('amount_paid', 0):,.2f}
                    - **Balance:** ₦{selected_sale.get('amount_balance', 0):,.2f}
                    - **Payment Method:** {selected_sale['payment_method']}
                    - **Payment Status:** {selected_sale['payment_status']}
                    - **Notes:** {selected_sale.get('notes', 'None')}   """)

            # 🔁 Step 4: PDF generation
                if st.button("Download Receipt PDF", key="download_selected_receipt_btn"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt=safe_text(f"{tenant_name} SALES RECEIPT"), ln=True, align="C")
                    pdf.ln(10)

                    for key, value in {
                          "Sale ID": selected_sale["sale_id"],
                          "Employee": selected_sale.get("employee_name", "N/A"),
                          "Date": selected_sale["sale_date"],
                          "Customer": selected_sale["customer_name"],
                          "Item": selected_sale["item_name"],
                          "Quantity": selected_sale["quantity"],
                          "Unit Price": f"NGN{selected_sale['unit_price']:,.2f}",
                          "Total": f"NGN{selected_sale['total_amount']:,.2f}",
                          "Amount Paid": f"NGN{selected_sale.get('amount_paid', 0):,.2f}",
                          "Balance": f"NGN{selected_sale.get('amount_balance', 0):,.2f}",
                          "Payment Method": selected_sale["payment_method"],
                          "Payment Status": selected_sale["payment_status"],
                          "Notes": selected_sale.get("notes", "None") 
                     }.items():
                        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
                
                    receipt_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
                    pdf.output(receipt_file)
                    

                    with open(receipt_file, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

                        download_link = f'<a href="data:application/pdf;base64,{base64_pdf}" download="receipt_{selected_sale["sale_id"]}.pdf">📥 Download Receipt PDF</a>'
                        st.markdown(download_link, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Failed to fetch sales: {e}")

    with col2:
        search_query = st.text_input("🔍 Search by Customer/Supplier Name or Invoice Number")

# Perform search if query is provided
        if search_query:
            filtered_data = search_transactions(search_query, sales_df, expenses_df, restock_df, payment_df)
    
            if not filtered_data.empty:    
                st.write(filtered_data)
            else:
                st.warning("No transactions found matching your search.")
        else:
            st.write("Please enter a search term to begin.")









        
    # ========== VIEW RECENT ==========
    st.markdown("---")
    st.header("📊 Recent Sales & Expenses")

    col1, col2 = st.columns(2)

    

    with col1:
        
        with st.expander('View sales Data'):
            st.subheader("🧾 Sales")
            sales = supabase.table("sales_master_history").select("*").eq("user_id", user_id).order("sale_date", desc=True).limit(10).execute()
            sales2 = supabase.table("sales_master_log").select("*").eq("user_id", user_id).order("sale_date", desc=True).limit(10).execute()
            st.dataframe(sales.data)
            st.write('Temporary Data')
            st.dataframe(sales2.data)

    with col2:
        with st.expander('View Expenses',expanded=False):
            st.subheader("💸 Expenses")
            expenses = supabase.table("expenses_master").select("*").eq("user_id", user_id).order("expense_date", desc=True).limit(10).execute()
            st.dataframe(expenses.data)




# To fetch expense naster table  data
@st.cache_data(ttl=7200)
def fetch_expenses_master_data(user_id):
    response = supabase.table("expenses_master").select("*").eq("user_id", user_id).execute()
    data = response.data or []
    
    expenses_df = pd.DataFrame(data)
    
    if not expenses_df.empty:
        return expenses_df
    else:
        print("No data found or an error occurred.")
        return pd.DataFrame()  # Return empty DataFrame instead of None

# Fetch and display the payment data
def fetch_payment_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('payments').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame() 


# to get outstanding debt from the expense table


def get_pending_transactions(user_id):
    sales = supabase.table("sales_master_history") \
        .select("*") \
        .eq("user_id", user_id) \
        .in_("payment_status", ["partial", "credit"]) \
        .execute().data

    purchases = supabase.table("goods_bought_history") \
        .select("*") \
        .eq("user_id", user_id) \
        .in_("payment_status", ["partial", "credit"]) \
        .execute().data

    expenses = supabase.table("expenses_master") \
        .select("*") \
        .eq("user_id", user_id) \
        .in_("payment_status", ["partial", "credit"]) \
        .execute().data

    # Combine all results into one list
    combined = sales + purchases + expenses

    return combined



def insert_payment(user_id, sale_id, purchase_id, amount, payment_method, notes, transaction_date):
    # Example: insert into payments table
    supabase.table("payments").insert({
        "user_id": user_id,
        "sale_history_id": sale_id,
        "purchase_id": purchase_id,
        "amount": amount,
        "payment_method": payment_method,
        "notes": notes,
        "transaction_date": transaction_date,
         "payment_date": datetime.now().isoformat()
    }).execute()


def update_related_tables(user_id, sale_id, purchase_id, new_amount_paid, new_status,outstanding_amount, expense_id=None):
    if sale_id:
        supabase.table("sales_master_history").update({
            "amount_paid": new_amount_paid,
            "payment_status": new_status,
            "amount_balance": outstanding_amount
        }).eq("sale_history_id ", sale_id).execute()
    
    if purchase_id:
        supabase.table("goods_bought_history").update({
            "total_price_paid": new_amount_paid,
            "payment_status": new_status,
            "amount_balance": outstanding_amount
        }).eq("purchase_id", purchase_id).execute()
        # Calculate the amount balance (what's still owed)
        
    
    if expense_id:
        supabase.table("expenses_master").update({
            "amount_paid": new_amount_paid,
            "payment_status": new_status,
            "amount_balance": outstanding_amount
        }).eq("expense_id", expense_id).execute()




# to update paymenin all table, e.g sales, supply, expense from credit to paid
def update_payment_status(table_name, id_column, record_id,user_id):
    # Step 1: Get all payments related to the record
    payment_query = supabase.table("payments").select("amount").eq(id_column, record_id).eq("user_id", user_id).execute()
    total_paid = sum(p["amount"] for p in payment_query.data)

    # Step 2: Get the record from the correct table (sales, expense, or supply)
    if table_name == 'expenses_master':
        record_query = supabase.table('expenses_master').select("total_amount", "payment_status").eq("user_id", user_id).eq(id_column, record_id).single().execute()
        total_amount_key = "total_amount"
    elif table_name == 'sales_master_history':
        record_query = supabase.table('sales_master_history').select("total_amount", "payment_status").eq("user_id", user_id).eq('sale_history_id', record_id).single().execute()
        total_amount_key = "total_amount"
    elif table_name == 'goods_bought_history':
        record_query = supabase.table('goods_bought_history').select("total_cost", "payment_status").eq("user_id", user_id).eq(id_column, record_id).single().execute()
        total_amount_key = "total_cost"
    else:
        return None  # Invalid table
    total_amount = record_query.data[total_amount_key]
    current_status = record_query.data["payment_status"]

    # Step 3: Determine new payment status
    # If it's already paid, we don't change anything
    if current_status == "paid":
        return "paid"

    # If the current status is "credit", keep it as "credit" unless it's fully paid
    if current_status == "credit" and total_paid < total_amount:
        return "credit"
    
    # If the total paid is greater than or equal to the total amount, update to "paid"
    if total_paid >= total_amount:
        new_status = "paid"
    else:
        # If not fully paid, set status to "partial"
        new_status = "partial"

    # Step 4: Update the main record's payment status and amount_paid
    supabase.table('payments').update({
        "payment_status": new_status,
        "amount_paid": total_paid
    }).eq(id_column, record_id).eq("user_id", user_id).execute()

    return new_status

# restock table


with tab2:
    st.title("💰 View Customers with Pending Payments")
    st.caption("Review and Mark Customers with Outstanding Balances.")
    
    
# to get the debtors information and displays it on the payment page
    transactions = get_pending_transactions(user_id)
     
    for tx in transactions:
        # Identify transaction type
        sale_id = tx.get('sale_history_id')
        purchase_id = tx.get('purchase_id')
        expense_id = tx.get('expense_id')

        # Get transaction date from the correct table
        transaction_date = (
            tx.get('sale_date') or 
            tx.get('purchase_date') or 
            tx.get('expense_date') or 
            tx.get('restock_date') or 
            'unknown'
        )

        # Get names
        customer_name = tx.get('customer_name', 'Unknown Customer')
        supplier_name = tx.get('supplier_name', 'Unknown Supplier')
        expense_name = tx.get('vendor_name', 'Unknown Expense')

        # Get amounts
        total_amount = tx.get('total_amount') or 0.0
        amount_paid = tx.get('amount_paid') or 0.0

        total_amount = (
            tx.get('total_cost') or  # restock: total cost (total amount)
            tx.get('total_amount') or  # sales: total amount
            tx.get('expense_total_amount') or  # expenses: total amount
             0.0)
        
        amount_paid = (
              tx.get('total_price_paid') or  # restock: total price paid (amount paid)
              tx.get('amount_paid') or  # sales: amount paid
              tx.get('expense_amount_paid') or  # expenses: amount paid
              0.0)
        
        # Calculate outstanding amount safely
        total_amount = float(total_amount)
        amount_paid = float(amount_paid)
        outstanding_amount = total_amount - amount_paid

        

        # Get status, payment method, due date
        payment_status = tx.get('payment_status', 'unknown')
        payment_method = tx.get('payment_method', 'unknown')
        due_date = tx.get('due_date', 'unknown')

        st.write("---")
        if sale_id:
            st.write(f"**Type:** Sale")
            st.write(f"**Customer:** {customer_name}")
        elif purchase_id:
            st.write(f"**Type:** Purchase")
            st.write(f"**Supplier:** {supplier_name}")
        elif expense_id:
            st.write(f"**Type:** Expense")
            st.write(f"**Expense Item:** {expense_name}")

        st.write(f"**Total Amount:** ₦{total_amount}")
        st.write(f"**Amount Paid:** ₦{amount_paid}")
        st.write(f"**Outstanding Amount:** ₦{outstanding_amount}")
        st.write(f"**Payment Status:** {payment_status}")
        st.write(f"**Payment Method:** {payment_method}")
        st.write(f"**Due Date:** {due_date}")
        st.write(f"**Transaction Date:** {transaction_date}")

        # Make sure outstanding transactions (partial or credit) can be updated
        if payment_status in ['partial', 'credit']:
            col1, col2 = st.columns(2)
            with col1:
                update_type = st.radio(
                    f"Select update type",
                    ["Partial Payment", "Fully Paid"],
                    key=f"update_type_{sale_id or purchase_id or expense_id or str(uuid.uuid4())}"
                )
            with col2:
                if update_type == "Partial Payment":
                    if outstanding_amount > 0:
                        partial_amount = st.number_input(
                           f"Amount paying now (₦)",
                           min_value=0.0,
                           max_value=outstanding_amount,
                           key=f"partial_amount_{sale_id or purchase_id or expense_id or str(uuid.uuid4())}")
                    else:
                        st.warning("❗ Outstanding amount is zero or negative. Cannot accept partial payment.")
                        partial_amount = 0.0
                else:
                    partial_amount = outstanding_amount

            if st.button(f"💰 Update Payment", key=f"update_btn_{sale_id or purchase_id or expense_id or str(uuid.uuid4())}"):
                new_amount_paid = amount_paid + partial_amount
                new_status = "paid" if new_amount_paid >= total_amount else "partial"

                # Insert payment record
                insert_payment(
                    user_id, sale_id, purchase_id, partial_amount, 
                    payment_method, f"{update_type} via dashboard", transaction_date
                )

                # Update related tables
                update_related_tables(user_id, sale_id, purchase_id, new_amount_paid, new_status, outstanding_amount,expense_id)

                st.success(f"✅ Payment updated! New status: **{new_status.upper()}**")
                # 💥 REFRESH transactions from the database
                transactions = get_pending_transactions(user_id)
                st.rerun()





# To get payment table
    with st.expander('View All Payments'):
        payment_df=fetch_payment_history(user_id)
        if not payment_df.empty:
            st.write('All payments',payment_df)
            st.write('Last 10 rows', payment_df.tail(10))
        else:
            st.error("❌ No data found!")# 

    



# ========== ADD EXPENSE ==========
def get_paid_expenses(user_id):
    # Fetch records where payment status is "paid"
    paid_expenses = supabase.table("expenses_master").select("*").eq("payment_status", "paid").eq("user_id", user_id).execute()
    return paid_expenses.data



# Function to update payment and change payment status
def update_payment(expense_id, payment_amount,user_id):
    # Get the current expense record
    expense = supabase.table("expenses_master").select("*").eq("id", expense_id).eq("user_id", user_id).execute().get("data", [])[0]
    
    if expense:
        # Calculate the new amount paid
        new_amount_paid = expense.get("amount_paid", 0) + payment_amount
        
        # Check if the full amount has been paid
        if new_amount_paid >= expense["total_amount"]:
            new_payment_status = "paid"
            new_amount_paid = expense["total_amount"]  # Ensure amount paid doesn't exceed total
        else:
            new_payment_status = expense["payment_status"]  # Keep the same status if partial payment

        # Update the database with new payment info
        updated_data = {
            "amount_paid": new_amount_paid,
            "payment_status": new_payment_status
        }
        
        # Update the expense record
        supabase.table("expenses_master").update(updated_data).eq("id", expense_id).eq("user_id", user_id).execute()

        return new_payment_status
    return None






with tab3:
    st.header("Record a New Expense")

    
    employee_name=st.text_input("user",value= user_name, disabled=True,key="expense_name_input")

    employee_id=st.text_input("user",value= user_id, disabled=True)

    expense_date = st.date_input("Expense Date", value=date.today(), key="exp_date")
    vendor_name = st.text_input("Vendor Name")
    total_exp_amount = st.number_input("Total Amount", min_value=0.0, key="amt2")
    exp_payment_method = st.selectbox("Payment Method", ["cash", "card", "transfer"], key="pm2")
    exp_payment_status = st.selectbox("Payment Status", ["paid", "credit", "partial"], key="ps2")
    exp_due_date = st.date_input("Due Date", value=date.today(), key="dd2") if exp_payment_status != "paid" else None
    exp_invoice_number = st.text_input("Invoice Number (optional)", key="inv2")
    exp_notes = st.text_area("Notes", key="note2")

    # Show amount paid only for credit or partial payments
    amount_paid = None
    if exp_payment_status in ["credit", "partial"]:
        amount_paid = st.number_input("Amount Paid", min_value=0.0, max_value=total_exp_amount, key="amt_paid")
        remaining_balance = total_exp_amount - amount_paid
        st.info(f"💰 Remaining Balance: {remaining_balance:.2f}")

    # Upload invoice if not fully paid
    # Upload Invoice File (Optional)
    st.markdown("📎 **Upload Invoice (PDF/Image)**")
    exp_invoice_file = st.file_uploader("Upload Invoice", type=["pdf", "jpg", "jpeg", "png"], key="exp_file")
    exp_invoice_file_url = None
    # to name the file
    user_invoice_name = st.text_input("Enter desired invoice name (without extension)", value=f"invoice_{employee_id}_{date.today().isoformat()}")
    
    if st.button("💾 Save Expense"):
        error_msgs = []
        if exp_payment_status in ["paid", "credit", "partial"] and not (exp_invoice_number or exp_invoice_file):
            error_msgs.append("📄 Please provide either an invoice number or upload the invoice file for paid, credit, or partial expenses.")
        if not vendor_name:
            error_msgs.append("🏪 Vendor name is required.")
        if total_exp_amount == 0.0:
            error_msgs.append("💰 Expense amount must be greater than zero.")
        # --- Stop if any validation errors exist ---
        if error_msgs:
            for msg in error_msgs:
                st.error(msg)
            st.stop()
            
        if exp_invoice_file:
                extension = os.path.splitext(exp_invoice_file.name)[1]
                safe_name = user_invoice_name.strip().replace(" ", "_")
                unique_suffix = uuid.uuid4().hex[:8]
                filename = f"{safe_name}_{unique_suffix}{extension}"
                st.write(f"Uploading file as: {filename}")
                exp_invoice_file_url = upload_invoice(exp_invoice_file,"salesinvoices", filename,user_id)
                if exp_invoice_file_url:
                    st.success("✅ Invoice uploaded successfully!")
                    st.write(f"[View Invoice]({exp_invoice_file_url})")
                else:
                    st.warning("⚠️ Invoice not uploaded. Please check for errors above.")
         # upload inoive when i click save
       
        exp_data = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "user_id":user_id,
            "expense_date": str(expense_date),
            "vendor_name": vendor_name,
            "total_amount": total_exp_amount,
            "payment_method": exp_payment_method,
            "payment_status": exp_payment_status,
            "due_date": str(exp_due_date) if exp_due_date else None,
            "invoice_number": exp_invoice_number,
            "invoice_file_url": exp_invoice_file_url,
            "notes": exp_notes,
            "amount_paid": amount_paid if amount_paid is not None else total_exp_amount  # Full if "paid"
        }
        supabase.table("expenses_master").insert(exp_data).execute()
        st.success("✅ Expense recorded successfully!")
        st.rerun()


    
# Streamlit form to make a payment

    df_expenses = fetch_expenses_master_data(user_id)
    with st.expander('View Expenses table'):
        if df_expenses is not None:
            st.write('expenses table')
            st.dataframe(df_expenses)  # Display the DataFrame in Streamlit
        else:
            st.write("Error fetching data from the database.")



   
with tab4:
    st.header("🗑️ Delete Sale or Expense Record by table ID")
    
    if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()

    sale_or_expense_id = st.text_input("Enter Sale ID or Expense ID to Delete", "")
    user_id = st.session_state.get("user_id")

    sales_history_data = None
    sales_log_data = None
    selected_sale = None
    selected_expense = None

    if sale_or_expense_id:
        # 🔍 Search for Sale record
        sales_history_data = supabase.table("sales_master_history").select("*").eq("sale_id", sale_or_expense_id).eq("user_id", user_id).execute().data
        sales_log_data = supabase.table("sales_master_log").select("*").eq("sale_id", sale_or_expense_id).eq("user_id", user_id).execute().data

        # 🔍 If not sale, check Expense
        if not sales_history_data and not sales_log_data:
            expense_data = supabase.table("expenses_master").select("*").eq("expense_id", sale_or_expense_id).eq("user_id", user_id).execute().data
            if expense_data:
                selected_expense = expense_data[0]

    # ========================= 💼 DELETE SALE =========================
    if sales_history_data:
        selected_sale = sales_history_data[0]
    elif sales_log_data:
        selected_sale = sales_log_data[0]

    if selected_sale:
        st.subheader("Sale Details to Delete")
        st.write(f"**Invoice Number:** {selected_sale['invoice_number']}")
        st.write(f"**Item Name:** {selected_sale['item_name']}")
        st.write(f"**Quantity Sold:** {selected_sale['quantity']}")
        st.write(f"**Total Amount:** {selected_sale['total_amount']}")
        st.write(f"**Sale Date:** {selected_sale['sale_date']}")
        st.write(f"**Employee Name:** {selected_sale['employee_name']}")

        if st.button("🗑️ Delete This Sale"):
            try:
                # 1. Delete from sales_master_history
                if sales_history_data:
                    supabase.table("sales_master_history").delete().eq("sale_id", selected_sale["sale_id"]).eq("user_id", user_id).execute()

                # 2. Delete from sales_master_log
                if sales_log_data:
                    supabase.table("sales_master_log").delete().eq("sale_id", selected_sale["sale_id"]).eq("user_id", user_id).execute()

                # 3. Update inventory: subtract the sold quantity from stock_out
                item_id = selected_sale.get("item_id")
                quantity_sold = selected_sale.get("quantity")

                if item_id and quantity_sold:
                    inventory_item = supabase.table("inventory_master_log").select("stock_out").eq("item_id", item_id).eq("user_id", user_id).single().execute().data
                    if inventory_item:
                        current_quantity = inventory_item.get("stock_out", 0)
                        new_quantity = max(current_quantity - quantity_sold, 0)

                        supabase.table("inventory_master_log").update({"stock_out": new_quantity}).eq("item_id", item_id).eq("user_id", user_id).execute()

                st.success("✅ Sale record deleted and inventory updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to delete sale: {e}")

    # ========================= 💼 DELETE EXPENSE =========================
    elif selected_expense:
        st.subheader("Expense Record to Delete")
        st.write(f"**Vendor Name:** {selected_expense['vendor_name']}")
        st.write(f"**Total Amount:** ₦{selected_expense['total_amount']}")
        st.write(f"**Expense Date:** {selected_expense['expense_date']}")
        st.write(f"**Employee:** {selected_expense['employee_name']}")

        if st.button("🗑️ Delete This Expense Record"):
            try:
                supabase.table("expenses_master").delete().eq("expense_id", selected_expense["expense_id"]).eq("user_id", user_id).execute()
                st.success("✅ Expense record deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to delete expense: {e}")

    # ========================= ❌ NOTHING FOUND =========================
    elif sale_or_expense_id:
        st.error("❌ No sale or expense record found with the given ID.")




def fetch_sale_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('sales_master_history').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data





# --- Report sections ---
from datetime import date, timedelta


with tab5:
    if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()
    st.subheader("📊 Sales Summary Report")

    # Fetch sales and expenses data
    df = fetch_sale_history(user_id)
    expenses_df = fetch_expenses_master_data(user_id)

    if df.empty:
        st.warning("No sales history found.")
    else:
        import plotly.express as px
        import numpy as np

        # --- Clean and prepare sales data ---
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
        df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
        df["amount_paid"] = pd.to_numeric(df.get("amount_paid", pd.Series([0]*len(df))), errors="coerce")
        df["quantity"] = pd.to_numeric(df.get("quantity", pd.Series([0]*len(df))), errors="coerce")

        # Drop rows with invalid dates
        df = df.dropna(subset=["sale_date"])

        # Set default start/end dates from sales or fallback
        default_start = date.today() 
        default_end = date.today()

        # Let users pick any date, defaulting to 30 days ago and today
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=default_start)
        with col2:
            end_date = st.date_input("End Date", value=default_end)

        # Filter sales data based on selected dates
        filtered_sales = df[
            (df["sale_date"].dt.date >= start_date) &
            (df["sale_date"].dt.date <= end_date)
        ]

        if expenses_df is not None and not expenses_df.empty:
            for col in ['expense_date', 'total_amount', 'amount_paid']:
                if col not in expenses_df.columns:
                    expenses_df[col] = pd.NA
            expenses_df["expense_date"] = pd.to_datetime(expenses_df["expense_date"], errors="coerce")
            expenses_df["total_amount"] = pd.to_numeric(expenses_df["total_amount"], errors="coerce")
            expenses_df["amount_paid"] = pd.to_numeric(expenses_df["amount_paid"], errors="coerce")

            filtered_expenses = expenses_df[
                (expenses_df["expense_date"].dt.date >= start_date) &
                (expenses_df["expense_date"].dt.date <= end_date)
            ]
        else:
            st.warning("⚠️ No expenses data found.")
            filtered_expenses = pd.DataFrame(columns=['expense_date', 'total_amount', 'amount_paid'])

        # --- Summary Metrics ---
        
        total_sales = filtered_sales["total_amount"].sum()
        total_paid = filtered_sales["amount_paid"].sum()
        total_credit = (filtered_sales["total_amount"] - filtered_sales["amount_paid"]).sum()

        total_expenses = filtered_expenses["total_amount"].sum()
        expenses_paid = filtered_expenses["amount_paid"].sum()
        expenses_credit = (filtered_expenses["total_amount"] - filtered_expenses["amount_paid"]).sum()

        profit = total_paid - expenses_paid

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Sales", f"₦{total_sales:,.2f}")
        col2.metric("🧾 Amount Paid", f"₦{total_paid:,.2f}")
        col3.metric("🧮 Credit Owed", f"₦{total_credit:,.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("💸 Total Expenses", f"₦{total_expenses:,.2f}")
        col5.metric("✅ Expenses Paid", f"₦{expenses_paid:,.2f}")
        col6.metric("🕗 Expenses Credit", f"₦{expenses_credit:,.2f}")

        st.metric("📈 Estimated Profit", f"₦{profit:,.2f}")

         # --- Payment Method Breakdown ---
        if "payment_method" in filtered_sales.columns:
            # Filter for only Card, Transfer, Cash methods
            common_methods = ["Card", "Transfer", "Cash"]
            method_filtered = filtered_sales[filtered_sales["payment_method"].isin(common_methods)]
            if not method_filtered.empty:
                st.markdown("### 💳 Payment Method Summary (Card / Transfer / Cash)") 
                # Group and sum
                method_summary = (
                    method_filtered
                    .groupby("payment_method")["total_amount"]
                    .sum()
                    .reset_index()
                    .sort_values("total_amount", ascending=False))
                method_summary.columns = ["Payment Method", "Total Sales (₦)"]
                st.dataframe(method_summary)

                # Pie chart
                fig = px.pie(method_summary,
                             names="Payment Method",
                               values="Total Sales (₦)",
                               title="Sales Distribution by Payment Method" )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales with Card, Transfer, or Cash method.")
        else:
            st.warning("No 'payment_method' column found in data.")


        # --- Pie Charts ---
        st.markdown("### 🥧 Payment Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            if "payment_status" in filtered_sales.columns and not filtered_sales.empty:
                fig1 = px.pie(filtered_sales, names="payment_status", title="Payment Status")
                st.plotly_chart(fig1, use_container_width=True)
        with col2:
            if "payment_method" in filtered_sales.columns and not filtered_sales.empty:
                fig2 = px.pie(filtered_sales, names="payment_method", title="Payment Method")
                st.plotly_chart(fig2, use_container_width=True)

        # --- Line Chart: Sales Over Time ---
        st.markdown("### ⏱️ Sales Over Time")
        if not filtered_sales.empty:
            sales_time = (filtered_sales
                .groupby(filtered_sales["sale_date"].dt.to_period("D"))
                .agg(total_sales=("total_amount", "sum"))
                .reset_index())
            sales_time["sale_date"] = sales_time["sale_date"].dt.to_timestamp()
            if len(sales_time) >= 2:
                sales_time["date_ordinal"] = sales_time["sale_date"].map(pd.Timestamp.toordinal)
                slope, intercept = np.polyfit(sales_time["date_ordinal"], sales_time["total_sales"], 1)
                sales_time["trendline"] = slope * sales_time["date_ordinal"] + intercept

                fig3 = px.line(sales_time, x="sale_date", y="total_sales", markers=True, title="Total Sales Over Time")
                fig3.add_scatter(x=sales_time["sale_date"], y=sales_time["trendline"], mode="lines",
                         name="Trendline", line=dict(dash="dash", color="red"))
                st.plotly_chart(fig3, use_container_width=True)

                if slope > 0:
                    st.success(f"✅ Sales are increasing over time, with an average daily growth of ₦{slope:,.2f}.")
                elif slope < 0:
                    st.warning(f"⚠️ Sales are decreasing over time, dropping by approximately ₦{abs(slope):,.2f} per day.")
                else:
                    st.info("➖ Sales have remained stable over the selected period.")

            else:
                st.info("ℹ️ Not enough data points to determine a trend.")
        else:
            st.info("ℹ️ Not enough data points to determine a trend.")

        # --- Top Products ---
        st.markdown("### 🏆 Top Selling Products")
        if "item_name" in filtered_sales.columns and not filtered_sales.empty:
            top_products = filtered_sales.groupby("item_name").agg(
                Quantity_Sold=("quantity", "sum"),
                Total_Sales=("total_amount", "sum"),
                Sales_Count=("item_name", "count")
            ).sort_values("Quantity_Sold", ascending=False).reset_index()
            st.dataframe(top_products)
            
        st.markdown("### Low Selling Products")
        if "item_name" in filtered_sales.columns:
            low_products = filtered_sales.groupby("item_name").agg(
            Quantity_Sold=("quantity", "sum"),
            Total_Sales=("total_amount", "sum")
        ).sort_values("Quantity_Sold").reset_index()
        st.dataframe(low_products.head(10))


        # --- Top Customers ---
        st.markdown("### 👤 Top Customers")
        if "customer_name" in filtered_sales.columns and not filtered_sales.empty:
            top_customers = filtered_sales.groupby("customer_name").agg(
                Total_Spent=("total_amount", "sum"),
                Purchases=("customer_name", "count")
            ).sort_values("Total_Spent", ascending=False).reset_index()
            st.dataframe(top_customers)

        # --- Credit Sales ---
        st.markdown("### 🧾 Credit Sales")
        credit_sales = filtered_sales[filtered_sales["amount_paid"] < filtered_sales["total_amount"]]
        st.dataframe(credit_sales)

        # --- Partial Payments ---
        st.markdown("### ⚖️ Partial Payments")
        partial_sales = filtered_sales[
            (filtered_sales["amount_paid"] > 0) & (filtered_sales["amount_paid"] < filtered_sales["total_amount"])
        ]
        st.dataframe(partial_sales)

        # --- All Sales ---
        st.markdown("### 📋 All Sales Records")
        st.dataframe(filtered_sales.sort_values("sale_date", ascending=False).reset_index(drop=True))

        # --- Unpaid Expenses ---
        st.markdown("### 🧾 Unpaid Expenses")
        unpaid_expenses = filtered_expenses[filtered_expenses["amount_paid"] < filtered_expenses["total_amount"]]
        st.dataframe(unpaid_expenses)
