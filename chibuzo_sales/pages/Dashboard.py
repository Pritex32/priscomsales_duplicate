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

import json
import os
from dotenv import load_dotenv
import jwt
import streamlit.components.v1 as components

## 🔐 Same secret key must be used across all pages

load_dotenv()

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

def restore_login_from_jwt():
    if not st.session_state.get("logged_in"):
        token = st_javascript("""localStorage.getItem("login_token");""")
        if token and token != "null":
            user_data = decode_jwt(token)
            st.write("Decoded JWT:", user_data)
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "Login"

restore_login_from_jwt()
def save_token_to_localstorage(token):
    st_javascript(f"""localStorage.setItem("login_token", "{token}");""")

def refresh_subscription_from_jwt():
    token = st.session_state.get("jwt_token")
    if not token:
        st.session_state.plan = "free"
        st.session_state.is_active = False
        return

    payload = decode_jwt(token)
    st.session_state.plan = payload.get("plan", "free").lower()
    st.session_state.is_active = payload.get("is_active", False)


from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database



# contact developer
st.sidebar.markdown("---")  # Adds a separator
if st.sidebar.button("📩 Contact Developer"):
    st.sidebar.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/prisca-ukanwa-800a1117a/)")

# ✅ Initialize session state variables ONCE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'  # default page







if "page" not in st.session_state:
    st.session_state.page = "Login"

menu = ["Login", "Register","Delete Account"]

choice = st.selectbox("Navigate 👇", menu, index=0)

if choice != st.session_state.page:
    st.session_state.page = choice
    st.rerun()
choice = st.session_state.page
# Secret Keys for Role-Based Registration
SECRET_KEYS = {
   

    "MD": "MD-1qXz$Df@78"
}


def hash_password(password: str) -> str:
    # Hash the password using SHA-256 (or a stronger hashing function like bcrypt)
    return hashlib.sha256(password.encode()).hexdigest()



def register_user(username, email, password_hash, role,plan, secret_key):
    try:
        # Check if username already exists in the users table
        existing_user = supabase.table("users").select("username").eq("username", username).execute()
        
        if existing_user.data:
            return f"Error: Username '{username}' already exists."

        # Check if email already exists in the users table
        existing_email = supabase.table("users").select("email").eq("email", email).execute()
        
        if existing_email.data:
            return f"Error: Email '{email}' already exists."
        
        if role == "MD":
            if secret_key != "MD-1qXz$Df@78":
                return "❌ Invalid secret key for MD registration."
        
        # Insert user details into the users table
        result = supabase.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role
        }).execute()
        # ✅ Extract user_id from the insert result
        if result.data and len(result.data) > 0:
            user_id = result.data[0].get("user_id")
        else:
            return "Error: Could not retrieve user_id after registration."
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
        
        # Check if there was an error in the response
        return "✅ User registered successfully!"

        

    except Exception as e:
        return f"Error: {str(e)}"

# get md subscription status
def get_md_subscription(md_user_id):
    response = supabase.table("subscription")\
        .select("plan, is_active, expires_at")\
        .eq("user_id", md_user_id)\
        .order("created_at", desc=True)\
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
                st_javascript(f"""localStorage.setItem("login_token", "{token}");""")

                st.success("Login successful!")
            else:
                st.error("Invalid login")



            # If you later switch to bcrypt (recommended), use:
            # if bcrypt.checkpw(password.encode(), stored_password_hash.encode()):
            #     return user

        return None
    except Exception as e:
        print(f"Login error: {e}")  # Add error logging
        return None











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
        .select("plan, is_active")\
        .eq("user_id", md_user_id)\
        .order("started_at", desc=True)\
        .limit(1)\
        .execute()

    subscription = sub_response.data[0] if sub_response.data else {}

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

    # ✅ Generate a JWT for the employee
    jwt_token = generate_jwt(
    user_id=md_user_id,
    username=user_data.get("name"),
    email=user_data.get["email"],
    role=user_data.get("role", "employee")
)


    # ✅ Save the JWT to browser localStorage using JavaScript
    st_javascript(f"""localStorage.setItem("login_token", "{jwt_token}");""")

    # Optional visual feedback
    st.success(f"✅ Welcome {user_data.get('name')} (Employee)!")
    st.write(f"🆔 Your Employee ID: `{st.session_state.employee_id}`")
    return True
    

# to fetch subcription data
def fetch_subscription_data(user_id):
    try:
        # Example: fetch all subscription records for this user_id (if multiple rows)
        response = supabase.table("subscription").select("*").eq("user_id", user_id).execute()
        data = response.data if response.data else []
        # Convert to DataFrame for easier display
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error fetching subscription data: {e}")
        return pd.DataFrame()  # empty df on error
# to limit you to 10 rows
def show_user_data():
    FREE_LIMIT = 10
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("User not logged in.")
        return

    plan = st.session_state.get("plan", "free")
    subscription_active = st.session_state.get("is_active", False)
    plan = st.session_state.get("plan", "free")
    is_active = st.session_state.get("is_active", False)
    # 👇 Show plan type and status message
    if plan == "free" and not is_active:
        st.info("🆓 You are currently on the **Free Plan**. Limited to 10 transactions.")
    elif plan == "pro" and is_active:
        st.success("💼 You are on the **Pro Plan**. Enjoy unlimited access!")
    else:
        st.warning("⚠️ Your subscription status is unclear. Please contact support.")
    df = fetch_subscription_data(user_id)
    transaction_count = len(df)
    if plan == "free" and not is_active and transaction_count >= FREE_LIMIT:
        st.error("🚫 Your free plan has been exhausted. Please subscribe to continue using the app.")
        st.stop()  # Prevent access to the rest of the app

if st.session_state.get("logged_in"):
    show_user_data()


def login_md(email, password):
    user = login_user(email, password)
    
    if not user:
        st.error("❌ Invalid email or password.")
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
        sub_result = supabase.table("subscription")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        sub = sub_result.data if sub_result.data else {}
    except Exception as e:
        st.warning(f"⚠️ Could not retrieve subscription info: {str(e)}")
        sub = {}

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
    jwt_token = generate_jwt(user_id=user_id, username=user.get("username") or user["email"],email=user["email"], role=role)

    st_javascript(f"""localStorage.setItem("login_token", "{jwt_token}");""")

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
    with st.form("registration_form"):
        # Input fields
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        plan = st.selectbox("Choose Plan", ["free", "pro"])

        role = st.selectbox("Select Role", ["MD"])
        secret_key = st.text_input("Secret Key", type="password")
        
        # Submit button
        submitted = st.form_submit_button("Register")

        if submitted:
            if username and email and password and plan and secret_key:
                # Hash the password
                hashed_password = hash_password(password)

                # Register user in the users table
                result = register_user(username, email, hashed_password, role, plan,secret_key)
                # Show success and redirect
                if isinstance(result, str) and "successfully" in result.lower():
                    st.success(result)
                    st.info("Redirecting to login...")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error(result if result else "⚠️ Unknown error.")
 # Refresh the page
                
            else:
                st.warning("⚠️ Please fill in all fields.")

## to redirect you to dashboard after login
 # force rerun to redirect to dashboard








# Get from session or input
elif choice == 'Delete Account':
    is_employee = st.session_state.get("employee_logged_in")
    is_md = st.session_state.get("logged_in")

    if not (is_employee or is_md):
        st.warning("⚠️ You are not logged in.")
    else:
        # Identify which table and name column to use
        if is_employee:
            table_name = "employees"
            email = st.session_state.get("employee_user", {}).get("email")
            name_field = "name"
            name_value = st.session_state.get("employee_user", {}).get("name")
            password_column = "password"
        else:
            table_name = "users"  # or "mds", based on your actual MD table name
            email = st.session_state.get("username")
            name_field = "username"
            password_column = "password_hash"
            name_value = st.session_state.get("user", {}).get("username")
        st.write("🔍 Debug Info")
        st.write("Email:", email)
        st.write("Name:", name_value)
        st.write("Password Hash:", hash_password(password_column))
        # Confirm deletion
        st.write(f"Logged in as: `{email}`")
        confirm = st.text_input("🔐 Confirm your password to delete account", type="password")

        if st.button("❌ Delete My Account"):
            # Re-authenticate
            hashed_pw = hash_password(confirm)
            login_check = supabase.table(table_name)\
                .select("*")\
                .eq("email", email)\
                .eq(password_column, hashed_pw)\
                .execute()

            if not login_check.data:
                st.error("❌ Password incorrect or account not found.")
            else:
                # Proceed to delete
                delete_result = supabase.table(table_name)\
                    .delete()\
                    .eq("email", email)\
                    .eq(name_field,name_value)\
                    .execute()

                if not hasattr(delete_result, "error") or not delete_result.error:
                    st.success("✅ Account deleted successfully.")
                    # ✅ Clear all session data
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.session_state.clear()
                    st_javascript("localStorage.removeItem('login_token');")
                    time.sleep(1)

    # ✅ Redirect to home page
                    st_javascript("""
                                          window.location.href = "/";    """)
                    st.stop()
                else:
                    st.error(f"❌ Deletion failed: {delete_result.error}")












    


   








# Check if already logged in (MD or Employee)
# this is to message after a suucessful login  instead of login form
elif choice == 'Login':
    # ✅ If already logged in, show welcome message instead of login form
    if st.session_state.get("logged_in") or st.session_state.get("employee_logged_in"):
        user_role = st.session_state.get("role", "Employee")  # This comes from the JWT

        if user_role == "MD":
            user_name = st.session_state.get("user", {}).get("username", "Unknown User")
        else:  # Employee
            user_name = st.session_state.get("employee_user", {}).get("name", "Unknown User")

        st.title(f"👋 Welcome back, {user_name}!")
        st.info(f"You are logged in as **{user_role}**.")

        # Action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔁 Go to Sales Page"):
                switch_page("sales")
        with col2:
            if st.button("🚪 Logout", key="logout_dashboard"):
                st.session_state.clear()
                st_javascript("localStorage.removeItem('login_token');")
                st.success("You’ve been logged out.")
                time.sleep(1)
                st.rerun()

    else:
        # 🔐 Login form
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

                        if login_type == "MD":
                            st.success(f"✅ Welcome {display_name} (MD)! Redirecting to Sales...")
                        elif login_type == "Employee":
                            employee_name = st.session_state.get("employee_user", {}).get("name")
                            st.success(f"✅ Welcome {employee_name} (Employee)! Redirecting to Sales...")

                        time.sleep(2)
                        switch_page("Sales")

        # ❗ Login validation warnings
        if login_type == "MD" and not st.session_state.get("logged_in"):
            st.error("❌ You must be logged in as an MD to access this page.")

        if login_type == "Employee" and not st.session_state.get("employee_logged_in"):
            st.error("❌ You must be logged in as an Employee to access this page.")



# Employee account creation form (only visible to logged-in MD)
# employee create account form when the md logins
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
                            else:
                                st.error("❌ Failed to create employee account.")
                    except Exception as e:
                        st.error(f"⚠️ Error: {str(e)}")











import requests

# Use your Paystack **SECRET** key here (starts with sk_live...) — not the PUBLIC key
PAYSTACK_SECRET_KEY = "sk_test_b4d6bbad64ad55d65008808f70cf8ba74ff830d7"   # this is to hide the real key from public eyes
CALLBACK_URL = "https://priscomac-sales-software.onrender.com/Dashboard"  # Optional, can be your app URL

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
    st.write(data)
    response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    st.write("Paystack Response:", response.json()) 
    return response.json()
    

# Simulated user info — in production, this should come from your auth/session
if "user_id" not in st.session_state or "user_email" not in st.session_state:
    st.error("User information missing. Please log in.")
    st.stop()

user_id = st.session_state["user_id"]
email = st.session_state["user_email"]

if st.button("Upgrade to Pro (₦1000)"):
    result = initialize_payment(email, 1000, user_id)
    st.write("🔍 Paystack Init Result:", result)  # DEBUG

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
    st.write("📅 Subscription upsert response:", response)
    return response
# ✅ Update session state
st.session_state.plan = "pro"
st.session_state.is_active = True

# transaction is saved on the subcription table
def save_transaction(user_id, reference, amount, status):
    supabase.table("subscription").insert({
        "user_id": user_id,
        "reference": reference,
        "amount": amount,
        "status": status
    }).execute()



#

# ✅ 3. Handle Paystack payment verification
query_params = st.query_params
st.write("🧪 Full Query Params:", st.query_params)
reference = query_params.get("reference")
tref=query_params.get('trxref')
st.write(tref)
st.write(reference)
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
        st.write("User ID extracted:", user_id)
        st.write("Full reference:", reference)
    else:
        st.error("❌ Payment failed or could not be verified.")
else:
    st.info("ℹ️ No payment reference in URL.")


def login_or_upgrade_success(user_id, username, role, plan, is_active):
    token = generate_jwt(user_id, username, role, plan, is_active)
    st.session_state.jwt_token = token
    save_token_to_localstorage(token)
    restore_login_from_jwt()  # Refresh session state
    st.success(f"Welcome, {username}! You are now on the {plan.title()} plan.")
