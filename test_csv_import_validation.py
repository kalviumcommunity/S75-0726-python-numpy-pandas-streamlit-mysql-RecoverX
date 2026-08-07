import pandas as pd

from src.data_cleaning import validate_import_dataframe


def test_validate_import_dataframe_flags_missing_columns_and_invalid_values():
    df = pd.DataFrame(
        [
            {
                "transaction_id": "TXN-1",
                "customer_id": "CUST-1",
                "amount": "50.5",
                "initial_status": "PENDING",
                "created_at": "2026-07-31 10:00:00",
            },
            {
                "transaction_id": "TXN-2",
                "customer_id": "CUST-2",
                "amount": "bad-value",
                "initial_status": "SUCCESS",
                "created_at": "2026-07-31 11:00:00",
            },
        ]
    )

    result = validate_import_dataframe(df, "transactions")

    assert result["valid"] is True
    assert result["invalid_rows"] == 1
    assert result["cleaned_rows"] == 1
