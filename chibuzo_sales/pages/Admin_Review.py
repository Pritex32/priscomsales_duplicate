
import streamlit as st
# to hide streamlit icons
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

 # Protect this page — allow only MDs
if "role" not in st.session_state or st.session_state.role != "md":
    st.warning("🚫 You are not authorized to view this page.")
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
            save_token_to_localstorage(token)

            # ⚠️ Notify user
            st.warning("🔔 Your Pro subscription has expired. You've been downgraded to the Free Plan.")

    except Exception as e:
        st.error(f"Subscription check failed: {e}")

if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    block_if_subscription_expired()
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    block_free_user_if_limit_exceeded()
    show_plan_status()



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


# ✅ Get user ID from session once
user_id = st.session_state.get("user_id")

# ✅ Fetch all unverified sales for this user
unverified_result = (
    supabase
    .table("sales_master_history")
    .select("*")
    .eq("is_verified", False)
    .eq("user_id", user_id)
    .order("sale_date", desc=True)
    .execute()
)

unverified_sales = unverified_result.data or []

# ✅ Optional download as Excel
if unverified_sales:
    df = pd.DataFrame(unverified_sales)
    st.download_button(
        label="📥 Download Unverified Sales as Excel",
        data=df.to_csv(index=False),
        file_name="unverified_sales.csv",
        mime="text/csv"
    )

# ✅ Loop and display each sale inside an expander
for sale in unverified_sales:
    with st.expander(f"🧾 Sale #{sale.get('invoice_number') or sale['sale_id']} — ₦{sale['total_amount']}"):
        st.write(f"**Date:** {sale['sale_date']}")
        st.write(f"**Customer Phone:** {sale.get('customer_phone', 'N/A')}")
        st.write(f"**Customer:** {sale['customer_name']}")
        st.write(f"**Amount:** ₦{sale['total_amount']}")
        st.write(f"**Payment Method:** {sale['payment_method']}")
        st.write(f"**Payment Status:** {sale['payment_status']}")
        st.write(f"**Entered By:** {sale['employee_name']}")

        # ✅ Show uploaded invoice
        invoice_url = sale.get("invoice_file_url")
        if invoice_url:
            if invoice_url.endswith(".pdf"):
                st.markdown(f"[📎 View PDF Invoice]({invoice_url})", unsafe_allow_html=True)
            else:
                st.image(invoice_url, caption="Uploaded Invoice / POP")
        else:
            st.info("No invoice uploaded.")

        # ✅ Admin action form
        with st.form(key=f"verify_form_{sale['sale_id']}"):
            notes = st.text_area("📝 Admin Review / Notes", key=f"note_{sale['sale_id']}")
            verify_button = st.form_submit_button("✅ Mark as Verified")
            flag_button = st.form_submit_button("🚩 Flag Sale")

            if verify_button:
                supabase.table("sales_master_history").update({
                    "is_verified": True,
                    "verified_by": st.session_state.get("user_email", "admin"),
                    "verified_at": str(datetime.now()),
                    "verification_notes": notes
                }).eq("sale_id", sale["sale_id"]).eq("user_id", user_id).execute()
                st.success("✅ Sale marked as verified.")
                st.rerun()

            if flag_button:
                update = {
                    "is_verified": False,
                    "verified_by": st.session_state.get("user_email", "admin"),
                    "verified_at": str(datetime.now()),
                    "verification_notes": f"[FLAGGED] {notes or 'Flagged for follow-up'}"
                }
                supabase.table("sales_master_history").update(update).eq("sale_id", sale["sale_id"]).eq("user_id", user_id).execute()
                st.warning("🚩 Sale has been flagged.")
                st.rerun()




# Assume you have a list of sales (e.g., from Supabase)
# Example: sales_list = fetch_sales_data(user_id)
user_id = st.session_state.get("user_id")



# Assume you have a list or DataFrame of sales (e.g., from Supabase)
# sales_list = fetch_sales_data(user_id)

st.subheader('🧾 View Sales Invoice Records')

# ✅ Get user ID from session
user_id = st.session_state.get("user_id", None)

# ✅ Check if user is logged in
if user_id:
    # 🔁 Fetch data
    sales_list = fetch_sales_data(user_id)  # Replace with your actual function
    sales_df = pd.DataFrame(sales_list)

    with st.expander("📄 View Your Sales Invoice History"):
        if sales_df is not None and not sales_df.empty:
            st.write("### Sales Summary with Invoice Preview")

            # 🧼 Clean and prepare data
            sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"], errors="coerce")
            sales_df["total_amount"] = pd.to_numeric(sales_df["total_amount"], errors="coerce")

            if "sale_date" in sales_df.columns:
                sales_df = sales_df.sort_values(by="sale_date", ascending=False)

            # ----------------------- 🔍 FILTERS -----------------------
            st.subheader("🔍 Filter Options")

            customer_filter = st.text_input("Search by Customer Name")

            item_options = sales_df["item_name"].dropna().unique().tolist()
            item_filter = st.selectbox("Filter by Item Bought", options=["All"] + item_options)

            # 📅 Date range
            min_date = sales_df["sale_date"].min()
            max_date = sales_df["sale_date"].max()
            start_date = st.date_input("🗓️ Start Date", value=min_date,key="sales_start_date")
            end_date = st.date_input("🗓️ End Date", value=max_date,key="sales_end_date")

            # ------------------- ✅ APPLY FILTERS --------------------
            filtered_sales = sales_df.copy()

            if customer_filter:
                filtered_sales = filtered_sales[
                    filtered_sales["customer_name"].str.contains(customer_filter, case=False, na=False)
                ]

            if item_filter != "All":
                filtered_sales = filtered_sales[filtered_sales["item_name"] == item_filter]

            filtered_sales = filtered_sales[
                (filtered_sales["sale_date"] >= pd.to_datetime(start_date)) &
                (filtered_sales["sale_date"] <= pd.to_datetime(end_date))
            ]

            # ------------------- 📋 SHOW RESULTS -------------------
            if not filtered_sales.empty:
                st.success(f"Showing {len(filtered_sales)} matching sales invoice(s)")
                for _, sale in filtered_sales.iterrows():
                    st.subheader(f"🧾 Sale #{sale.get('invoice_number') or sale.get('sale_id')}")

                    st.write(f"**Customer Name:** {sale.get('customer_name', 'N/A')}")
                    st.write(f"**Item Bought:** {sale.get('item_name', 'N/A')}")
                    st.write(f"**Sale Date:** {sale.get('sale_date', 'N/A')}")
                    st.write(f"**Total Amount Paid:** ₦{sale.get('total_amount', 'N/A')}")

                    st.write("**Invoice:**")
                    invoice_url = sale.get("invoice_file_url")

                    if invoice_url:
                        if invoice_url.endswith(".pdf"):
                            st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                        else:
                            st.image(invoice_url, caption=f"Invoice for Sale #{sale.get('invoice_number') or sale.get('sale_id')}")
                    else:
                        st.info("No invoice file uploaded.")

                    st.markdown("---")
            else:
                st.info("No matching sales invoices found based on the filters.")
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

st.subheader('View Good Bought Invoice Hstory')

# ✅ Get user ID from session
user_id = st.session_state.get("user_id", None)

# ✅ Check if user is logged in
if user_id:
    # 🔁 Fetch data
    df_url = fetch_goods_bought_history(user_id)

    with st.expander("📄 View Your Goods Bought Invoice History"):
        if df_url is not None and not df_url.empty:
            st.write("### Goods Bought History with Invoice Preview")

            # 🧼 Clean and prepare data
            df_url["purchase_date"] = pd.to_datetime(df_url["purchase_date"], errors="coerce")
            df_url["total_price_paid"] = pd.to_numeric(df_url["total_price_paid"], errors="coerce")

            if "purchase_date" in df_url.columns:
                df_url = df_url.sort_values(by="purchase_date", ascending=False)

            # ----------------------- 🔍 FILTERS -----------------------
            st.subheader("🔍 Filter Options")

            item_filter = st.text_input("Search by Item Name")

            customer_options = df_url["supplier_name"].dropna().unique().tolist()
            customer_filter = st.selectbox("Filter by Supplier Name", options=["All"] + customer_options)

            # 📅 Date range
            min_date = df_url["purchase_date"].min()
            max_date = df_url["purchase_date"].max()
            start_date = st.date_input("🗓️ Start Date", value=min_date,key="goods_start_date")
            end_date = st.date_input("🗓️ End Date", value=max_date,key="goods_end_date")

           
            # ------------------- ✅ APPLY FILTERS --------------------
            filtered_df = df_url.copy()

            if item_filter:
                filtered_df = filtered_df[filtered_df["item_name"].str.contains(item_filter, case=False, na=False)]

            if customer_filter != "All":
                filtered_df = filtered_df[filtered_df["supplier_name"] == customer_filter]

           
                filtered_df = filtered_df[
                 (filtered_df["purchase_date"] >= pd.to_datetime(start_date)) &
                 (filtered_df["purchase_date"] <= pd.to_datetime(end_date))]

           
            # ------------------- 📋 SHOW RESULTS -------------------
            if not filtered_df.empty:
                st.success(f"Showing {len(filtered_df)} matching invoice(s)")
                for _, item in filtered_df.iterrows():
                    st.subheader(f"🛒 Item: {item.get('item_name', 'Unknown')}")

                    st.write(f"**Supplier:** {item.get('supplier_name', 'N/A')}")
                    st.write(f"**Purchase Date:** {item.get('purchase_date', 'N/A')}")
                    st.write(f"**Total Price Paid:** ₦{item.get('total_price_paid', 'N/A')}")

                    invoice_url = item.get("invoice_file_url")
                    st.write("**Invoice:**")

                    if invoice_url:
                        if invoice_url.endswith(".pdf"):
                            st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                        else:
                            st.image(invoice_url, caption=f"Invoice for {item.get('item_name', '')}")
                    else:
                        st.info("No invoice file uploaded.")
                    
                    st.markdown("---")
            else:
                st.info("No matching invoices found based on the filters.")
        else:
            st.info("ℹ️ No purchase history found for this user.")
else:
    st.warning("⚠️ Please log in to view your invoice history.")



st.header('Expense Invoice')
@st.cache_data(ttl=7200)
def fetch_expenses_master_data(user_id):
    try:
        response = supabase.table("expenses_master").select("*").eq("user_id", user_id).execute()
        data = response.data or []
        expenses_df = pd.DataFrame(data)

        if expenses_df.empty:
            print("No data found.")
        return expenses_df  # Always return a DataFrame (even if empty)

    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

st.subheader('💸 View Expense Invoice Records')

# ✅ Get user ID from session
user_id = st.session_state.get("user_id", None)

# ✅ Check if user is logged in
if user_id:
    # 🔁 Fetch data
    expense_df = fetch_expenses_master_data(user_id)

    with st.expander("📄 View Your Expense Invoice Records"):
        if expense_df is not None and not expense_df.empty:
            st.write("### Expense Summary with Invoice Preview")

            # 🧼 Clean and prepare data
            expense_df["expense_date"] = pd.to_datetime(expense_df["expense_date"], errors="coerce")
            expense_df["total_amount"] = pd.to_numeric(expense_df["total_amount"], errors="coerce")
            expense_df["amount_balance"] = pd.to_numeric(expense_df["amount_balance"], errors="coerce")

            if "expense_date" in expense_df.columns:
                expense_df = expense_df.sort_values(by="expense_date", ascending=False)

            # ----------------------- 🔍 FILTERS -----------------------
            st.subheader("🔍 Filter Options")

            vendor_filter = st.text_input("Search by Vendor Name")

            status_options = expense_df["payment_status"].dropna().unique().tolist()
            status_filter = st.selectbox("Filter by Payment Status", options=["All"] + status_options)

            # 📅 Date range
            min_date = expense_df["expense_date"].min()
            max_date = expense_df["expense_date"].max()
            start_date = st.date_input("🗓️ Start Date", value=min_date,key="expense_start_date")
            end_date = st.date_input("🗓️ End Date", value=max_date,key="expense_end_date")

            # ------------------- ✅ APPLY FILTERS --------------------
            filtered_expense = expense_df.copy()

            if vendor_filter:
                filtered_expense = filtered_expense[
                    filtered_expense["vendor_name"].str.contains(vendor_filter, case=False, na=False)
                ]

            if status_filter != "All":
                filtered_expense = filtered_expense[filtered_expense["payment_status"] == status_filter]

            filtered_expense = filtered_expense[
                (filtered_expense["expense_date"] >= pd.to_datetime(start_date)) &
                (filtered_expense["expense_date"] <= pd.to_datetime(end_date))
            ]

            # ------------------- 📋 SHOW RESULTS -------------------
            if not filtered_expense.empty:
                st.success(f"Showing {len(filtered_expense)} matching expense record(s)")
                for _, expense in filtered_expense.iterrows():
                    st.subheader(f"🏷️ Vendor: {expense.get('vendor_name', 'Unknown')}")

                    st.write(f"**Total Amount:** ₦{expense.get('total_amount', 'N/A')}")
                    st.write(f"**Payment Status:** {expense.get('payment_status', 'N/A')}")
                    st.write(f"**Expense Date:** {expense.get('expense_date', 'N/A')}")
                    st.write(f"**Balance:** ₦{expense.get('amount_balance', 'N/A')}")

                    st.write("**Invoice:**")
                    invoice_url = expense.get("invoice_file_url")

                    if invoice_url:
                        if invoice_url.endswith(".pdf"):
                            st.markdown(f"[📎 Open PDF Invoice]({invoice_url})", unsafe_allow_html=True)
                        else:
                            st.image(invoice_url, caption=f"Invoice for {expense.get('vendor_name', '')}")
                    else:
                        st.info("No invoice file uploaded.")

                    st.markdown("---")
            else:
                st.info("No matching expense records found based on the filters.")
        else:
            st.info("ℹ️ No expenses found for this user.")
else:
    st.warning("⚠️ Please log in to view your expense records.")




st.markdown('___')
# Pagination helper
def paginate_dataframe(df, page_size=10):
    page = st.number_input("Page", min_value=1, max_value=max(1, (len(df) - 1) // page_size + 1), step=1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return df.iloc[start_idx:end_idx]

# Unified Deletion UI
def delete_invoice_ui():
    st.header("🗑️ Delete Invoice Records")

    delete_category = st.selectbox("🗂️ Select Category", ["Sales", "Goods Bought", "Expenses"])
    user_id = st.session_state.get("user_id", None)

    if not user_id:
        st.warning("⚠️ Please log in to manage invoices.")
        return

    # ----------------- SALES ------------------
    if delete_category == "Sales":
        sales_data = fetch_sales_data(user_id)
        df = pd.DataFrame(sales_data)

        if not df.empty:
            st.subheader("🔍 Filter Sales Records")
            df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
            customer = st.text_input("Filter by Customer")
            item = st.text_input("Filter by Item")
            start = st.date_input("Start Date", df["sale_date"].min())
            end = st.date_input("End Date", df["sale_date"].max())

            filtered = df.copy()
            if customer:
                filtered = filtered[filtered["customer_name"].str.contains(customer, case=False, na=False)]
            if item:
                filtered = filtered[filtered["item_name"].str.contains(item, case=False, na=False)]
            filtered = filtered[(filtered["sale_date"] >= pd.to_datetime(start)) & (filtered["sale_date"] <= pd.to_datetime(end))]

            if not filtered.empty:
                st.write(f"Found {len(filtered)} sale(s)")
                for idx, row in paginate_dataframe(filtered).iterrows():
                    cols = st.columns([1, 2, 2, 2, 1])
                    cols[0].write(f"**#{idx+1}**")
                    cols[1].write(row.get("customer_name"))
                    cols[2].write(row.get("item_name"))
                    cols[3].write(str(row.get("sale_date")))
                    if cols[4].button("🗑️ Delete", key=f"del_sale_{idx}"):
                        supabase.table("sales_master_history").delete().eq("sale_id", row.get("sale_id")).eq("user_id", user_id).execute()
                        st.success("✅ Sale deleted!")
                        st.rerun()
            else:
                st.info("No matching sales.")

    # ----------------- GOODS BOUGHT ------------------
    elif delete_category == "Goods Bought":
        df = fetch_goods_bought_history(user_id)
        if not df.empty:
            st.subheader("🔍 Filter Goods Bought")
            df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
            supplier = st.text_input("Filter by Supplier")
            item = st.text_input("Filter by Item Name")
            start = st.date_input("Start Date", df["purchase_date"].min())
            end = st.date_input("End Date", df["purchase_date"].max())

            filtered = df.copy()
            if supplier:
                filtered = filtered[filtered["supplier_name"].str.contains(supplier, case=False, na=False)]
            if item:
                filtered = filtered[filtered["item_name"].str.contains(item, case=False, na=False)]
            filtered = filtered[(filtered["purchase_date"] >= pd.to_datetime(start)) & (filtered["purchase_date"] <= pd.to_datetime(end))]

            if not filtered.empty:
                st.write(f"Found {len(filtered)} record(s)")
                for idx, row in paginate_dataframe(filtered).iterrows():
                    cols = st.columns([1, 2, 2, 2, 1])
                    cols[0].write(f"**#{idx+1}**")
                    cols[1].write(row.get("supplier_name"))
                    cols[2].write(row.get("item_name"))
                    cols[3].write(str(row.get("purchase_date")))
                    if cols[4].button("🗑️ Delete", key=f"del_goods_{idx}"):
                        supabase.table("goods_bought_history").delete().eq("purchase_id", row.get("purchase_id")).eq("user_id", user_id).execute()
                        st.success("✅ Goods bought record deleted!")
                        st.rerun()
            else:
                st.info("No matching goods bought records.")

    # ----------------- EXPENSES ------------------
    elif delete_category == "Expenses":
        df = fetch_expenses_master_data(user_id)
        if not df.empty:
            st.subheader("🔍 Filter Expenses")
            df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce")
            vendor = st.text_input("Filter by Vendor")
            status = st.selectbox("Filter by Payment Status", ["All"] + df["payment_status"].dropna().unique().tolist(), key="expense_status")
            start = st.date_input("Start Date", df["expense_date"].min())
            end = st.date_input("End Date", df["expense_date"].max())

            filtered = df.copy()
            if vendor:
                filtered = filtered[filtered["vendor_name"].str.contains(vendor, case=False, na=False)]
            if status != "All":
                filtered = filtered[filtered["payment_status"] == status]
            filtered = filtered[(filtered["expense_date"] >= pd.to_datetime(start)) & (filtered["expense_date"] <= pd.to_datetime(end))]

            if not filtered.empty:
                st.write(f"Found {len(filtered)} expense(s)")
                for idx, row in paginate_dataframe(filtered).iterrows():
                    cols = st.columns([1, 2, 2, 2, 1])
                    cols[0].write(f"**#{idx+1}**")
                    cols[1].write(row.get("vendor_name"))
                    cols[2].write(row.get("payment_status"))
                    cols[3].write(str(row.get("expense_date")))
                    if cols[4].button("🗑️ Delete", key=f"del_exp_{idx}"):
                        supabase.table("expenses_master").delete().eq("expense_id", row.get("expense_id")).eq("user_id", user_id).execute()
                        st.success("✅ Expense deleted!")
                        st.rerun()
            else:
                st.info("No matching expenses.")

# --- Call the UI ---
delete_invoice_ui()












