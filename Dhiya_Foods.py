import streamlit as st
import pandas as pd
import random
import string
import json
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Load Google Credentials from Secret (GitHub Actions or Streamlit Cloud env var) ---
import tempfile

# Load from Streamlit secrets
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
    tmp_file.write(json.dumps(st.secrets["GOOGLE_CREDENTIALS"]).encode("utf-8"))
    creds_file = tmp_file.name 

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
client = gspread.authorize(creds)
sheet = client.open("DiyaFoodTruckOrders").sheet1

# --- Load food items from CSV ---
@st.cache_data
def load_menu():
    return pd.read_csv("https://raw.githubusercontent.com/your-username/your-repo-name/main/menu.csv")

menu_df = load_menu()

# --- Generate Random Order Number ---
def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# --- Tab Navigation ---
tab1, tab2 = st.tabs(["Order Billing", "Order Queue"])

with tab1:
    st.title("Place a New Order")
    order_no = generate_order_number()
    st.write(f"*Order Number:* {order_no}")

    food_items = []
    quantities = []

    for i in range(4):
        col1, col2 = st.columns([2, 1])
        with col1:
            item = st.selectbox(f"Select Food Item {i+1}", menu_df["Item"], key=f"item_{i}")
        with col2:
            qty = st.number_input(f"Qty {i+1}", min_value=0, step=1, key=f"qty_{i}")
        food_items.append(item)
        quantities.append(qty)

    add_more = st.checkbox("Add more items")
    if add_more:
        n = st.number_input("How many more?", min_value=1, max_value=10)
        for i in range(int(n)):
            col1, col2 = st.columns([2, 1])
            with col1:
                item = st.selectbox(f"Extra Item {i+1}", menu_df["Item"], key=f"extra_item_{i}")
            with col2:
                qty = st.number_input(f"Extra Qty {i+1}", min_value=0, step=1, key=f"extra_qty_{i}")
            food_items.append(item)
            quantities.append(qty)

    ordered_items = [(item, qty) for item, qty in zip(food_items, quantities) if qty > 0]
    total = 0
    for item, qty in ordered_items:
        price = menu_df[menu_df["Item"] == item]["Price"].values[0]
        total += price * qty

    if ordered_items:
        st.subheader(f"Total Amount: ₹{total}")

    if st.button("Place Order"):
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        day = datetime.now().strftime("%A")
        item_str = ", ".join([f"{item} x{qty}" for item, qty in ordered_items])
        sheet.append_row([order_no, date, time, day, item_str, total, "Queued"])
        st.success("Order placed and added to queue!")

with tab2:
    st.title("Order Queue")
    data = pd.DataFrame(sheet.get_all_records())
    queue_data = data[data["Status"] == "Queued"]

    for index, row in queue_data.iterrows():
        st.markdown(f"### Order No: {row['Order No']}")
        st.write(f"*Items:* {row['Food Items']}")
        col1, col2 = st.columns(2)
        if col1.button("Served", key=f"serve_{row['Order No']}"):
            sheet.update_cell(index + 2, 7, "Served")  # Status column
            st.experimental_rerun()
        if col2.button("Cancelled", key=f"cancel_{row['Order No']}"):
            sheet.update_cell(index + 2, 7, "Cancelled")
            st.experimental_rerun()
