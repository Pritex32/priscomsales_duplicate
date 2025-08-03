import streamlit as st
st.set_page_config(page_title="settings", layout="wide")
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
import hashlib
import random
import string

from streamlit_option_menu import option_menu
from datetime import datetime,date,timedelta
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


# Restore login from browser localStorage
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

# === Restore Login from JWT ===
def restore_login_from_jwt():
    if not st.session_state.get("logged_in"):
        token = st_javascript("""localStorage.getItem("login_token");""")
        if token and token != "null":
            user_data = decode_jwt(token)
            if user_data and user_data != "expired":
           
                st.session_state.logged_in = True
                st.session_state.jwt_token = token  # ✅ Store token
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
            elif user_data == "expired":
                handle_session_expiration()
            else:
                # 🛑 Token is invalid or expired — force logout
                st.session_state.clear()
                st_javascript("""localStorage.removeItem("login_token");""")
                st.session_state.login_failed = True


# Run this first

# === Session Validation ===
# === Session Validation === # this stops you when you are logged out
def handle_session_expiration():
    st.session_state["logged_in"] = False
    st.session_state["session_expired"] = True
    st.rerun()# or redirect logic

restore_login_from_jwt()

if st.session_state.get("session_expired", False):
    st.markdown("""
        <div style="
            background-color: #ffe6e6;
            border-left: 1px solid #ff9999;
            padding: 10px;
            border-radius: 6px;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-top: 20px;
        ">
            <h3 style="color: #cc0000; margin: 0 0 8px; font-size: 18px;">❌ Session Expired</h3>
            <p style="color: #333; font-size: 15px; margin: 0;">
                Your session has expired. Redirecting to login page...
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Wait before redirect
    time.sleep(3)

    # Reset so message won't repeat
    st.session_state["session_expired"] = False
     # Redirect
    switch_page("Dasboard")

# === Session Validation ===
  


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

   

 


def hash_password(password: str) -> str:
    # Hash the password using SHA-256 (or a stronger hashing function like bcrypt)
    return hashlib.sha256(password.encode()).hexdigest()


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
  











if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()

choice = st.radio("Select an Option", ["Settings",'Change Access Code',"Change Password", "API Integration"])



if choice == "Settings":
    st.subheader("⚙️ Settings")
    st.markdown("""
    <div style="
    background-color:#fff8e1; 
    border-left:6px solid #ff9800; 
    padding:16px; 
    border-radius:8px; 
    font-family:Arial, sans-serif; 
    color:#333;
    ">
    <h3 style="margin:0; color:#ff9800;">⚙️ Settings</h3>
    <p style="font-size:16px; margin:8px 0;">
        You are now on the <strong>Settings</strong> page.<br>
        Manage your preferences above.
    </p>
</div>
""", unsafe_allow_html=True)

elif choice == "Change Access Code":
    st.title("🔐 Change Access Code")

    # ✅ Fetch MD user data
    user_data = supabase.table("users").select("access_code").eq("user_id", user_id).single().execute().data

    if not user_data:
        st.error("❌ Unable to load MD details. Please log in as MD.")
    else:
        current_access_code = user_data.get("access_code", "")

        # ✅ Show current access code
        st.markdown(f"**Current Access Code:** `{current_access_code if current_access_code else 'Not Set'}`")

        st.divider()

        # ✅ Option 1: Generate a new random access code
        st.subheader("Generate a New Access Code")
        if st.button("🔑 Generate New Access Code"):
            new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))  # Example: AB12CD34
            supabase.table("users").update({"access_code": new_code}).eq("user_id", user_id).execute()
            st.success(f"✅ New Access Code Generated: {new_code}")
            time.sleep(5)
            st.rerun()

        st.divider()

        # ✅ Option 2: Set a Custom Access Code
        st.subheader("Set a Custom Access Code")
        new_manual_code = st.text_input("Enter New Access Code")
        if st.button("💾 Save Custom Access Code"):
            if new_manual_code.strip():
                supabase.table("users").update({"access_code": new_manual_code.strip()}).eq("user_id", user_id).execute()
                st.success(f"✅ Access Code changed to: {new_manual_code}")
                time.sleep(4)
                st.rerun()
            else:
                st.warning("⚠ Please enter a valid access code.")





elif choice == "Change Password":
    
    st.subheader("🔐 Change Your Password")

    with st.form("change_password_form"):
        email = st.text_input("Enter your registered Email")
        access_code = st.text_input("Enter your Access Code")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update Password")

        if submitted:
            if not email or not access_code or not new_password or not confirm_password:
                st.warning("⚠️ All fields are required.")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match.")
            else:
                # ✅ Fetch user by email
                user_check = supabase.table("users").select("access_code").eq("email", email).execute()

                if not user_check.data:
                    st.error("❌ No account found with this email.")
                    st.stop()
                else:
                    stored_access_code = user_check.data[0]["access_code"]

                    if stored_access_code != access_code:
                        st.error("❌ Invalid Access Code.")
                        st.stop()
                    else:
                        # ✅ Hash new password and update
                        hashed_new_password = hash_password(new_password)
                        update_result = supabase.table("users").update({"password_hash": hashed_new_password}).eq("email", email).execute()

                        if update_result.data:
                            st.success("✅ Password updated successfully!")
                            time.sleep(1)
                            st.session_state.clear()
                            st_javascript("localStorage.removeItem('login_token');",key="remove_login_token_6")
                            time.sleep(1)
                            switch_page('Dashboard')
                        else:
                            st.error("❌ Failed to update password. Please try again.")
