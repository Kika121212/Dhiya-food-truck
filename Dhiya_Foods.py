import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime
import requests

# Constants for your GitHub CSV (you'll need to update URLs)
FOOD_DATA_URL = "https://raw.githubusercontent.com/Kika121212/Dhiya-food-truck/refs/heads/main/menu.csv"
ORDERS_CSV_URL = "https://raw.githubusercontent.com/<your-username>/<your-repo>/main/orders.csv"
ORDERS_LOCAL_FILE = "orders.csv"

def load_food_data():
    return pd.read_csv(FOOD_DATA_URL)

def load_order_data():
    try:
        return pd.read_csv(ORDERS_CSV_URL)
    except:
        return pd.DataFrame(columns=["Order No", "Date", "Time", "Day", "Food Items", "Total", "Status"])

def save_order_data(df):
    df.to_csv(ORDERS_LOCAL_FILE, index=False)
    st.success("Order data updated locally. Please push the CSV to GitHub manually.")

def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def format_datetime():
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), now.strftime("%A")

# UI Start
st.set_page_config(page_title="Diya Food Truck Billing App", layout="wide")

tab1, tab2 = st.tabs(["Take Order", "Queue"])

with tab1:
    st.header("Take Order")
    
    food_df = load_food_data()
    order_number = generate_order_number()

    st.subheader("Order Number: " + order_number)

    selected_items = []
    quantities = []

    item_cols = st.columns(4)
    for i in range(4):
        with item_cols[i]:
            item = st.selectbox(f"Select Item {i+1}", options=[""] + food_df['Item'].tolist(), key=f"item{i}")
            if item:
                qty = st.number_input(f"Quantity for {item}", min_value=1, value=1, key=f"qty{i}")
                selected_items.append(item)
                quantities.append(qty)

    if st.button("Add More Items"):
        st.experimental_rerun()

    # Calculate total
    total = 0
    item_price_dict = dict(zip(food_df['Item'], food_df['Price']))
    summary = []

    for item, qty in zip(selected_items, quantities):
        price = item_price_dict.get(item, 0)
        total += price * qty
        summary.append(f"{item} x{qty}")

    st.write("### Order Summary")
    st.write(", ".join(summary))
    st.write(f"*Total Amount:* ₹{total}")

    if st.button("Place Order"):
        date, time_str, day = format_datetime()
        new_order = {
            "Order No": order_number,
            "Date": date,
            "Time": time_str,
            "Day": day,
            "Food Items": ", ".join(summary),
            "Total": total,
            "Status": "Queued"
        }
        order_df = load_order_data()
        order_df = pd.concat([order_df, pd.DataFrame([new_order])], ignore_index=True)
        save_order_data(order_df)
        st.success("Order placed successfully!")

with tab2:
    st.header("Order Queue")
    queue_df = load_order_data()
    queue_df = queue_df[queue_df["Status"] == "Queued"]

    for idx, row in queue_df.iterrows():
        st.markdown(f"### Order No: {row['Order No']}")
        st.markdown(f"*Items*: {row['Food Items']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Mark as Served - {row['Order No']}"):
                all_orders = load_order_data()
                all_orders.loc[all_orders["Order No"] == row["Order No"], "Status"] = "Served"
                save_order_data(all_orders)
                st.experimental_rerun()
        with col2:
            if st.button(f"Cancel Order - {row['Order No']}"):
                all_orders = load_order_data()
                all_orders.loc[all_orders["Order No"] == row["Order No"], "Status"] = "Cancelled"
                save_order_data(all_orders)
                st.experimental_rerun()
