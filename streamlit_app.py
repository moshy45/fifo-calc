import streamlit as st
import pandas as pd
from collections import deque

st.title("FIFO Transaction Gain/Loss Calculator")
with st.sidebar:
    st.markdown("""
        This tool helps you calculate gain/loss using the FIFO method on your financial product transactions.

        ### Usage
        Please get and upload an Excel/CSV file from your financial institution with records of all historical transactions.   
        Your file must contain a columns with a header for each of the following: Date, Transaction Type, Quantity, Price, and a unique Identifier for the product. 
        
        Sales with no recorded purchase will be marked as 'Unknown'.


        ### Date Format Help
        Use Python datetime formatting:
        - `%Y-%m-%d` → 2024-07-18
        - `%d/%m/%Y` → 18/07/2024
        - `%m-%d-%Y` → 07-18-2024

        [See full format reference](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    """)
    st.markdown("---")
    st.markdown(
        '<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp by <a href="https://twitter.com/_mbernstein">@_mbernstein</a></h6>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin-top: 0.75em;"><a href="https://coff.ee/mbernstein" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("*This tool was created for your convenience, the creator accepts no responsibility for the accuracy of the results. Your data is never saved.*")

uploaded_file = st.file_uploader("Upload your transaction history (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Load data
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df = df.dropna(how='all')  # Drop rows where all elements are NaN
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        st.stop()

    if df.empty or len(df.columns) < 4:
        st.error("Uploaded file must contain at least four columns of data.")
        st.stop()

    st.write("Sample of uploaded data:")
    st.dataframe(df.head())

    # Column mapping
    st.subheader("Map your columns")
    date_col = st.selectbox("Date column", df.columns)
    type_col = st.selectbox("Transaction type column (Buy/Sell)", df.columns)
    qty_col = st.selectbox("Quantity column", df.columns)
    price_col = st.selectbox("Price per unit column", df.columns)
    id_col = st.selectbox("Identifier column", df.columns)
    currency_col = st.selectbox("Currency column (optional)", ['<None>'] + list(df.columns))
    extra_id_cols = st.multiselect("Additional identification columns (e.g., Ticker, Name)", df.columns)

    # Check for missing values in selected columns
    required_cols = [id_col, date_col, type_col, qty_col, price_col]
    if currency_col != '<None>':
        required_cols.append(currency_col)
    required_cols += extra_id_cols

    missing_rows = df[required_cols].isnull().any(axis=1)
    num_missing = missing_rows.sum()
    if num_missing > 0:
        st.markdown(f"<span style='color:red'>Warning: {num_missing} row(s) have missing values in the selected columns and will be skipped.</span>", unsafe_allow_html=True)
        df = df[~missing_rows]

    # Rounding option
    round_gains = st.checkbox("Round output Gain/Loss to 2 decimal places", True)

    # Date format options
    st.subheader("Date Format Options")
    input_date_format = st.text_input("Input date format (leave blank to auto-detect)", value="")
    output_date_format = st.text_input("Output date format (e.g. %Y-%m-%d)", value="%Y-%m-%d")

    # Transaction values
    st.subheader("Define Buy and Sell values")
    try:
        unique_values = df[type_col].dropna().unique().tolist()
    except Exception as e:
        st.error(f"Error accessing transaction type values: {e}")
        st.stop()

    buy_vals = st.multiselect("Values representing a Buy", unique_values)
    sell_vals = st.multiselect("Values representing a Sell", unique_values)

    if not buy_vals or not sell_vals:
        st.error("Please select at least one Buy and one Sell transaction type.")
        st.stop()

    if st.button("Run FIFO Calculation"):
        try:
            if input_date_format:
                df[date_col] = pd.to_datetime(df[date_col], format=input_date_format, errors='coerce')
            else:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

            df = df.sort_values(by=date_col)
            df['Identifier'] = df[id_col]
            
            has_currency = currency_col != '<None>'
            if has_currency:
                df['Currency'] = df[currency_col]
            else:
                df['Currency'] = 'N/A'

            results = []

            for (identifier, currency), group in df.groupby(['Identifier', 'Currency']):
                fifo_queue = deque()
                for _, row in group.iterrows():
                    try:
                        date = row[date_col]
                        t_type = row[type_col]
                        qty = abs(float(row[qty_col].replace(',', '') if isinstance(row[qty_col], str) else row[qty_col]))
                        price = float(row[price_col].replace(',', '') if isinstance(row[price_col], str) else row[price_col])
                    except Exception as e:
                        st.warning(f"Skipping row due to invalid data: {e}")
                        continue

                    identifiers = {col: row[col] for col in extra_id_cols}

                    if t_type in buy_vals:
                        fifo_queue.append([qty, price, date])
                    elif t_type in sell_vals:
                        sell_qty = qty
                        total_gain = 0
                        lots = []

                        while sell_qty > 0:
                            if fifo_queue:
                                buy_qty, buy_price, buy_date = fifo_queue[0]
                                used_qty = min(sell_qty, buy_qty)
                                gain = used_qty * (price - buy_price)
                                if round_gains:
                                    gain = round(gain, 2)
                                total_gain += gain
                                lots.append((used_qty, buy_price, buy_date, price, gain))

                                if used_qty == buy_qty:
                                    fifo_queue.popleft()
                                else:
                                    fifo_queue[0][0] -= used_qty
                            else:
                                used_qty = sell_qty
                                gain = 'Unknown'
                                lots.append((used_qty, 'Unknown', 'Unknown', price, gain))

                            sell_qty -= used_qty

                        results.append({
                            'Date': date,
                            'Identifier': identifier,
                            'Currency': currency,
                            'Sell Price': price,
                            'Sell Qty': qty,
                            'Gain/Loss': total_gain if isinstance(total_gain, (int, float)) else 'Unknown',
                            'Matched Lots': lots,
                            **identifiers
                        })
        except Exception as e:
            st.error(f"An error occurred during FIFO calculation: {e}")
            st.stop()

        # Expand lots to show in output
        expanded_results = []
        for row in results:
            for lot in row['Matched Lots']:
                base = {
                    'Identifier': row['Identifier'],
                    'Buy Date': lot[2].strftime(output_date_format) if isinstance(lot[2], pd.Timestamp) else lot[2],
                    'Buy Price': lot[1],
                    'Sell Date': row['Date'].strftime(output_date_format) if pd.notnull(row['Date']) else 'Invalid Date',
                    'Sell Price': row['Sell Price'],
                    'Sell Qty': row['Sell Qty'],
                    'Used Qty': lot[0],
                    'Gain/Loss': lot[4]
                }
                if has_currency:
                    base['Currency'] = row['Currency']
                for col in extra_id_cols:
                    base[col] = row.get(col, '')
                expanded_results.append(base)

        results_df = pd.DataFrame(expanded_results)

        # Show results
        st.subheader("FIFO Gain/Loss Results")
        st.dataframe(results_df)

        csv = results_df.to_csv(index=False)
        st.download_button("Download Results as CSV", csv, "fifo_results.csv", "text/csv")
