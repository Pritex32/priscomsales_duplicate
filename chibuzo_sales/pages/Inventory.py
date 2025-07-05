from http import cookies
import streamlit as st
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


import json
import time
from collections import defaultdict
import io
import plotly.express as px
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from datetime import datetime, timedelta
import jwt



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





# this shows the logged user info
if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    st.warning("Please log in first.")
    st.stop()



# connecting to supabase

from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client
 # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database






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
    
    # 🔍 Check if Pro subscription has expired
    handle_subscription_expiration(user_id)
    block_free_user_if_limit_exceeded()
    show_plan_status()

st.subheader("📦 REAL TIME INVENTORY MANAGEMENT SYSTEM")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # ✅ Clear cached data
    st.rerun() # ✅ Force rerun of the app

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
@st.cache_data(ttl=60 * 5)
def fetch_inventory(user_id):
    return supabase.table("inventory_master_log").select("*").eq("user_id", user_id).execute().data

@st.cache_data(ttl=60 * 5) # to load requisition table
def fetch_requisitions(user_id):
    return supabase.table( "sales_master_log").select("*").eq("sale_date", today).eq("user_id", user_id).execute().data

@st.cache_data(ttl=60 * 5) # this is to load restock table
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


# Then show other dashboard info below...

# === Load data ===
with st.spinner("Fetching data..."): # this is to show data is loading and not to show error until data loads
    inventory = fetch_inventory(user_id)
    requisitions = fetch_requisitions(user_id)
    restocks = fetch_restocks(user_id)


df_inventory = pd.DataFrame(inventory)

# === Display Inventory ===
if selected == 'Home':
    st.subheader("📋 Current Inventory")
    df_inventory = pd.DataFrame(inventory)
    st.dataframe(df_inventory)
    selected_date = st.date_input("Select Date to Update Inventory", value=date.today())






# === Function to Move Today's Requisitions to Requisition History ===

def move_requisitions_to_history(selected_date, user_id):
    # Fetch today's requisitions
    requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", str(selected_date)).execute().data
    
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
    restocks_today = supabase.table("goods_bought").select("*").eq("purchase_date", str(selected_date)).execute().data
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
        st.info("ℹ️ No restocks found for today.")
            


## function to update and move the requisition and restock
def update_inventory_balances(selected_date,user_id):
    # Fetch today's requisitions and restocks
    requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", str(selected_date)).execute().data
    restocks_today = supabase.table("goods_bought").select("*").eq("user_id", user_id).eq("purchase_date", str(selected_date)).execute().data

   

    # If both are empty, show a warning and stop
    if not requisitions_today and not restocks_today:
        st.warning("⚠️ No sales or purchases to update today.")
        return

    # Process restocks
    restock_dict = defaultdict(int)
    for entry in restocks_today:
        restock_dict[entry["item_id"]] += entry.get("supplied_quantity", 0)
   

    # Process requisitions
    requisition_dict = defaultdict(int)
    return_dict = defaultdict(int)
    for entry in requisitions_today:
        requisition_dict[entry["item_id"]] += entry.get("quantity", 0)
        return_dict[entry["item_id"]] += entry.get("return_quantity", 0)

    # Fetch existing inventory
    inventory_response = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).execute().data
    inventory = pd.DataFrame(inventory_response)

    # Track updated items
    updated_count = 0
    failed_items = []


    for item in inventory.itertuples():
        item_id = item.item_id
        item_name = item.item_name
        prev_closing = 0 if pd.isna(item.closing_balance) else item.closing_balance

        supplied_quantity = restock_dict.get(item_id, 0)

        stock_out = requisition_dict.get(item_id, 0)
        return_quantity = return_dict.get(item_id, 0)

        # Ensure integers
        try:
            stock_out = int(stock_out or 0)
            supplied_quantity = int(supplied_quantity  or 0)
            
            return_quantity = int(return_quantity or 0)
            open_balance = int(prev_closing or 0)
            total_available = open_balance + supplied_quantity + return_quantity
            #this is to stop items that is stock out
            if total_available <= 0:
                st.warning(f"🚫 You are out of stock for '{item_name}'. No stock-out will be recorded.")
                continue  # Skip updating this item
            closing_balance = total_available - stock_out
            closing_balance = int(closing_balance)

## this code is to make sure what is updated doesnt disappear
            existing_log = next((entry for entry in inventory_response 
            if entry["item_id"] == item_id and entry["log_date"] == selected_date.isoformat()),
            None)

             # Merge with existing values if any
            if existing_log:
                supplied_quantity += int(existing_log.get("supplied_quantity", 0))
                stock_out += int(existing_log.get("stock_out", 0))
                return_quantity += int(existing_log.get("return_quantity", 0))
                open_balance = int(existing_log.get("open_balance", open_balance))
            else:
                open_balance = int(prev_closing or 0)

            daily_log = {
                "item_id": item_id,
                "user_id": user_id,
                "item_name": item_name,
                "open_balance": open_balance,
                "supplied_quantity": supplied_quantity,
                "stock_out": stock_out,
                "return_quantity": return_quantity,
              
                "log_date":selected_date.isoformat(),
                "last_updated": selected_date.isoformat()
            }

            response = supabase.table("inventory_master_log").upsert(daily_log, on_conflict=["item_id", "log_date","user_id"]).execute()


            if response.data:
                updated_count += 1
            else:
                failed_items.append(item_name)

        except Exception as e:
            failed_items.append(f"{item_name} (Error: {e})")

    # Display results once
    if updated_count:
        st.success(f"✅ Inventory log updated for {updated_count} items.")
    if failed_items:
        st.error(f"❌ Failed to update: {', '.join(failed_items)}")

    st.cache_data.clear()

# Trigger Inventory Update and Move to History
if selected == 'Home':
    low_stock_items = get_low_stock_items(user_id)
    if low_stock_items:
        st.warning("⚠️ The following items are low in stock:")
        for item in low_stock_items:
            st.write(f"🔻 {item['item_name']}: {item['closing_balance']} units left (reorder level: {item['reorder_level']})")
    else:
        st.success("✅ All items are sufficiently stocked.")

    if st.button("🔄 Update Inventory Balances"):
        update_inventory_balances(selected_date, user_id)
        move_requisitions_to_history(selected_date,user_id)  # Move today's requisitions after updating the inventory
        move_restocks_to_history(selected_date,user_id)  # Move today's restocks to history

# Display Today's Logs
    with st.expander("📤 Today's Sale "):
        requisitions_today = supabase.table("sales_master_log").select("*").eq("user_id", user_id).eq("sale_date", str(selected_date)).execute().data
        st.dataframe(pd.DataFrame(requisitions_today))

    with st.expander("📥 Today's Restocks"):
        restocks_today = supabase.table("goods_bought").select("*").eq("user_id", user_id).eq("purchase_date", str(selected_date)).execute().data
        st.dataframe(pd.DataFrame(restocks_today))

# Display Daily Inventory Log by Date
    st.subheader("📆 Daily Inventory Log History")
    selected_log_date = st.date_input("Select a date", value=date.today())
    daily_history = supabase.table("inventory_master_log").select("*").eq("user_id", user_id).eq("log_date", str(selected_log_date)).execute().data


    if daily_history:
        st.dataframe(pd.DataFrame(daily_history))
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
        st.error(f"❌ Error fetching summary report: {e}")
        return pd.DataFrame()

# 🔹 Streamlit UI

if selected == 'Reports':
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
                    st.error(f"❌ Failed to delete item and related data: {e}")
            else:
                st.warning("❗ No inventory item found with that name.")





