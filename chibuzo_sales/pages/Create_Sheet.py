import streamlit as st
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





st.title("📄 Create a New Sheet")

# Simulated logged-in user
user_id = st.session_state.get("user_id")
if not user_id:
    st.error("Please log in.")
    st.stop()

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
    columns.append((col_name, col_type))

if st.button("Create Sheet"):
    if sheet_name and all(c[0] for c in columns):
        # Save metadata to user_sheets
        supabase.table("user_sheets").insert({
            "user_id": user_id,
            "sheet_name": sheet_name
        }).execute()

        # Generate CREATE TABLE SQL dynamically
        # Safely get short user_id for table name
        short_user_id = str(user_id)[:8]
        # Format the SQL correctly with user-defined columns
        cols_sql = ", ".join([f"{name} {dtype}" for name, dtype in columns])
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {sheet_name}_{short_user_id} (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                {cols_sql},
                        created_at TIMESTAMP DEFAULT NOW());"""

        # Send query to database (use your DB client here)
       

# Build the connection string
        DATABASE_URL = f"postgresql://postgres:wE4ptqRBpg2vjS1R@db.ecsrlqvifparesxakokl.supabase.co:5432/postgres"

        from sqlalchemy import create_engine
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(create_sql)

        st.success(f"✅ Sheet `{sheet_name}` created!")
    else:
        st.warning("Please fill all fields.")


st.title("🧾 Enter Data into Your Sheet")

# 1. Fetch available sheets for this user
response = supabase.table("user_sheets").select("*").eq("user_id", user_id).execute()
user_sheets = response.data

if not user_sheets:
    st.info("You haven't created any sheets yet.")
    st.stop()

# 2. Let user pick a sheet
sheet_option = st.selectbox("Choose a sheet", [s["sheet_name"] for s in user_sheets])
sheet_info = next(s for s in user_sheets if s["sheet_name"] == sheet_option)
table_name = f"{sheet_info['sheet_name']}_{user_id}"
 # same naming used during creation


# Build the connection string
DATABASE_URLL = f"postgresql://postgres:wE4ptqRBpg2vjS1R@db.ecsrlqvifparesxakokl.supabase.co:5432/postgres"

# Connect to your database
engine = create_engine(DATABASE_URLL)
inspector = inspect(engine)

with engine.connect() as conn:
    columns = inspector.get_columns(table_name)
    column_names = [col["name"] for col in columns if col["name"] not in ["id", "user_id", "created_at"]]



data = {}
st.subheader(f"➕ Add Data to: {sheet_option}")

for col in column_names:
    data[col] = st.text_input(f"{col}", key=col)

if st.button("Submit Row"):
    # Insert the row
    insert_query = f"""
    INSERT INTO {table_name} (user_id, {', '.join(data.keys())})
    VALUES (%s, {', '.join(['%s'] * len(data))})
    """

    values = [user_id] + list(data.values())

    with engine.connect() as conn:
        conn.execute(insert_query, values)

    st.success("✅ Row added successfully!")


st.subheader("📄 Current Sheet Data")
with engine.connect() as conn:
    df = pd.read_sql(f"SELECT * FROM {table_name} WHERE user_id = %s", conn, params=[user_id])

st.dataframe(df)
