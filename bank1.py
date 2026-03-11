import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from fpdf import FPDF
import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Finance Dashboard", layout="wide")
# --- ABOUT THE PROJECT ---
with st.expander("ℹ️ About this Project & Key Features"):
    st.markdown("""
    ### 🚀 Key Features
    - **MoM Trend Tracking:** Automatically calculates percentage changes in spending.
    - **AI Forecasting:** Uses Linear Regression to predict future expenses.
    - **Financial Health Gauge:** Visualizes savings rates using Plotly.
    - **Automated Reporting:** Generates professional PDF audits for specific months.

    ### 🛠️ Tech Stack
    - **Python** (Pandas, Scikit-Learn)
    - **Streamlit** (UI & Deployment)
    - **Plotly** (Interactive Visualizations)
    - **FPDF** (Automated Report Generation)
    
    *Created by **Basit Ali** | Masters in Finance & Data Science*
    """)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    stMetric { border: 1px solid #30363d; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PDF GENERATION FUNCTION ---
def create_pdf(income, expense, balance, goal, df, month_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(200, 15, txt=f"Finance Audit: {month_name}", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Financial Summary", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Total Income:  Rs. {income:,.2f}", ln=True)
    pdf.cell(200, 8, txt=f"Total Expense: Rs. {expense:,.2f}", ln=True)
    pdf.cell(200, 8, txt=f"Net Balance:   Rs. {balance:,.2f}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Category Breakdown", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(90, 10, "Category", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Amount (Rs.)", 1, 1, 'C', 1)

    pdf.set_font("Arial", size=12)
    cat_totals = df[df['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
    for _, row in cat_totals.iterrows():
        pdf.cell(90, 10, str(row['Category']), 1)
        pdf.cell(60, 10, f"{row['Amount']:,.2f}", 1, 1, 'R')
        
    return pdf.output(dest='S').encode('latin-1')

# --- 3. SIDEBAR & FILE UPLOADER ---
st.sidebar.title("💳 Finance Settings")
uploaded_file = st.sidebar.file_uploader("Upload Practice CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.strftime('%B %Y')
    df['Day_Name'] = df['Date'].dt.day_name()
    df = df.sort_values('Date')

    # --- Month Selector ---
    month_list = list(df['Month'].unique())
    selected_month = st.sidebar.selectbox("Select Analysis Month", month_list, index=len(month_list)-1)
    
    # --- Budget Goal ---
    budget_goal = st.sidebar.slider("Monthly Budget Limit (₹)", 10000, 100000, 40000, 1000)

    # --- Filtered Data ---
    filtered_df = df[df['Month'] == selected_month].copy()
    total_income = filtered_df[filtered_df['Type'] == 'Income']['Amount'].sum()
    total_expense = filtered_df[filtered_df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense

    # --- Trend Indicator Calculation ---
    current_idx = month_list.index(selected_month)
    delta_val = None
    if current_idx > 0:
        prev_month = month_list[current_idx - 1]
        prev_exp = df[(df['Month'] == prev_month) & (df['Type'] == 'Expense')]['Amount'].sum()
        if prev_exp > 0:
            delta_val = ((total_expense - prev_exp) / prev_exp) * 100

    # --- 4. MAIN DASHBOARD ---
    st.title(f"📊 {selected_month} Insights")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Income", f"₹{total_income:,}")
    m2.metric("Expenses", f"₹{total_expense:,}", delta=f"{delta_val:.1f}%" if delta_val else None, delta_color="inverse")
    m3.metric("Net Balance", f"₹{balance:,}")

    # --- Savings Gauge ---
    st.markdown("---")
    savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = savings_rate,
        title = {'text': "Monthly Savings Rate %"},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#2ecc71"},
                 'steps': [{'range': [0, 20], 'color': "#ff4d4d"}, {'range': [20, 50], 'color': "#f1c40f"}, {'range': [50, 100], 'color': "#27ae60"}]}))
    fig_gauge.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["📈 Analysis", "🤖 AI Forecast", "📑 PDF Report"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Category Spend")
            fig_pie = px.pie(filtered_df[filtered_df['Type']=='Expense'], values='Amount', names='Category', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            st.subheader("Daily Intensity (Heatmap)")
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_data = df[df['Type'] == 'Expense'].groupby('Day_Name')['Amount'].sum().reindex(days_order).reset_index()
            fig_heat = px.bar(heatmap_data, x='Day_Name', y='Amount', color='Amount', color_continuous_scale='Reds')
            st.plotly_chart(fig_heat, use_container_width=True)

    with tab2:
        st.subheader("AI Future Spending Prediction")
        exp_only = df[df['Type'] == 'Expense'].copy()
        exp_only['Day_Num'] = (exp_only['Date'] - exp_only['Date'].min()).dt.days
        if len(exp_only) > 1:
            model = LinearRegression().fit(exp_only[['Day_Num']], exp_only['Amount'])
            prediction = model.predict([[exp_only['Day_Num'].max() + 7]])
            st.info(f"AI Prediction: Your next major expense is likely to be around **₹{prediction[0]:,.2f}**")
        else:
            st.warning("More data needed for AI analysis.")

    with tab3:
        st.subheader("Generate Statement")
        pdf_data = create_pdf(total_income, total_expense, balance, budget_goal, filtered_df, selected_month)
        st.download_button(label="📥 Download PDF Report", data=pdf_data, file_name=f"Report_{selected_month}.pdf", mime="application/pdf")

else:
    st.info("👋 Welcome Basit! Please upload your CSV file in the sidebar to begin.")

