import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# ================= CUSTOM CSS =================
st.markdown("""
    <style>
    .login-header { font-size: 40px; font-weight: bold; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #FF4B4B; color: white; width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# ================= GOOGLE SHEET CONFIG =================
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# TTL set kora hoyeche jate API Quota error na dey
def load_data(worksheet_name):
    conn = get_connection()
    # ttl=300 mane 5 minute por por data fetch korbe (Quota protection)
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=300)

# ================= IMAGE PROCESSING =================
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img.thumbnail((400, 400)) 
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

# ================= LOGIN SYSTEM =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

if not st.session_state.logged_in:
    e1, login_col, e2 = st.columns([1, 2, 1])
    with login_col:
        st.markdown('<p class="login-header">🔐 Everglow Gems Portal</p>', unsafe_allow_html=True)
        user = st.text_input("Username").strip().lower()
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "fahim" and pw == "gemsadmin":
                st.session_state.logged_in = True
                st.session_state.user_role = "Fahim (Admin)"
                st.rerun()
            elif user == "shahela" and pw == "shahela123":
                st.session_state.logged_in = True
                st.session_state.user_role = "Shahela (Partner)"
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    st.stop()

# ================= LOAD DATABASE =================
try:
    inventory_df = load_data("Inventory")
    orders_df = load_data("Orders")
    conn = get_connection()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# ================= SIDEBAR & LOGOUT =================
st.sidebar.title(f"👤 {st.session_state.user_role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

# ================= SHAHELA'S PARTNER PORTAL =================
if st.session_state.user_role == "Shahela (Partner)":
    st.title("📦 Customer Order Submission")
    
    with st.form("shahela_order", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Customer Info")
            c_name = st.text_input("Full Name")
            c_phone = st.text_input("Contact Number")
            c_address = st.text_area("Delivery Address")
        with col2:
            st.subheader("Order Info")
            sku_list = inventory_df["Product Code"].tolist()
            selected_sku = st.selectbox("Product SKU", sku_list)
            qty = st.number_input("Quantity", min_value=1, step=1)
            total_price = st.number_input("Total Amount (BDT)", min_value=0)
        
        if st.form_submit_button("Send Order to Fahim"):
            if c_name and c_phone and c_address:
                new_order = pd.DataFrame([{
                    "Order ID": f"EG-{datetime.now().strftime('%m%d%H%M')}",
                    "Product Code": selected_sku, "Requested Quantity": qty,
                    "Partner Name": "Shahela", "Customer Name": c_name,
                    "Customer Phone": c_phone, "Address": c_address,
                    "Total Price": total_price, "Status": "Pending", "Date": datetime.now().strftime("%Y-%m-%d")
                }])
                updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                st.success("Order sent successfully!")
            else:
                st.error("Please fill all fields.")

# ================= FAHIM'S ADMIN PORTAL =================
else:
    st.title("👑 Admin Control Panel")
    tab1, tab2, tab3 = st.tabs(["Pending Orders", "Inventory Manager", "➕ Add New Product"])

    with tab1:
        st.subheader("Orders for Delivery")
        # Column existence check (Prevents KeyError)
        if "Customer Name" in orders_df.columns:
            pending = orders_df[orders_df["Status"] == "Pending"]
            if not pending.empty:
                for i, row in pending.iterrows():
                    with st.expander(f"Order {row['Order ID']} - {row['Customer Name']}"):
                        st.write(f"**Item:** {row['Product Code']} | **Price:** {row['Total Price']} BDT")
                        st.write(f"**Address:** {row['Address']} | **Phone:** {row['Customer Phone']}")
                        if st.button("Handover to Pathao", key=f"ship_{i}"):
                            orders_df.at[i, "Status"] = "With Pathao"
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                            st.rerun()
            else:
                st.info("No pending orders.")
        else:
            st.error("Error: 'Customer Name' column missing in Orders Sheet!")

    with tab2:
        st.subheader("Edit or Remove Inventory")
        edited_inv = st.data_editor(inventory_df, use_container_width=True)
        if st.button("Save Edits"):
            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
            st.success("Changes saved!")
        
        st.markdown("---")
        st.subheader("🗑️ Delete Product")
        to_delete = st.selectbox("Select SKU to Remove", inventory_df["Product Code"].tolist())
        if st.button("Confirm Delete", type="primary"):
            updated_inventory = inventory_df[inventory_df["Product Code"] != to_delete]
            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inventory)
            st.warning(f"Product {to_delete} removed.")
            st.rerun()

    with tab3:
        st.subheader("Add New Product")
        with st.form("new_product", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca:
                sku = st.text_input("SKU")
                name = st.text_input("Name")
                cat = st.selectbox("Category", ["Rings", "Necklaces", "Earrings", "Bracelets"])
            with cb:
                stk = st.number_input("Stock", min_value=0)
                pprice = st.number_input("Paikari Price", min_value=0)
                sprice = st.number_input("Sell Price", min_value=0)
            img_file = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("Register Product"):
                if sku and name and img_file:
                    b64 = image_to_base64(img_file)
                    new_item = pd.DataFrame([{
                        "Product Code": sku, "Product Name": name, "Category": cat,
                        "Stock": stk, "Paikari Price": pprice, "Sell Price": sprice,
                        "Pic_URL": f"data:image/png;base64,{b64}"
                    }])
                    updated_inventory = pd.concat([inventory_df, new_item], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inventory)
                    st.success("Added successfully!")
                    st.rerun()
