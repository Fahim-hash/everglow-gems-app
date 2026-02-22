import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Everglow Gems | Business Portal",
    layout="wide",
    page_icon="💎"
)

# ---------------- DATABASE CONFIG ----------------
SHEET_ID = "1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"


# ---------------- CONNECTION ----------------
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def load_inventory(conn):
    return conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)


def load_orders(conn):
    return conn.read(spreadsheet=SHEET_URL, worksheet="Orders", ttl=0)


def update_inventory(conn, df):
    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=df)


def update_orders(conn, df):
    conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=df)


# ---------------- INIT ----------------
try:
    conn = get_connection()
    inventory_df = load_inventory(conn)
    orders_df = load_orders(conn)
except Exception as e:
    st.error(f"Google Sheets Connection Error: {e}")
    st.stop()

if inventory_df is None or orders_df is None:
    st.warning("Ensure Google Sheet tabs are named 'Inventory' and 'Orders'.")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Everglow Gems")
role = st.sidebar.radio("Navigation", ["Partner Portal", "Admin Dashboard"])


# ==========================================================
# ===================== PARTNER PORTAL =====================
# ==========================================================
if role == "Partner Portal":

    st.title("💎 Partner Ordering Portal")

    product_codes = inventory_df['Product Code'].astype(str).tolist()
    search_code = st.selectbox("Select Product Code", product_codes)

    item_match = inventory_df[
        inventory_df['Product Code'].astype(str) == search_code
    ]

    if not item_match.empty:

        idx = item_match.index[0]
        product = inventory_df.iloc[idx]
        stock = int(product['Stock'])

        col1, col2 = st.columns([1, 1])

        with col1:
            if pd.notna(product['Pic_URL']):
                st.image(product['Pic_URL'], use_container_width=True)

        with col2:
            st.header(product['Product Name'])
            st.write(f"**Category:** {product['Category']}")
            st.write(f"**Paikari Price:** {product['Paikari Price']} BDT")

            # Stock Display Logic
            if stock <= 0:
                st.error("Out of Stock")
                st.stop()
            elif stock <= 5:
                st.error(f"Only {stock} left!")
            elif stock <= 10:
                st.warning(f"{stock} available")
            else:
                st.success(f"{stock} available")

            # ---------------- ORDER FORM ----------------
            with st.form("order_form", clear_on_submit=True):

                qty = st.number_input(
                    "Requested Quantity",
                    min_value=1,
                    max_value=stock,
                    step=1
                )

                p_name = st.text_input("Partner Name")

                submit = st.form_submit_button("Place Order")

                if submit:

                    if not p_name.strip():
                        st.error("Partner Name is required.")
                        st.stop()

                    # Reload fresh inventory (Race-condition protection)
                    latest_inventory = load_inventory(conn)

                    latest_match = latest_inventory[
                        latest_inventory['Product Code'].astype(str) == search_code
                    ]

                    if latest_match.empty:
                        st.error("Product not found.")
                        st.stop()

                    latest_idx = latest_match.index[0]
                    current_stock = int(latest_inventory.at[latest_idx, 'Stock'])

                    if qty > current_stock:
                        st.error("Stock changed. Please try again.")
                        st.stop()

                    # Deduct stock safely
                    latest_inventory.at[latest_idx, 'Stock'] = current_stock - qty
                    update_inventory(conn, latest_inventory)

                    # Create Unique Order ID
                    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

                    new_order = pd.DataFrame([{
                        "Order ID": order_id,
                        "Product Code": search_code,
                        "Requested Quantity": qty,
                        "Partner Name": p_name,
                        "Status": "Pending",
                        "Date": datetime.now().strftime("%Y-%m-%d")
                    }])

                    latest_orders = load_orders(conn)
                    updated_orders = pd.concat([latest_orders, new_order], ignore_index=True)

                    update_orders(conn, updated_orders)

                    st.success(f"Order {order_id} placed successfully!")
                    st.rerun()


# ==========================================================
# ===================== ADMIN DASHBOARD ====================
# ==========================================================
else:

    st.title("👑 Admin Control Panel")

    tab1, tab2, tab3 = st.tabs(["Stock Manager", "Orders & Pathao", "Analytics"])

    # ---------------- STOCK MANAGER ----------------
    with tab1:

        st.subheader("Manage Inventory")

        edited_inventory = st.data_editor(
            inventory_df,
            num_rows="fixed",
            use_container_width=True
        )

        if st.button("Save Inventory Changes"):
            update_inventory(conn, edited_inventory)
            st.success("Inventory Updated!")
            st.rerun()

    # ---------------- ORDERS ----------------
    with tab2:

        st.subheader("Current Orders")

        for i, row in orders_df.iterrows():

            if row['Status'] == "Pending":

                cols = st.columns([4, 1])

                cols[0].info(
                    f"{row['Order ID']} | "
                    f"{row['Partner Name']} requested "
                    f"{row['Requested Quantity']}x "
                    f"{row['Product Code']}"
                )

                if cols[1].button("Handover to Pathao", key=f"btn_{i}"):

                    orders_df.at[i, 'Status'] = "With Pathao"
                    update_orders(conn, orders_df)

                    st.success(f"{row['Order ID']} sent to Pathao!")
                    st.rerun()

            else:
                st.write(
                    f"{row['Order ID']} → {row['Status']}"
                )

    # ---------------- ANALYTICS ----------------
    with tab3:

        st.subheader("Business Insights")

        total_products = len(inventory_df)
        total_stock = inventory_df['Stock'].sum()
        total_stock_value = (
            inventory_df['Stock'] * inventory_df['Paikari Price']
        ).sum()

        pending_orders = len(
            orders_df[orders_df['Status'] == "Pending"]
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Products", total_products)
        col2.metric("Total Units in Stock", int(total_stock))
        col3.metric("Inventory Value (BDT)", int(total_stock_value))
        col4.metric("Pending Orders", pending_orders)
