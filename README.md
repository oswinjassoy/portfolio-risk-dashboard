# Portfolio Risk Dashboard

A Python dashboard for analysing portfolio performance, comparing returns against the S&P 500, and measuring investment risk.

## Features
- Portfolio allocation and performance analysis
- S&P 500 benchmark comparison
- Annualised volatility and maximum drawdown
- Daily 95% Value at Risk (VaR)
- Sharpe Ratio and rolling Sharpe Ratio
- Asset correlation heatmap

## Technologies
- Python
- Streamlit
- Pandas
- yfinance
- Plotly

## How to Run

1. Clone or download this repository.
2. Open a terminal and navigate to the project folder.
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the required packages:

   ```bash
   pip install streamlit pandas yfinance plotly
   ```

5. Run the dashboard:

   ```bash
   python3 -m streamlit run app.py
   ```

## Disclaimer

This project is for educational purposes and is not financial advice.

