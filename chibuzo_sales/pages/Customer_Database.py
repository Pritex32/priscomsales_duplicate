
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
                if user_data["role"] == "employee":
                    st.session_state.employee_user = {"name": user_data["username"]}
            else:
                # 🛑 Token is invalid or expired — force logout
                st.session_state.clear()
                st_javascript("""localStorage.removeItem("login_token");""")
                st.session_state.login_failed = True

# Run this first
restore_login_from_jwt()

# this makes all button green color
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






st.title("👥 Add Your Customers")

customer_lookup = supabase.table("customers").select(
    "customer_id, name, phone, email, address, created_at"
).eq("user_id", user_id).execute()

customers_list = customer_lookup.data if customer_lookup.data else []

with st.form("add_customer_form"):
    st.subheader("➕ Add New Customer")
    name = st.text_input("Customer Name", key="new_customer_name")
    phone = st.text_input("Phone Number", key="new_customer_phone")
    email = st.text_input("Email (optional)", key="new_customer_email")
    address = st.text_area("Address (optional)", key="new_customer_address")
    submitted = st.form_submit_button("💾 Save Customer")

    if submitted:
        if not name or not phone:
            st.error("❌ Name and Phone are required.")
            st.stop()
        else:
            try:
                # ✅ Check if customer already exists (same phone and user)
                existing_customer = (
                    supabase.table("customers")
                    .select("customer_id, name")
                    .eq("phone", phone)
                    .eq("user_id", user_id)
                    .execute()
                )

                if existing_customer.data:
                    st.warning(
                        f"⚠️ Customer '{existing_customer.data[0]['name']}' with this phone already exists."
                    )
                else:
                    # ✅ Insert new customer
                    customer_data = {
                        "user_id": user_id,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "address": address,
                    }
                    supabase.table("customers").insert(customer_data).execute()
                    st.success("✅ Customer added successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save customer: {e}")



st.markdown("___")
st.subheader("📋 Customer List")

if customers_list:
    # ✅ Convert to DataFrame
    df_customers = pd.DataFrame(customers_list)

    # ✅ Rename columns for better display
    df_customers = df_customers.rename(columns={
        "customer_id": "Customer ID",
        "name": "Name",
        "phone": "Phone",
        "email": "Email",
        "address": "Address",
        "created_at": "Created At"
    })

    with st.expander('📂 View Customer List'):
        st.dataframe(df_customers.tail(10), use_container_width=True)

        # ✅ Convert DataFrame to CSV for download
        csv = df_customers.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Customer List (CSV)",
            data=csv,
            file_name="customer_list.csv",
            mime="text/csv",
            key="download_customer_list"
        )
else:
    st.info("No customers found. Add your first customer above!")



st.markdown("___")
st.subheader("Search Bar")
if customers_list:
    # ✅ Convert Supabase data to DataFrame
    df_customers = pd.DataFrame(customers_list)
    df_customers = df_customers.rename(columns={
        "customer_id": "Customer ID",
        "name": "Name",
        "phone": "Phone",
        "email": "Email",
        "address": "Address",
        "created_at": "Created At"
    })

    # ✅ Search bar
    search_query = st.text_input("🔍 Search by Name or Phone")

    # ✅ Filter DataFrame based on search input
    if search_query:
        df_filtered = df_customers[
            df_customers["Name"].str.contains(search_query, case=False, na=False) |
            df_customers["Phone"].str.contains(search_query, case=False, na=False)
        ]
    else:
        df_filtered = df_customers
    with st.expander('📂 View Search Result'):
        st.dataframe(df_filtered, use_container_width=True)

        # ✅ Download filtered list as CSV
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Customer List (CSV)",
            data=csv,
            file_name="customer_list.csv",
            mime="text/csv",
            key="download_customer_list_2025"  # ✅ Added unique key
        )

    
else:
    st.info("No customers found. Add your first customer above!")


st.markdown("___")
col33, col44 = st.columns([3, 1])

# ✅ Search Bar
search_query = st.text_input("🔍 Search Customer by Name or Phone", "")

# ✅ Filter DataFrame
if search_query:
    df_filtered = df_customers[df_customers.apply(
        lambda row: search_query.lower() in str(row['Name']).lower() or search_query in str(row['Phone']),
        axis=1
    )]
else:
    df_filtered = df_customers

# ✅ Customer List in Left Column
with col33:
    st.subheader("📂 View & Manage Customer List")
    with st.expander("Customer List", expanded=True):
        if df_filtered.empty:
            st.warning("❌ No matching customers found.")
        else:
            for idx, row in df_filtered.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.write(f"**{row['Name']}** | 📞 {row['Phone']} | ✉️ {row['Email'] or 'N/A'} | 🏠 {row['Address'] or 'N/A'}")
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{row['Customer ID']}"):
                            st.session_state["edit_customer_id"] = row['Customer ID']
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{row['Customer ID']}"):
                            # ✅ Confirmation before deleting
                            if st.confirm_dialog(f"Are you sure you want to delete {row['Name']}?"):
                                supabase.table("customers").delete().eq("customer_id", row['Customer ID']).execute()
                                st.success("✅ Customer deleted successfully!")
                                st.rerun()

# ✅ Edit Customer Form in Right Column
with col44:
    if "edit_customer_id" in st.session_state:
        edit_id = st.session_state["edit_customer_id"]
        response = supabase.table("customers").select("*").eq("customer_id", edit_id).single().execute()
        edit_customer = response.data

        st.subheader(f"✏️ Edit Customer")
        with st.form("edit_customer_form"):
            new_name = st.text_input("Customer Name", value=edit_customer["name"])
            new_phone = st.text_input("Phone Number", value=edit_customer["phone"])
            new_email = st.text_input("Email", value=edit_customer.get("email", ""))
            new_address = st.text_area("Address", value=edit_customer.get("address", ""))
            save_changes = st.form_submit_button("💾 Update Customer")

            if save_changes:
                # ✅ Validate phone uniqueness
                existing = supabase.table("customers").select("customer_id").eq("phone", new_phone).neq("customer_id", edit_id).execute()
                if existing.data:
                    st.error("❌ Phone number already exists for another customer.")
                else:
                    update_data = {
                        "name": new_name,
                        "phone": new_phone,
                        "email": new_email,
                        "address": new_address,
                    }
                    supabase.table("customers").update(update_data).eq("customer_id", edit_id).execute()
                    st.success("✅ Customer updated successfully!")
                    del st.session_state["edit_customer_id"]
                    st.rerun()
    else:
        st.info("Select a customer to edit from the list.")



          
