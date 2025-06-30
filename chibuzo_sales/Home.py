import streamlit as st
st.set_page_config(
    page_title='SALES MANAGEMENT SYSTEM',
    page_icon='👋 ',

)
#to hide streamlit icons 
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
from datetime import datetime
import json
import time

from PIL import Image, ImageOps
import hashlib
import uuid
from datetime import date, timedelta
import sys
import importlib.util
import requests
import numpy as np
import matplotlib.pyplot as plt

from streamlit_extras.switch_page_button import switch_page
from PIL import Image

import json
import os
from urllib.parse import urlencode
from supabase import create_client


import streamlit as st
image_path = "priscomac_blacktransparent_logo_rockyart.png"
image = Image.open(image_path)  
 # Manually rotate the image 180 degrees to rotate the image
img = ImageOps.exif_transpose(image)
img = img.rotate(270, expand=True) # the image was turned upside down, this is to turn it to the right position
# Resize the image (set new width & height)
resized_image = img.resize((200,100)) # Adjust size as needed
# Display in Streamlit
st.sidebar.image(resized_image,width=150)






# supabase configurations
def get_supabase_client():
    supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client




# dessinging the homepage, this makes the app look like html and css design
# Custom CSS styling
st.markdown("""
    <style>
        /* Customize headers */
        h1, h2, h3 {
            color: #00FFC6;
            font-family: 'Courier New', monospace;
        }

        /* Buttons */
        .stButton>button {
            background-color: #00FFC6;
            color: black;
            border-radius: 10px;
            padding: 8px 20px;
            font-weight: bold;
        }

        /* Hover effect */
        .stButton>button:hover {
            background-color: #0E0E2C;
            color: #00FFC6;
            border: 1px solid #00FFC6;
        }
    </style>
""", unsafe_allow_html=True)














# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database
col1,col2=st.columns([7,2])
# Load the image
with col1:  
    st.title('PriscomSales')
    
with col2:
    image_path = "priscomac_blacktransparent_logo_rockyart.png"
    image = Image.open(image_path)
    
    # Manually rotate the image 180 degrees to rotate the image
    img = ImageOps.exif_transpose(image)
    img = img.rotate(270, expand=True)
# Resize the image (set new width & height)
    resized_image = img.resize((200,100)) # Adjust size as needed
# Display in Streamlit
    st.image(resized_image)


# contact developer
st.sidebar.markdown("---")  # Adds a separator
if st.sidebar.button("📩 Contact Developer"):
    st.sidebar.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/prisca-ukanwa-800a1117a/)")












    



        
    



   


col11,col22=st.columns([7.5,1])
with col11:
    
    st.markdown("""
### Empowering You to Run a Smarter Business  
At **Priscomac**, we provide powerful tools to help you record sales, manage inventory, forecast growth, and generate daily reports — all from one easy-to-use platform.

""")
with col22:  
    if st.button("Login/Signup"):
        switch_page("Dashboard") 


col12,col21=st.columns(2)
with col12:
    sales_img='photo-1666875753105-c63a6f3bdc86.jfif'
    sales_im=Image.open(sales_img)
    img_s=sales_im.resize((500,300))
    st.image(img_s,caption="Smart tools for smart businesses")
with col21:
    st.markdown(
    """<span style="color:green; font-weight:bold;font-size:24px;">
    What is the health of your business?
    </span>""",
    unsafe_allow_html=True
)
st.markdown(" ")

     

# --- Features & Highlights ---
with st.container():
    st.markdown("## 🤝 Let’s Grow Your Business with **Priscomac**")
    st.markdown("### Your all-in-one platform for smarter sales and financial tracking.")

    st.markdown("""
    - 🧾 **Record and manage daily sales**  
    - 📊 **Automatically generate daily sales reports**  
    - 🧾 **Create professional invoices in seconds**  
    - 💸 **Track expenses and control costs**  
    - 📈 **Monitor profits — today and in the future**
    """)

    st.success("📈 Gain full visibility into your business health with Priscomac.")



# Simulated data for demo purposes
st.subheader('Priscomac user  analysis')
total_sales = 500000 # in NGN
num_clients = 32
active_subscriptions = 25
monthly_growth = 10 # %
# KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales (₦)", f"{total_sales:,}")
col2.metric("Clients", num_clients)
col3.metric("Active Subscriptions", active_subscriptions)
col4.metric("Monthly Growth", f"{monthly_growth}%")

# Sales Trends
   

# Generate sample monthly sales data
months = pd.date_range(end=pd.Timestamp.today(), periods=5, freq='ME').strftime('%b %Y')
sales = np.random.randint(700000, 1500000, size=5)

    

# Top Products (sample data)
st.subheader("Top Products")
top_products = pd.DataFrame({
    "Product": ["Data Analytics Suite", "Predictive Model Pro", "Consulting Package", "Training Course"],
    "Sales": [4500000, 3500000, 2500000, 1500000]
})

st.bar_chart(top_products.set_index("Product"))



