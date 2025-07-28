
import streamlit as st
st.set_page_config(page_title="inventory", layout="wide")
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
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime,timedelta ,date
from streamlit_extras.switch_page_button import switch_page 
from datetime import datetime, timedelta

import json
import time
import uuid
from collections import defaultdict
import io
import plotly.express as px
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from datetime import datetime, timedelta
import jwt




# to design the entire lay out

st.markdown("""
    <style>
    /* Custom section divider */
    .section-divider {
        border: none;
        height: 2px;
        background: linear-gradient(to right, #ccc, #888, #ccc);
        margin: 20px 0;
    }

    /* Custom title & subheader */
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 600;
        color: #34495e;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* Button styling */
    div.stButton > button {
        background-color: #27ae60;
        color: white;
        font-weight: bold;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }

    div.stButton > button:hover {
        background-color: #219150;
    }

    /* Expander styling */
    details summary {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)





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
        token = st_javascript("""localStorage.getItem("login_token");""",key=f"get_login_token_1998")
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
                st_javascript("""localStorage.removeItem("login_token");""",key=f"get_login_token_1778")
                st.session_state.login_failed = True

# Run this first
if st.session_state.get("logged_in"):
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





# this shows the logged user info
if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    st.warning("Please log in first.")
    st.stop()



# connecting to supabase

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
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    block_free_user_if_limit_exceeded()
    show_plan_status()



st.subheader("**📦 REAL-TIME INVENTORY MANAGEMENT SYSTEM**")

with st.sidebar:
    selected = option_menu(
        menu_title=('Options'),
        options=["Home", "Filter","Reports",'Delete'],
        icons=["house", "plus-circle","bar-chart-line"],
        default_index=0
    )

# === Helper function to get today's date ===
# === Setup ===
today = str(date.today()) #this is to set up the todays date

# === Fetch data from Supabase ===
@st.cache_data(ttl=7200)
def fetch_inventory(user_id):
    return supabase.table("inventory_master_log").select("*").eq("user_id", user_id).execute().data

@st.cache_data(ttl=7200) # to load requisition table
def fetch_requisitions(user_id):
    return supabase.table( "sales_master_log").select("*").eq("sale_date", today).eq("user_id", user_id).execute().data

@st.cache_data(ttl=7200) # this is to load restock table
def fetch_restocks(user_id):
    return supabase.table("goods_bought").select("*").eq("purchase_date", today).eq("user_id", user_id).execute().data

# for reorder level alert
def get_low_stock_items(user_id):
    records = supabase.table("inventory_master_log")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute().data

    low_stock = [
        item for item in records
        if item.get("closing_balance", 0) <= item.get("reorder_level", 0)
    ]

    return low_stock

# this is to design the dataframe



# === Load data ===
with st.spinner("Fetching data..."): # this is to show data is loading and not to show error until data loads
    inventory = fetch_inventory(user_id)
    requisitions = fetch_requisitions(user_id)
    restocks = fetch_restocks(user_id)


df_inventory = pd.DataFrame(inventory)

# === Display Inventory ===
col9,col10=st.columns([4,1])
if selected == 'Home':
    with col9:
        st.subheader("📋 Current Inventory")
    with col10:
        st.markdown("<div style='padding-top: 8px;'></div>", unsafe_allow_html=True)  # Align button vertically
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    df_inventory = pd.DataFrame(inventory)
   
    st.dataframe(df_inventory.tail(10))
    # to download the entire data
    csv = df_inventory.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Full Inventory CSV", data=csv, file_name='full_inventory.csv', mime='text/csv')

    selected_date = st.date_input("**Select Date to Update Inventory**", value=date.today())
    

    
    



# === Function to Move Today's Requisitions to Requisition History ===

def move_requisitions_to_history(selected_date, user_id):
    # Fetch today's requisitions
    requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", selected_date).execute().data
    
    if requisitions_today:
        # Get the schema of the requisition_history table
        table_schema = supabase.table("sales_master_log").select("*").limit(1).execute().data
        if not table_schema:
            st.error("❌ Failed to retrieve sale history table schema!")
            return

        # Extract columns from the schema to ensure only valid columns are inserted
        valid_columns = table_schema[0].keys()

        # Filter requisitions_today to only include valid columns
        filtered_requisitions = [
            {key: entry[key] for key in entry if key in valid_columns} 
            for entry in requisitions_today
        ]

        # Loop over requisitions and update or insert as necessary
        for entry in filtered_requisitions:
            requisition_id = entry.get("sale_id")

            # Try to update existing records
            update_response = supabase.table("sales_master_history").upsert(entry,on_conflict=["sale_id", "user_id"]).execute()

            # Check if the response is successful
            if update_response.data:
                # If update was successful, delete the requisition from today's list
                delete_response = supabase.table("sales_master_log").delete().eq("user_id", user_id).eq("sale_id", requisition_id).execute()
                
                if delete_response.data:  # Check if delete response is successful
                    st.success(f"✅sale ID {requisition_id} moved to salehistory.")
                else:
                    st.error(f"❌ Failed to delete sale ID {requisition_id}: {delete_response.error}")
            else:
                st.error(f"❌ Failed to update sale ID {requisition_id}: {update_response.error}")
    else:
        st.info("ℹ️ No sale found for today.")
## function to move the retock part



def move_restocks_to_history(selected_date,user_id):
    # Fetch today's restocks
    restocks_today = supabase.table("goods_bought").select("*").eq("purchase_date", selected_date).execute().data
    if restocks_today:
        for restock in restocks_today:
            restock.pop("total_price", None) # to hide total price column in order to update
            # Check if restock can be moved to history
            response = supabase.table("goods_bought_history").upsert(restock,on_conflict=["purchase_id", "user_id"]).execute()
            if response.data:
                # Delete restock from today's list
                delete_response = supabase.table("goods_bought").delete().eq("user_id", user_id).eq("purchase_id", restock["purchase_id"]).execute()
                if delete_response.data:
                    st.success(f"✅ Restock ID {restock['purchase_id']} moved to history.")
                else:
                    st.error("❌ Failed to delete restock from today.")
            else:
                st.error(f"❌ Failed to move restock ID {restock['purchase_id']} to history.")
    else:
        
        st.markdown("""
<div style="padding: 15px; background-color: #FFA500; border-left: 6px solid #2196F3; border-radius: 5px;">
    ℹ️ <strong>Info:</strong> No restocks found for today.
</div>
""", unsafe_allow_html=True)

            
processed_sale_ids = set()
processed_purchase_ids = set()

## function to update and move the requisition and restock
def update_inventory_balances(selected_date,user_id):
    # Fetch today's requisitions and restocks
    requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", selected_date).execute().data
    restocks_today = supabase.table("goods_bought").select("*").eq("user_id", user_id).eq("purchase_date", selected_date).execute().data

   

    # If both are empty, show a warning and stop
    if not requisitions_today and not restocks_today:
        st.warning("⚠️ No sales or purchases to update today.")
        return
    
     # Combine and group by (item_id, transaction_date)
    transaction_map = defaultdict(lambda: {"supplied_quantity": 0, "stock_out": 0, "return_quantity": 0})


    # Process restocks
    
    for entry in restocks_today:
        purchase_id = entry.get("purchase_id")

    # 🔒 Check if this purchase_id already exists in the inventory log
        existing_purchase_log = supabase.table("inventory_master_log")\
        .select("purchase_id")\
        .eq("user_id", user_id)\
        .eq("purchase_id", purchase_id)\
        .execute().data

        if existing_purchase_log:
            st.warning(f"🚫 Purchase ID {purchase_id} already exists in inventory log. Skipping to avoid double update.")
            continue
         # 🧠 Check if it's already processed in this session
        if purchase_id in processed_purchase_ids:
            st.error(f"❌ Purchase ID {purchase_id} has already been processed. Duplicate detected.")
            continue
         # Add to processed list
        processed_purchase_ids.add(purchase_id)
        key = (entry["item_id"], entry["purchase_date"])
        transaction_map[key]["supplied_quantity"] += entry.get("supplied_quantity", 0)
   

    # Process requisitions
   
    for entry in requisitions_today:
        sale_id = entry.get("sale_id")
         # 🔒 Check if this sale_id already exists in the inventory log
        existing_sale_log = supabase.table("inventory_master_log")\
        .select("sale_id")\
        .eq("user_id", user_id)\
        .eq("sale_id", sale_id)\
        .execute().data

        if existing_sale_log:
            st.warning(f"🚫 Sale ID {sale_id} already exists in inventory log. Skipping to avoid double update.")
            continue

    # 🧠 Check if it's already processed in this session
        if sale_id in processed_sale_ids:
            st.error(f"❌ Sale ID {sale_id} has already been processed. Duplicate detected.")
            continue
        processed_sale_ids.add(sale_id)
        key = (entry["item_id"], entry["sale_date"])
        transaction_map[key]["stock_out"] += entry.get("quantity", 0)
        transaction_map[key]["return_quantity"] += entry.get("return_quantity", 0)

    # Fetch existing inventory
    inventory_response = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).execute().data
    inventory = pd.DataFrame(inventory_response)

    # Track updated items
    updated_count = 0
    failed_items = []


    for (item_id, log_date), values in transaction_map.items():
        # Normalize log_date from string or datetime to just YYYY-MM-DD string
        if isinstance(log_date,date):
            parsed_date = log_date
        else:
            parsed_date = datetime.fromisoformat(str(log_date)).date()

            log_date = parsed_date.isoformat()
           

         # 🔎 Find the last log date for this item before the selected date
        prev_day_log = supabase.table("inventory_master_log")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("item_id", item_id)\
            .lt("log_date", parsed_date.isoformat())\
            .order("log_date", desc=True)\
            .limit(1)\
            .execute().data



        if prev_day_log:
            prev_closing = int(prev_day_log[0].get("closing_balance", 0) or 0) # thi one updae the closing balance with closing balance from yesterday
        else:
            prev_closing = 0


    # ✅ Use pandas to get item info
        item_row = inventory[inventory["item_id"] == item_id]
        if item_row.empty:
            continue  # Skip if item not found in inventory

        item_name = item_row.iloc[0]["item_name"]
        
         # 📦 Get transaction values
        supplied_quantity = values.get("supplied_quantity", 0)
        stock_out = values.get("stock_out", 0)
        return_quantity = values.get("return_quantity", 0)


   



        # Ensure integers
        try:
            stock_out = int(stock_out or 0)
            supplied_quantity = int(supplied_quantity  or 0)
            
            return_quantity = int(return_quantity or 0)
            open_balance = int(prev_closing or 0)
            
           
## this code is to make sure what is updated doesnt disappear
           
            existing_log = next((entry for entry in inventory_response 
                                 if entry["item_id"] == item_id and entry["log_date"] == selected_date.isoformat()), None)


             # Merge with existing values if any
            
            if existing_log:            
                supplied_quantity += int(existing_log.get("supplied_quantity", 0))
                stock_out += int(existing_log.get("stock_out", 0))
                return_quantity += int(existing_log.get("return_quantity", 0))
                open_balance = int(existing_log.get("open_balance", open_balance))
                        
            else:                
                open_balance = int(prev_closing or 0)
                
                if supplied_quantity == 0 and stock_out == 0 and return_quantity == 0: # this one makes sure that no date is over written
                    continue

            total_available = open_balance + supplied_quantity + return_quantity # this calculate the closing bal to knw when u r out stock
            
            if total_available <= 0: # this ensure once you are out of stock , nodeduction can be made
                st.warning(f"🚫 You are out of stock for '{item_name}'. No stock-out will be recorded.")
                st.info(f"📊 Debug Info for {item_name}: OB={open_balance}, IN={supplied_quantity}, RETURN={return_quantity}, Total={total_available}")
                continue

            closing_balance = total_available - stock_out  # this updates the closing blance
           
               

            daily_log = {
                "item_id": item_id,
                "user_id": user_id,
                "item_name": item_name,
                "open_balance": open_balance,
                "supplied_quantity": supplied_quantity,
                "stock_out": stock_out,
                "return_quantity": return_quantity,
                
                "log_date":log_date,
                "last_updated": selected_date.isoformat()
            }
            # Track origin # sale id and purchase id is inserted only if the exist in entry
            if "sale_id" in entry:
                daily_log["sale_id"] = entry["sale_id"]
            if "purchase_id" in entry:
                daily_log["purchase_id"] = entry["purchase_id"]
            # Check if a record for this item/date/user already exists , this is to make sure that Allow duplicates for the same item across different days
            # ❌ But no duplicates for the same item on the same day
            existing_log = supabase.table("inventory_master_log")\
                 .select("*")\
                .eq("user_id", user_id)\
                .eq("item_id", item_id)\
                .eq("log_date", log_date)\
                 .execute().data

            if existing_log:
                response = supabase.table("inventory_master_log")\
                                .update(daily_log)\
                             .eq("user_id", user_id)\
                             .eq("item_id", item_id)\
                             .eq("log_date", log_date)\
                                 .execute()
            else:
                response = supabase.table("inventory_master_log")\
                    .insert(daily_log)\
                        .execute()


            if response.data:
                updated_count += 1
                st.info(f"🗓️ Log created for {item_name} on {log_date}: OB={open_balance}, IN={supplied_quantity}, OUT={stock_out}, CB={closing_balance}")
                

            else:
                failed_items.append(item_name)

        except Exception as e:
            failed_items.append(f"{item_name} (❌ Failed to log due to a system error)")

    # Display results once
    if updated_count:
        st.success(f"✅ Inventory log updated for {updated_count} items.")
       
    if failed_items:
        st.error(f"❌ Failed to update: {', '.join(failed_items)}")

    st.cache_data.clear()

# Trigger Inventory Update and Move to History
if selected == 'Home':
    col5, col6 = st.columns(2)
    
    # ✅ Left Column: Low Stock Items
    with col5:
        low_stock_items = get_low_stock_items(user_id)
        if low_stock_items:
            st.markdown("""
                <div style="padding: 15px; background-color: #fff4e5; border-left: 6px solid #ffa726; border-radius: 5px; color: black;">
                ⚠️<strong>Warning:</strong> The following items are low in stock:  
                </div>
            """, unsafe_allow_html=True)
            max_display = 3  # Show first 3
            for item in low_stock_items[:max_display]:
                st.write(f"**🔻 {item['item_name']}: {item['closing_balance']} units left (reorder level: {item['reorder_level']})**")
            if len(low_stock_items) > max_display:
                with st.expander(f"**View all {len(low_stock_items)} low-stock items**"):
                    for item in low_stock_items[max_display:]:
                        st.write(f"**🔻 {item['item_name']}: {item['closing_balance']} units left (reorder level: {item['reorder_level']})**")
        else:
            st.success("✅ All items are sufficiently stocked.")
    
    # ✅ Right Column: Return Item to Inventory
    with col6:
        with st.expander('**➕ Return Item to Inventory**'):
            
            # ✅ Step 1: Access Code Security Check
            access_input = st.text_input("Enter Access Code", type="password", key="access_code_input")
            correct_access_code = st.session_state.get("access_code")
            
            if access_input:
                if access_input == correct_access_code:
                    st.success("✅ Access granted. You can now return an item.")
                    
                    with st.form("return_inventory_form"):
                        item_dict = fetch_inventory_items(user_id)
                        item_options = ["Select an item"] + list(item_dict.keys())
                        item_name = st.selectbox("Select Item", item_options, key="item_selectbox")
                        item_id = item_dict.get(item_name, None)
                        
                        return_quantity = st.number_input('Return Quantity', min_value=1, step=1)
                        # ✅ Fetch previous closing balance for preview
                        prev_closing = 0
                        if item_id and item_name != "Select an item":
                            prev_day_log = supabase.table("inventory_master_log") \
                                .select("*") \
                                .eq("user_id", user_id) \
                                .eq("item_id", item_id) \
                                .lt("log_date", selected_date.isoformat()) \
                                .order("log_date", desc=True) \
                                .limit(1) \
                                .execute().data
                            if prev_day_log:
                                prev_closing = int(prev_day_log[0].get("closing_balance", 0) or 0)
                                # ✅ Display previous and expected new balance
                                expected_new_balance = prev_closing + return_quantity
                                st.info(f"📦 Previous Closing Balance: {prev_closing} units")
                                st.info(f"🔄 After returning {return_quantity}, expected stock: {expected_new_balance} units")
                            else:
                                st.warning("⚠️ No previous record found for this item.")

                        submit = st.form_submit_button("Submit")
                        
                        if submit:
                            if item_name == "Select an item" or item_id is None:
                                st.warning("Please select a valid item.")
                                st.stop()
                            else:
                                try:
                                    log_data = {
                                        "user_id": user_id,
                                        "item_id": item_id,
                                        "item_name": item_name,
                                        "log_date": selected_date.isoformat(),
                                        "last_updated": selected_date.isoformat()
                                    }
                                    
                                    # ✅ Check if an entry already exists for today
                                    existing_log = supabase.table("inventory_master_log") \
                                        .select("*") \
                                        .eq("user_id", user_id) \
                                        .eq("item_id", item_id) \
                                        .eq("log_date", selected_date) \
                                        .execute().data
                                    
                                    if existing_log:
                                        existing_entry = existing_log[0]
                                        previous_return = int(existing_entry.get("return_quantity", 0))
                                        log_data["return_quantity"] = previous_return + return_quantity
                                        log_data["stock_out"] = existing_entry.get("stock_out", 0)
                                        log_data["supplied_quantity"] = existing_entry.get("supplied_quantity", 0)
                                        log_data["opening_balance"] = prev_closing  # ✅ Ensure opening balance updates too
                                        
                                        response = supabase.table("inventory_master_log") \
                                            .update(log_data) \
                                            .eq("user_id", user_id) \
                                            .eq("item_id", item_id) \
                                            .eq("log_date", selected_date) \
                                            .execute()
                                    else:
                                        # ✅ If new, insert fresh log
                                        log_data["opening_balance"] = prev_closing  # <-- Add here
                                        log_data["return_quantity"] = return_quantity
                                        log_data["stock_out"] = 0
                                        log_data["supplied_quantity"] = 0
                                        response = supabase.table("inventory_master_log") \
                                            .insert(log_data) \
                                            .execute()
                                    
                                    st.success(f"{return_quantity} units of '{item_name}' returned and stock updated.")
                                    st.rerun()
                                    
                                    # ✅ Show updated log for this date
                                    updated_row = inventory[
                                        (inventory["item_id"] == item_id) & (inventory["log_date"] == selected_date)
                                    ]
                                    if not updated_row.empty:
                                        st.info("📦 Updated inventory log:")
                                        st.dataframe(updated_row)
                                    else:
                                        st.info("ℹ️ No inventory log found for this item today.")
                                
                                except Exception as e:
                                    st.error(f"❌ Failed to process the return. Please try again later: {e}")
                else:
                    st.error("❌ Incorrect access code. Please try again.")

        # this add divided line                    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    
    if st.button("**🔄 Update Inventory Balances**"):
            
        update_inventory_balances(selected_date, user_id)
        move_requisitions_to_history(selected_date,user_id)  # Move today's requisitions after updating the inventory
        move_restocks_to_history(selected_date,user_id)  # Move today's restocks to history

# Display Today's Logs
    with st.expander("📤 Today's Sale "):
        requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", selected_date).execute().data
        st.dataframe(pd.DataFrame(requisitions_today))

    with st.expander("📥 Today's Restocks"):
        restocks_today = supabase.table("goods_bought").select("*").eq("user_id", user_id).eq("purchase_date", selected_date).execute().data
        st.dataframe(pd.DataFrame(restocks_today))
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
# Display Daily Inventory Log by Date
    col17,col18=st.columns([3,1])
    with col17: 
        st.subheader("📆 Daily Inventory Log History")
    with col18:
        # Fetch inventory items using cached function
        inventory_dict = fetch_inventory_items(user_id)

         # Calculate unique inventory count
        unique_inventory_count = len(inventory_dict)

         # Display as a metric
        st.metric(label="📦 Total Inventory Items", value=unique_inventory_count)

    selected_log_date = st.date_input("Select a date", value=date.today())
    daily_history = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).eq("log_date", str(selected_log_date)).execute().data


    if daily_history:
        st.dataframe(pd.DataFrame(daily_history).tail(100))
    else:
        st.info("ℹ️ No inventory log found for this date.")




## filter sections
# Fetch all inventory master logs
all_logs = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).execute().data
df_logs = pd.DataFrame(all_logs)
if selected == 'Filter':
    st.subheader('Filter inventory')
    if not df_logs.empty:
        with st.expander("🔍 Filter Inventory Log", expanded=True):
            df_logs["log_date"] = pd.to_datetime(df_logs["log_date"])

        # Get unique values for filters
            item_options = df_logs["item_name"].unique()
            min_date = df_logs["log_date"].min().date()
            max_date = df_logs["log_date"].max().date()
            min_supply = int(df_logs["supplied_quantity"].min())
            max_supply = int(df_logs["supplied_quantity"].max())

        # Sidebar filters
            selected_item = st.selectbox("Select an Item", options=item_options)
            date_range = st.date_input("Select Date Range", [min_date, max_date])

        # Handle slider safely
        if min_supply == max_supply:
            st.warning("⚠️ All supply values are the same, slider is disabled.")
            supply_range = (min_supply, max_supply)
        else:
            supply_range = st.slider(
            "Supply Range",
            min_value=min_supply,
            max_value=max_supply,
            value=(min_supply, max_supply)
            )

        # Apply filters
        filtered_df = df_logs[
            (df_logs["item_name"] == selected_item) &
            (df_logs["log_date"] >= pd.to_datetime(date_range[0])) &
            (df_logs["log_date"] <= pd.to_datetime(date_range[1])) &
            (df_logs["supplied_quantity"] >= supply_range[0]) &
            (df_logs["supplied_quantity"] <= supply_range[1])
        ]

        # Show filtered table
        st.dataframe(filtered_df)

    else:
        st.warning("⚠️ Inventory log table is empty.")


## report section

def get_summary_report(time_period, start_date, end_date):
    try:
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        response = supabase.table("inventory_master_log") \
            .select("log_date", "item_name", "open_balance", "supplied_quantity", "return_quantity", "stock_out", "closing_balance") \
            .gte("log_date", start_date_str) \
            .lte("log_date", end_date_str) \
            .eq("user_id", user_id)\
            .execute()

        if hasattr(response, "error") and response.error:
            st.error(f"❌ Supabase Error: {response.error}")
            return pd.DataFrame()

        if not hasattr(response, "data") or not response.data:
            st.warning("⚠️ No data returned from Supabase.")
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        df["log_date"] = pd.to_datetime(df["log_date"])  # Ensure datetime format

        time_trunc_map = {
            "Weekly": "W",
            "Monthly": "M",
            "Yearly": "Y"
        }

        if time_period not in time_trunc_map:
            st.error("❌ Invalid time period selected!")
            return pd.DataFrame()

        df_summary = (
            df.groupby([pd.Grouper(key="log_date", freq=time_trunc_map[time_period]), "item_name"])
            .agg(
                total_open_stock=('open_balance', 'sum'),
                total_stock_in=("supplied_quantity", "sum"),
                total_returned=("return_quantity", "sum"),
                total_stock_out=("stock_out", "sum")
            )
            .reset_index()
        )

        df_summary['total_closing_stock'] = (
            df_summary['total_open_stock'] + df_summary['total_returned'] +
            df_summary['total_stock_in'] - df_summary['total_stock_out']
        )

        df_summary.rename(columns={"log_date": "period"}, inplace=True)
        return df_summary

    except Exception as e:
        st.error(f"❌ Error fetching summary report.")
        return pd.DataFrame()

# 🔹 Streamlit UI

if selected == 'Reports':
    if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()
    st.title("📦 Inventory Summary Reports")

# Select Report Type
    report_type = st.selectbox("📆 Select Report Type", ["Weekly", "Monthly", "Yearly"])

# Select Date Range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Start Date", datetime.today().replace(day=1))
    with col2:
        end_date = st.date_input("📅 End Date", datetime.today())

# Generate Button
    if st.button("📈 Generate Report"):
        if start_date > end_date:
            st.error("❌ Start date cannot be after end date!")
        else:
            summary_df = get_summary_report(report_type, start_date, end_date)

        if not summary_df.empty:
            st.success(f"✅ {report_type} Report Generated Successfully!")
            st.dataframe(summary_df, use_container_width=True)

            # Download Excel
            buffer = io.BytesIO()
            summary_df.to_excel(buffer, index=False, sheet_name="Summary Report")
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download Report as Excel",
                data=buffer,
                file_name=f"{report_type.lower()}_inventory_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            
        else:
            st.warning("⚠️ No data found for the selected date range.")


if selected =='Delete':
    st.subheader("🗑️ Delete Inventory Item")
    if "role" not in st.session_state or st.session_state.role != "md":
        st.warning("🚫 You are not authorized to view this page.")
        st.stop()
    item_name_to_delete = st.text_input("Enter Item Name to Delete", "")

    if item_name_to_delete and user_id:
        # Step 1: Get the inventory item record
        inventory_items = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).eq("item_name", item_name_to_delete).execute().data

        if inventory_items:
            item = inventory_items[0]
            item_id = item.get("item_id")
            st.write(f"**Item ID:** {item_id}")
            st.write(f"**Item Name:** {item.get('item_name')}")
            st.write(f"**Stock In:** {item.get('supplied_quantity', 0)}")
            st.write(f"**Stock Out:** {item.get('stock_out', 0)}")
            confirm = st.checkbox("⚠️ I understand that this will delete related sales, purchases, restocks, etc.")

            if confirm and st.button("🗑️ Delete This Inventory Item"):
                try:
                    # 🔁 Step 2: Manually delete from all related tables using item_id
                    tables_to_clean = [
                        "sales_master_history",
                        "sales_master_log",
                        "goods_bought_history",
                        "goods_bought" ]
 
                    for table in tables_to_clean:
                        supabase.table(table).delete().eq("item_id", item_id).eq("user_id", user_id).execute()

                    # 🔁 Step 3: Delete the item itself from inventory
                    supabase.table("inventory_master_log").delete().eq("item_id", item_id).eq("user_id", user_id).execute()

                    st.success(f"✅ Item '{item_name_to_delete}' and all linked records deleted successfully.")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to delete item and related data.")
        else:
            st.warning("❗ No inventory item found with that name.")





# ✅ That means:

# Allow duplicates for the same item across different days

# ❌ But no duplicates for the same item on the same day

