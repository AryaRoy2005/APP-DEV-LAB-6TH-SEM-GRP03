import yfinance as yf
import pandas as pd
import json
from collections import Counter
import os

def fetch_market_data(symbol="BTC-INR", period="max"):
    """
    Downloads historical market data from Yahoo Finance.
    """
    print(f"⏳ Downloading MAX history for {symbol}...")
    
    # Fetch unlimited history
    df = yf.download(symbol, period=period, interval="1h", progress=False)
    
    # Handle MultiIndex columns (fixes potential issues with newer yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.dropna()
    print(f"✅ Data Acquired: {len(df)} hours of trading history!")
    return df

def classify_market_event(row):
    """
    Classifies a trading hour based on percentage change.
    """
    if row['Open'] == 0: return "STABLE"

    change_pct = ((row['Close'] - row['Open']) / row['Open']) * 100

    if change_pct >= 1.5: return "PUMP_HUGE"
    elif change_pct >= 0.3: return "PUMP_SMALL"
    elif change_pct <= -1.5: return "DUMP_HUGE"
    elif change_pct <= -0.3: return "DUMP_SMALL"
    else: return "STABLE"

def mine_patterns(df):
    """
    Scans data for patterns and OVERWRITES the JSON file.
    """
    print("⚙️ Applying Smart Classification...")
    df['Event'] = df.apply(classify_market_event, axis=1)

    SEQUENCE_LENGTH = 3
    TARGET_PROFIT = 0.5  # 0.5% profit target
    sequences = []
    
    print(f"⏳ Scanning for patterns leading to {TARGET_PROFIT}% profit...")

    # Logic to find winning sequences
    for i in range(len(df) - SEQUENCE_LENGTH - 1):
        current_pattern = df['Event'].iloc[i : i + SEQUENCE_LENGTH].tolist()
        next_open = df['Open'].iloc[i + SEQUENCE_LENGTH + 1]
        next_close = df['Close'].iloc[i + SEQUENCE_LENGTH + 1]
        
        future_profit = 0
        if next_open > 0:
            future_profit = ((next_close - next_open) / next_open) * 100

        if future_profit >= TARGET_PROFIT:
            current_pattern.append("PROFIT_HIT")
            sequences.append(current_pattern)

    print(f"✅ Found {len(sequences)} winning trades.")

    if len(sequences) > 0:
        # Convert to string to count duplicates
        seq_strings = [json.dumps(seq) for seq in sequences]
        counts = Counter(seq_strings)

        golden_patterns = []
        
        # Keep top 50 patterns that appear at least 5 times
        for seq_str, count in counts.most_common(50):
            if count >= 5:
                full_seq = json.loads(seq_str)
                golden_patterns.append(full_seq[:-1]) # Remove 'PROFIT_HIT'

        # Save to JSON (Overwrite Mode)
        filename = 'golden_patterns.json'
        
        # 'w' mode truncates the file first, ensuring a clean overwrite
        with open(filename, 'w') as f:
            json.dump(golden_patterns, f)

        print(f"\n💎 SUCCESS! Overwrote {filename} with {len(golden_patterns)} fresh patterns.")
    else:
        print("❌ No matches found. File not updated.")

if __name__ == "__main__":
    df = fetch_market_data()
    if not df.empty:
        mine_patterns(df)
    else:
        print("❌ Error: No data fetched.")
