import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Everglow Gems Portal", layout="wide")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0/edit#gid=0"

# --- DATA LOAD ---
def get_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory")
        ord = conn.read(spreadsheet=SHEET_URL, worksheet="Orders")
        return conn, inv, ord
    except:
        return None, None, None

conn, inv_df, ord_df = get_data()

# --- VALIDATION ---
if inv_df is None:
    st.error("Connection Error. Please check your TOML Secrets.")
    st.stop()

# --- NAVIGATION ---
st.sidebar.title("Everglow Gems")
role = st.sidebar.selectbox("Access Level", ["Partner", "Admin"])

# --- PARTNER PORTAL ---
if role == "Partner":
    st.title("💎 Partner Portal")
    sku = st.text_input("Enter Product Code").strip().upper()
    
    if sku:
        match = inv_df[inv_df['Product Code'].str.upper() == sku]
        if not match.empty:
            idx = match.index[0]
            item = inv_df.iloc[idx]
            
            c1, c2 = st.columns(2)
            with c1:
                if pd.notna(item['Pic_URL']):
                    st.image(item['Pic_URL'], use_container_width=True)
            with c2:
                st.header(item['Product Name'])
                st.write(f"**Stock:** {int(item['Stock'])} pcs")
                
                with st.form("order_form"):
                    qty = st.number_input("Quantity", 1, int(item['Stock']))
                    shop = st.text_input("Partner Name")
                    if st.form_submit_button("Submit Order"):
                        # Process: Update stock and orders
                        inv_df.at[idx, 'Stock'] = int(item['Stock']) - qty
                        new_log = pd.DataFrame([{"Order ID": datetime.now().strftime("%H%M%S"), 
                                               "Product Code": sku, "Qty": qty, 
                                               "Partner": shop, "Status": "Pending"}])
                        
                        conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inv_df)
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=pd.concat([ord_df, new_log]))
                        st.success("Order Placed!")
                        st.rerun()
        else:
            st.error("Product Code not found.")

# --- ADMIN PORTAL ---
else:
    st.title("👑 Admin Panel")
    tab1, tab2 = st.tabs(["Stock Manager", "Order Approvals"])
    
    with tab1:
        updated_inv = st.data_editor(inv_df, num_rows="dynamic")
        if st.button("Save Inventory Changes"):
            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inv)
            st.success("Database Updated!")
            
    with tab2:
        for i, row in ord_df.iterrows():
            if row['Status'] == "Pending":
                cols = st.columns([3, 1])
                cols[0].write(f"Order {row['Order ID']}: {row['Product Code']} (Qty: {row['Qty']})")
                if cols[1].button("Handover to Pathao", key=f"btn_{i}"):
                    ord_df.at[i, 'Status'] = "With Pathao"
                    conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=ord_df)
                    st.rerun()
