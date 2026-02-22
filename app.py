import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# --- DATABASE CONFIG ---
# Tomar Sheet ID ta ekhane thakbe
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Tab names must be exact: "Inventory" and "Orders"
        inventory = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory")
        orders = conn.read(spreadsheet=SHEET_URL, worksheet="Orders")
        return conn, inventory, orders
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None, None, None

conn, inventory_df, orders_df = load_data()

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_value=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://via.placeholder.com/150?text=Everglow+Gems", width=150) # Replace with your logo
st.sidebar.title("Navigation")
role = st.sidebar.radio("Switch View", ["Partner Portal", "Admin Dashboard"])

if inventory_df is not None:
    # ---------------------------
    # FACILITY 1: PARTNER PORTAL
    # ---------------------------
    if role == "Partner Portal":
        st.title("💎 Everglow Gems Partner Portal")
        st.info("Enter a Product Code to view details and place orders.")
        
        search_code = st.text_input("Product Code (e.g., EG-101)").strip().upper()
        
        if search_code:
            # Match code in Inventory
            item_match = inventory_df[inventory_df['Product Code'].astype(str).str.upper() == search_code]
            
            if not item_match.empty:
                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1.2])
                
                with col1:
                    if pd.notna(product['Pic_URL']):
                        # Maintaining facial consistency as per 2026-02-09 instructions
                        st.image(product['Pic_URL'], caption=product['Product Name'], use_container_width=True)
                    else:
                        st.warning("No image available.")
                
                with col2:
                    st.header(product['Product Name'])
                    st.metric("In Stock", f"{int(product['Stock'])} units")
                    st.write(f"**Wholesale Price:** {product.get('Paikari Price', 'N/A')} BDT")
                    
                    with st.form("order_form", clear_on_submit=True):
                        order_qty = st.number_input("Order Quantity", min_value=1, max_value=int(product['Stock']), step=1)
                        partner_name = st.text_input("Your Shop/Name")
                        
                        if st.form_submit_button("Confirm Order"):
                            # Update Stock locally
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - order_qty
                            
                            # Create Order entry
                            new_order = pd.DataFrame([{
                                "Order ID": f"EG-{datetime.now().strftime('%d%H%M%S')}",
                                "Product Code": search_code,
                                "Qty": order_qty,
                                "Partner": partner_name,
                                "Status": "Pending",
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }])
                            
                            updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                            
                            # Update Google Sheets
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                            
                            st.success(f"Order for {order_qty} units placed successfully!")
                            st.balloons()
                            st.rerun()
            else:
                st.error("Invalid Product Code. Please check the code and try again.")

    # ---------------------------
    # FACILITY 2: ADMIN DASHBOARD
    # ---------------------------
    else:
        st.title("👑 Admin Control Panel")
        tab1, tab2, tab3 = st.tabs(["Stock Management", "Order Approvals", "Analytics"])
        
        with tab1:
            st.subheader("Live Inventory Editor")
            # FACILITY 3: DATA EDITOR (Edit stock/prices directly)
            edited_inv = st.data_editor(inventory_df, num_rows="dynamic", key="inv_editor")
            if st.button("Save Inventory Changes"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
                st.success("Google Sheets updated!")

        with tab2:
            st.subheader("Pending Orders")
            # FACILITY 4: AUTOMATIC PATHAO STATUS UPDATER
            pending_orders = orders_df[orders_df['Status'] == "Pending"]
            
            if not pending_orders.empty:
                for i, row in pending_orders.iterrows():
                    with st.expander(f"Order {row['Order ID']} - {row['Partner']}"):
                        st.write(f"Item: {row['Product Code']} | Qty: {row['Qty']}")
                        if st.button(f"Handover to Pathao", key=f"pathao_{i}"):
                            orders_df.at[i, 'Status'] = "With Pathao"
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                            st.toast(f"Status updated for {row['Order ID']}")
                            st.rerun()
            else:
                st.write("No pending orders to show.")

        with tab3:
            st.subheader("Business Overview")
            st.write(f"Total Products: {len(inventory_df)}")
            st.write(f"Total Orders: {len(orders_df)}")
            # Quick Chart
            st.bar_chart(inventory_df.set_index('Product Code')['Stock'])

else:
    st.warning("Database not connected. Check your TOML Secrets and Sheet permissions.")
