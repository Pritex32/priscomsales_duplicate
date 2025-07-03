
import streamlit as st
import bcrypt
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime,date, timedelta
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

jwt_SECRET_KEY = "4606"  # Use env vars in production
ALGORITHM = "HS256"

#Decode function
def generate_jwt(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
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

# Run this first
restore_login_from_jwt()

# === Session Validation ===
if not st.session_state.get("logged_in"):
    st.warning("⏳ Waiting for session to restore from browser...")
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

def enforce_free_plan_limit():
    if st.session_state.plan == "free" and not st.session_state.is_active:
        df = fetch_subscription_data(user_id)
        if len(df) >= 10:
            st.error("🚫 Your free plan is exhausted. Please upgrade to continue.")
            st.stop()
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
if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    block_if_subscription_expired()

def show_plan_status():
    if st.session_state.plan == "free" and not st.session_state.is_active:
        st.info("🆓 You are currently on the **Free Plan**. Limited to 10 transactions.")
    elif st.session_state.plan == "pro" and st.session_state.is_active:
        st.success("💼 You are on the **Pro Plan**. Enjoy unlimited access!")
    else:
        st.warning("⚠️ Your subscription status is unclear. Please contact support.")

show_plan_status()
enforce_free_plan_limit()


   # this will check is the person has subcribe or not         
def block_free_user_if_limit_exceeded():
    user_id = st.session_state.get("user_id")
    plan = st.session_state.get("plan", "free")
    is_active = st.session_state.get("is_active", False)

    df = fetch_subscription_data(user_id)
    if plan == "free" and not is_active and len(df) >= 10:
        st.error("🚫 Your free plan is exhausted. Please upgrade to continue using the sales features.")
        st.stop()

#



import tempfile
import mimetypes



# to restrict acess
if st.session_state.get("role") != "md":
    st.error("🚫 Access denied: Only the Managing Director can access this page.")
    st.stop()



#
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
        print("No sales data found or an error occurred.")
        return pd.DataFrame()
    
    





st.header("🔍 Admin - Review Sales & Invoices")
# refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # ✅ Clear cached data
    st.rerun() 

st.caption('Confirm the Amount recieved from sales with invoice')
# ✅ STEP 1: Fetch all unverified sales for the current user
unverified_result = (
    supabase
    .table("sales_master_history")
    .select("*")
    .eq("is_verified", False)
    .eq("user_id", user_id)
    .execute()
)

unverified_sales = unverified_result.data

# ✅ STEP 2: Loop through each sale
for sale in unverified_sales:
    st.markdown("----")
    st.subheader(f"🧾 Sale #{sale['invoice_number'] or sale['sale_id']}")

    st.write(f"**Date:** {sale['sale_date']}")
    st.write(f"**Customer Phone:** {sale.get('customer_phone', 'N/A')}")
    st.write(f"**Customer:** {sale['customer_name']}")
    st.write(f"**Amount:** ₦{sale['total_amount']}")
    st.write(f"**Payment Method:** {sale['payment_method']}")
    st.write(f"**Payment Status:** {sale['payment_status']}")
    st.write(f"**Entered By:** {sale['employee_name']}")

    # ✅ Show uploaded invoice (image or PDF)
    if sale["invoice_file_url"]:
        if sale["invoice_file_url"].endswith(".pdf"):
            st.markdown(f"[📎 View PDF Invoice]({sale['invoice_file_url']})", unsafe_allow_html=True)
        else:
            st.image(sale["invoice_file_url"], caption="Uploaded Invoice / POP")

    # ✅ STEP 3: Admin Verification Form
    user_id = st.session_state.get("user_id")
    with st.form(key=f"verify_form_{sale['sale_id']}"):
        verification_notes = st.text_area("📝 Admin Review / Notes", key=f"note_{sale['sale_id']}")
        verify_button = st.form_submit_button("✅ Mark as Verified")
        flag_button = st.form_submit_button("🚩 Flag Sale")

        if verify_button:
            supabase.table("sales_master_history").update({
                "is_verified": True,
                "verified_by": st.session_state.get("user_email", "admin"),
                "verified_at": str(datetime.now()),
                "verification_notes": verification_notes
            }).eq("sale_id", sale["sale_id"]).eq("user_id", user_id).execute()
            st.success("✅ Sale marked as verified.")
            st.rerun()

        if flag_button:
            supabase.table("sales_master_history").update({
                "is_verified": False,
                "verified_by": st.session_state.get("user_email", "admin"),
                "verified_at": str(datetime.now()),
                "verification_notes": verification_notes or "Flagged for follow-up"
            }).eq("sale_id", sale["sale_id"]).eq("user_id", user_id).execute()
            st.warning("🚩 Sale flagged for review.")
            st.rerun()

        if flag_button:
            update = {
                "is_verified": False,
                "verified_by": st.session_state.get("user_email", "admin"),
                "verified_at": str(datetime.now()),
                "verification_notes": f"[FLAGGED] {verification_notes}"
            }
            supabase.table("sales_master_history").update(update).eq("sale_id", sale["sale_id"]).eq("user_id", user_id).execute()
            st.warning("🚩 Sale has been flagged.")
            st.rerun()






# Assume you have a list of sales (e.g., from Supabase)
# Example: sales_list = fetch_sales_data(user_id)
user_id = st.session_state.get("user_id")

st.header('View Sales Invoice')

# Assume you have a list or DataFrame of sales (e.g., from Supabase)
# sales_list = fetch_sales_data(user_id)

if user_id:
    sales_list = fetch_sales_data(user_id)  # Replace with your function
    sales_df = pd.DataFrame(sales_list)

    if not sales_df.empty and "sale_date" in sales_df.columns:
        # ✅ Ensure sale_date is datetime and sort newest first
        sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])
        sales_df = sales_df.sort_values(by="sale_date", ascending=False)

        with st.expander("🧾 View Sales Invoice"):
            for _, sale in sales_df.iterrows():
                st.subheader(f"Sale #{sale.get('invoice_number') or sale.get('sale_id')}")

                # ✅ Display core sale info
                st.write(f"**Customer Name:** {sale.get('customer_name', 'N/A')}")
                st.write(f"**Item Bought:** {sale.get('item_name', 'N/A')}")
                st.write(f"**Sale Date:** {sale.get('sale_date', 'N/A')}")
                st.write(f"**Total Amount Paid:** ₦{sale.get('total_amount', 'N/A')}")

                # ✅ Invoice Preview
                invoice_url = sale.get("invoice_file_url")

                if invoice_url:
                    st.write("Invoice URL:", invoice_url)

                    if invoice_url.endswith(".pdf"):
                        st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                    else:
                        st.image(invoice_url, caption=f"Invoice for Sale #{sale.get('invoice_number') or sale.get('sale_id')}")
                else:
                    st.info("No invoice file uploaded.")

                st.markdown("---")
    else:
        st.info("ℹ️ No sales records found.")
else:
    st.warning("⚠️ Please log in to view your invoice history.")








@st.cache_data()
def fetch_goods_bought_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('goods_bought_history').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data


df_url = fetch_goods_bought_history(user_id)



# Simulate a logged-in user ID (you would typically get this from session or login state)
user_id = st.session_state.get("user_id", None)

st.header('Goods Bought Invoice')

# Simulate a logged-in user ID (you would typically get this from session or login state)
user_id = st.session_state.get("user_id", None)

# Check if user is logged in
if user_id:
    df_url = fetch_goods_bought_history(user_id)

    with st.expander("📄 View Your Goods Bought Invoice History"):
        if not df_url.empty:
            st.write("### Goods Bought History with Invoice Preview")
            if "purchase_date" in df_url.columns:
                df_url = df_url.sort_values(by="purchase_date", ascending=False)

            for _, item in df_url.iterrows():
                st.subheader(f"Item: {item.get('item_name', 'Unknown')}")

                st.write(f"**Purchase Date:** {item.get('purchase_date', 'N/A')}")
                st.write(f"**Total Price Paid:** ₦{item.get('total_price_paid', 'N/A')}")

                # ✅ Uploaded invoice preview
                st.write("**Invoice:**")
                invoice_url = item.get("invoice_file_url")

                if invoice_url:
                    st.write("Invoice URL:", invoice_url)

                    if invoice_url.endswith(".pdf"):
                        st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                    else:
                        st.image(invoice_url, caption=f"Invoice for {item.get('item_name', '')}")
                else:
                    st.info("No invoice file uploaded.")

                st.markdown("---")
        else:
            st.info("ℹ️ No purchase history found for this user.")
else:
    st.warning("⚠️ Please log in to view your invoice history.")





st.header('Expense Invoice')
@st.cache_data(ttl=7200)
def fetch_expenses_master_data(user_id):
    response = supabase.table("expenses_master").select("*").eq("user_id", user_id).execute()
    data = response.data or []
    
    expenses_df = pd.DataFrame(data)
    
    if expenses_df is not None and not expenses_df.empty:
        return expenses_df
    else:
        print("No data found or an error occurred.")
# Check if user is logged in
if user_id:
    expense_df = fetch_expenses_master_data(user_id)

    with st.expander("💸 View Your Expense Records"):
        if not expense_df.empty:
            st.write("### Expenses Summary")
            if "expense_date" in df_url.columns:
                expense_df = expense_df.sort_values(by="expense_date", ascending=False)

            for idx, expense in expense_df.iterrows():
                st.subheader(f"Vendor: {expense.get('vendor_name', 'Unknown')}")

                st.write(f"**Total Amount:** ₦{expense.get('total_amount', 'N/A')}")
                st.write(f"**Payment Status:** {expense.get('payment_status', 'N/A')}")
                st.write(f"**Expense Date:** {expense.get('expense_date', 'N/A')}")
                st.write(f"**Balance:** ₦{expense.get('amount_balance', 'N/A')}")

                # ✅ Uploaded invoice preview
                st.write("**Invoice:**")
                invoice_url = expense.get("invoice_file_url")

                if invoice_url:
                    st.write("Invoice URL:", invoice_url)

                    if invoice_url.endswith(".pdf"):
                        st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                    else:
                        st.image(invoice_url, caption=f"Invoice for {expense.get('vendor_name', '')}")
                else:
                    st.info("No invoice file uploaded.")

                st.markdown("---")
        else:
            st.info("ℹ️ No expenses found for this user.")
else:
    st.warning("⚠️ Please log in to view your expense records.")
