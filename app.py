import streamlit as st
import pandas as pd
from models import Category, InsufficientFundsError
from utils import import_ledger, export_ledger

# 1. Page Configuration
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="assets/favicon.svg",
    layout="wide"
)

# 2. Inject targeted CSS overrides
with open("assets/style.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# 3. Session State Initialization
if "categories" not in st.session_state:
    st.session_state.categories = {}
if "focus_category" not in st.session_state:
    st.session_state.focus_category = None

active_data = st.session_state.categories

PRESET_CATEGORIES = [
    "Groceries",
    "Housing & Rent",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Savings"
]


def generate_sample_ledger() -> dict[str, Category]:
    """Generate a sample ledger with realistic categories and transaction records."""
    food = Category("Groceries")
    food.deposit(12000, "Monthly Grocery Budget")
    food.withdraw(2450, "Supermarket Purchase")
    food.withdraw(680, "Fresh Produce")

    transport = Category("Transportation")
    transport.deposit(5000, "Commute Allowance")
    transport.withdraw(1500, "Fuel")
    transport.withdraw(400, "Transit Pass")

    entertainment = Category("Entertainment")
    entertainment.deposit(3500, "Discretionary Allocation")
    entertainment.withdraw(799, "Streaming Subscription")

    return {
        "Groceries": food,
        "Transportation": transport,
        "Entertainment": entertainment
    }


# 4. Onboarding State (Empty Ledger)
if not active_data:
    st.title("BUDGET TRACKER")
    st.divider()
    
    st.markdown("Take control of your finances. Create your first category or import an existing ledger to get started.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_fresh, col_import = st.columns(2)
    
    with col_fresh:
        with st.container(border=True):
            st.subheader("Start Fresh")
            st.markdown("Select a standard category or enter a custom name.")
            selection = st.selectbox(
                "Category Selection",
                options=PRESET_CATEGORIES + ["Custom..."],
                key="onboard_preset"
            )
            if selection == "Custom...":
                new_cat = st.text_input("Category Name", placeholder="e.g., Subscriptions", key="onboard_custom").strip()
            else:
                new_cat = selection

            if st.button("Create Category", use_container_width=True):
                if new_cat:
                    st.session_state.categories[new_cat] = Category(new_cat)
                    st.session_state.focus_category = new_cat
                    st.rerun()
                
    with col_import:
        with st.container(border=True):
            st.subheader("Import Ledger")
            st.markdown("Upload an existing JSON ledger.")
            uploaded_file = st.file_uploader("Choose a file", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    json_string = uploaded_file.getvalue().decode("utf-8")
                    st.session_state.categories = import_ledger(json_string)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to import ledger: {e}")

    # Secondary Sample Data Prompt
    with st.container(border=True):
        col_demo_text, col_demo_btn = st.columns([3, 1])
        with col_demo_text:
            st.markdown("**Want to test the dashboard first?** Explore the interface and analytics with a pre-configured sample ledger.")
        with col_demo_btn:
            if st.button("Load Sample Data", use_container_width=True):
                st.session_state.categories = generate_sample_ledger()
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        with st.container(border=True):
            st.markdown("### 🔒 Privacy First\n100% local JSON storage. Your financial data never leaves your machine.")
    with fc2:
        with st.container(border=True):
            st.markdown("### 📊 Real-time Insights\nTrack your spending distribution instantly with dynamic analytics.")
    with fc3:
        with st.container(border=True):
            st.markdown("### 💾 Portability\nStateless architecture. Export and backup your ledger anywhere.")
                
    st.stop()


# 5. Main Application (Tabbed Layout)
st.title("BUDGET TRACKER")
st.divider()
tab_dashboard, tab_transactions, tab_data = st.tabs(["DASHBOARD", "TRANSACTIONS", "DATA MANAGEMENT"])


# --- TAB 1: DASHBOARD ---
with tab_dashboard:
    st.button("🔄 Refresh Data")
    
    active_categories = {name: cat for name, cat in active_data.items() if len(cat.ledger) > 0}
    
    if not active_categories:
        st.info("No transactions logged yet.")
    else:
        sorted_cats = sorted(active_categories.items(), key=lambda x: x[1].get_balance(), reverse=True)
        display_names = [name for name, _ in sorted_cats][:4]
        
        metric_cols = st.columns(len(display_names))
        for index, name in enumerate(display_names):
            with metric_cols[index]:
                st.metric(label=name, value=f"₹{active_categories[name].get_balance():.2f}")
                
        st.divider()
        
        col_log, col_chart = st.columns([1.5, 1])
        
        with col_log:
            st.subheader("Transaction Log")
            audit_trail = []
            for name, cat in active_categories.items():
                for entry in cat.ledger:
                    amt = entry["amount"]
                    sign = "+" if amt > 0 else "\u2212"
                    audit_trail.append({
                        "Date": entry.get("timestamp", "N/A")[:10],
                        "Category": name,
                        "Type": "Deposit" if amt > 0 else "Withdrawal",
                        "Amount": f"{sign}\u00a0₹{abs(amt):.2f}",
                        "Description": entry["description"] if entry["description"] else "N/A"
                    })
            if audit_trail:
                df_log = pd.DataFrame(audit_trail)
                df_log = df_log.iloc[::-1].reset_index(drop=True)
                st.dataframe(
                    df_log,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Date": st.column_config.TextColumn("Date", width="small"),
                        "Category": st.column_config.TextColumn("Category", width="medium"),
                        "Type": st.column_config.TextColumn("Type", width="small"),
                        "Amount": st.column_config.TextColumn("Amount", width="small"),
                        "Description": st.column_config.TextColumn("Description", width="large")
                    }
                )
            else:
                st.info("Log empty.")
                
        with col_chart:
            st.subheader("Relative Spending")
            withdrawal_data = {}
            total_spent = 0
            for name, cat in active_categories.items():
                spent = sum(abs(entry["amount"]) for entry in cat.ledger if entry["amount"] < 0)
                if spent > 0:
                    withdrawal_data[name] = spent
                    total_spent += spent
                    
            if withdrawal_data and total_spent > 0:
                sorted_withdrawals = sorted(withdrawal_data.items(), key=lambda x: x[1], reverse=True)
                for cat_name, spent in sorted_withdrawals:
                    percentage = (spent / total_spent) * 100
                    st.markdown(f"**{cat_name}** — ₹{spent:.2f} ({percentage:.1f}%)")
                    st.progress(int(percentage))
            else:
                st.info("No spending recorded yet.")


# --- TAB 2: TRANSACTIONS ---
with tab_transactions:
    st.subheader("Record Transaction")
    cat_options = list(active_data.keys())
    
    default_index = 0
    if st.session_state.focus_category in cat_options:
        default_index = cat_options.index(st.session_state.focus_category)
        
    with st.container(border=True):
        action = st.radio("Transaction Type", ["Deposit", "Withdraw", "Transfer"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_cat = st.selectbox("Source Category", cat_options, index=default_index)
            
            target_cat = None
            if action == "Transfer":
                target_options = [cat for cat in cat_options if cat != selected_cat]
                if not target_options:
                    st.warning("Requires a second category for transfer.")
                else:
                    target_cat = st.selectbox("Target Category", target_options)
            else:
                desc = st.text_input("Description (Optional)")
                
        with col2:
            amount = st.number_input("Amount (₹)", value=1.0, step=100.0, format="%.2f")
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit_col, _ = st.columns([1, 4])
        with submit_col:
            submit_btn = st.button("Submit", use_container_width=True)
            
        if submit_btn:
            try:
                cat_obj = active_data[selected_cat]
                st.session_state.focus_category = selected_cat
                
                if action == "Deposit":
                    cat_obj.deposit(amount, desc)
                    st.toast("Deposit successful.")
                    
                elif action == "Withdraw":
                    cat_obj.withdraw(amount, desc)
                    st.toast("Withdrawal successful.")
                    
                elif action == "Transfer":
                    if not target_cat:
                        st.error("Target category is missing.")
                    else:
                        receiver_obj = active_data[target_cat]
                        cat_obj.transfer(amount, receiver_obj)
                        st.toast("Transfer successful.")
                        
            except ValueError as ve:
                st.error(str(ve))
            except InsufficientFundsError as ife:
                st.error(str(ife))


# --- TAB 3: DATA MANAGEMENT ---
with tab_data:
    col_data_left, col_data_right = st.columns(2)
    
    with col_data_left:
        with st.container(border=True):
            st.subheader("New Category")
            st.markdown("Add a new category to your ledger.")
            available_presets = [c for c in PRESET_CATEGORIES if c not in active_data]
            preset_options = available_presets + ["Custom..."] if available_presets else ["Custom..."]
            
            selection = st.selectbox(
                "Category Selection",
                options=preset_options,
                key="manage_preset"
            )
            if selection == "Custom...":
                add_cat = st.text_input("Category Name", placeholder="e.g., Subscriptions", key="manage_custom").strip()
            else:
                add_cat = selection

            if st.button("Create", use_container_width=True):
                if add_cat and add_cat not in active_data:
                    st.session_state.categories[add_cat] = Category(add_cat)
                    st.session_state.focus_category = add_cat
                    st.toast(f"Category '{add_cat}' created.")
                    st.rerun()
                elif add_cat in active_data:
                    st.error("Category already exists.")
                    
        with st.container(border=True):
            st.subheader("Factory Reset")
            st.markdown("Permanently delete all local session data.")
            with st.popover("Wipe Ledger", use_container_width=True):
                st.markdown("⚠️ **Are you sure?** This cannot be undone.")
                if st.button("Confirm Wipe", type="primary", use_container_width=True):
                    st.session_state.categories = {}
                    st.rerun()
                    
        with st.container(border=True):
            st.subheader("Sample Data")
            st.markdown("Reset your session with pre-configured categories and transactions.")
            with st.popover("Load Sample Data", use_container_width=True):
                st.markdown("⚠️ **Warning:** This will overwrite your current ledger entries.")
                if st.button("Confirm Overwrite", type="primary", use_container_width=True):
                    st.session_state.categories = generate_sample_ledger()
                    st.rerun()
                
    with col_data_right:
        with st.container(border=True):
            st.subheader("Export")
            st.markdown("Save your ledger locally.")
            json_data = export_ledger(active_data)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name="ledger.json",
                mime="application/json",
                use_container_width=True
            )
            
        with st.container(border=True):
            st.subheader("Import")
            st.markdown("Overwrite current session with a saved ledger.")
            uploaded_file = st.file_uploader("Upload JSON file", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                if st.button("Confirm Import", use_container_width=True):
                    try:
                        json_string = uploaded_file.getvalue().decode("utf-8")
                        st.session_state.categories = import_ledger(json_string)
                        st.toast("Ledger imported successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to import ledger: {e}")
