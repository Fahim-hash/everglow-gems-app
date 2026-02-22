import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# --- DATABASE CONFIG ---
# ID use kora beshi safe manual link er cheye
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Worksheet name gulo oboshoy Google Sheet er tab name er moto hote hobe
        inventory = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory")
        orders = conn.read(spreadsheet=SHEET_URL, worksheet="Orders")
        return conn, inventory, orders
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None, None, None

conn, inventory_df, orders_df = load_data()

# --- STYLING (Fixed Typo Here) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True) # Change: allow_html, not allow_value

# --- MAIN APP LOGIC ---
if inventory_df is not None:
    st.sidebar.title("Everglow Gems")
    role = st.sidebar.radio("Navigation", ["Partner Portal", "Admin Dashboard"])

    # --- PARTNER PORTAL ---
    if role == "Partner Portal":
        st.title("💎 Partner Ordering Portal")
        search_code = st.text_input("Enter Product Code").strip().upper()
        
        if search_code:
            item_match = inventory_df[inventory_df['Product Code'].astype(str).str.upper() == search_code]
            
            if not item_match.empty:
                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if pd.notna(product['Pic_URL']):
                        # Strict identity guidelines apply to all images displayed [cite: 2026-02-09]
                        st.image(product['Pic_URL'], use_container_width=True)
                with col2:
                    st.header(product['Product Name'])
                    st.subheader(f"Available: {int(product['Stock'])} pcs")
                    
                    with st.form("order_form"):
                        qty = st.number_input("Quantity", 1, int(product['Stock']))
                        p_name = st.text_input("Shop/Partner Name")
                        if st.form_submit_button("Place Order"):
                            # Update local data
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - qty
                            new_row = pd.DataFrame([{"Order ID": datetime.now().strftime("%H%M%S"), "Product Code": search_code, "Qty": qty, "Partner": p_name, "Status": "Pending"}])
                            
                            # Update Sheets
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=pd.concat([orders_df, new_row]))
                            st.success("Order Placed Successfully!")
                            st.rerun()
            else:
                st.error("Code not found.")

    # --- ADMIN DASHBOARD ---
    else:
        st.title("👑 Admin Control Panel")
        tab1, tab2 = st.tabs(["Stock Manager", "Orders"])
        
        with tab1:
            edited = st.data_editor(inventory_df, num_rows="dynamic")
            if st.button("Save Changes"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited)
                st.success("Sheet Updated!")
        
        with tab2:
            st.write("Manage Pending Orders")
            for i, row in orders_df.iterrows():
                if row['Status'] == "Pending":
                    c = st.columns([3, 1])
                    c[0].write(f"{row['Partner']} ordered {row['Qty']}x {row['Product Code']}")
                    if c[1].button("Handover to Pathao", key=f"btn_{i}"):
                        orders_df.at[i, 'Status'] = "With Pathao"
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.rerun()
else:
    st.info("Waiting for database connection...")
