import streamlit as st
st.set_page_config(page_title="restock", layout="wide")
# to hide streamlit feautres and icons
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
from datetime import datetime, timedelta

from PIL import Image
import io
import os
import plotly.express as px
import numpy as np
from storage3.exceptions import StorageApiError
import tempfile
import mimetypes
import uuid
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import jwt

 # or from auth import initialize_session
# to show spiner rotating when the app is laoding
# Only show spinner on first load
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
def generate_jwt(user_id, username, role,plan="free", is_active=False, email=None,access_code=None):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
         "plan": plan,
        "is_active": is_active,
        "email": email,
        "access_code": access_code,
        "exp": datetime.utcnow() + timedelta(hours=4)
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
                st.session_state.access_code = user_data.get("access_code", "")
                if user_data["role"] == "employee":
                    st.session_state.employee_user = {"name": user_data["username"]}
            else:
                # 🛑 Token is invalid or expired — force logout
                st.session_state.clear()
                st_javascript("""localStorage.removeItem("login_token");""")
                st.session_state.login_failed = True


# Run this first
restore_login_from_jwt()



# this will make all button green
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
                Your session has expired.  Redirecting to login page....
            </p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    switch_page("Dashboard")  # Replace "Login" with your actual login page name
   
    st.stop()
   
    


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





# this shows the logged user info
if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    st.warning("Please log in first.")
    st.stop()



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
        st.error(f"❌ Failed to sync subscription info: ")


# this restores and shows if the person is on free plan or pro
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
        st.warning(f"⚠️ Could not fetch subscription info.")


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
        st.error(f"Error fetching subscription data.")
        return pd.DataFrame()



# to prevent usage after plan expired on employee
def block_if_subscription_expired():
    plan = st.session_state.get("plan", "free")
    is_active = st.session_state.get("is_active", False)
    user_id = st.session_state.get("user_id")

    if plan == "free" or not is_active:
        # Check row count (example: from 'sales' table)
        response1 = supabase.table("goods_bought_history").select("purchase_id", count="exact").eq("user_id", user_id).execute()
        row_count1 = response1.count or 0
        response2 = supabase.table("goods_bought").select("purchase_id", count="exact").eq("user_id", user_id).execute()
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



# to import restock page on home page
# this is to get the user id and make it is rightly restored
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
        st.error(f"Subscription check failed.")

if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    sync_plan_from_db(user_id)
    block_if_subscription_expired()
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    show_plan_status()
    
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
                st.error("❌ Failed to upload invoice due to a system issue. Please try again later.")
        else:  # error_info is a string, just display it
            st.error("❌ Failed to upload invoice. Please ensure the file is valid and try again.")

    return None

    

@st.cache_data(ttl=7200)
def fetch_goods_bought(user_id):
    # Fetch data from 'goods_bought' table
    response = supabase.table('goods_bought').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data

# Fetch the data and cache it
@st.cache_data(ttl=7200)
def fetch_goods_bought_history(user_id):
    # Fetch data from 'goods_bought history' table
    response = supabase.table('goods_bought_history').select('*').eq("user_id", user_id).execute()
    
    if response.data:
        return pd.DataFrame(response.data)  # Convert data to DataFrame
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data


df = fetch_goods_bought(user_id)



# ---------- Utility Functions ----------
def get_employee_dict(user_id):
    employees = supabase.table("employees").select("employee_id, name").eq("user_id", user_id).execute()
    return {emp["name"]: emp["employee_id"] for emp in employees.data}





# ---------- UI Begins ----------
# refresh pages
col5,col7=st.columns([3,1])
with col5:
    st.header("🛒 Record Goods Bought")
with col7:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()  # ✅ Clear cached data
        st.rerun() 


tab1,tab2,tab3,tab4=st.tabs(["🛒Goods_purchased",'🛢️Data','Delete','Report'])

# Get employee dict
employee_dict = get_employee_dict(user_id)

@st.cache_data(ttl=7200)
def fetch_inventory_items(user_id):
    response = supabase.table("inventory_master_log").select("item_id, item_name").eq("user_id", user_id).execute()
      # Show the data in Streamlit
    items = response.data
    item_dict = {item["item_name"]: item["item_id"] for item in items}
    return item_dict

item_dict = fetch_inventory_items(user_id)


## to fetcher the user id
if not st.session_state.get("logged_in"):
    st.warning("Please log in.")
    st.stop()

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")
role = st.session_state.get("role")

if user_id is None:
    st.error("User ID is missing from session.")
    st.stop()

if "role" not in st.session_state or st.session_state.role != "md":
    st.warning("🚫 You are not authorized to view this page.")
    st.stop()
# Purchase details






with tab1:
    
##  this is add new item section
    col1, col2 = st.columns([2, 1])  # Wider left for goods bought, narrower right for add item

    with col1:
        
        st.subheader("📥 Restocks An Item")
        st.markdown("""
        <div style="
            padding: 15px;
            background-color: #e8f5e9;
            border-left: 5px solid #28a745;
            border-radius: 5px;
            font-size: 15px;
            color: #2e7d32;
             margin-bottom: 20px;">
           <strong>👉 First add a new item</strong> before restocking the item over time.
        </div>""", unsafe_allow_html=True)

        

    with col2:
        with st.expander("**➕ Add New Item**"):
            st.markdown("""
            <style>
            [data-testid="stExpander"] summary {
                color: #fd7e14;
                font-weight: bold;
                font-size: 16px;}
            </style>""", unsafe_allow_html=True )
            with st.form("new_item_form"):
                employee_name=st.text_input("user",value= user_name, disabled=True)
                employee_id=st.text_input("user",value= user_id, disabled=True)
                selected_date = st.date_input("Select Date to Update Inventory", value=date.today())
                item_name = st.text_input("Item Name")
                quantity = st.number_input("Initial Quantity Supplied", min_value=0, step=1)
                reorder_level = st.number_input("Reorder Level", min_value=0, step=1)
                unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01)
                supplier = st.text_input("Supplier Name (Optional)")
                purchase_date = st.date_input("Purchase Date", value=date.today())
                description = st.text_area("Description (Optional)")
                payment_status = st.selectbox("Payment Status", ["paid", "credit", "partial"])
                payment_method = st.selectbox("Payment Method", ["cash", "card", "transfer", "cheque"])
                due_date = st.date_input("Due Date", value=date.today()) if payment_status != "paid" else None
                notes = st.text_area("Notes (Optional)")
                invoice_file_url = None
                total_cost = quantity * unit_price
                total_price_paid = 0.0
                if payment_status == "paid":
                    total_price_paid = total_cost
                elif payment_status == "partial":
                    total_price_paid = st.number_input("Total Price Paid", min_value=0.0, max_value=total_cost, step=0.01, format="%.2f")
               
                st.markdown("📎 **Upload Invoice (PDF/Image)**")
                invoice_file = st.file_uploader("Upload Invoice", type=["pdf", "jpg", "jpeg", "png"], key="exp_file_2")
                invoice_name = st.text_input("Enter desired invoice name (without extension)", value=f"invoice_{employee_id}_{date.today().isoformat()}")
                submitted = st.form_submit_button("Add Item")
            
                if submitted:
                    if not item_name or quantity < 0:
                        st.error("❌ Please fill in all required fields.")
                        st.stop()
                          # Check if item already exists
                    else:
                        check_item = supabase.table("inventory_master_log").select("item_name").eq("item_name", item_name).eq("user_id", user_id).execute()

                   
                        if check_item.data:
                            st.warning("⚠️ Item already exists in inventory.")
                        else:
                            invoice_file_url = None
                            if invoice_file:
                                extension = os.path.splitext(invoice_file.name)[1]
                                safe_name = invoice_name.strip().replace(" ", "_")
                                unique_suffix = uuid.uuid4().hex[:8]
                                filename = f"{safe_name}_{unique_suffix}{extension}"
                                st.write(f"Uploading file as: {filename}")
                                invoice_file_url = upload_invoice(invoice_file,"salesinvoices", filename,user_id)
                                if invoice_file_url:
                                    st.success("✅ Invoice uploaded successfully!")
                                    st.write(f"[View Invoice]({invoice_file_url})")
                                else:
                                    st.warning("⚠️ Invoice not uploaded. Please check for errors above.")
                             # Insert into inventory_master_log
                            new_item = {
                                "item_name": item_name,
                                "supplied_quantity": quantity,
                                 "open_balance": 0,
                                "log_date": purchase_date.isoformat(),
                                 "user_id": user_id,
                                "reorder_level": reorder_level}

                            item_response = supabase.table("inventory_master_log").insert(new_item).execute()

                            if item_response.data:
                                new_item_id = item_response.data[0]["item_id"]

                                # Insert into goods_bought
                                restock_entry = {
                                    "item_id": new_item_id,
                                    "user_id": user_id,
                                    "employee_id":employee_id,
                                    "employee_name":employee_name,
                                    "item_name": item_name,
                                    "supplied_quantity": quantity,
                                    "unit_price": unit_price,
                                   "supplier_name": supplier,
                                   "purchase_date": purchase_date.isoformat(),
                                   "payment_status": payment_status,
                                   "payment_method": payment_method,
                                   "due_date": due_date.isoformat() if due_date else None,
                                   "total_price_paid": total_price_paid,
                                   "invoice_file_url": invoice_file_url,
                                    "notes": notes}

                                restock_response = supabase.table("goods_bought_history").upsert(restock_entry).execute()

                                if restock_response.data:
                                    st.success("✅ New item added and restocked successfully.")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Item added, but restock not recorded.")
                            else:
                                st.error("❌ Failed to add item to inventory.")


## this  is the add restock section   

    
    employee_name=st.text_input("user",value= user_name, disabled=True)

    employee_id=st.text_input("user",value= user_id, disabled=True)
    purchase_date = st.date_input("Purchase Date", value=date.today())
    supplier_name = st.text_input("Supplier Name")
    supplier_phone=st.text_input('supplier phone number')
    item_options = ["Select an item"] + list(item_dict.keys())
    item_name = st.selectbox("Select Item", item_options, key="item_selectbox")
    item_id = item_dict.get(item_name, None)
    quantity = st.number_input("supplied_quantity", min_value=0, step=1)
    unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01, format="%.2f", value=0.0)
    total_cost = quantity * unit_price

    payment_status = st.selectbox("Payment Status", ["paid", "credit", "partial"])
    payment_method = st.selectbox("Payment Method", ["cash", "card", "transfer", "cheque"])
    due_date = st.date_input("Due Date", value=date.today()) if payment_status != "paid" else None
    notes = st.text_area("Notes (Optional)")

    # 🧾 Invoice uploader
    # Invoice uploader
    st.markdown("📎 **Upload Invoice (PDF/Image)**")
    exp_invoice_file = st.file_uploader("Upload Invoice", type=["pdf", "jpg", "jpeg", "png"], key="exp_file")
    exp_invoice_file_url = None
    
    
# Total paid logic
    total_price_paid = 0.0
    if payment_status == "paid":
        total_price_paid = total_cost
    elif payment_status == "partial":
        total_price_paid = st.number_input(
        "Enter Partial Amount Paid",
        min_value=0.0,
        max_value=total_cost,
        step=0.01,
        format="%.2f",
        value=0.0
    )

# Calculate outstanding balance
    outstanding_amount = total_cost - total_price_paid
    user_invoice_name = st.text_input("Enter desired invoice name (without extension)", value=f"invoice_{employee_id}_{date.today().isoformat()}")
# Save Button
    if st.button("💾 Save Purchase Record"):
        try:
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

            
            if payment_status == "partial" and total_price_paid == 0.0:
                st.warning("⚠️ Please enter the partial amount paid.")
            else:
                purchase_data = {
                "purchase_date": str(purchase_date),
                "supplier_name": supplier_name,
                'supplier_phone':supplier_phone if supplier_phone else None,
                "user_id": user_id,
                "item_name": item_name,
                "item_id": item_id,
                "supplied_quantity": quantity,
                "unit_price": unit_price,
                "total_cost": total_cost,
                "payment_status": payment_status,
                "payment_method": payment_method,
                "due_date": str(due_date) if due_date else None,
                "total_price_paid": total_price_paid,
                "amount_balance": outstanding_amount,
                "notes": notes,
                "invoice_file_url": exp_invoice_file_url,
                "employee_id": employee_id,
                "employee_name": employee_name,
            }

                result = supabase.table("goods_bought").insert(purchase_data).execute()
                st.success("✅ Goods bought record saved successfully!")
                
                time.sleep(2)
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error saving record.")
       



# with the table 
with tab2:
    df = fetch_goods_bought(user_id)
    df2=fetch_goods_bought_history(user_id)
     
    # Display the DataFrame in Streamlit
    if not df.empty:
        st.write('Temporary data',df)
    else:
        st.error("❌ No data found!")
    st.markdown("___")

    if not df2.empty:
        st.write('**Restock supplies Table**',df2.tail(10))
        st.download_button(
            label="⬇️ Download Restock Supplies as CSV",
            data=df2.to_csv(index=False),
            file_name="restock_supplies.csv",
            mime="text/csv"
        )
        
    else:
        st.error("❌ No data found!")


 #delete section
with tab3:
    if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()

    # 1. Input the ID to delete
   # title
    st.markdown(
    "<h1 style='color: red;'>🗑️ Delete purchase Record by ID</h1>",
    unsafe_allow_html=True)

    # 1. Input the Restock ID and Date to delete
    restock_id_to_delete = st.text_input("Enter purchase ID to Delete", "")
    date_to_delete = st.date_input("Enter purchase Date to Delete")

    # Check if the necessary inputs are provided
    if restock_id_to_delete and date_to_delete:
        # 2. Fetch restock records from both tables
        restock_history_data = supabase.table("goods_bought_history")\
            .select("*")\
            .eq("purchase_id", restock_id_to_delete)\
            .eq("purchase_date", date_to_delete)\
            .eq("user_id", user_id)\
            .execute().data

        restock_log_data = supabase.table("goods_bought")\
            .select("*")\
            .eq("purchase_id", restock_id_to_delete)\
            .eq("purchase_date", date_to_delete)\
            .eq("user_id", user_id)\
            .execute().data

        # Combine data from both tables
        if restock_history_data:
            selected_restock = restock_history_data[0]
        elif restock_log_data:
            selected_restock = restock_log_data[0]
        else:
            selected_restock = None

        # Check if a restock record is found
        if selected_restock:
            # Display the restock details for confirmation
            st.subheader("Restock Details to Delete")
            st.write(f"**Restock ID:** {selected_restock['purchase_id']}")
            st.write(f"**Item ID:** {selected_restock['item_id']}")
            st.write(f"**Supply Added:** {selected_restock['supplied_quantity']}")
            st.write(f"**Restock Date:** {selected_restock['purchase_date']}")

            # 3. Confirm deletion
            if st.button("🗑️ Delete This supply"):
                try:
                    # 4. Delete from restock_history if the record exists
                    if restock_history_data:
                        supabase.table("goods_bought_history").delete()\
                            .eq("purchase_id", selected_restock["purchase_id"])\
                            .eq("purchase_date", selected_restock["purchase_date"]).eq("user_id", user_id).execute()
                             

                    # 5. Delete from restock_log if the record exists
                    if restock_log_data:
                        supabase.table("goods_bought").delete()\
                            .eq("purchase_id", selected_restock["purchase_id"])\
                            .eq("purchase_date", selected_restock["purchase_date"]).eq("user_id", user_id).execute()
                    supabase.table("payments").delete()\
                         .eq("purchase_id", selected_restock["purchase_id"])\
                         .eq("user_id", user_id).execute()

                    # 6. Optionally, update inventory if the record exists
                    item_id = selected_restock.get("item_id")
                    supply_added = selected_restock.get("supplied_quantity")

                    if item_id and supply_added:
                        # Fetch current inventory data
                        inventory_item = supabase.table("inventory_master_log")\
                            .select("supplied_quantity")\
                            .eq("item_id", item_id)\
                            .eq("user_id", user_id)\
                            .limit(1).execute().data
                        
                        if inventory_item:
                            # Deduct the added supply from inventory (since we are deleting the restock)
                            new_supply = inventory_item["supplied_quantity"] - supply_added
                            supabase.table("inventory_master_log").update({"supplied_quantity": new_supply})\
                                .eq("item_id", item_id).eq("user_id", user_id).execute()

                    # Success message after deletion from both tables and inventory update
                    st.success("✅ Restock record deleted and inventory updated successfully.")
                    

                except Exception as e:
                    st.error(f"❌ Failed to delete.")
        else:
            st.error("❌ No restock record found with the given Restock ID and Date.")
    else:
        st.info("Please enter a Restock ID and Restock Date to delete.")



## report section

with tab4:
    st.subheader("📊 Restock Summary Report")

    df = fetch_goods_bought_history(user_id)

    if df.empty:
        st.warning("No restock history found.")
    else:
        import plotly.express as px

        # Convert date and ensure numeric
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
        df["total_price_paid"] = pd.to_numeric(df["total_price_paid"], errors="coerce")
        df["supplied_quantity"] = pd.to_numeric(df["supplied_quantity"], errors="coerce")

        # ---- DATE RANGE FILTER ----
        min_date = df["purchase_date"].min()
        max_date = df["purchase_date"].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_value=min_date.date(), max_value=max_date.date(), value=min_date.date())
        with col2:
            end_date = st.date_input("End Date", min_value=min_date.date(), max_value=max_date.date(), value=max_date.date())

        # ---- ITEM FILTER ----
        item_filter = st.selectbox("🔍 Filter by Item Name (Optional)", ["All"] + sorted(df["item_name"].dropna().unique().tolist()))

        # ---- Apply Filters ----
        filtered_df = df[
            (df["purchase_date"].dt.date >= start_date) &
            (df["purchase_date"].dt.date <= end_date)
        ]

        if item_filter != "All":
            filtered_df = filtered_df[filtered_df["item_name"] == item_filter]

        if filtered_df.empty:
            st.warning("No data found for the selected filters.")
        else:
            # ---- Summary Metrics ----
            st.markdown("### 📈 Summary")
            total_amount = filtered_df["total_price_paid"].sum()
            total_quantity = filtered_df["supplied_quantity"].sum()
            transaction_count = len(filtered_df)

            col3, col4, col5 = st.columns(3)
            col3.metric("💰 Total Spent", f"₦{total_amount:,.2f}")
            col4.metric("📦 Total Quantity Restocked", f"{total_quantity:,.0f}")
            col5.metric("🧾 Transactions", f"{transaction_count}")

            # ---- Pie Chart: Payment Status ----
            st.markdown("___")
            st.markdown("### 🥧 Payment Status Distribution")
            status_counts = filtered_df["payment_status"].value_counts()
            fig1 = px.pie(names=status_counts.index, values=status_counts.values, title="Payment Status")
            st.plotly_chart(fig1, use_container_width=True)
            most_common_status = status_counts.idxmax()
            most_common_percent = status_counts.max() / status_counts.sum() * 100

            least_common_status = status_counts.idxmin()
            least_common_percent = status_counts.min() / status_counts.sum() * 100

            st.markdown(f"🧾 **Interpretation:**")
            st.markdown(f"- The most frequent payment status is **{most_common_status}**, making up about **{most_common_percent:.1f}%** of all records.")
            st.markdown(f"- The least common status is **{least_common_status}**, representing just **{least_common_percent:.1f}%**.")


            # ---- Pie Chart: Payment Method ----
            st.markdown("___")
            st.markdown("### 💳 Payment Method Distribution")
            method_counts = filtered_df["payment_method"].value_counts()
            fig2 = px.pie(names=method_counts.index, values=method_counts.values, title="Payment Method")
            st.plotly_chart(fig2, use_container_width=True)
            most_used = method_counts.idxmax()
            most_used_percent = method_counts.max() / method_counts.sum() * 100

            least_used = method_counts.idxmin()
            least_used_percent = method_counts.min() / method_counts.sum() * 100

            st.markdown(f"🧾 **Interpretation:**")
            st.markdown(f"- The most commonly used payment method is **{most_used}**, accounting for approximately **{most_used_percent:.1f}%** of all payments.")
            st.markdown(f"- The least used method is **{least_used}**, making up about **{least_used_percent:.1f}%**.")


            # ---- 📆 Purchases Over Time ----
            st.markdown("___")
            st.markdown("### ⏱️ Purchases Over Time")
            # Group data by day
            time_df = (filtered_df.groupby(filtered_df["purchase_date"].dt.to_period("D"))
             .agg(total_spent=("total_price_paid", "sum"))
              .reset_index())

# Convert period to timestamp
            time_df["purchase_date"] = time_df["purchase_date"].dt.to_timestamp()

# Polynomial regression (linear: degree=1)
# Convert dates to ordinal for regression
            x = time_df["purchase_date"].map(pd.Timestamp.toordinal).values
            y = time_df["total_spent"].values

# Fit a 1st-degree polynomial (linear trend)
            coeffs = np.polyfit(x, y, deg=1)
            trend = np.poly1d(coeffs)

# Interpretation
            slope = coeffs[0]
            if slope > 0:
                st.success("📈 Your spending has been **increasing** over time.")
            elif slope < 0:
                st.info("📉 Your spending has been **decreasing** over time.")
            else:
                st.warning("➖ Your spending trend is relatively **flat** over time.")

# Optional: Add trend line to the chart
            time_df["trend"] = trend(x)

            fig3 = px.line(time_df, x="purchase_date", y="total_spent", markers=True,title="Total Amount Spent Over Time")
            fig3.add_scatter(x=time_df["purchase_date"], y=time_df["trend"],
                 mode="lines", name="Trend Line", line=dict(dash='dot', color='orange'))
            st.plotly_chart(fig3, use_container_width=True)

            # ---- 🏆 Top Purchased Items ----
            # ---- 🏆 Top Restocked Items (Table) ---
            st.markdown("___")
            st.markdown("### 🏆 Top 10 Restocked Items (by Quantity)")

            top_items_table = (
            filtered_df.groupby("item_name").agg(
            Total_Quantity=("supplied_quantity", "sum"),
            Total_Spent=("total_price_paid", "sum"),
            Times_Supplied=("item_name", "count")).sort_values("Total_Quantity", ascending=False).reset_index())

            st.dataframe(top_items_table.head(10))


            # ---- Table ----
            st.markdown("___")
            st.markdown("### 📋 Filtered Restock Records")
            sorted_restock_df = filtered_df.sort_values("purchase_date", ascending=False).reset_index(drop=True)
            st.dataframe(sorted_restock_df.head(10))

           # Create CSV for download
            csv = sorted_restock_df.to_csv(index=False)
            st.download_button(
                 label="⬇️ Download Restock Records as CSV",
                 data=csv.encode('utf-8'),
                 file_name="restock_records.csv",
                 mime="text/csv")
