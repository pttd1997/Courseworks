import streamlit as st
import seaborn as sns
import pandas as pd
import random
import matplotlib.pyplot as plt

# Function to ensure required columns exist
def preprocess_data(data):
    if 'transaction_qty' not in data.columns:
        data['transaction_qty'] = random.choices(range(1, 10), k=len(data))
    if 'unit_price' not in data.columns:
        data['unit_price'] = random.choices(range(10, 100), k=len(data))
    if 'Revenue' not in data.columns:
        data['Revenue'] = data['transaction_qty'] * data['unit_price']
    if 'product_id' not in data.columns:
        data['product_id'] = [f"P{i:03d}" for i in range(len(data))]
    if 'transaction_date' not in data.columns:
        data['transaction_date'] = pd.date_range(start='2022-01-01', periods=len(data))
    if 'customer_id' not in data.columns:
        data['customer_id'] = [f"CUST-{i:03d}" for i in range(len(data))]
    if 'customer_name' not in data.columns:
        first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Fay", "Grace", "Hank", "Ivy", "Jack"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        data['customer_name'] = [
            f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(len(data))
        ]
    return data

# Function to perform ABC Analysis
def abc_analysis(data):
    product_sales = (
        data.groupby('product_id')
        .agg({'Revenue': 'sum'})
        .reset_index()
        .sort_values(by='Revenue', ascending=False)
    )
    product_sales['Cumulative_Percentage'] = product_sales['Revenue'].cumsum() / product_sales['Revenue'].sum() * 100
    product_sales['ABC_Class'] = product_sales['Cumulative_Percentage'].apply(
        lambda x: 'A' if x <= 70 else 'B' if x <= 90 else 'C'
    )
    return product_sales

# Function to perform FRM Analysis
def frm_analysis(data):
    data['transaction_date'] = pd.to_datetime(data['transaction_date'], errors='coerce')
    reference_date = data['transaction_date'].max()
    frm = (
        data.groupby('customer_id')
        .agg({
            'transaction_date': lambda x: (reference_date - x.max()).days,
            'transaction_id': 'count' if 'transaction_id' in data.columns else lambda x: len(x),
            'Revenue': 'sum',
        })
        .reset_index()
        .rename(columns={'transaction_date': 'Recency', 'transaction_id': 'Frequency', 'Revenue': 'Monetary'})
    )

    # Segment Customers Based on FRM
    recency_bins = [0, 1, 7, 30, frm['Recency'].max() + 1]
    frm['Recency_Group'] = pd.cut(frm['Recency'], bins=recency_bins, labels=["Very Recent", "Recent", "Less Recent", "Old"], right=False)

    frequency_bins = [0, 1, 2, 5, float('inf')]
    frm['Frequency_Group'] = pd.cut(frm['Frequency'], bins=frequency_bins, labels=["Low", "Medium", "High", "Very High"], right=False)

    monetary_bins = [0, 50, 100, 500, float('inf')]
    frm['Monetary_Group'] = pd.cut(frm['Monetary'], bins=monetary_bins, labels=["Low", "Medium", "High", "Very High"], right=False)

    return frm

# Function to plot sales trends
def plot_sales_trends(data, period):
    data['transaction_date'] = pd.to_datetime(data['transaction_date'], errors='coerce')
    data = data.dropna(subset=['transaction_date'])
    data = data.sort_values(by='transaction_date')

    if period == 'Daily':
        sales = data.resample('D', on='transaction_date')['Revenue'].sum()
    elif period == 'Weekly':
        sales = data.resample('W', on='transaction_date')['Revenue'].sum()
    elif period == 'Monthly':
        sales = data.resample('M', on='transaction_date')['Revenue'].sum()

    fig, ax = plt.subplots()
    sales.plot(ax=ax)
    ax.set_title(f'{period} Sales Trend')
    ax.set_xlabel('Date')
    ax.set_ylabel('Revenue')
    return fig

# App Title
st.title("☕ Dynamic Coffee Shop Analysis Dashboard")

# File Uploader
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    data = preprocess_data(data)

    st.sidebar.title("Analysis Options")
    analysis_option = st.sidebar.radio(
        "Choose an analysis", ["Data Overview", "ABC Analysis", "FRM Analysis", "Generate Report"]
    )

    if analysis_option == "Data Overview":
        st.subheader("Uploaded Data Preview")
        st.write(data.head())
        st.subheader("Data Summary")
        st.write(data.describe())

        st.subheader("Filter Data")
        columns = data.columns.tolist()
        selected_column = st.selectbox("Select column to filter by", columns)
        unique_values = data[selected_column].unique()
        selected_value = st.selectbox("Select value", unique_values)
        filtered_df = data[data[selected_column] == selected_value]
        st.write(filtered_df)

        # Plot sales trends
        st.subheader("Sales Trends")
        period = st.selectbox("Select time period:", ["Daily", "Weekly", "Monthly"], index=0)
        fig = plot_sales_trends(data, period)
        st.pyplot(fig)

    elif analysis_option == "ABC Analysis":
        st.subheader("ABC Analysis")
        abc_results = abc_analysis(data)
        st.write(abc_results)

        st.write("### Category Distribution")  # Display summary
        st.write(abc_results['ABC_Class'].value_counts())

        st.write("### ABC Distribution Bar Chart")           # Add bar chart for ABC distribution
        abc_distribution = abc_results['ABC_Class'].value_counts()
        fig, ax = plt.subplots()
        abc_distribution.plot(kind='bar', ax=ax, color=['green', 'orange', 'red'])
        ax.set_title('ABC Category Distribution')
        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        st.pyplot(fig)

        st.write("### Top 5 Products by Revenue")
        top_5_products = abc_results.head(5)
        st.bar_chart(top_5_products.set_index('product_id')['Revenue'])
        
    elif analysis_option == "FRM Analysis":
        st.subheader("FRM Analysis")
        frm_results = frm_analysis(data)
        st.write(frm_results)

        # Segment Customers Based on FRM
        st.write("### Customer Segments")
        segment_counts = frm_results[['Recency_Group', 'Frequency_Group', 'Monetary_Group']].apply(pd.Series.value_counts).fillna(0)
        st.write(segment_counts)

        # Visualize Recency, Frequency, and Monetary Segments
        st.write("### Visualizing Recency, Frequency, and Monetary Segments")
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))

        frm_results['Recency_Group'].value_counts().plot(kind='bar', ax=axs[0], color='skyblue')
        axs[0].set_title('Recency Distribution')
        axs[0].set_xlabel('Recency Group')
        axs[0].set_ylabel('Count')

        frm_results['Frequency_Group'].value_counts().plot(kind='bar', ax=axs[1], color='orange')
        axs[1].set_title('Frequency Distribution')
        axs[1].set_xlabel('Frequency Group')
        axs[1].set_ylabel('Count')

        frm_results['Monetary_Group'].value_counts().plot(kind='bar', ax=axs[2], color='green')
        axs[2].set_title('Monetary Distribution')
        axs[2].set_xlabel('Monetary Group')
        axs[2].set_ylabel('Count')

        st.pyplot(fig)

        # Financial Risk Management Analysis
        st.header('Financial Risk Management (FRM) Analysis')
        confidence_level = st.slider('Select Confidence Level:', 0.90, 0.99, 0.95)
        VaR = frm_results['Monetary'].quantile(1 - confidence_level)
        st.write(f'Value at Risk (VaR) at {confidence_level*100}% confidence level:', VaR)

        st.write('Historical Value at Risk (VaR):')
        rolling_VaR = frm_results['Monetary'].rolling(window=30).quantile(1 - confidence_level)
        fig, ax = plt.subplots()
        ax.plot(rolling_VaR, label=f'{confidence_level*100}% VaR')
        ax.set_title('Historical Value at Risk (VaR)')
        ax.legend()
        st.pyplot(fig)

        st.write('Return Distribution:')
        fig, ax = plt.subplots()
        sns.histplot(frm_results['Monetary'], bins=20, kde=True, ax=ax)
        ax.set_title('Return Distribution')
        st.pyplot(fig)

    
    elif analysis_option == "Generate Report":
        st.title("Coffee Shop Analysis Report 🌿")
        st.markdown("---")

        # Perform ABC and FRM analyses
        abc_results = abc_analysis(data)
        frm_results = frm_analysis(data)

        # Overview Section
        st.header("Overview")
        st.write(
            """
            This report provides an in-depth analysis of sales performance (ABC Analysis) 
            and customer behavior (FRM Analysis). The goal is to optimize inventory, 
            boost revenue, and enhance customer retention strategies.
            """
        )
        st.markdown("---")

        # ABC Analysis Section
        st.header("ABC Analysis Summary")
        st.markdown("### 🥤🧋🍵 Product Analysis")
        top_category = abc_results['ABC_Class'].value_counts().idxmax()
        st.metric("Top Category", f"Category {top_category}")
        st.metric("Total Products Analyzed", len(abc_results))
        st.write("### Category Distribution")
        st.bar_chart(abc_results['ABC_Class'].value_counts())
        st.write("### Top 5 Products by Revenue")
        if 'product_name' in abc_results.columns:
            st.write(
                abc_results[['product_name', 'Revenue']]
                .head(5)
                .style.format({"Revenue": "${:,.2f}"})
                .to_html(),
                unsafe_allow_html=True,
            )
        else:
            st.write(abc_results.head(5).to_string(index=False))
        st.info("🌟**Recommendation:** Focus on Category 'A' products for revenue growth and optimize inventory for Category 'C' products.")
        st.markdown("---")

        # FRM Analysis Section
        st.header("FRM Analysis Summary")
        st.markdown("### 📈 Customer Analysis")
        high_value_customers = frm_results[frm_results['Monetary'] > 500]
        st.metric("Total Customers Analyzed", len(frm_results))
        st.metric("High-Value Customers", len(high_value_customers))
        st.write("#### Recency Groups")
        st.bar_chart(frm_results['Recency_Group'].value_counts())
        st.write("#### Frequency Groups")
        st.bar_chart(frm_results['Frequency_Group'].value_counts())
        st.write("#### Monetary Groups")
        st.bar_chart(frm_results['Monetary_Group'].value_counts())
        st.write("### Top 5 High-Value Customers")
        st.write(high_value_customers.nlargest(5, 'Monetary').to_string(index=False))
        st.warning("🌟**Key Insight:** Retain high-value customers with targeted loyalty programs and promotions.")
        st.markdown("---")

        # Recommendations Section
        st.header("Overall Recommendations")
        st.markdown(
            """
            1. Focus on high-revenue Category 'A' products and reduce overstocking of 'C' products.
            2. Retain high-value customers through loyalty rewards.
            3. Use targeted campaigns for customers in the 'Very Recent' and 'Very High' frequency groups.
            4. Regularly update ABC and FRM analyses to adapt to dynamic business needs.
            """
        )
        st.success("This report is designed to help you make data-driven decisions to optimize performance.")
    
    else:
        st.write("Waiting for file upload...")

