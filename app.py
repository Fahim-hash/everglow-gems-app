import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io

# ... (Previous Page Config & CSS remains the same) ...

# ================= HELPER FUNCTION: IMAGE TO BASE64 =================
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        # Resizing for faster loading in GSheet
        img.thumbnail((400, 400))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

# ================= CONNECTION & DATA LOADING =================
# ... (Connection logic remains same as previous version) ...

# ================= FAHIM'S ADMIN PORTAL =================
if st.session_state.user_role == "Admin":
    st.title("👑 Fahim | Admin Control")
    tab1, tab2, tab3 = st.tabs(["Pending Orders", "Inventory Manager", "➕ Add New Product"])
    
    # ... (Tab 1 & Tab 2 logic remains same) ...

    # ================= TAB 3: ADD NEW PRODUCT (WITH FILE UPLOAD) =================
    with tab3:
        st.subheader("✨ Register New Jewelry Item")
        
        with st.form("add_product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_sku = st.text_input("Product Code (e.g., EG-B105)")
                new_name = st.text_input("Product Name")
                new_cat = st.selectbox("Category", ["Rings", "Necklaces", "Earrings", "Bracelets", "Other"])
            
            with col2:
                new_stock = st.number_input("Initial Stock", min_value=0, step=1)
                new_paikari = st.number_input("Paikari Price (BDT)", min_value=0)
                new_sell = st.number_input("Sell Price (BDT)", min_value=0)
            
            # FILE UPLOADER (No links needed!)
            uploaded_img = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("Add Product to Inventory"):
                if new_sku and new_name and uploaded_img:
                    # Convert image to data string
                    img_data = image_to_base64(uploaded_img)
                    
                    new_product_data = pd.DataFrame([{
                        "Product Code": new_sku,
                        "Product Name": new_name,
                        "Category": new_cat,
                        "Stock": new_stock,
                        "Paikari Price": new_paikari,
                        "Sell Price": new_sell,
                        "Pic_URL": f"data:image/png;base64,{img_data}" # Storing as data URI
                    }])
                    
                    # Sync with GSheet
                    updated_inventory = pd.concat([inventory_df, new_product_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=updated_inventory)
                    
                    st.success(f"Successfully added {new_name} to inventory!")
                    st.rerun()
                else:
                    st.error("Please fill SKU, Name, and Upload an Image.")
