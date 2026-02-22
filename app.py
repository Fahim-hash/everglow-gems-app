import streamlit as st
from medical_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Everglow Gems Dashboard", layout="wide")

# 1. Connection to Google Sheets
url = "https://docs.google.com/spreadsheets/d/1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, worksheet="Inventory")

# 2. User Authentication (Simple)
role = st.sidebar.radio("Login as:", ["Partner", "Admin"])

if role == "Partner":
    st.title("💎 Everglow Gems: Partner Portal")
    search_code = st.text_input("Search Product Code (e.g., EG-R001)")

    if search_code:
        # Match case-insensitive
        item = df[df['Product Code'].str.upper() == search_code.upper()]
        
        if not item.empty:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(item['Pic_URL'].values[0], caption=item['Product Name'].values[0])
            with c2:
                st.subheader(f"Code: {item['Product Code'].values[0]}")
                st.write(f"**Current Stock:** {item['Stock'].values[0]} pcs")
                st.metric("Wholesale Price", f"{item['Paikari Price'].values[0]} BDT")
                st.metric("Retail Price", f"{item['Sell Price'].values[0]} BDT")
                
                # Order Form
                with st.expander("Place Order Request"):
                    order_qty = st.number_input("Quantity", min_value=1)
                    if st.button("Submit Order"):
                        st.success("Order request sent to Admin!")
        else:
            st.error("Product code not found.")

elif role == "Admin":
    st.title("👑 Admin Control Panel")
    st.write("Current Inventory Overview")
    st.dataframe(df)

    with st.expander("Add New Jewelry Item"):
        with st.form("new_item"):
            new_code = st.text_input("Product Code")
            new_name = st.text_input("Name")
            new_stock = st.number_input("Initial Stock", min_value=0)
            new_paikari = st.number_input("Paikari Price")
            new_sell = st.number_input("Sell Price")
            new_pic = st.text_input("Image Link (URL)")
            
            if st.form_submit_button("Add to Database"):
                st.info("In a full setup, this would write back to Google Sheets.")
