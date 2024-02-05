import pandas as pd
import yfinance as yf

def get_ticker(company_name):
    try:
        search_results = yf.Ticker(company_name)
        # Assuming the first result is the most relevant
        if search_results and 'symbol' in search_results.info:
            return search_results.info['symbol']
        else:
            return ""
    except Exception:
        return ""

def main():
    # Load the CSV file
    file_path = 'data/majority_vote_ratings.csv'  # Replace with your CSV file path
    df = pd.read_csv(file_path)

    # Process each issuer name and get tickers
    df['issuer_name'] = df['issuer_name'].str.replace('"', '')  # Remove quotation marks
    df['Ticker'] = df['issuer_name'].apply(get_ticker)

    # Save the new CSV file
    new_file_path = 'tickers.csv'  # Replace with your desired output file path
    df.to_csv(new_file_path, index=False)

    print(f"File saved to {new_file_path}")

if __name__ == "__main__":
    main()