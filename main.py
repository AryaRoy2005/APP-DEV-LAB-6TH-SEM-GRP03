import yfinance as yf
import pandas as pd
import json
from collections import Counter

def fetch_market_data(symbol="BTC-INR", period="max"):
    """
    Downloads historical market data from Yahoo Finance.
    """
    print(f"⏳ Downloading MAX history for {symbol}...")
    
    # Fetch unlimited history
    df = yf.download(symbol, period=period, interval="1h", progress=False)
    
    # Handle MultiIndex columns if present (common in new yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Drop rows with missing values
    df = df.dropna()
    
    print(f"✅ Data Acquired: {len(df)} hours of trading history!")
    return df

def classify_market_event(row):
    """
    Classifies a trading hour into a specific event category based on percentage change.
    """
    # Protect against division by zero
    if row['Open'] == 0:
        return "STABLE"

    change_pct = ((row['Close'] - row['Open']) / row['Open']) * 100

    # "Goldilocks" Rules
    if change_pct >= 1.0: 
        return "PUMP_HUGE"    # Whale Buy (>1%)
    elif change_pct >= 0.3: 
        return "PUMP_SMALL"   # Retail Buy (>0.3%)
    elif change_pct <= -1.0: 
        return "DUMP_HUGE"    # Whale Sell (<-1%)
    elif change_pct <= -0.3: 
        return "DUMP_SMALL"   # Retail Sell (<-0.3%)
    else: 
        return "STABLE"       # Noise

def mine_patterns(df):
    """
    Scans the data for profitable patterns and saves them to a JSON file.
    """
    print("⚙️ Applying Smart Classification...")
    df['Event'] = df.apply(classify_market_event, axis=1)
    
    # Show breakdown in logs
    print("✅ Breakdown of Smart Events:")
    print(df['Event'].value_counts())

    SEQUENCE_LENGTH = 3
    TARGET_PROFIT = 0.5  # 0.5% profit target
    sequences = []
    
    print(f"⏳ Scanning for patterns leading to {TARGET_PROFIT}% profit...")

    # Sliding window to find winning sequences
    # We iterate up to the point where we still have enough data for the "next" result
    for i in range(len(df) - SEQUENCE_LENGTH - 1):
        # Extract the pattern of 3 events
        current_pattern = df['Event'].iloc[i : i + SEQUENCE_LENGTH].tolist()

        # Look at the outcome (the hour immediately AFTER the pattern)
        next_open = df['Open'].iloc[i + SEQUENCE_LENGTH + 1]
        next_close = df['Close'].iloc[i + SEQUENCE_LENGTH + 1]
        
        # Calculate if that next hour was profitable
        if next_open > 0:
            future_profit = ((next_close - next_open) / next_open) * 100
        else:
            future_profit = 0

        if future_profit >= TARGET_PROFIT:
            # We append a marker just for counting purposes
            current_pattern.append("PROFIT_HIT")
            sequences.append(current_pattern)

    print(f"✅ Found {len(sequences)} winning trades.")

    if len(sequences) > 0:
        # Convert list to string for counting
        seq_strings = [json.dumps(seq) for seq in sequences]
        counts = Counter(seq_strings)

        golden_patterns = []

        print("\n🏆 TOP SMART PATTERNS FOUND:")
        # Filter for patterns that appeared at least 5 times
        for seq_str, count in counts.most_common(50):
            if count >= 5:
                full_seq = json.loads(seq_str)
                # Remove the "PROFIT_HIT" marker to get the raw trigger pattern
                trigger_pattern = full_seq[:-1]
                golden_patterns.append(trigger_pattern)

                # Log the top 5 for verification
                if len(golden_patterns) <= 5:
                    print(f"   🔥 {trigger_pattern} -> Won {count} times")

        # Save to JSON
        filename = 'golden_patterns.json'
        with open(filename, 'w') as f:
            json.dump(golden_patterns, f)

        print(f"\n💎 SUCCESS! Saved {len(golden_patterns)} patterns to {filename}")
    else:
        print("❌ No matches found.")

if __name__ == "__main__":
    # Main execution flow
    df = fetch_market_data()
    if not df.empty:
        mine_patterns(df)
    else:
        print("❌ Error: No data fetched.")
