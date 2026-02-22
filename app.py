import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Everglow Gems | Inventory", layout="wide")

# --- DATABASE ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0/edit#gid=0"

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory")
        ord = conn.read(spreadsheet=SHEET_URL, worksheet="Orders")
        return conn, inv, ord
    except Exception:
        return None, None, None

conn, inventory_df, orders_df = load_data()

# --- SIDEBAR ---
st.sidebar.title("Everglow Gems")
role = st.sidebar.radio("Access Level", ["Partner", "Admin"])

# --- ERROR CHECK ---
if inventory_df is None:
    st.error("Database Connection Failed. Check Secrets.")
    st.stop()

# --- PARTNER PORTAL ---
if role == "Partner":
    st.title("💎 Partner Portal")
    search_code = st.text_input("Enter Product Code").strip().upper()
    
    if search_code:
        match = inventory_df[inventory_df['Product Code'].str.upper() == search_code]
        if not match.empty:
            idx = match.index[0]
            item = inventory_df.iloc[idx]
            
            c1, c2 = st.columns(2)
            with c1:
                if pd.notna(item['Pic_URL']):
                    st.image(item['Pic_URL'], use_container_width=True)
            with c2:
                st.header(item['Product Name'])
                st.metric("Stock Available", f"{int(item['Stock'])} pcs")
                
                with st.form("order_form"):
                    qty = st.number_input("Quantity", min_value=1, max_value=int(item['Stock']))
                    shop = st.text_input("Shop Name")
                    if st.form_submit_button("Place Order"):
                        # Update Inventory
                        inventory_df.at[idx, 'Stock'] = int(item['Stock']) - qty
                        # Log Order
                        new_order = pd.DataFrame([{
                            "Order ID": datetime.now().strftime("%H%M%S"),
                            "Product Code": search_code,
                            "Qty": qty,
                            "Partner": shop,
                            "Status": "Pending",
                            "Date": datetime.now().strftime("%Y-%m-%d")
                        }])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=pd.concat([orders_df, new_order]))
                        st.success("Order Sent!")
                        st.rerun()
        else:
            st.error("Code not found.")

# --- ADMIN PORTAL ---
else:
    st.title("👑 Admin Panel")
    t1, t2 = st.tabs(["Inventory", "Orders"])
    
    with t1:
        edited = st.data_editor(inventory_df, num_rows="dynamic")
        if st.button("Save Stock Updates"):
            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited)
            st.success("Saved!")
            
    with t2:
        for i, r in orders_df.iterrows():
            if r['Status'] == "Pending":
                cols = st.columns([3, 1])
                cols[0].write(f"Order {r['Order ID']}: {r['Product Code']} (Qty: {r['Qty']})")
                if cols[1].button("Handover to Pathao", key=f"btn_{i}"):
                    orders_df.at[i, 'Status'] = "With Pathao"
                    conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                    st.rerun()                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    if pd.notna(product['Pic_URL']):
                        st.image(product['Pic_URL'], use_container_width=True)
                
                with col2:
                    st.header(product['Product Name'])
                    st.subheader(f"Available Stock: {int(product['Stock'])} pcs")
                    st.write(f"**Wholesale:** {product['Paikari Price']} BDT")
                    
                    with st.form("place_order"):
                        order_qty = st.number_input("Order Quantity", min_value=1, max_value=int(product['Stock']))
                        p_name = st.text_input("Partner/Shop Name")
                        if st.form_submit_button("Submit Order"):
                            # Update Stock
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - order_qty
                            
                            # Log Order
                            new_order = pd.DataFrame([{
                                "Order ID": f"ORD-{datetime.now().strftime('%m%d%H%M')}",
                                "Product Code": search_code,
                                "Qty": order_qty,
                                "Partner": p_name,
                                "Status": "Pending",
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }])
                            updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                            
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                            st.success("Order Placed Successfully!")
                            st.rerun()
            else:
                st.error("Product not found.")

    # --- ADMIN PORTAL ---
    elif role == "Admin":
        st.title("👑 Admin Control Panel")
        tab1, tab2, tab3 = st.tabs(["Inventory", "Orders", "Add New"])
        
        with tab1:
            edited_inv = st.data_editor(inventory_df, num_rows="dynamic")
            if st.button("Update Inventory"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
                st.success("Google Sheet Updated!")

        with tab2:
            st.subheader("Manage Orders")
            for i, row in orders_df.iterrows():
                if row['Status'] != "Completed":
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"{row['Order ID']} | {row['Product Code']} | Qty: {row['Qty']}")
                    if c2.button("Pathao Handover", key=f"order_{i}"):
                        orders_df.at[i, 'Status'] = "With Pathao"
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.rerun()

        with tab3:
            with st.form("add_item"):
                c_code = st.text_input("Product Code")
                c_name = st.text_input("Name")
                c_stock = st.number_input("Initial Stock", min_value=1)
                c_pic = st.text_input("Image URL")
                if st.form_submit_button("Save Item"):
                    new_row = pd.DataFrame([{"Product Code": c_code, "Product Name": c_name, "Stock": c_stock, "Pic_URL": c_pic}])
                    updated_inv = pd.concat([inventory_df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inv)
                    st.success("New Item Added!")

else:
    st.warning("Please check your database connection or Secrets configuration.")                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    if pd.notna(product['Pic_URL']):
                        st.image(product['Pic_URL'], use_container_width=True)
                
                with col2:
                    st.header(product['Product Name'])
                    st.subheader(f"Available Stock: {int(product['Stock'])} pcs")
                    st.write(f"**Wholesale (Paikari):** {product['Paikari Price']} BDT")
                    
                    with st.form("place_order"):
                        order_qty = st.number_input("Order Quantity", min_value=1, max_value=int(product['Stock']))
                        partner_name = st.text_input("Your Name / Shop Name")
                        if st.form_submit_button("Submit Order"):
                            # Logic: Deduct Stock
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - order_qty
                            
                            # Logic: Add Order
                            new_order = pd.DataFrame([{
                                "Order ID": f"ORD-{datetime.now().strftime('%m%d%H%M')}",
                                "Product Code": search_code,
                                "Qty": order_qty,
                                "Status": "Pending Approval",
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }])
                            updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                            
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                            st.success("Order Placed!")
                            st.rerun()
            else:
                st.error("Product not found.")

    # --- ADMIN PORTAL ---
    elif role == "Admin":
        st.title("👑 Admin Control Panel")
        tab1, tab2, tab3 = st.tabs(["Stock Management", "Order Approvals", "Add Items"])
        
        with tab1:
            edited_inv = st.data_editor(inventory_df, num_rows="dynamic")
            if st.button("Save Changes"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
                st.success("Updated!")

        with tab2:
            st.subheader("Orders")
            for i, row in orders_df.iterrows():
                if row['Status'] == "Pending Approval":
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"{row['Order ID']} - {row['Product Code']} (Qty: {row['Qty']})")
                    if c2.button("Handover to Pathao", key=f"p_{i}"):
                        orders_df.at[i, 'Status'] = "With Pathao"
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.rerun()

        with tab3:
            with st.form("add_new"):
                code = st.text_input("Product Code")
                name = st.text_input("Name")
                stock = st.number_input("Stock", min_value=1)
                pic = st.text_input("Pic URL")
                if st.form_submit_button("Add Product"):
                    # Brand Check: Ensure Pic URL follows consistency [2026-02-09]
                    new_row = pd.DataFrame([{"Product Code": code, "Product Name": name, "Stock": stock, "Pic_URL": pic}])
                    updated_inv = pd.concat([inventory_df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inv)
                    st.success("Added!")
else:
    st.warning("Please check your database connection or Secrets configuration.")        search_code = st.text_input("Enter Product Code").strip().upper()

        if search_code:
            # Find product in inventory
            item_match = inventory_df[inventory_df['Product Code'].str.upper() == search_code]
            
            if not item_match.empty:
                idx = item_match.index[0]
                product = inventory_df.iloc[idx]
                
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    # Brand consistency: Displays the high-end model face [cite: 2026-02-09]
                    if pd.notna(product['Pic_URL']):
                        st.image(product['Pic_URL'], use_container_width=True)
                
                with col2:
                    st.header(product['Product Name'])
                    st.subheader(f"Available Stock: {int(product['Stock'])} pcs")
                    st.write(f"**Wholesale (Paikari):** {product['Paikari Price']} BDT")
                    st.write(f"**Retail (Sell):** {product['Sell Price']} BDT")
                    
                    st.divider()
                    
                    # ORDER FORM
                    with st.form("place_order"):
                        order_qty = st.number_input("Order Quantity", min_value=1, max_value=int(product['Stock']))
                        partner_name = st.text_input("Your Name / Shop Name")
                        submit_order = st.form_submit_button("Submit Order Request")
                        
                        if submit_order:
                            # 1. Update Inventory Dataframe
                            inventory_df.at[idx, 'Stock'] = int(product['Stock']) - order_qty
                            
                            # 2. Create Order Record
                            new_order = pd.DataFrame([{
                                "Order ID": f"ORD-{datetime.now().strftime('%m%d%H%M')}",
                                "Product Code": search_code,
                                "Qty": order_qty,
                                "Partner Name": partner_name,
                                "Status": "Pending Approval",
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }])
                            
                            updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                            
                            # 3. Write back to Google Sheets
                            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory_df)
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                            
                            st.success(f"Order for {order_qty} units placed! Stock has been updated.")
                            st.rerun()
            else:
                st.error("Product code not found.")

    # --- ADMIN PORTAL ---
    elif role == "Admin":
        st.title("👑 Admin Control Panel")
        
        tab1, tab2, tab3 = st.tabs(["Stock Management", "Order Approvals", "Add New Items"])
        
        with tab1:
            st.subheader("Current Inventory Status")
            # Editable table for quick stock fixes
            edited_inv = st.data_editor(inventory_df, key="inv_editor", num_rows="dynamic")
            if st.button("Save Inventory Changes"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
                st.success("Changes saved to Google Sheets!")

        with tab2:
            st.subheader("Pending Orders & Pathao Handover")
            if not orders_df.empty:
                for i, row in orders_df.iterrows():
                    # Only show active/pending orders
                    if row['Status'] != "Completed":
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{row['Order ID']}** - {row['Product Code']} (Qty: {row['Qty']})")
                        c2.info(f"Status: {row['Status']}")
                        
                        if row['Status'] == "Pending Approval":
                            if c3.button("Handover to Pathao", key=f"apprv_{i}"):
                                orders_df.at[i, 'Status'] = "With Pathao"
                                conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                                st.rerun()
            else:
                st.write("No orders found.")

        with tab3:
            st.subheader("Register New Jewelry Item")
            with st.form("new_product"):
                n_code = st.text_input("New Product Code")
                n_name = st.text_input("Name")
                n_stock = st.number_input("Initial Stock", min_value=1)
                n_pkr = st.number_input("Paikari Price")
                n_sel = st.number_input("Sell Price")
                n_pic = st.text_input("Direct Image Link (URL)")
                
                if st.form_submit_button("Create Product"):
                    new_row = pd.DataFrame([{"Product Code": n_code, "Product Name": n_name, "Stock": n_stock, "Paikari Price": n_pkr, "Sell Price": n_sel, "Pic_URL": n_pic}])
                    updated_inv = pd.concat([inventory_df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inv)
                    st.success("Product successfully added to the database!")

else:
    st.warning("Please check your database connection or Secrets configuration.")            col1, col2 = st.columns(2)
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
