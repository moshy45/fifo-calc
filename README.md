# Streamlit - Financial Transaction FIFO Gain/Loss Calculator 

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fifo-calc.streamlit.app)

## Usage
Please get and upload an Excel/CSV file from your financial institution with records of all historical transactions.   
Your file must contain a columns with a header for each of the following: Date, Transaction Type, Quantity, Price, and a unique Identifier for the product. 

Sales with no recorded purchase will be marked as 'Unknown'.


### Date Format Help
Use Python datetime formatting:
- `%Y-%m-%d` → 2024-07-18
- `%d/%m/%Y` → 18/07/2024
- `%m-%d-%Y` → 07-18-2024

[See full format reference](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)


*This tool was created for your convenience, the creator accepts no responsibility for the accuracy of the results.*