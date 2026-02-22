import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# --- DATABASE CONFIG ---
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Using ttl=0 ensures you always see the latest data from the sheet
        inventory = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
        orders = conn.read(spreadsheet=SHEET_URL, worksheet="Orders", ttl=0)
        return conn, inventory, orders
    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return None, None, None

conn, inventory_df, orders_df = load_data()

# --- MAIN LOGIC ---
if inventory_df is not None and orders_df is not None:
    st.sidebar.title("Everglow Gems")
    role = st.sidebar.radio("Navigation", ["Partner Portal", "Admin Dashboard"])

    # --- PARTNER PORTAL ---
    if role == "Partner Portal":
        st.title("💎 Partner Ordering Portal")
        search_code = st.text_input("Enter Product Code (e.g., EG-R001)").strip().upper()
        
        if search_code:
            item_match = inventory_df[inventory_df['Product Code'].astype(str).str.upper() == search_code]
            
            if not item_match.empty:
                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if pd.notna(product['Pic_URL']):
                        st.image(product['Pic_URL'], use_container_width=True)
                with col2:
                    st.header(product['Product Name'])
                    st.write(f"**Category:** {product['Category']}")
                    st.write(f"**Price:** {product['Paikari Price']} BDT")
                    st.write(f"**Stock Available:** {int(product['Stock'])} pcs")
                    
                    with st.form("order_form", clear_on_submit=True):
                        # Matching your sheet columns: "Requested Quantity" and "Partner Name"
                        qty = st.number_input("Requested Quantity", 1, int(product['Stock']))
                        p_name = st.text_input("Partner Name")
                        
                        if st.form_submit_button("Place Order"):
                            # 1. Update Inventory locally
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - qty
                            
                            # 2. Log new order using your EXACT column names
                            new_row = pd.DataFrame([{
                                "Order ID": f"ORD-{datetime.now().strftime('%H%M%S')}", 
                                "Product Code": search_code, 
                                "Requested Quantity": qty, 
                                "Partner Name": p_name, 
                                "Status": "Pending",
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }])
                            
                            # 3. Update Google Sheets
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=pd.concat([orders_df, new_row], ignore_index=True))
                            
                            st.success("Order Placed Successfully!")
                            st.rerun()
            else:
                st.error("Product Code not found.")

    # --- ADMIN DASHBOARD ---
    else:
        st.title("👑 Admin Control Panel")
        tab1, tab2 = st.tabs(["Stock Manager", "Orders & Pathao"])
        
        with tab1:
            st.write("Edit Stock and Prices below:")
            edited = st.data_editor(inventory_df, num_rows="dynamic")
            if st.button("Save All Changes"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited)
                st.success("Inventory Updated!")
        
        with tab2:
            st.write("Current Orders")
            for i, row in orders_df.iterrows():
                # Checking your "Status" column
                if row['Status'] == "Pending":
                    c = st.columns([3, 1])
                    c[0].info(f"Order {row['Order ID']}: {row['Partner Name']} requested {row['Requested Quantity']}x {row['Product Code']}")
                    if c[1].button("Handover to Pathao", key=f"btn_{i}"):
                        orders_df.at[i, 'Status'] = "With Pathao"
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.success(f"Order {row['Order ID']} status updated!")
                        st.rerun()
                else:
                    st.write(f"Order {row['Order ID']} is {row['Status']}")
else:
    st.warning("Please ensure your Google Sheet tabs are named 'Inventory' and 'Orders' and contain data.")
