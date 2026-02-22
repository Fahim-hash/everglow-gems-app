import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# ================= GOOGLE SHEET CONFIG =================
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    conn = get_connection()
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=0)

# ================= LOAD DATA =================
try:
    inventory_df = load_data("Inventory")
    orders_df = load_data("Orders")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# ================= SIDEBAR =================
st.sidebar.title("Everglow Gems")
role = st.sidebar.radio("Navigation", ["Partner Portal", "Admin Dashboard"])

# ==========================================================
# ===================== PARTNER PORTAL =====================
# ==========================================================
if role == "Partner Portal":
    st.title("💎 Customer Order Entry Form")
    st.info("Partner-ra tader customer-er order info ekhane fill-up korbe.")

    with st.form("customer_order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Customer Details")
            c_name = st.text_input("Customer Name")
            c_phone = st.text_input("Customer Phone Number")
            c_address = st.text_area("Full Delivery Address")
        
        with col2:
            st.subheader("📦 Product Details")
            product_list = inventory_df["Product Code"].astype(str).tolist()
            selected_sku = st.selectbox("Select Product", product_list)
            
            # Auto-fetch price for calculation
            item_data = inventory_df[inventory_df["Product Code"] == selected_sku].iloc[0]
            qty = st.number_input("Quantity", min_value=1, step=1)
            
            # Partner can add their own selling price or extra charges
            total_price = st.number_input("Total Bill Amount (Including Delivery)", min_value=0)
            partner_ref = st.text_input("Partner/Shop Name (Reference)")

        submit_order = st.form_submit_button("Send Order to Admin")

        if submit_order:
            if not c_name or not c_phone or not c_address or not partner_ref:
                st.error("Please fill all the fields!")
            else:
                # Generate Order ID
                order_id = f"CUST-{datetime.now().strftime('%m%d%H%M%S')}"
                
                # Create new entry
                new_entry = pd.DataFrame([{
                    "Order ID": order_id,
                    "Product Code": selected_sku,
                    "Requested Quantity": qty,
                    "Partner Name": partner_ref,
                    "Customer Name": c_name,
                    "Customer Phone": c_phone,
                    "Address": c_address,
                    "Total Price": total_price,
                    "Status": "Pending",
                    "Date": datetime.now().strftime("%Y-%m-%d")
                }])

                # Update Orders Sheet
                conn = get_connection()
                updated_orders = pd.concat([orders_df, new_entry], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                
                st.success(f"Order {order_id} sent to Admin successfully!")
                st.balloons()

# ==========================================================
# ===================== ADMIN DASHBOARD ====================
# ==========================================================
else:
    st.title("👑 Admin Control Panel")
    tab1, tab2 = st.tabs(["Inventory", "Customer Orders"])

    with tab1:
        st.data_editor(inventory_df, use_container_width=True)

    with tab2:
        st.subheader("Orders to Deliver")
        # Displaying customer details for Pathao entry
        for i, row in orders_df.iterrows():
            if row["Status"] == "Pending":
                with st.expander(f"Order: {row['Order ID']} - {row['Customer Name']}"):
                    st.write(f"**Phone:** {row['Customer Phone']}")
                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**Product:** {row['Product Code']} (Qty: {row['Requested Quantity']})")
                    st.write(f"**Total Bill:** {row['Total Price']} BDT")
                    st.write(f"**Partner:** {row['Partner Name']}")
                    
                    if st.button("Handover to Pathao", key=f"pathao_{i}"):
                        orders_df.at[i, "Status"] = "With Pathao"
                        get_connection().update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.rerun()
