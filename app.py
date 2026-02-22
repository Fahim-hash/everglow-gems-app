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

# ================= LOGIN SYSTEM =================
st.sidebar.title("🔐 Everglow Gems Login")
user_access = st.sidebar.selectbox("Choose Portal", ["Shahela (Partner)", "Fahim (Admin)"])

# Password protection (Simple version)
password = st.sidebar.text_input("Enter Password", type="password")

# Basic Password Logic (Tumi pore eita change kore nite parbe)
if password == "gems123": 
    try:
        inventory_df = load_data("Inventory")
        orders_df = load_data("Orders")
        conn = get_connection()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

    # ==========================================================
    # ================= SHAHELA'S PARTNER PORTAL ===============
    # ==========================================================
    if user_access == "Shahela (Partner)":
        st.title("💎 Shahela's Partner Portal")
        st.markdown("---")
        
        with st.form("shahela_order_form", clear_on_submit=True):
            st.subheader("📝 New Customer Order")
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("Customer Name")
                c_phone = st.text_input("Customer Phone")
                c_address = st.text_area("Delivery Address")
            with c2:
                product_list = inventory_df["Product Code"].astype(str).tolist()
                selected_sku = st.selectbox("Select Product", product_list)
                qty = st.number_input("Quantity", min_value=1, step=1)
                total_bill = st.number_input("Total Bill (BDT)", min_value=0)
            
            if st.form_submit_button("Submit Order to Fahim"):
                if c_name and c_phone and c_address:
                    new_order = pd.DataFrame([{
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
                    updated_orders = pd.concat([orders_df, new_order], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=updated_orders)
                    st.success("Order submitted to Fahim!")
                else:
                    st.error("Please fill all customer details.")

    # ==========================================================
    # =================== FAHIM'S ADMIN PORTAL =================
    # ==========================================================
    else:
        st.title("👑 Fahim's Admin Dashboard")
        st.markdown(f"Welcome back, Fahim! You have **{len(orders_df[orders_df['Status']=='Pending'])}** pending orders.")
        
        tab1, tab2, tab3 = st.tabs(["Order Approvals", "Inventory Management", "Sales Insights"])

        with tab1:
            st.subheader("Orders from Partners")
            pending = orders_df[orders_df["Status"] == "Pending"]
            if not pending.empty:
                for i, row in pending.iterrows():
                    with st.expander(f"Order {row['Order ID']} - From: {row['Partner Name']}"):
                        st.write(f"**Customer:** {row['Customer Name']} ({row['Customer Phone']})")
                        st.write(f"**Address:** {row['Address']}")
                        st.write(f"**Product:** {row['Product Code']} | **Bill:** {row['Total Price']} BDT")
                        
                        if st.button("Handover to Pathao", key=f"f_pathao_{i}"):
                            # Update local DF
                            orders_df.at[i, "Status"] = "With Pathao"
                            # Sync with GSheet
                            conn.update(spreadsheet=SHEET_URL, worksheet="Orders", data=orders_df)
                            st.success(f"Order {row['Order ID']} sent to Pathao!")
                            st.rerun()
            else:
                st.info("No new orders at the moment.")

        with tab2:
            st.subheader("Live Inventory Editor")
            # Fahim can edit stock, prices, or add Pic_URLs directly
            edited_inv = st.data_editor(inventory_df, num_rows="dynamic")
            if st.button("Update Inventory"):
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=edited_inv)
                st.success("Inventory Sheet Updated!")

        with tab3:
            st.subheader("Quick Stats")
            st.metric("Total Revenue (BDT)", f"{orders_df['Total Price'].sum():,.2f}")

else:
    st.warning("Please enter the correct password in the sidebar to access the portals.")
