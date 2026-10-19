
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(
    page_title="Portfolio Risk Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("Portfolio Risk Dashboard")
st.subheader("Portfolio Summary")
st.write("An overview of portfolio performance against the S&P 500 benchmark.")
st.caption("Portfolio Performance | Benchmark Analysis")

# Hypothetical £10,000 portfolio
portfolio = pd.DataFrame({
    "Asset": ["Apple", "Microsoft", "NVIDIA", "S&P 500 ETF", "US Treasury ETF"],
    "Ticker": ["AAPL", "MSFT", "NVDA", "SPY", "IEF"],
    "Investment (£)": [2000, 2500, 1500, 2500, 1500]
})

total_value = portfolio["Investment (£)"].sum()
portfolio["Weight (%)"] = portfolio["Investment (£)"] / total_value * 100



def compute_performance(prices, holdings, invested):
    """Build return, benchmark and risk metrics from downloaded prices."""
    if prices is None or prices.empty:
        return None

    if "^GSPC" not in prices.columns:
        return None

    weights = holdings.set_index("Ticker")["Investment (£)"] / invested
    missing = [ticker for ticker in weights.index if ticker not in prices.columns]

    if missing or "^GSPC" not in prices.columns:
        return None

    prices = prices.dropna(subset=list(weights.index) + ["^GSPC"])

    if len(prices) < 2:
        return None

    # Normalise each asset to its starting price.
    asset_growth  = prices[weights.index].div(prices[weights.index].iloc[0])
    portfolio_growth = asset_growth.dot(weights)

    # Normalise the benchmark to the same starting value.
    benchmark_growth = prices["^GSPC"] / prices["^GSPC"].iloc[0]

    # Calculate daily returns for risk metrics.
    portfolio_returns = portfolio_growth.pct_change().dropna()
    
    rolling_mean = portfolio_returns.rolling(252).mean()
    rolling_std = portfolio_returns.rolling(252).std()

    rolling_sharpe = (
    (rolling_mean * 252 - 0.04)
    / (rolling_std * (252 ** 0.5))
)
    if portfolio_returns.empty:
        return None

    daily_volatility = portfolio_returns.std()

    risk_free_rate = 0.04
    annualised_return = (1 + portfolio_returns.mean()) ** 252 - 1
    annualised_std = portfolio_returns.std() * (252 ** 0.5)

    sharpe_ratio = (
        (annualised_return - risk_free_rate) / annualised_std
    if annualised_std != 0 else 0
)

    running_peak = portfolio_growth.cummax()
    drawdown = portfolio_growth / running_peak - 1

    portfolio_return = (portfolio_growth.iloc[-1] - 1) * 100
    benchmark_return = (benchmark_growth.iloc[-1] - 1) * 100

    return {
        "sharpe_ratio": sharpe_ratio,
        "rolling_sharpe": rolling_sharpe,
        "portfolio_return": portfolio_return,
        "benchmark_return": benchmark_return,
        "relative_performance": portfolio_return - benchmark_return,
        "annualised_volatility": daily_volatility * (252 ** 0.5),
        "max_drawdown": drawdown.min(),
        "daily_var_95": portfolio_returns.quantile(0.05),
        "comparison": pd.DataFrame({
            "Portfolio": (portfolio_growth - 1) * 100,
            "S&P 500": (benchmark_growth - 1) * 100,
        }),
        "correlation": prices[weights.index].pct_change().dropna().corr(),
    }

analysis = None
if (
    st.session_state.get("analysis_ready")
    and "market_prices" in st.session_state
):
    analysis = compute_performance(
        st.session_state["market_prices"],
        portfolio,
        total_value,
    )

st.subheader("Portfolio Summary")
sum1, sum2, sum3, sum4 = st.columns(4)

sum1.metric("Total Invested", f"£{total_value:,.0f}")

if analysis is not None:
    sum2.metric("Portfolio Return", f"{analysis['portfolio_return']:.2f}%")
    sum3.metric("S&P 500 Return", f"{analysis['benchmark_return']:.2f}%")
    sum4.metric(
        "Relative Performance",
        f"{analysis['relative_performance']:+.2f} pp"
    )
else:
    awaiting = "Awaiting market data"
    sum2.metric("Portfolio Return", awaiting)
    sum3.metric("S&P 500 Return", awaiting)
    sum4.metric("Relative Performance", awaiting)
    st.caption(
        "Total invested is based on the hypothetical £10,000 portfolio. "
        "Return metrics require market data — click **Run Performance Analysis** below."
    )

col1, col2 = st.columns(2)
col1.metric("Initial Portfolio Value", f"£{total_value:,.0f}")
col2.metric("Number of Holdings", len(portfolio))

st.subheader("Portfolio Allocation")
fig = px.pie(
    portfolio,
    names="Asset",
    values="Investment (£)",
    hole=0.45
)
st.plotly_chart(fig, use_container_width=True)




st.subheader("Portfolio vs S&P 500 Benchmark")

period_options = {
    "1 Year": "1y",
    "2 Years": "2y",
    "3 Years": "3y",
    "4 Years": "4y",
    "5 Years": "5y",
}

selected_period = st.selectbox(
    "Historical analysis period",
    options=list(period_options.keys()),
    index=2,
    key="historical_period",
)

if st.button("Run Performance Analysis"):
    with st.spinner("Downloading market data..."):
        tickers = portfolio["Ticker"].tolist() + ["^GSPC"]

        data = yf.download(
            tickers,
            period=period_options[selected_period],
            auto_adjust=True,
            progress=False,
        )

        if data.empty:
            st.session_state["analysis_ready"] = False
            st.session_state.pop("market_prices", None)
            st.error("Market data unavailable. Please try again.")

        else:
            prices = data["Close"].dropna()
            prices = prices.dropna(axis=0, how="any")

            if prices.empty or "^GSPC" not in prices.columns:
                st.session_state["analysis_ready"] = False
                st.session_state.pop("market_prices", None)
                st.error("Could not retrieve all required prices.")

            else:
                analysis = compute_performance(
                    prices, portfolio, total_value
                )

                if analysis is None:
                    st.session_state["analysis_ready"] = False
                    st.session_state.pop("market_prices", None)
                    st.error(
                        "Could not calculate performance from the downloaded prices."
                    )

                else:
                    st.session_state["market_prices"] = prices
                    st.session_state["analysis_ready"] = True
                    st.session_state["selected_period_label"] = selected_period
                    st.rerun()


if st.session_state.get("analysis_ready", False):
    st.caption(
        f"Historical period: "
        f"{st.session_state.get('selected_period_label', 'Selected period')} "
        f"| Data from "
        f"{st.session_state['market_prices'].index.min().date()} "
        f"to {st.session_state['market_prices'].index.max().date()}"
    )

if analysis is not None:
    fig = px.line(
        analysis["comparison"],
        labels={
            "value": "Return (%)",
            "index": "Date",
            "variable": "Investment",
        },
        title="Cumulative Return: Portfolio vs Benchmark",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Portfolio Risk Metrics")

    risk1, risk2, risk3, risk4 = st.columns(4)

    risk1.metric(
        "Annualised Volatility",
        f"{analysis['annualised_volatility'] * 100:.2f}%"
    )

    risk2.metric(
        "Maximum Drawdown",
        f"{analysis['max_drawdown'] * 100:.2f}%"
    )

    risk3.metric(
        "Daily 95% VaR",
        f"{analysis['daily_var_95'] * 100:.2f}%"
    )
    risk4.metric(
        "Sharpe Ratio",
        f"{analysis['sharpe_ratio']:.2f}"
)
    st.subheader("Rolling Sharpe Ratio")

    fig_rolling = px.line(
        analysis["rolling_sharpe"],
        title="252-Day Rolling Sharpe Ratio",
        labels={"value": "Sharpe Ratio", "index": "Date"},
    )

    fig_rolling.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig_rolling, use_container_width=True)
    st.subheader("Asset Correlation Heatmap")

    correlation = analysis["correlation"]

    fig_corr = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdYlGn",
        zmin=-1,
        zmax=1,
        title="Correlation Between Portfolio Assets",
    )

    st.plotly_chart(fig_corr, use_container_width=True)

             

st.subheader("Portfolio Stress Testing")
st.write("Model hypothetical market scenarios.")

scenario = st.selectbox(
        "Choose a scenario",
        [
            "Market correction",
            "Technology sell-off",
            "Recession",
        ],
        key="stress_scenario",
    )

shocks = {
        "Market correction": {
            "AAPL": -0.10,
            "MSFT": -0.10,
            "NVDA": -0.15,
            "SPY": -0.10,
            "IEF": 0.02,
        },
        "Technology sell-off": {
            "AAPL": -0.15,
            "MSFT": -0.20,
            "NVDA": -0.30,
            "SPY": -0.12,
            "IEF": 0.03,
        },
        "Recession": {
            "AAPL": -0.25,
            "MSFT": -0.25,
            "NVDA": -0.35,
            "SPY": -0.20,
            "IEF": 0.05,
        },
    }

scenario_returns = portfolio["Ticker"].map(shocks[scenario])
portfolio["Scenario Return (%)"] = scenario_returns * 100
portfolio["Scenario P/L (£)"] = (
        portfolio["Investment (£)"] * scenario_returns
    )

estimated_pnl = portfolio["Scenario P/L (£)"].sum()
stressed_value = total_value + estimated_pnl

stress1, stress2 = st.columns(2)
stress1.metric(
        "Estimated Gain / Loss",
        f"£{estimated_pnl:,.0f}"
    )
stress2.metric(
        "Stressed Portfolio Value",
        f"£{stressed_value:,.0f}"
    )

st.dataframe(
        portfolio[
            [
                "Asset",
                "Investment (£)",
                "Scenario Return (%)",
                "Scenario P/L (£)",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.caption(
        "Hypothetical shocks, not forecasts. Assumes fixed "
        "holdings and ignores correlations, trading costs, "
        "taxes and currency effects."
    )
st.subheader("Best and Worst Performing Holdings")

if st.session_state.get("analysis_ready", False):
    prices = st.session_state["market_prices"]
    asset_returns = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    holdings_returns = asset_returns.drop(
        labels=["^GSPC"], errors="ignore"
    ).sort_values(ascending=False)

    best_holdings = holdings_returns.head(2)
    worst_holdings = holdings_returns.tail(2).sort_values()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Best Performing Holdings**")
        for ticker, performance in best_holdings.items():
            st.metric(ticker, f"{performance:+.2f}%")

    with col2:
        st.markdown("**Worst Performing Holdings**")
        for ticker, performance in worst_holdings.items():
            st.metric(ticker, f"{performance:+.2f}%")


st.subheader("Individual Holding Returns")

if st.session_state.get("analysis_ready", False):
    st.bar_chart(holdings_returns)
    st.subheader("Risk Interpretation")

if st.session_state.get("analysis_ready", False):
    st.markdown("""
    **Annualised Volatility**  
    Measures how much portfolio returns fluctuate over time.
    Higher volatility generally means greater uncertainty.

    **Maximum Drawdown**  
    Shows the largest peak-to-trough decline during the
    period analysed.

    **Daily 95% Value at Risk (VaR)**  
    Estimates the daily loss threshold that the portfolio
    would be expected to exceed on approximately 5% of days,
    based on historical returns. This is not a maximum-loss limit.
    """)
