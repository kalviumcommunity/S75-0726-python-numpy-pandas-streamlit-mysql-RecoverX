import time

from src.db import execute_query


def measure_query(query, name):
    """
    Execute a SQL query and measure its execution time.
    """

    print("=" * 60)
    print(name)

    start = time.perf_counter()

    result = execute_query(query, fetch=True)

    end = time.perf_counter()

    elapsed = (end - start) * 1000

    rows = len(result) if result else 0

    print(f"Rows Returned : {rows}")
    print(f"Execution Time: {elapsed:.2f} ms")

    if elapsed < 100:
        print("Status: ✅ Excellent")

    elif elapsed < 500:
        print("Status: 🟡 Good")

    else:
        print("Status: 🔴 Slow")

    print()


def main():

    print("\nRecoverX Database Performance Test\n")

    measure_query(
        "SELECT * FROM transactions;",
        "Transactions Table"
    )

    measure_query(
        "SELECT * FROM payment_retries;",
        "Payment Retries Table"
    )

    measure_query(
        "SELECT * FROM bank_response_codes;",
        "Bank Response Codes"
    )

    measure_query(
        "SELECT * FROM failure_classifications;",
        "Failure Classifications"
    )


if __name__ == "__main__":
    main()