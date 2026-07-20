import pandas as pd
from src.data_cleaning import (
    clean_transactions,
    clean_payment_retries,
    clean_bank_response_codes,
    merge_payment_lifecycle
)

# Test cleaning transactions
print("Testing transactions cleaning...")
txn_df = pd.read_csv("example_transactions.csv")
cleaned_txn = clean_transactions(txn_df)
print(cleaned_txn.head())
print("-" * 50)

# Test cleaning payment retries
print("Testing payment retries cleaning...")
retries_df = pd.read_csv("example_payment_retries.csv")
cleaned_retries = clean_payment_retries(retries_df)
print(cleaned_retries.head())
print("-" * 50)

# Test cleaning bank response codes
print("Testing bank response codes cleaning...")
codes_df = pd.read_csv("example_bank_response_codes.csv")
cleaned_codes = clean_bank_response_codes(codes_df)
print(cleaned_codes.head())
print("-" * 50)

# Test merge
print("Testing payment lifecycle merge...")
lifecycle = merge_payment_lifecycle(cleaned_txn, cleaned_retries)
print(lifecycle.head())
print("-" * 50)

print("All cleaning functions tested successfully!")
