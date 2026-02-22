import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Page setup for a professional jewelry brand look
st.set_page_config(page_title="Everglow Gems | Inventory Portal", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE CONNECTION ---
# Your unique Google Sheet URL
sheet_url = "https://docs.google.com/spreadsheets/d/1wRYbLJ_Jx1ZO5mJokpu8ggei7fzkG239VMSCzQFBnl0/edit#gid=0"

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # We read the 'Inventory' tab
        data = conn.read(spreadsheet=sheet_url, worksheet="Inventory")
        return data
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

df = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3024/3024508.png", width=100) # Generic Gem Icon
st.sidebar.title("Everglow Gems")
role = st.sidebar.radio("Login Access", ["Partner", "Admin"])

# --- INTERFACE LOGIC ---
if df is not None:
    if role == "Partner":
        st.title("💎 Partner Stock Check")
        st.info("Enter a Product Code below to see real-time stock and pricing.")
        
        search_code = st.text_input("Product Code (e.g., EG-R001)", placeholder="Type here...")

        if search_code:
            # Case-insensitive search
            item = df[df['Product Code'].astype(str).str.upper() == search_code.upper()]
            
            if not item.empty:
                product = item.iloc[0]
                
                col1, col2 = st.columns([1, 1.2])
                
                with col1:
                    # Facial Consistency: Displays the model image linked in your sheet
                    if pd.notna(product['Pic_URL']):
                        st.image(product['Pic_URL'], caption=product['Product Name'], use_container_width=True)
                    else:
                        st.warning("No image available for this item.")
                
                with col2:
                    st.header(product['Product Name'])
                    st.divider()
                    
                    # Stock and Pricing metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Current Stock", f"{int(product['Stock'])} pcs")
                    c2.write("") # Spacer
                    
                    st.subheader("Pricing Details")
                    st.write(f"🏷️ **Paikari (Wholesale):** {product['Paikari Price']} BDT")
                    st.write(f"💰 **Sell Price (Retail):** {product['Sell Price']} BDT")
                    
                    st.divider()
                    # Order Request Section
                    with st.expander("📝 Make an Order Request"):
                        order_qty = st.number_input("How many pieces?", min_value=1, max_value=int(product['Stock']))
                        if st.button("Submit Request to Admin"):
                            st.success(f"Request for {order_qty}x {product['Product Code']} has been logged!")
                            # Note: To save this to the 'Orders' sheet, further write-back logic is needed.
            else:
                st.error("Product code not found. Please check the code and try again.")

    elif role == "Admin":
        st.title("👑 Admin Dashboard")
        st.subheader("Full Inventory Overview")
        
        # Display the full table for the Admin
        st.dataframe(df, use_container_width=True)
        
        # Add New Product Section
        with st.expander("➕ Add New Product"):
            st.warning("To add products, update your Google Sheet directly. The app will refresh automatically.")
            st.write(f"[Open Google Sheet Database]({sheet_url})")

else:
    st.error("Could not load database. Please check your internet or Google Sheet permissions.")

# Footer
st.markdown("---")
st.caption("Everglow Gems Inventory Management System v1.0")
