import pandas as pd
import numpy as np
import streamlit as st
from scipy.stats import norm
import plotly.express as px
import plotly.graph_objs as go


st.set_page_config(page_title='VaR DeFi Fund Composition', layout='wide')

# Custom CSS
custom_css = """
<style>
    body {
        background-color: #F5F5F5;
        color: #333333;
    }
    .sidebar .sidebar-content {
        background-color: #F5F5F5;
        color: #333333;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2E4053;
    }
    .stProgress > div > div > div > div {
        background-color: #2E4053;
    }
    .stSlider > div > div > div:nth-child(2) > div {
        background-color: #2E4053;
    }
    .stButton > button {
        background-color: #2E4053;
        border: none;
        color: #FFFFFF;
    }
    .stButton > button:hover {
        background-color: #1A2734;
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 2px rgba(46, 64, 83, 0.6);
    }
</style>
"""
# Custom CSS for table
custom_table_css = """
<style>
    .dataframe {
        color: #333333;
        font-family: Arial, sans-serif;
        font-size: 1rem;
        border-collapse: collapse;
        border-spacing: 0;
    }
    .dataframe th {
        text-align: left;
        background-color: #2E4053;
        color: #FFFFFF;
        font-weight: bold;
        border: 1px solid #d9d9d9;
        padding: 0.5rem;
    }
    .dataframe td {
        border: 1px solid #d9d9d9;
        padding: 0.5rem;
    }
    .dataframe tr:nth-child(even) {
        background-color: #F2F2F2;
    }
    .dataframe tr:hover {
        background-color: #D5D5D5;
    }
</style>
"""

st.markdown(custom_table_css, unsafe_allow_html=True)

st.markdown(custom_css, unsafe_allow_html=True)

# # Custom CSS
# custom_css = """
# <style>
#     /* Add your custom CSS here */
# </style>
# """
#
# st.markdown(custom_css, unsafe_allow_html=True)

st.title("Test DeFi Fund Composition")

# Load daily returns data
daily_returns = pd.read_csv("daily_returns.csv", index_col=0)

# Get available assets
assets = daily_returns.columns

with st.sidebar:
    st.header("Select Assets and Weights")

    # Initialize portfolio dictionary
    portfolio = {}

    # Allow user to select assets
    selected_assets = st.multiselect("Select assets:", options=list(assets))

    # Allow user to assign weights to selected assets
    weights = {}

    try:
        for asset in selected_assets:
            max_value = max(0, 100 - int(sum(weights.values())))
            if max_value > 0:
                weight = st.slider(f"{asset} weight (%)", 0, max_value)
                if weight >= 0:
                    weights[asset] = weight
            else:
                st.warning("Cannot assign more weights. The sum of weights is already 100%.")
    except:
        st.warning("Cannot assign more weights. The sum of weights is already 100%. Change weights!")

# Add unallocated cash to portfolio
portfolio["cash"] = 100 - int(sum(weights.values()))

# Risk parity optimization
def risk_parity_optimizer(returns):
    cov_matrix = returns.cov()
    inverse_volatility = 1 / np.sqrt(np.diag(cov_matrix))
    risk_parity_weights = inverse_volatility / np.sum(inverse_volatility)
    return risk_parity_weights

# Calculate VaR
def calculate_var(returns, weights, confidence_level=0.99):
    portfolio_returns = returns.dot(weights)
    var = -np.percentile(portfolio_returns, 100 * (1 - confidence_level))
    return round(var * 100, 2)

if sum(weights.values()) == 100:
    try:
        weights_vector = [weights[asset] / 100 for asset in assets if asset in selected_assets]

        selected_daily_returns = daily_returns[selected_assets]
        var = calculate_var(selected_daily_returns, weights_vector)
        st.markdown(
            f"Initial Portfolio has a 95% chance of not losing Total Value Locked more than <span style='color: red; font-weight: bold;'>{var}%</span> of its value.",
            unsafe_allow_html=True)

        # st.write(f"Initial Portfolio has a 95% chance of not losing more than {var}% of its value.")
    except:
        st.warning("Cannot assign more weights. The sum of weights is already 100%. Change weights!")

if st.button("Optimize Portfolio using Risk Parity approach"):
    try:
        risk_parity_weights = risk_parity_optimizer(daily_returns[selected_assets])

        weights = {asset: weight * 100 for asset, weight in zip(selected_assets, risk_parity_weights)}
    except:
        st.error("Please, decrease a portion of the previous Protocols or delete the last one")
        st.stop()

    portfolio.update(weights)
    portfolio["cash"] = 0

    try:
        weights_vector = [weights[asset] / 100 for asset in assets if asset in selected_assets]
    except:
        st.error("Please, decrease a portion of the previous Protocols or delete the last one")
        st.stop()

    selected_daily_returns = daily_returns[selected_assets]
    var = calculate_var(selected_daily_returns, weights_vector)
    st.markdown(
        f"Optimized Portfolio has a 95% chance of not losing Total Value Locked more than <span style='color: red; font-weight: bold;'>{var}%</span> of its value.",
        unsafe_allow_html=True)
    # st.write(f"Optimized Portfolio VaR at 95% confidence level: {var}%")

    # Display weights, VaR and a pie chart
    data = {
        "Asset": list(weights.keys()),
        "Weight (%)": list(weights.values()),
        "Value at Risk (%)": [var] * len(weights)
    }
    df = pd.DataFrame(data)
    st.dataframe(df)

    # st.write(df)

    # fig = px.pie(df, values="Weight (%)", names="Asset", title="Portfolio Allocation")
    # st.plotly_chart(fig)
    # Pie chart
    fig = go.Figure(go.Pie(labels=list(weights.keys()),
                           values=list(weights.values()),
                           hole=.3,
                           pull=[0.1 if asset == max(weights, key=weights.get) else 0 for asset in weights],
                           textinfo='label+percent',
                           marker=dict(line=dict(color='#000000', width=2))))

    fig.update_layout(title='Portfolio Allocation',
                      font=dict(family='Arial', size=14, color='#333333'),
                      legend=dict(orientation='h', yanchor='bottom', xanchor='center', y=-0.1, x=0.5))

    st.plotly_chart(fig)

else:
    st.warning("Please allocate the remaining cash to assets.")
