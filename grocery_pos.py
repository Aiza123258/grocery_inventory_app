import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(page_title="Grocery POS Dashboard", layout="wide")

BASE_DIR = os.path.dirname(__file__)
PRODUCTS_FILE = os.path.join(BASE_DIR, "products.csv")
SALES_FILE = os.path.join(BASE_DIR, "sales.csv")

# ------------------------------------------------------------------
# Load / initialize data
# ------------------------------------------------------------------
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        return pd.read_csv(PRODUCTS_FILE)
    else:
        sample = pd.DataFrame([
            {"Product_ID": 1, "Name": "Rice (1kg)", "Category": "Grains", "Price": 250, "Stock": 50},
            {"Product_ID": 2, "Name": "Sugar (1kg)", "Category": "Grains", "Price": 180, "Stock": 40},
            {"Product_ID": 3, "Name": "Milk (1L)", "Category": "Dairy", "Price": 220, "Stock": 30},
            {"Product_ID": 4, "Name": "Eggs (dozen)", "Category": "Dairy", "Price": 320, "Stock": 25},
            {"Product_ID": 5, "Name": "Cooking Oil (1L)", "Category": "Oil", "Price": 550, "Stock": 20},
            {"Product_ID": 6, "Name": "Bread", "Category": "Bakery", "Price": 150, "Stock": 15},
            {"Product_ID": 7, "Name": "Apples (1kg)", "Category": "Fruits", "Price": 300, "Stock": 35},
            {"Product_ID": 8, "Name": "Bananas (dozen)", "Category": "Fruits", "Price": 160, "Stock": 45},
            {"Product_ID": 9, "Name": "Chicken (1kg)", "Category": "Meat", "Price": 650, "Stock": 18},
            {"Product_ID": 10, "Name": "Detergent (1kg)", "Category": "Household", "Price": 400, "Stock": 22},
        ])
        sample.to_csv(PRODUCTS_FILE, index=False)
        return sample


def load_sales():
    if os.path.exists(SALES_FILE):
        return pd.read_csv(SALES_FILE)
    else:
        sales = pd.DataFrame(columns=[
            "Sale_ID", "Date", "Product_ID", "Product_Name", "Category", "Quantity", "Unit_Price", "Total_Price"
        ])
        sales.to_csv(SALES_FILE, index=False)
        return sales


def save_products():
    st.session_state.products.to_csv(PRODUCTS_FILE, index=False)


def save_sales():
    st.session_state.sales.to_csv(SALES_FILE, index=False)


if "products" not in st.session_state:
    st.session_state.products = load_products()
if "sales" not in st.session_state:
    st.session_state.sales = load_sales()
if "cart" not in st.session_state:
    st.session_state.cart = []

st.title("🛒 Grocery Store POS Dashboard")

# ------------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------------
page = st.sidebar.radio("📌 Navigate", ["Dashboard", "Billing / New Sale", "Manage Inventory"])

# ====================================================================
# PAGE 1: DASHBOARD
# ====================================================================
if page == "Dashboard":
    products = st.session_state.products
    sales = st.session_state.sales.copy()
    if not sales.empty:
        sales["Date"] = pd.to_datetime(sales["Date"])

    st.sidebar.header("🔍 Filters")
    category_options = sorted(products["Category"].unique())
    category_filter = st.sidebar.multiselect("Category", options=category_options, default=category_options)

    if not sales.empty:
        min_date, max_date = sales["Date"].min(), sales["Date"].max()
        date_range = st.sidebar.date_input("Date Range", (min_date.date(), max_date.date()))
    else:
        date_range = None

    filtered_sales = sales[sales["Category"].isin(category_filter)] if not sales.empty else sales
    if date_range and len(date_range) == 2 and not filtered_sales.empty:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_sales = filtered_sales[(filtered_sales["Date"] >= start) & (filtered_sales["Date"] <= end)]

    filtered_products = products[products["Category"].isin(category_filter)]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", len(filtered_products))
    col2.metric("Total Sales Transactions", len(filtered_sales))
    col3.metric("Total Revenue", f"Rs {filtered_sales['Total_Price'].sum():,.0f}" if not filtered_sales.empty else "Rs 0")
    low_stock = filtered_products[filtered_products["Stock"] < 10]
    col4.metric("Low Stock Items (<10)", len(low_stock))

    if len(low_stock) > 0:
        st.warning(f"⚠️ Low stock alert: {', '.join(low_stock['Name'].tolist())}")

    st.divider()

    st.subheader("📦 Current Inventory")
    st.dataframe(filtered_products, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📊 Sales Insights")

    if filtered_sales.empty:
        st.info("No sales yet. Go to 'Billing / New Sale' to record your first sale.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Line Chart — Revenue Over Time**")
            daily_sales = filtered_sales.groupby(filtered_sales["Date"].dt.date)["Total_Price"].sum().reset_index()
            fig_line = px.line(daily_sales, x="Date", y="Total_Price", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        with chart_col2:
            st.markdown("**Bar Chart — Top Selling Products**")
            top_products = filtered_sales.groupby("Product_Name", as_index=False)["Quantity"].sum() \
                .sort_values("Quantity", ascending=False).head(10)
            fig_bar = px.bar(top_products, x="Product_Name", y="Quantity", color="Product_Name")
            st.plotly_chart(fig_bar, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.markdown("**Pie Chart — Revenue Share by Category**")
            pie_data = filtered_sales.groupby("Category", as_index=False)["Total_Price"].sum()
            fig_pie = px.pie(pie_data, names="Category", values="Total_Price")
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col4:
            st.markdown("**Scatter Chart — Quantity vs Revenue per Sale**")
            fig_scatter = px.scatter(
                filtered_sales, x="Quantity", y="Total_Price",
                color="Category", hover_name="Product_Name", size="Total_Price"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.divider()
        st.subheader("🧾 Sales History")
        st.dataframe(filtered_sales.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

# ====================================================================
# PAGE 2: BILLING / NEW SALE
# ====================================================================
elif page == "Billing / New Sale":
    st.subheader("🧾 New Sale — Add Items to Cart")

    products = st.session_state.products

    with st.form("add_to_cart_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            product_name = st.selectbox("Select Product", options=products["Name"])
        product_row = products[products["Name"] == product_name].iloc[0]
        with c2:
            st.metric("Price (per unit)", f"Rs {product_row['Price']}")
        with c3:
            st.metric("In Stock", int(product_row["Stock"]))
        qty = st.number_input("Quantity", min_value=1, max_value=int(product_row["Stock"]) if product_row["Stock"] > 0 else 1, value=1)
        add_btn = st.form_submit_button("➕ Add to Cart")

        if add_btn:
            if product_row["Stock"] < qty:
                st.error("Not enough stock available.")
            else:
                st.session_state.cart.append({
                    "Product_ID": int(product_row["Product_ID"]),
                    "Product_Name": product_row["Name"],
                    "Category": product_row["Category"],
                    "Quantity": qty,
                    "Unit_Price": product_row["Price"],
                    "Total_Price": qty * product_row["Price"]
                })
                st.success(f"Added {qty} x {product_name} to cart.")
                st.rerun()

    st.divider()
    st.subheader("🛒 Current Cart")

    if len(st.session_state.cart) == 0:
        st.info("Cart is empty. Add products above.")
    else:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df, use_container_width=True, hide_index=True)

        grand_total = cart_df["Total_Price"].sum()
        st.markdown(f"### 💰 Grand Total: Rs {grand_total:,.0f}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Checkout & Save Sale"):
                sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                next_id = (st.session_state.sales["Sale_ID"].max() + 1) if len(st.session_state.sales) > 0 else 1

                new_sales_rows = []
                for item in st.session_state.cart:
                    new_sales_rows.append({
                        "Sale_ID": next_id,
                        "Date": sale_date,
                        "Product_ID": item["Product_ID"],
                        "Product_Name": item["Product_Name"],
                        "Category": item["Category"],
                        "Quantity": item["Quantity"],
                        "Unit_Price": item["Unit_Price"],
                        "Total_Price": item["Total_Price"],
                    })
                    # reduce stock
                    idx = st.session_state.products[st.session_state.products["Product_ID"] == item["Product_ID"]].index[0]
                    st.session_state.products.loc[idx, "Stock"] -= item["Quantity"]

                st.session_state.sales = pd.concat(
                    [st.session_state.sales, pd.DataFrame(new_sales_rows)], ignore_index=True
                )
                save_sales()
                save_products()
                st.session_state.cart = []
                st.success("Sale completed and saved!")
                st.rerun()

        with col_b:
            if st.button("🗑️ Clear Cart"):
                st.session_state.cart = []
                st.rerun()

# ====================================================================
# PAGE 3: MANAGE INVENTORY (CRUD)
# ====================================================================
elif page == "Manage Inventory":
    st.subheader("📦 Manage Inventory — Add / Update / Delete Products")

    mode = st.radio("Choose action", ["Add New Product", "Update / Delete Existing Product"], horizontal=True)

    if mode == "Add New Product":
        with st.form("add_product_form", clear_on_submit=True):
            name = st.text_input("Product Name")
            category = st.text_input("Category")
            price = st.number_input("Price (Rs)", 0.0, value=0.0, step=1.0)
            stock = st.number_input("Stock Quantity", 0, value=0)
            submitted = st.form_submit_button("Add Product")

            if submitted:
                if name.strip() == "" or category.strip() == "":
                    st.warning("Please enter both Product Name and Category.")
                else:
                    next_id = (st.session_state.products["Product_ID"].max() + 1) if len(st.session_state.products) > 0 else 1
                    new_row = pd.DataFrame([{
                        "Product_ID": next_id, "Name": name, "Category": category,
                        "Price": price, "Stock": stock
                    }])
                    st.session_state.products = pd.concat([st.session_state.products, new_row], ignore_index=True)
                    save_products()
                    st.success(f"Added product '{name}'.")
                    st.rerun()

    else:
        products = st.session_state.products
        if len(products) == 0:
            st.info("No products available.")
        else:
            selected_id = st.selectbox(
                "Select Product to Update",
                options=products["Product_ID"],
                format_func=lambda x: f"{x} - {products.loc[products['Product_ID'] == x, 'Name'].values[0]}"
            )
            record = products[products["Product_ID"] == selected_id].iloc[0]

            with st.form("update_product_form"):
                name = st.text_input("Product Name", value=record["Name"])
                category = st.text_input("Category", value=record["Category"])
                price = st.number_input("Price (Rs)", 0.0, value=float(record["Price"]), step=1.0)
                stock = st.number_input("Stock Quantity", 0, value=int(record["Stock"]))

                col_update, col_delete = st.columns(2)
                update_submitted = col_update.form_submit_button("Update Product")
                delete_submitted = col_delete.form_submit_button("🗑️ Delete Product")

                if update_submitted:
                    idx = st.session_state.products[st.session_state.products["Product_ID"] == selected_id].index[0]
                    st.session_state.products.loc[idx, ["Name", "Category", "Price", "Stock"]] = [name, category, price, stock]
                    save_products()
                    st.success(f"Updated product '{name}'.")
                    st.rerun()

                if delete_submitted:
                    st.session_state.products = st.session_state.products[
                        st.session_state.products["Product_ID"] != selected_id
                    ].reset_index(drop=True)
                    save_products()
                    st.success("Product deleted.")
                    st.rerun()

            st.divider()
            st.subheader("📋 Full Product List")
            st.dataframe(st.session_state.products, use_container_width=True, hide_index=True)