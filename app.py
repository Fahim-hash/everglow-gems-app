import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Everglow Gems Portal", layout="wide")

# --- DATABASE CONNECTION ---
# Replace with your actual Sheet URL
URL = "https://docs.google.com/spreadsheets/d/1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    inventory = conn.read(spreadsheet=URL, worksheet="Inventory")
    orders = conn.read(spreadsheet=URL, worksheet="Orders")
    return inventory, orders

inventory_df, orders_df = get_data()

# --- SIDEBAR ---
st.sidebar.title("Everglow Gems")
role = st.sidebar.radio("Access Level", ["Partner", "Admin"])

# --- PARTNER FLOW ---
if role == "Partner":
    st.title("💎 Partner Ordering System")
    search_code = st.text_input("Search Product Code").strip().upper()

    if search_code:
        # Match product
        item_index = inventory_df.index[inventory_df['Product Code'].str.upper() == search_code].tolist()
        
        if item_index:
            idx = item_index[0]
            product = inventory_df.iloc[idx]
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(product['Pic_URL'], use_container_width=True)
            with col2:
                st.header(product['Product Name'])
                st.subheader(f"Available Stock: {product['Stock']}")
                st.write(f"**Paikari:** {product['Paikari Price']} | **Sell:** {product['Sell Price']}")
                
                # Ordering Logic
                with st.form("order_form"):
                    qty = st.number_input("Order Quantity", min_value=1, max_value=int(product['Stock']))
                    submit = st.form_submit_button("Place Order Request")
                    
                    if submit:
                        # 1. Logic: Reduce Stock
                        inventory_df.at[idx, 'Stock'] = product['Stock'] - qty
                        
                        # 2. Logic: Create Order Record
                        new_order = pd.DataFrame([{
                            "Order ID": f"ORD-{datetime.now().strftime('%d%H%M%S')}",
                            "Product Code": search_code,
                            "Qty": qty,
                            "Status": "Pending Approval",
                            "Date": datetime.now().strftime("%Y-%m-%d")
                        }])
                        updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                        
                        # 3. Write back to Google Sheets
                        conn.update(spreadsheet=URL, worksheet="Inventory", data=inventory_df)
                        conn.update(spreadsheet=URL, worksheet="Orders", data=updated_orders)
                        st.success("Order Placed! Stock updated.")
                        st.rerun()
        else:
            st.error("Product not found.")

# --- ADMIN FLOW ---
elif role == "Admin":
    tab1, tab2, tab3 = st.tabs(["Inventory Mgmt", "Orders & Pathao", "Add New Product"])
    
    with tab1:
        st.subheader("Manage Current Stock")
        edited_df = st.data_editor(inventory_df)
        if st.button("Save Inventory Changes"):
            conn.update(spreadsheet=URL, worksheet="Inventory", data=edited_df)
            st.success("Inventory Updated!")

    with tab2:
        st.subheader("Order Requests & Delivery")
        # Logic: Update status to "Handover to Pathao"
        for i, row in orders_df.iterrows():
            col_a, col_b, col_c = st.columns([2,1,1])
            col_a.write(f"{row['Order ID']} | {row['Product Code']} (Qty: {row['Qty']})")
            col_b.write(f"Status: {row['Status']}")
            if row['Status'] == "Pending Approval":
                if col_c.button("Handover to Pathao", key=f"btn_{i}"):
                    orders_df.at[i, 'Status'] = "With Pathao"
                    conn.update(spreadsheet=URL, worksheet="Orders", data=orders_df)
                    st.rerun()

    with tab3:
        with st.form("add_product"):
            st.write("Add New Item to Catalog")
            new_code = st.text_input("New Code")
            new_name = st.text_input("Product Name")
            new_stock = st.number_input("Starting Stock", min_value=0)
            new_paikari = st.number_input("Paikari Price")
            new_sell = st.number_input("Sell Price")
            new_pic = st.text_input("Pic URL (Ensuring Facial Consistency)")
            
            if st.form_submit_button("Add Product"):
                new_row = pd.DataFrame([{"Product Code": new_code, "Product Name": new_name, "Stock": new_stock, "Paikari Price": new_paikari, "Sell Price": new_sell, "Pic_URL": new_pic}])
                updated_inv = pd.concat([inventory_df, new_row], ignore_index=True)
                conn.update(spreadsheet=URL, worksheet="Inventory", data=updated_inv)
                st.success("New product added to Everglow Gems!")
