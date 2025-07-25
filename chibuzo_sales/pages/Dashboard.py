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
from datetime import datetime, date
from datetime import datetime, timedelta
import string
import random

import json
import time
import re
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

from streamlit_extras.switch_page_button import switch_page # for streamlit to redirect you to a difereent page
from PIL import Image
from itsdangerous import URLSafeTimedSerializer # to generate email verification token

import os
from dotenv import load_dotenv #to load keys stored in the .env file
import jwt # to store login session on the web local stoarge so that you dont  get logged out after refresh
import streamlit.components.v1 as components # for streamlit jwt token storage






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
    
## 🔐 Same secret key must be used across all pages

load_dotenv()

import os


jwt_SECRET_KEY = "4606"  # Use env vars in production
ALGORITHM = "HS256"



def generate_jwt(user_id, username, role,plan="free", is_active=False,email=None):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "plan": plan,
        "email": email,
        "is_active": is_active,
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
    

def restore_login_from_jwt():
    if not st.session_state.get("logged_in"):
        token = st_javascript("""localStorage.getItem("login_token");""",key=f"get_save_token_990")
        if token and token != "null":
            user_data = decode_jwt(token)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_id = int(user_data["user_id"])
                st.session_state.username = user_data["username"]
                st.session_state.role = user_data["role"]
                st.session_state.user_email = user_data.get("email")
                st.session_state.user = user_data
                st.session_state.plan = user_data.get("plan", "free").lower()
                st.session_state.is_active = user_data.get("is_active", False)

                # ✅ This is the critical fix
                if user_data["role"] == "employee":
                    st.session_state.employee_user = {"name": user_data["username"]}
            else:
                # 🛑 Token is invalid or expired — force logout
                st.session_state.clear()
                st_javascript("""localStorage.removeItem("login_token");""", key=f"get_login_token_888")
                st.session_state.login_failed = True


# Only call restore function if not already logged in

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "Login"

if not st.session_state.logged_in:
    restore_login_from_jwt()

def save_token_to_localstorage(token):
    st_javascript(f"""localStorage.setItem("login_token", "{token}");""",key="saved_token_login_token")
# to get the payment details after upgrade

# def refresh_subscription_from_jwt():
   # token = st.session_state.get("jwt_token")
   # if not token:
     #   st.session_state.plan = "free"
      #  st.session_state.is_active = False
      #  return

   # payload = decode_jwt(token)
   # st.session_state.plan = payload.get("plan", "free").lower()
   # st.session_state.is_active = payload.get("is_active", False)


   








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



# ✅ Initialize session state variables ONCE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'  # default page







if "page" not in st.session_state:
    st.session_state.page = "Login"

# designing the header
st.markdown("""
    <style>
    .header-container {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .header-text {
        font-size: 2.2rem;
        font-weight: 700;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }

    .header-subtext {
        font-size: 1.2rem;
        color: #dcdcdc;
        margin-top: 0.5rem;
        font-family: 'Segoe UI', sans-serif;
    }
    </style>

    <div class="header-container">
        <div class="header-text">PriscomSales</div>
        <div class="header-subtext">Smart Sales, Smarter Decisions</div>
    </div>
""", unsafe_allow_html=True)

menu = ["Login", "Register","Delete Account"]

choice = st.selectbox("Navigate 👇", menu, index=0)

if choice != st.session_state.page:
    st.session_state.page = choice
    st.rerun()
choice = st.session_state.page


def hash_password(password: str) -> str:
    # Hash the password using SHA-256 (or a stronger hashing function like bcrypt)
    return hashlib.sha256(password.encode()).hexdigest()
from email.message import EmailMessage

# pip install pyhton-dotenv
from dotenv import load_dotenv

load_dotenv()
    
def mask_email(email):
    try:
        name, domain = email.split("@")
        # Mask part of the name (e.g., jo***)
        if len(name) >= 3:
            name_masked = name[:2] + "***"
        else:
            name_masked = name[0] + "***"
        return f"{name_masked}@{domain}"
    except:
        return None
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, email)



def register_user(username, email, email_confirmation,password_hash, role,plan,access_code):
    try:
        # Step 1: Validate email format
        if not is_valid_email(email):
            return "❌ Invalid email format."

        # Step 2: Match confirmation
        if email != email_confirmation:
            return "❌ Email confirmation does not match."

        # Check if username already exists in the users table
        existing_user = supabase.table("users").select("username").eq("username", username).execute()
        if existing_user.data:
            return f"Error: Username '{username}' already exists."

        # Check if email already exists in the users table
        existing_email = supabase.table("users").select("email").eq("email", email).execute()
        if existing_email.data:
            return f"Error: Email '{email}' already exists."
                   
        

               
        # Insert user details into the users table
        result = supabase.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "is_verified":  True ,
             "access_code": access_code
            
        }).execute()
        # ✅ Extract user_id from the insert result
        
                
        if not result.data or "user_id" not in result.data[0]:
            return "❌ Error: Could not retrieve user_id after registration."

        user_id = result.data[0]["user_id"]

        # Set default values based on plan
        is_active = True if plan == "pro" else False
        started_at = date.today() if plan == "pro" else None
        expires_at = date.today() + timedelta(days=30) if plan == "pro" else None
        

        # 5. Insert into subscription table
        supabase.table("subscription").insert({
            "user_id": user_id,
            "plan": plan,
            "is_active": is_active,
            "started_at": started_at,
            "expires_at": expires_at
        }).execute()
        
        # Send verification email
        # ✅ Step 6: Send verification email
        try:
           emp_check = supabase.table("employees").select("*").eq("user_id", user_id).limit(1).execute()
           if not emp_check.data:
           # Automatically register as employee
               supabase.table("employees").insert({
                "user_id": user_id,
                "name": username, 
                'password':password,
                "email":email,# or any preferred name field
                "role": "employee"
            }).execute()
               st.success("✅ MD was also registered as an employee.")
               
        except Exception as e:
            st.warning(f"⚠️ Could not verify/create employee record.")
        return "✅ Registration successful! Kindly login."
    
         
    except Exception as e:
        return "❌ Something went wrong. Please try again later."




# get md subscription status
def get_md_subscription(md_user_id):
    response = supabase.table("subscription")\
        .select("plan, is_active, expires_at")\
        .eq("user_id", md_user_id)\
        .order("started_at", desc=True)\
        .limit(1)\
        .execute()

    if response.data:
        sub = response.data[0]
        end_date = sub.get("expires_at")
        is_active = sub.get("is_active", False)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            if end_date < datetime.now():
                is_active = False  # expired

        return {
            "plan": sub.get("plan", "free"),
            "is_active": is_active
        }
    return {"plan": "free", "is_active": False}





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
        st.error(f"❌ Failed to sync subscription info.")
    
# Function to Authenticate Login
## login function
def login_user(email, password):
    # Set cookies after login
        
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        user_data = response.data

        if user_data:
            user = user_data[0]
            stored_password_hash = user["password_hash"]

            # If you are using SHA-256:
            if stored_password_hash == hashlib.sha256(password.encode()).hexdigest():
                return user
            if user:
                token = generate_jwt(user["id"], user["username"],user["email"])
                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.username = user["username"]

        # Store token in browser localStorage via JS
                st_javascript(f"""localStorage.setItem("login_token", "{token}");""",key="remove_login_token_4")

                st.success("Login successful!")
            else:
                st.error("Invalid login")



            # If you later switch to bcrypt (recommended), use:
            # if bcrypt.checkpw(password.encode(), stored_password_hash.encode()):
            #     return user

        return None
    except Exception as e:
        st.error("❌ Login failed. Please check your credentials or try again later.")
        return None

# to generate access code
def generate_access_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))




# ✅ Fetch subscription data
def fetch_subscription_data(user_id):
    try:
        response = supabase.table("subscription").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching subscription data.")
        return pd.DataFrame()





import hashlib

def login_employee(email, password):
    """
    Employee login scoped to a specific user_id (MD tenant).
    """
    hashed_password = hash_password(password)

    result = supabase.table("employees")\
        .select("*")\
        .eq("email", email)\
        .eq("password", hashed_password)\
        .execute()

    if not result.data:
        st.error("❌ Employee with this email not found.")
        return False

    user_data = result.data[0]
    
    # Check for MD linkage
    md_user_id = user_data.get("user_id")
    if not md_user_id:
        st.error("⚠️ This employee is not linked to any MD account.")
        return False

    # Fetch the MD’s subscription
    sub_response = supabase.table("subscription")\
        .select("plan, is_active,expires_at")\
        .eq("user_id", md_user_id)\
        .order("started_at", desc=True)\
        .limit(1)\
        .execute()

    subscription = sub_response.data[0] if sub_response.data else {}
    is_active = subscription.get("is_active", False)
    expires_at = subscription.get("expires_at")
    if expires_at:
        try:
            expires_date = datetime.strptime(expires_at, "%Y-%m-%d")
            if expires_date < datetime.now():
                is_active = False
        except:
            pass  # Handle inval

    # Store session data
    st.session_state.employee_logged_in = True
    st.session_state.employee_user = user_data
    st.session_state.logged_in = True  # 🔥 Add this
    st.session_state.role = user_data.get("role", "employee")  # 🔥 Add this too
    st.session_state.username = user_data.get("name")
    st.session_state.email = user_data.get("email")


    st.session_state.employee_role = user_data.get("role", "employee")
    st.session_state.employee_id = user_data.get("employee_id")
    st.session_state.user_id = md_user_id  # MD this employee belongs to
    st.session_state.plan = subscription.get("plan", "free")
    st.session_state.is_active = subscription.get("is_active", False)
    st.session_state.is_active = is_active

    # ✅ Generate a JWT for the employee
    jwt_token = generate_jwt(
    user_id=md_user_id,
    username=user_data.get("name"),
    email=user_data.get("email"),
    role=user_data.get("role", "employee"),
    plan=subscription.get("plan", "free"),
    is_active=subscription.get("is_active", False)
)



    # ✅ Save the JWT to browser localStorage using JavaScript
    st_javascript(f"""localStorage.setItem("login_token", "{jwt_token}");""",key="remove_login_token_3")

    # Optional visual feedback
    st.success(f"✅ Welcome {user_data.get('name')} (Employee)!")
    st.write(f"🆔 Your Employee ID: `{st.session_state.employee_id}`")
    return True
    


# Custom button style (applies to both)
# to color log out and sales button
st.markdown("""
    <style>
    /* Target "Go to Sales Page" button */
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        padding: 10px 16px;
    }

    /* Target "Logout" button specifically */
    div.stButton:nth-of-type(2) > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        padding: 10px 16px;
    }

    </style>
""", unsafe_allow_html=True)


# to fetch subcription data
from datetime import date

def show_user_data():
    FREE_LIMIT = 10
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("User not logged in.")
        return

    plan = st.session_state.get("plan", "free")
    is_active = st.session_state.get("is_active", False)
    email = st.session_state.get("user_email", None)
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "user")
    # ✅ Fetch subscription info
    df = fetch_subscription_data(user_id)
    if not df.empty:
        expires_at_str = df.iloc[-1]["expires_at"]  # Most recent record
        if expires_at_str:
            expires_at = date.fromisoformat(expires_at_str)
            today = date.today()

            if today > expires_at  and (plan != "free" or is_active):
                # ❌ Subscription expired
                plan = "free"
                is_active = False

                # Update session
                st.session_state.plan = "free"
                st.session_state.is_active = False

                # Optional: update backend (Supabase)
                supabase.table("subscription").update({
                    "is_active": False,
                    "plan": "free"
                }).eq("user_id", user_id).execute()

                # Optional: regenerate JWT
                token = generate_jwt(user_id, username, role, plan, is_active, email)
                st.session_state.jwt_token = token
                st_javascript(f"""localStorage.setItem("login_token", "{token}");""",key="remove_login_token_2")

                st.warning("🔔 Your subscription has expired. You are now on the Free Plan.")

    # ✅ Show plan info
    if plan == "free" and not is_active:
        st.info("🆓 You are currently on the **Free Plan**. Limited to 10 transactions.")
    elif plan == "pro" and is_active:
        st.success("💼 You are on the **Pro Plan**. Enjoy unlimited access!")
    else:
        st.warning("⚠️ Your subscription status is unclear. Please contact support.")
   

# to show the subcription status
if st.session_state.get("logged_in"):
    show_user_data()


def login_md(email, password):
    user = login_user(email, password)
    
    if not user:
        st.error("❌ Invalid email or password.")
        return False
    # ✅ Add this verification check
    if not user.get("is_verified", False):
        st.warning("⚠️ Your account is not verified. Please check your email or contact support.")
        return False
    

    role = user.get('role', '').strip().lower()
    if role != 'md':
        st.error(f"❌ Not authorized as MD. Your role: {role}")
        return False

    # Get MD's user ID
    user_id = user.get("id") or user.get("user_id") or user.get("uid")
    if not user_id:
        st.warning("⚠️ User ID not found.")
        return False

    # Try fetching subscription
    try:
       sub = get_md_subscription(user_id)
    except Exception as e:
        st.warning(f"⚠️ Could not retrieve subscription info: {str(e)}")
        return False

    # ✅ Update session state
    st.session_state.user_id = user_id
    st.session_state.logged_in = True
    st.session_state.user = user
    st.session_state.role = role
    st.session_state.plan = sub.get("plan", "free")
    st.session_state.subscription_active = sub.get("is_active", False)
    st.session_state.username = user.get("username") or user.get("name") or user.get("email")
    st.session_state.user_email = user.get("email")


    # ✅ Generate and store JWT in localStorage using JS
    jwt_token = generate_jwt(
    user_id=user_id,
    username=user.get("username") or user["email"],
    email=user["email"],
    role=role,
    plan=st.session_state.plan,
    is_active=st.session_state.subscription_active
)

    st_javascript(f"""localStorage.setItem("login_token", "{jwt_token}");""",key="remove_login_token_5")

    # ✅ Visual feedback
    display_name = user.get('username') or user['email']
    if st.session_state.plan == "free":
        st.info("You are on the free plan and limited to 10 rows.")
    
    st.success(f"✅ Welcome {display_name} (MD)!")
    st.write(f"🆔 Your MD ID: `{user_id}`")
    return True



   
# employee loggin
# Initialize session state
def init_session_state():
    defaults = {
        'logged_in': False,
        'role': None,
        'user': {},
        'user_id': None,
        'employee_logged_in': False,
        'employee_user': {},
        'employee_role': None,
        'employee_id': None,
        'show_employee_form': False,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()



import requests
# to get client ip
def get_client_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip', 'Unknown')
    except:
        return "Unknown"



# to track logins
import socket
import platform
from datetime import datetime

def track_login(user_id, role):
    # ✅ Get client IP (from Streamlit headers if running on Streamlit Cloud)
    try:
        ip_address = st.context.headers.get("X-Forwarded-For", "Unknown")  # Handles proxy IP
    except:
        ip_address = "Unknown"

    # ✅ Get device info
    device_info = f"{platform.system()} {platform.release()}"

    # ✅ Prepare data for Supabase
    login_data = {
        "user_id": user_id,
        "role": role,
        "login_time": str(datetime.now()),
        "ip_address": ip_address,
        "device": device_info
    }

    # ✅ Insert into Supabase
    try:
        supabase.table("login_logs").insert(login_data).execute()
        print(f"✅ Login tracked: {login_data}")
    except Exception as e:
        print(f"❌ Failed to track login: {e}")


# Sidebar Menu
# this is to ensure that when you register, it autoamtically takes you to login page
if "choice" not in st.session_state:
    st.session_state.choice = "Login"
if "redirect_to_login" not in st.session_state:
    st.session_state.redirect_to_login = False

if st.session_state.redirect_to_login:
    st.session_state.choice = "Login"
    st.session_state.redirect_to_login = False
    st.rerun()





# Registration Page
elif choice == "Register":
    st.subheader("📋 Register")

    # ✅ If access code exists in session, show it and Login button
    if "registration_success" in st.session_state and st.session_state.registration_success:
        access_code = st.session_state.get("access_code", "")
        st.success("✅ Registration completed successfully!")
        st.info(f"🔐 **Your Secret Access Code:** {access_code}\n\nPlease save it securely for password changes!")

        # ✅ Add Login button
        if st.button("👉 Go to Login"):
            st.session_state.page = "Login"
            st.session_state.registration_success = False  # Clear success state
            st.rerun()

    else:
        # 🧠 Only initialize once
        if "email_entered" not in st.session_state:
            st.session_state.email_entered = False
        if "temp_email" not in st.session_state:
            st.session_state.temp_email = ""

        with st.form("registration_form"):
            username = st.text_input("Full name or Business name")
            password = st.text_input("Password", type="password")
            plan = st.selectbox("Choose Plan", ["free"])
            role = st.selectbox("Select Role", ["MD"])

            if not st.session_state.email_entered:
                email = st.text_input("Enter your email")

                if st.form_submit_button("Next"):
                    if email and "@" in email:
                        st.session_state.temp_email = email
                        st.session_state.email_entered = True
                        st.rerun()
                    else:
                        st.warning("Please enter a valid email.")
            else:
                # Email was previously submitted
                def mask_email(email):
                    try:
                        name, domain = email.split("@")
                        name_masked = name[:2] + "***" if len(name) >= 3 else name[0] + "***"
                        return f"{name_masked}@{domain}"
                    except:
                        return "*****@unknown.com"

                masked = mask_email(st.session_state.temp_email)
                st.info(f"To confirm, please complete this email: `{masked}`")
                email_confirmation = st.text_input("Confirm your email")

                submitted = st.form_submit_button("Register")

                if submitted:
                    if username and password and email_confirmation:
                        if email_confirmation != st.session_state.temp_email:
                            st.error("❌ Email confirmation doesn't match.")
                        else:
                            hashed_password = hash_password(password)

                            # ✅ Generate Access Code
                            access_code = generate_access_code()

                            result = register_user(
                                username,
                                st.session_state.temp_email,
                                email_confirmation,
                                hashed_password,
                                role,
                                plan,
                                access_code
                            )

                            if "successfully" in result:
                                # ✅ Save to session
                                st.session_state.registration_success = True
                                st.session_state.access_code = access_code
                                st.session_state.do_rerun = True
                                st.markdown(f"""<div style="
                                  background-color: #f0f8ff; 
                                  border-left: 6px solid #1e90ff; 
                                   padding: 16px; 
                                    border-radius: 8px;
                                    font-family: Arial, sans-serif;
                                     color: #333;
                                     ">
                                    <h3 style="margin: 0; color: #1e90ff;">🔐 Your Secret Access Code</h3>
                                    <p style="font-size: 20px; font-weight: bold; color: #000;">{access_code}</p>
                                   <p style="font-size: 14px; color: #555;">Please save this code securely. You will need it for password changes!</p>
                                    </div> """,    unsafe_allow_html=True)

                                
                                st.rerun()
                            else:
                                st.error(result)
                    else:
                        st.warning("⚠️ Please fill in all fields.")

    # ✅ Trigger rerun outside the form
if st.session_state.get("do_rerun", False):
    st.session_state.do_rerun = False
    st.rerun()

## to redirect you to dashboard after login
 # force rerun to redirect to dashboard








# Get from session or input
elif choice == 'Delete Account':
    import time

    # ✅ Restrict access
    if st.session_state.get("role") != "md":
        st.error("⛔ Access Denied: This page is restricted to MD users only.")
        st.stop()

    # ✅ Check login state
    is_employee = st.session_state.get("employee_logged_in")
    is_md = st.session_state.get("logged_in")

    if not (is_employee or is_md):
        st.warning("⚠️ You are not logged in.")
        st.stop()

    # ✅ Determine table and session info
    if is_employee:
        table_name = "employees"
        email = st.session_state.get("employee_user", {}).get("email")
        name_value = st.session_state.get("employee_user", {}).get("name")
        password_column = "password"
        name_field = "name"
    else:
        table_name = "users"
        email = st.session_state.get("user", {}).get("email")
        # This was originally st.session_state.temp_email during registration
        name_value = st.session_state.get("user", {}).get("username")
        password_column = "password_hash"
        name_field = "username"

    st.write(f"🔐 Logged in as: `{email}`")
    confirm = st.text_input("Confirm your password to delete account", type="password")
    
    if st.button("❌ Delete My Account"):
        if not confirm:
            st.warning("⚠️ Please enter your password.")
            st.stop()

        # ✅ Hash the confirmation password (to match how it's stored)
        hashed_pw = hash_password(confirm)

        # ✅ Re-authenticate using hashed password
        login_check = supabase.table(table_name)\
            .select("*")\
            .eq("email", email)\
            .eq(password_column, hashed_pw)\
            .eq("deleted", False)\
            .execute()

        if not login_check.data:
            st.error("❌ Password incorrect or account not found.")
        else:
            # ✅ Perform soft delete
            delete_result = supabase.table(table_name)\
                .update({"deleted": True})\
                .eq("email", email)\
                .eq(name_field, name_value)\
                .execute()

            if not hasattr(delete_result, "error") or not delete_result.error:
                st.success("✅ Account deleted (soft delete).")

                # ✅ Clear session
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.clear()

                # ✅ Clear browser storage & redirect
                # ✅ Clear session and redirect to Login page in-app
                st_javascript("localStorage.removeItem('login_token');")
                time.sleep(1)
                st.session_state.page = "Login"  # 👈 Set to Login page
                st.rerun()

            else:
                st.error("❌ Failed to delete the account. Please try again later.")





# Check if already logged in (MD or Employee)
# this is to message after a suucessful login  instead of login form
elif choice == 'Login':
    # ✅ If already logged in, show welcome message instead of login form
    if st.session_state.get("logged_in") or st.session_state.get("employee_logged_in"):
        user_role = st.session_state.get("role", "Employee")  # This comes from the JWT

        if user_role == "md":
            user_name = st.session_state.get("user", {}).get("username", "Unknown User")
        else:  # Employee
            user_name = st.session_state.get("employee_user", {}).get("name", "Unknown User")
        

        st.markdown(f""" 
        <div style='padding: 20px; background-color: #f0f8ff; border-left: 6px solid #4CAF50; border-radius: 8px;'>
             <h2 style='color: #2c3e50;'>👋 Welcome back, <span style="color:#4CAF50;">{user_name}</span>!</h2>
             <p style='font-size: 18px; color: #555;'>
                 You are logged in as <strong style='color: #2c3e50;'>{user_role}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        


        st.markdown("___")

        # Action buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔁 Go to Sales Page"):
                switch_page("Sales")
        with col2:
            if st.button("🚪 Logout", key="logout_dashboard"):
                st.session_state.clear()
                st_javascript("localStorage.removeItem('login_token');",key="remove_login_token_6")
                st.success("You’ve been logged out.")
                time.sleep(1)
                st.rerun()

    else:
        # 🔐 Login form
        device = f"{platform.system()} {platform.release()}"
        login_type = st.radio("Login as:", ["MD", "Employee"], horizontal=True)

        with st.form("login_form"):
            st.subheader(f"🔐 {login_type} Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button(f"Login as {login_type}")

            if submit:
                if not email or not password:
                    st.warning("⚠️ Please enter both email and password.")
                else:
                    if login_type == "MD":
                        success = login_md(email, password)
                    elif login_type == "Employee":
                        # Only allow Employee login if MD is already identified
                        if "user_id" in st.session_state:
                            success = login_employee(email, password)
                        else:
                            st.error("❌ MD must be logged in first. No user_id (tenant) found.")
                            success = False

                    # ✅ After successful login
                    if success:
                        display_name = st.session_state.get("username") or st.session_state.get("user", {}).get("email")
                        with st.spinner("🔄 Logging you in..."):
                            # ✅ Track login in Supabase
                            user_id = st.session_state.get("user_id") 
                            role = st.session_state.get("role", "md")# Ensure you store this when MD logs in
                            ip_address = get_client_ip()  # You'll define this function
                            device = device    # Optional, can be from headers or user-agent
                            track_login(user_id, role)  # Ca
                            if login_type == "MD":
                                st.success(f"✅ Welcome {display_name} (MD)! Redirecting to Sales...")
                            elif login_type == "Employee":
                                employee_name = st.session_state.get("employee_user", {}).get("name")
                                st.success(f"✅ Welcome {employee_name} (Employee)! Redirecting...")
                            time.sleep(1.5)
                            st.rerun()
                      
        if st.session_state.get("employee_logged_in") or st.session_state.get("logged_in"):
            sync_plan_from_db(user_id)                

        # ❗ Login validation warnings
        if login_type == "MD" and not st.session_state.get("logged_in"):
            st.error("❌ You must be logged in as an MD to access this page.")

        if login_type == "Employee" and not st.session_state.get("employee_logged_in"):
            st.error("❌ You must be logged in as an Employee to access this page.")


st.markdown("___")
# Employee account creation form (only visible to logged-in MD)
# employee create account form when the md logins
if st.session_state.get("logged_in") and st.session_state.get("role") == "md":
    st.subheader('Create Employee Account')
if st.session_state.get("logged_in") and st.session_state.get("role") == "md":
    with st.expander('Create Employee Account'):
        st.subheader("👨‍💼 Create Employee Account")
        with st.form("create_employee_form"):
            name = st.text_input("Employee Name")
            email = st.text_input("Employee Email")
            password = st.text_input("Employee Password", type="password")
            role = st.selectbox("Role", ["employee"])  # optional roles

            create_button = st.form_submit_button("Create Employee")

            if create_button:
                if not name or not email or not password:
                    st.warning("⚠️ All fields are required.")
                else:
                    try:
                        hashed_password = hash_password(password)

                        # Automatically associate employee with MD's user_id
                        employee_data = {
                            "name": name.strip(),
                            "email": email.strip().lower(),
                            "password": hashed_password,
                            "role": role,
                            "user_id": st.session_state.user_id  # MD's ID
                        }

                        # Check if email already exists
                        existing_employee = supabase.table("employees") \
                            .select("email") \
                            .eq("email", employee_data["email"]) \
                            .execute()


                        if existing_employee.data:
                            st.error("❌ An employee with this email already exists. Please use a different email.")
                        else:
                            response = supabase.table("employees").insert(employee_data).execute()
                            if response.data:
                                st.success(f"✅ Employee account for '{name}' created successfully!-login")
                                st.rerun()
                            else:
                                st.error("❌ Failed to create employee account.")
                    except Exception as e:
                        st.error("⚠️ Something went wrong while creating the employee account. Please try again later.")











import requests

# Use your Paystack **SECRET** key here (starts with sk_live...) — not the PUBLIC key
PAYSTACK_SECRET_KEY =  os.getenv('PAYSTACK_SECRET_KEY')
    # this is to hide the real key from public eyes
CALLBACK_URL = "https://priscomsales.online/Dashboard"  # Optional, can be your app URL

def initialize_payment(email, amount, user_id):
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    unique_ref = f"{user_id}-{int(amount)}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    data = {
        "email": email,
        "amount": amount * 100,  # Convert to kobo
        "reference":  unique_ref,
        "callback_url": CALLBACK_URL
    }
   
    response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    return response.json()
    

# Simulated user info — in production, this should come from your auth/session
if "user_id" not in st.session_state or "user_email" not in st.session_state:
    st.error(" ")
    st.stop()

user_id = st.session_state["user_id"]
email = st.session_state["user_email"]

if st.button("Upgrade to Pro (₦20000)"):
    st.info('Upgrade to 1 month plan,you will have complete access to all your sales data.')
    result = initialize_payment(email, 20000, user_id)
    
    if result.get("status") and "data" in result:
        auth_url = result["data"].get("authorization_url")

        if auth_url:
            # ✅ Show the URL link (ALWAYS)
            st.markdown(f"[Click here to pay with Paystack]({auth_url})", unsafe_allow_html=True)

            # ✅ Also redirect automatically (optional)
            st.markdown(f"""
                <script>
                    window.location.href = "{auth_url}";
                </script>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ No authorization URL returned.")
    else:
        st.error("❌ Failed to initialize payment.")

# to verify is payment is recieved
def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def extract_user_id(reference):
    return int(reference.split('-')[0])

def activate_subscription(user_id):
    today = date.today()
    expires = today + timedelta(days=30)
    response = supabase.table("subscription").update({
        "plan": "pro",
        "is_active": True,
        "started_at": today.isoformat(),
        "expires_at": expires.isoformat()
    }).eq("user_id", user_id).execute()
    
    return response
# ✅ Update session state
st.session_state.plan = "pro"
st.session_state.is_active = True

# transaction is saved on the subcription table
def save_transaction(user_id, reference, amount, status):
    # Check if user already has a subscription
    existing = supabase.table("subscription").select("id").eq("user_id", user_id).execute()

    if existing.data:
        # Update existing subscription record
        supabase.table("subscription").update({
            "reference": reference,
            "amount": amount,
            "status": status,
            "plan": "pro",
            "is_active": True,
            "started_at": date.today().isoformat(),
            "expires_at": (date.today() + timedelta(days=30)).isoformat()
        }).eq("user_id", user_id).execute()
    else:
        # Insert new subscription record
        supabase.table("subscription").insert({
            "user_id": user_id,
            "reference": reference,
            "amount": amount,
            "status": status,
            "plan": "pro",
            "is_active": True,
            "started_at": date.today().isoformat(),
            "expires_at": (date.today() + timedelta(days=30)).isoformat()
        }).execute()

# ✅ 3. Handle Paystack payment verification
query_params = st.query_params
reference = query_params.get("reference")
tref=query_params.get('trxref')
if reference:
    reference = reference
    st.write("✅ Payment reference received:", reference)
    result = verify_payment(reference)
 
    if result["status"] and result["data"]["status"] == "success":
        user_id = extract_user_id(reference)
        activate_subscription(user_id)
        # ✅ Save transaction
        amount = result["data"]["amount"] // 100  # Convert from kobo to naira
        status = result["data"]["status"]
        save_transaction(user_id, reference, amount, status)
        
        st.success("🎉 Payment successful! Your Pro subscription is now active.")
                
    else:
        st.error("❌ Payment failed or could not be verified.")
else:
    st.info("ℹ️ No payment reference in URL.")

# to update the plan on jwt token
def login_or_upgrade_success(user_id, username, role, plan, is_active):
    email = st.session_state.get("user_email", None)
    token = generate_jwt(user_id, username, role, plan, is_active,email)
    st.session_state.jwt_token = token
    save_token_to_localstorage(token)
    restore_login_from_jwt()  # Refresh session state
    st.success(f"Welcome, {username}! You are now on the {plan.title()} plan.")



st.sidebar.subheader("💬 Feedback Form")

with st.sidebar.expander('Submit Feedback'):
    with st.sidebar.form("feedback_form"):
        name = st.sidebar.text_input("Your Name")
        email = st.sidebar.text_input("Your Email")
        feedback = st.sidebar.text_area("Your Feedback")

        submitted = st.form_submit_button("Submit")

        if submitted:
            if name and email and feedback:
                response = supabase.table("feedback").insert({
                    "name": name,
                    "email": email,
                    "feedback": feedback,
                    "user_id": st.session_state.get("user_id", None),
                }).execute()

                # Check if data is returned and no errors
                if response.data:
                    st.sidebar.success("✅ Thank you for your feedback!")
                    st.rerun()
                else:
                    st.sidebar.error("⚠️ Could not submit feedback. Please try again.")
                    






    




