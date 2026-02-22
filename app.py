import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Everglow Gems | Business Portal", layout="wide", page_icon="💎")

# ================= CUSTOM CSS FOR LOGIN =================
st.markdown("""
    <style>
    .login-header {
        font-size: 40px;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        width: 100%;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ================= GOOGLE SHEET CONFIG =================
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    conn = get_connection()
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=0)

# ================= SESSION STATE FOR LOGIN =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

# ================= LOGIN INTERFACE =================
if not st.session_state.logged_in:
    # Centering the login box
    empty_col1, login_col, empty_col2 = st.columns([1, 2, 1])
    
    with login_col:
        st.markdown('<p class="login-header">🔐 Everglow Gems | Portal</p>', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # FAHIM LOGIN
            if username == "fahim" and password == "gemsadmin":
                st.session_state.logged_in = True
                st.session_state.user_role = "Admin"
                st.rerun()
            # SHAHELA LOGIN
            elif username == "shahela" and password == "shahela123":
                st.session_state.logged_in = True
                st.session_state.user_role = "Partner"
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    st.stop()

# ================= DATA LOADING (Post-Login) =================
try:
    inventory_df = load_data("Inventory")
    orders_df = load_data("Orders")
    conn = get_connection()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# ================= LOGOUT BUTTON =================
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

# ==========================================================
# ================= SHAHELA'S PARTNER PORTAL ===============
# ==========================================================
if st.session_state.user_role == "Partner":
    st.title(f"👋 Welcome, Shahela")
    st.info("Fill in the customer order details below.")
    
    with st.form("customer_order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            c_name = st.text_input("Customer Name")
            c_phone = st.text_input("Customer Phone")
            c_address = st.text_area("Delivery Address")
        with col2:
            product_list = inventory_df["Product Code"].astype(str).tolist()
            selected_sku = st.selectbox("Select Product", product_list)
            qty = st.number_input("Quantity", min_value=1, step=1)
            total_bill = st.number_input("Total Bill (BDT)", min_value=0)
        
        if st.form_submit_button("Send Order to Fahim"):
            if c_name and c_phone and c_address:
                new_row = pd.DataFrame([{
                    "Order ID": f"EG-{datetime.now().strftime('%m%d%y%H%M')}",
                    "Product Code": selected_sku,
                    "Requested Quantity": qty,
                    "Partner Name": "Shahela",
                    "Customer Name": c_name,
                    "Customer Phone": c_phone,
                    "Address": c_address,
                    "Total Price": total_bill,
                    "Status": "Pending",
                    "Date": datetime.now().strftime("%Y-%m-%d")
                }])
                updated_orders = pd.concat([orders_df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                st.success("Order received! Fahim will process it soon.")
            else:
                st.error("Please provide complete customer info.")

# ==========================================================
# =================== FAHIM'S ADMIN PORTAL =================
# ==========================================================
else:
    st.title("👑 Fahim | Admin Control")
    tab1, tab2 = st.tabs(["Pending Orders", "Inventory Manager"])
    
    with tab1:
        st.subheader("Orders Needing Delivery")
        pending = orders_df[orders_df["Status"] == "Pending"]
        if not pending.empty:
            for i, row in pending.iterrows():
                with st.expander(f"Order: {row['Order ID']} | Customer: {row['Customer Name']}"):
                    st.write(f"**Address:** {row['Address']} | **Phone:** {row['Customer Phone']}")
                    st.write(f"**Item:** {row['Product Code']} | **Bill:** {row['Total Price']} BDT")
                    if st.button("Ship with Pathao", key=f"ship_{i}"):
                        orders_df.at[i, "Status"] = "With Pathao"
                        conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                        st.rerun()
        else:
            st.info("No orders waiting.")

    with tab2:
        st.subheader("Edit Inventory Items")
        edited_inv = st.data_editor(inventory_df, num_rows="dynamic")
        if st.button("Save Changes"):
            conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
            st.success("Database Updated!")
