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
import uuid
from urllib.parse import quote_plus

import streamlit as st
import bcrypt
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime, date
import json
import time

from PIL import Image
import hashlib
import uuid
from datetime import datetime, timedelta
from streamlit_javascript import st_javascript
import sys
import importlib.util
import requests
import numpy as np
import matplotlib.pyplot as plt

from streamlit_extras.switch_page_button import switch_page
from PIL import Image
from sqlalchemy import create_engine, inspect
import json
import os

import jwt
import streamlit.components.v1 as components




jwt_SECRET_KEY = "4606"  # Use env vars in production
ALGORITHM = "HS256"

#Decode function
def generate_jwt(user_id, username, role):
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





# to get the user id from browser storage
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
            save_token_to_localstorage(token)

            # ⚠️ Notify user
            st.warning("🔔 Your Pro subscription has expired. You've been downgraded to the Free Plan.")

    except Exception as e:
        st.error(f"Subscription check failed: {e}")

if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
    block_if_subscription_expired()
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    show_plan_status()





# Simulated logged-in user
user_id = st.session_state.get("user_id")
if not user_id:
    st.error("Please log in.")
    st.stop()


# --- Simulated login ---
if "user_id" not in st.session_state:
    # For testing, assign a dummy UUID - replace with your auth system
    st.session_state["user_id"] = "00000000-0000-0000-0000-000000000001"

user_id = st.session_state["user_id"]

st.title("📄 Create a New Sheet")
col3,col4=st.columns(2)
with col3:
    st.warning('create tables that are important')
with col4:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()  # ✅ Clear cached data
        st.rerun() 

# Step 1: Create Sheet
sheet_name = st.text_input("Enter Sheet Name (e.g., sales_june)")
num_cols = st.number_input("How many columns?", min_value=1, step=1)

columns = []
for i in range(int(num_cols)):
    col_name = st.text_input(f"Column {i+1} Name", key=f"col_name_{i}")
    col_type = st.selectbox(
        f"Column {i+1} Type",
        ["TEXT", "INTEGER", "FLOAT", "BOOLEAN", "DATE", "TIMESTAMP"],
        key=f"col_type_{i}"
    )
    columns.append({"name": col_name, "type": col_type})
for i, col in enumerate(columns):
    if not col["name"]:
        st.write(f"Column {i+1} name is empty!")


if st.button("Create Sheet"):
    if sheet_name and all(col["name"] for col in columns):
        # Check if sheet exists
        existing = supabase.table("user_sheets") \
            .select("*").eq("user_id", user_id).eq("sheet_name", sheet_name).execute()
        if existing.data:
            st.warning("Sheet with this name already exists!")
        else:
            # Insert sheet metadata with columns list
            insert_resp = supabase.table("user_sheets").insert({
                "user_id": user_id,
                "sheet_name": sheet_name,
                "columns": columns  # Must be a list of dicts [{name, type}, ...]
            }).execute()

            insert_resp = supabase.table("user_sheets").insert({
                     "user_id": user_id,
                     "sheet_name": sheet_name,
                      "columns": columns}).execute()

            if insert_resp.data is not None:
                st.success("Sheet created successfully!")
            else:
                st.error("Failed to create sheet.")


    else:
        st.warning("Please fill all fields.")


st.markdown("---")
st.title("🧾 Enter Data into Your Sheet")

# Step 2: Select sheet to add data
response = supabase.table("user_sheets").select("*").eq("user_id", user_id).execute()
user_sheets = response.data or []

if not user_sheets:
    st.info("You haven't created any sheets yet.")
    st.stop()

sheet_option = st.selectbox("Choose a sheet", [s["sheet_name"] for s in user_sheets])
sheet_info = next(s for s in user_sheets if s["sheet_name"] == sheet_option)

columns = sheet_info.get("columns")
if not columns:
    st.info(" Select previously created sheet or  Please recreate the sheet.")
    st.stop()


# Step 3: Input data for selected sheet
st.subheader(f"➕ Add Data to: {sheet_option}")

data = {}
for col in columns:
    col_name = col["name"]
    col_type = col["type"]
    # Basic input widgets based on type
    if col_type == "INTEGER":
        val = st.number_input(f"{col_name} (INTEGER)", step=1, key=f"input_{col_name}")
    elif col_type == "FLOAT":
        val = st.number_input(f"{col_name} (FLOAT)", format="%.5f", key=f"input_{col_name}")
    elif col_type == "BOOLEAN":
        val = st.checkbox(f"{col_name} (BOOLEAN)", key=f"input_{col_name}")
    elif col_type == "DATE":
        val = st.date_input(f"{col_name} (DATE)", key=f"input_{col_name}")
    elif col_type == "TIMESTAMP":
        val = st.text_input(f"{col_name} (TIMESTAMP, e.g. 2023-01-01 12:00:00)", key=f"input_{col_name}")
    else:  # TEXT and fallback
        val = st.text_input(f"{col_name} (TEXT)", key=f"input_{col_name}")

    data[col_name] = val

if st.button("Submit Row"):
    # Insert row as JSON data
    insert_resp = supabase.table("sheet_data").insert({
        "user_id": user_id,
        "sheet_name": sheet_option,
        "data": data
    }).execute()

    if insert_resp.data:
        st.success("Sheet created successfully!")
    else:
        st.error("Failed to create sheet.")

st.markdown("---")
st.subheader("📄 Current Sheet Data")

# Step 4: Display sheet data
with st.expander('View Current Data'):
    rows_resp = supabase.table("sheet_data").select("*") \
    .eq("user_id", user_id).eq("sheet_name", sheet_option).execute()

    rows = rows_resp.data or []

    if rows:
            # Normalize JSONB data column for display
        df = pd.json_normalize([row["data"] for row in rows])
        st.dataframe(df)
    else:
        st.info("No data found for this sheet yet.")



st.subheader('Select Rows to edit or delete')
# Fetch user rows for the selected sheet
rows_resp = supabase.table("sheet_data") \
    .select("*") \
    .eq("user_id", user_id) \
    .eq("sheet_name", sheet_option) \
    .execute()
rows = rows_resp.data or []

if not rows:
    st.info("No rows found.")
else:
    # Show a selectbox for user to pick a row to edit/delete
    row_options = [f"ID {r['id']} - Created {r['created_at']}" for r in rows]
    selected_row_str = st.selectbox("Select row to edit or delete", row_options)

    # Find selected row object
    selected_row = rows[row_options.index(selected_row_str)]
    row_data = selected_row.get("data", {})

    st.write("Current row data:")
    

    # Editable inputs for update
    updated_data = {}
    for col in columns:
        col_name = col["name"]
        current_val = row_data.get(col_name, "")
        updated_data[col_name] = st.text_input(f"{col_name}", value=str(current_val))

    if st.button("Update Selected Row"):
        update_resp = supabase.table("sheet_data").update({
            "data": updated_data
        }).eq("id", selected_row["id"]).execute()

        if update_resp.data is not None:
            st.success(f"Row {selected_row['id']} updated successfully.")
            st.rerun()
        else:
            st.error("Failed to update row.")

    if st.button("Delete Selected Row"):
        delete_resp = supabase.table("sheet_data").delete().eq("id", selected_row["id"]).execute()
        if delete_resp.data is not None:
            st.success(f"Row {selected_row['id']} deleted successfully.")
            st.rerun()
        else:
            st.error("Failed to delete row.")


st.title('Delete Entire sheet')
response = supabase.table("user_sheets").select("*").eq("user_id", user_id).execute()
user_sheets = response.data or []
st.subheader("Your Sheets")

for i, sheet in enumerate(user_sheets):
    sheet_name = sheet["sheet_name"]
    safe_sheet_name = sheet_name.replace(" ", "_").replace("-", "_")
    st.write(f"📄 {sheet_name}")
    if st.button(f"Delete '{sheet_name}'", key=f"delete_{safe_sheet_name}_{i}"):
        # Delete sheet metadata from user_sheets
        delete_meta = supabase.table("user_sheets").delete() \
            .eq("user_id", user_id).eq("sheet_name", sheet_name).execute()

        # Optionally delete all sheet data rows
        delete_data = supabase.table("sheet_data").delete() \
            .eq("user_id", user_id).eq("sheet_name", sheet_name).execute()

        if delete_meta.data is not None:
            st.success(f"Deleted sheet '{sheet_name}' and all its data.")
            st.rerun()  # use experimental_rerun to refresh the app
        else:
            st.error(f"Failed to delete sheet '{sheet_name}'.")
