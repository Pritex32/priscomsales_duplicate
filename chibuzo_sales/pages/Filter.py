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
from streamlit_extras.switch_page_button import switch_page 
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


import logging

from datetime import datetime, timedelta, timezone



# to show spiner rotating when the app is laoding
 #Only show spinner on first load
if "loaded" not in st.session_state:
    st.markdown("""
        <style>
        .loader {
          border: 4px solid #f3f3f3;
          border-top: 4px solid #00FFC6;
          border-radius: 50%;
          width: 30px;
          height: 30px;
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
        "exp": datetime.now(timezone.utc) + timedelta(hours=4),
        "iat": datetime.now(timezone.utc)  # issued at
    }
    
    token = jwt.encode(payload, jwt_SECRET_KEY, algorithm=ALGORITHM)
    return token
def decode_jwt(token):
    try:
        return jwt.decode(token, jwt_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


from supabase import create_client
# supabase configurations
@st.cache_resource
def get_supabase_client():
    supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
    try:
        supabase = create_client(supabase_url, supabase_key)
       
        return supabase

    except Exception as e:
        st.error("❌ Failed to connect to database. Please check your internet or try again later.")
        # Optional: Print or log error for debugging during development
        # st.write(e)
        st.stop()
    
# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database




def sync_plan_from_db(user_id):
    try:
        response = supabase.table("subscription").select("*").eq("user_id", user_id).order("expires_at", desc=True).limit(1).execute()
        data = response.data

        if data:
            sub = data[0]
            plan = sub.get("plan", "free")
            is_active = sub.get("is_active", False)

            # Update session
            st.session_state.plan = plan
            st.session_state.is_active = is_active

            # Update token with correct plan
            username = st.session_state.get("username", "")
            role = st.session_state.get("role", "user")
            email = st.session_state.get("user_email", "")

            token = generate_jwt(user_id, username, role, plan, is_active, email)
            st.session_state.jwt_token = token

            # Update localStorage with new token
            st.markdown(f"""
                <script>
                    localStorage.setItem("login_token", "{token}");
                </script>
            """, unsafe_allow_html=True)
        else:
            st.session_state.plan = "free"
            st.session_state.is_active = False

    except Exception as e:
        st.error(f"❌ Failed to sync subscription info. ")


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
                if user_data["role"] == "employee":
                    st.session_state.employee_user = {"name": user_data["username"]}
            else:
                # 🛑 Token is invalid or expired — force logout
                st.session_state.clear()
                st_javascript("""localStorage.removeItem("login_token");""")
                st.session_state.login_failed = True


# Run this first
restore_login_from_jwt()

# === Session Validation ===
# === Session Validation === # this stops you when you are logged out
if not st.session_state.get("logged_in"):
    st.markdown("""
        <div style="
            background-color: #ffe6e6;
            border-left: 6px solid #ff4d4d;
            padding: 16px;
            border-radius: 8px;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        ">
            <h3 style="color: #cc0000; margin: 0 0 10px;">❌ Session Expired</h3>
            <p style="color: #333; font-size: 16px; margin: 0;">
                Your session has expired. Redirecting to login page..
            </p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    switch_page("Dashboard")
   
   


if not st.session_state.get("logged_in"):
    st.stop()  # this stop the app from running after login expires


user_id = st.session_state.get("user_id")
if not user_id:
    st.error("❌ No valid user ID in session. Please log in again.")
    st.stop()

try:
    user_id = int(user_id)
except Exception:
    st.error("❌ User ID is not a valid integer.")
    st.stop()

# this changes all buttons to green
st.markdown("""
    <style>
    /* Style all Streamlit buttons */
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 16px;
        transition: background-color 0.3s ease;
    }

    /* Optional: Add hover effect */
    div.stButton > button:hover {
        background-color: #45a049;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)






if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    st.warning("Please log in first.")
    st.stop()








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

        # Check if response contains an error (even if no exception is raised)
        if hasattr(response, "error") and response.error:
            raise Exception(response.error)  # Manually raise an error to trigger the except block

        return pd.DataFrame(response.data) if response.data else pd.DataFrame()

    except Exception as e:
          # This logs the error to file or console
        st.error("❌ Error fetching subscription data. Please check your connection.")
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
        st.error(f"Subscription check failed")

if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    sync_plan_from_db(user_id)
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
            st.error(f"❌ Failed to upload invoice.")

    return None



import re





# to get employee names when logged in and put it in the table along side the record the person inputs , not manually
@st.cache_data(ttl=7200)
def get_employee_dict(user_id):
    # Assuming 'user_id' exists in the 'employees' table
    employees = supabase.table("employees").select("employee_id, name").eq("user_id", user_id).execute()
    return {emp["name"]: emp["employee_id"] for emp in employees.data}
    




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
def fetch_sales_data(user_id):
    
    response = supabase.table("sales_master_history").select("*") \
                .eq("user_id", user_id) \
                .order("sale_date", desc=True) \
                .execute()
    
    data = response.data or []
    
    # Convert the fetched data to a DataFrame
    sales_df = pd.DataFrame(data)
    
    if not sales_df.empty:
        return sales_df
    else:
        st.info("No sales data found or an error occurred.")
        return pd.DataFrame()

@st.cache_data(ttl=7200)
def fetch_expenses_master_data(user_id):
    response = supabase.table("expenses_master").select("*").eq("user_id", user_id).execute()
    data = response.data or []
    
    expenses_df = pd.DataFrame(data)
    
    if not expenses_df.empty:
        return expenses_df
    else:
        st.info("No data found or an error occurred.")

# Fetch and display the payment data
@st.cache_data(ttl=7200) # cache data for 2 hrs
def fetch_payment_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('payments').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame() 













import datetime
from io import BytesIO
# heading
st.markdown(
    """
    <style>
        .custom-title {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            color: #fff;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
            letter-spacing: 1px;
        }
        .custom-title .sub-title {
            color: #ffeb3b; /* ✅ Yellow subtitle */
            font-size: 20px; /* Optional: smaller than main title */
            margin-top: 10px;
            font-weight: normal;
        }
    </style>
    <div class="custom-title">
        📊 Filter Records  <div class="sub-title">Sales | Restock | Expenses | Payments</div>
    </div>
    """,
    unsafe_allow_html=True
)



# ✅ Fetch Data (From your cached Supabase functions)
restock_df = fetch_goods_bought_history(user_id)
sales_df = fetch_sales_data(user_id)
expenses_df = fetch_expenses_master_data(user_id)
payment_df = fetch_payment_history(user_id)

# ✅ Table Selection
table_option = st.selectbox("Select Table", ["Sales", "Restock", "Expenses", "Payments"])

# ✅ Helper: Download Button Function
def download_button(df, filename):
    if not df.empty:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="⬇ Download as Excel",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Download as CSV",
            data=csv_data,
            file_name=filename.replace(".xlsx", ".csv"),
            mime="text/csv"
        )

# ========================================
# ✅ SALES FILTERS
# ========================================
if table_option == "Sales" and not sales_df.empty:
    st.subheader("🔍 Filter Sales Data")

    sales_filter_option = st.selectbox(
        "Select a Filter for Sales",
        ["None", "Customer Name", "Employee Name", "Customer Phone", "Item Name", "Sale Date Range"]
    )

    filtered_df = sales_df.copy()

    if sales_filter_option == "Customer Name":
        name = st.text_input("Enter Customer Name")
        if name:
            filtered_df = filtered_df[filtered_df['customer_name'].str.contains(name, case=False, na=False)]

    elif sales_filter_option == "Employee Name":
        employee = st.text_input("Enter Employee Name")
        if employee:
            filtered_df = filtered_df[filtered_df['employee_name'].str.contains(employee, case=False, na=False)]

    elif sales_filter_option == "Customer Phone":
        phone = st.text_input("Enter Customer Phone")
        if phone:
            filtered_df = filtered_df[filtered_df['customer_phone'].str.contains(phone, case=False, na=False)]

    elif sales_filter_option == "Item Name":
        item = st.text_input("Enter Item Name")
        if item:
            filtered_df = filtered_df[filtered_df['item_name'].str.contains(item, case=False, na=False)]

    elif sales_filter_option == "Sale Date Range":
        today = datetime.date.today()
        start_date = st.date_input("Start Date", today)
        end_date = st.date_input("End Date", today)

        if start_date > end_date:
            st.error("⚠ Start date cannot be after end date")
        else:
            # Ensure date column is in datetime format
            filtered_df['sale_date'] = pd.to_datetime(filtered_df['sale_date'], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df['sale_date'] >= pd.to_datetime(start_date)) &
                (filtered_df['sale_date'] <= pd.to_datetime(end_date))
            ]

    st.write("### Filtered Sales Data")
    st.dataframe(filtered_df.tail(10))
    download_button(filtered_df, "filtered_sales.xlsx")

# ========================================
# ✅ RESTOCK FILTERS
# ========================================
elif table_option == "Restock" and not restock_df.empty:
    st.subheader("🔍 Filter Restock Data")

    restock_filter_option = st.selectbox(
        "Select a Filter for Restock",
        ["None", "Item Name", "Restock Date Range"]
    )

    filtered_df = restock_df.copy()

    if restock_filter_option == "Item Name":
        item = st.text_input("Enter Item Name")
        if item:
            filtered_df = filtered_df[filtered_df['item_name'].str.contains(item, case=False, na=False)]

    elif restock_filter_option == "Restock Date Range":
        today = datetime.date.today()
        start_date = st.date_input("Start Date", today)
        end_date = st.date_input("End Date", today)

        if start_date > end_date:
            st.error("⚠ Start date cannot be after end date")
        else:
            filtered_df['purchase_date'] = pd.to_datetime(filtered_df['purchase_date'], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df['purchase_date'] >= pd.to_datetime(start_date)) &
                (filtered_df['purchase_date'] <= pd.to_datetime(end_date))
            ]

    st.write("### Filtered Restock Data")
    st.dataframe(filtered_df.tail(10))
    download_button(filtered_df, "filtered_restock.xlsx")

# ========================================
# ✅ EXPENSE FILTERS
# ========================================
elif table_option == "Expenses" and not expenses_df.empty:
    st.subheader("🔍 Filter Expenses Data")

    expense_filter_option = st.selectbox(
        "Select a Filter for Expenses",
        ["None", "Vendor Name", "Expense Date Range"]
    )

    filtered_df = expenses_df.copy()

    if expense_filter_option == "Vendor Name":
        vendor = st.text_input("Enter Vendor Name")
        if vendor:
            filtered_df = filtered_df[filtered_df['vendor_name'].str.contains(vendor, case=False, na=False)]

    elif expense_filter_option == "Expense Date Range":
        today = datetime.date.today()
        start_date = st.date_input("Start Date", today)
        end_date = st.date_input("End Date", today)

        if start_date > end_date:
            st.error("⚠ Start date cannot be after end date")
        else:
            filtered_df['expense_date'] = pd.to_datetime(filtered_df['expense_date'], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df['expense_date'] >= pd.to_datetime(start_date)) &
                (filtered_df['expense_date'] <= pd.to_datetime(end_date))
            ]

    st.write("### Filtered Expenses Data")
    st.dataframe(filtered_df.tail(10))
    download_button(filtered_df, "filtered_expenses.xlsx")

# ========================================
# ✅ PAYMENT FILTERS
# ========================================
elif table_option == "Payments" and not payment_df.empty:
    st.subheader("🔍 Filter Payments Data")

    payment_filter_option = st.selectbox(
        "Select a Filter for Payments",
        ["None", "Payment Date Range", "Amount", "Payment Method"]
    )

    filtered_df = payment_df.copy()

    if payment_filter_option == "Payment Date Range":
        today = datetime.date.today()
        start_date = st.date_input("Start Date", today)
        end_date = st.date_input("End Date", today)

        if start_date > end_date:
            st.error("⚠ Start date cannot be after end date")
        else:
            filtered_df['payment_date'] = pd.to_datetime(filtered_df['payment_date'], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df['payment_date'] >= pd.to_datetime(start_date)) &
                (filtered_df['payment_date'] <= pd.to_datetime(end_date))
            ]

    elif payment_filter_option == "Amount":
        amount = st.number_input("Enter Amount", min_value=0.0, step=0.01)
        filter_type = st.radio("Filter Type", ["Equal To", "Greater Than or Equal To"])
        if amount > 0:
            if filter_type == "Equal To":
                filtered_df = filtered_df[filtered_df['amount'] == amount]
            else:
                filtered_df = filtered_df[filtered_df['amount'] >= amount]

    elif payment_filter_option == "Payment Method":
        methods = payment_df['payment_method'].dropna().unique().tolist()
        method = st.selectbox("Select Payment Method", methods)
        filtered_df = filtered_df[filtered_df['payment_method'] == method]

    

    st.write("### Filtered Payments Data")
    st.dataframe(filtered_df.tail(10))
    download_button(filtered_df, "filtered_payments.xlsx")

else:
    st.warning("No data available for the selected table.")
