import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_KEY = "recoverx-secret-key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def run_endpoint_test(method, endpoint, data=None, files=None, description=""):
    url = BASE_URL + endpoint
    print("\n" + "=" * 80)
    print(f"TEST: {description}")
    print(f"URL: {method} {url}")
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            if files:
                resp = requests.post(url, headers=HEADERS, files=files, timeout=30)
            else:
                resp = requests.post(url, headers=HEADERS, json=data, timeout=10)
        else:
            print(f"ERROR: Unsupported method {method}")
            return False
        
        print(f"STATUS CODE: {resp.status_code}")
        try:
            print("RESPONSE:")
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        except Exception:
            print(f"RESPONSE TEXT: {resp.text}")
        
        success = 200 <= resp.status_code < 300
        if success:
            print(f"[PASS] SUCCESS: {description}")
        else:
            print(f"[FAIL] FAILED: {description}")
        return success
    except Exception as e:
        print(f"[ERROR] EXCEPTION: {e}")
        return False


def main():
    print("=" * 80)
    print("RECOVERX API ENDPOINT TESTER")
    print(f"BASE URL: {BASE_URL}")
    print(f"API KEY: {API_KEY}")
    print("=" * 80)
    
    results = []
    
    # 1. Health Check
    results.append(("Health Check", run_endpoint_test("GET", "/", description="Health Check")))
    
    # 2. Analytics: Overview
    results.append(("Analytics Overview", run_endpoint_test("GET", "/api/analytics/overview", description="Analytics Overview")))
    
    # 3. Transactions: List
    results.append(("List Transactions", run_endpoint_test("GET", "/api/transactions?page=1&limit=10", description="List Transactions")))
    
    # 4. Transactions: Create
    txn_data = {
        "transaction_id": "TEST-TXN-001",
        "customer_id": "TEST-CUST-001",
        "amount": 100.50,
        "currency": "USD",
        "payment_method": "Credit Card",
        "gateway": "Stripe",
        "initial_status": "Pending",
        "final_status": "Success",
        "created_at": "2024-07-23T10:00:00Z"
    }
    results.append(("Create Transaction", run_endpoint_test("POST", "/api/transactions", data=txn_data, description="Create Transaction")))
    
    # 5. Transactions: Get One
    results.append(("Get Transaction", run_endpoint_test("GET", "/api/transactions/TEST-TXN-001", description="Get Single Transaction")))
    
    # 6. Payment Retries: Create
    retry_data = {
        "transaction_id": "TEST-TXN-001",
        "attempt_number": 1,
        "retry_timestamp": "2024-07-23T10:05:00Z",
        "retry_status": "Failed",
        "response_code": "51",
        "response_message": "Insufficient Funds"
    }
    results.append(("Create Retry", run_endpoint_test("POST", "/api/transactions/TEST-TXN-001/retries", data=retry_data, description="Create Retry")))
    
    # 7. Payment Retries: List
    results.append(("List Retries", run_endpoint_test("GET", "/api/transactions/TEST-TXN-001/retries?page=1&limit=10", description="List Retries")))
    
    # 8. Payment Lifecycle
    results.append(("Payment Lifecycle", run_endpoint_test("GET", "/api/payment-lifecycle?page=1&limit=10", description="Payment Lifecycle")))
    
    # 9. Bank Response Codes: List
    results.append(("List Bank Codes", run_endpoint_test("GET", "/api/bank-response-codes?page=1&limit=10", description="List Bank Response Codes")))
    
    # 10. Bank Response Codes: Temporary
    results.append(("Temporary Failures", run_endpoint_test("GET", "/api/bank-response-codes/temporary?page=1&limit=10", description="Temporary Failures")))
    
    # 11. Bank Response Codes: Permanent
    results.append(("Permanent Failures", run_endpoint_test("GET", "/api/bank-response-codes/permanent?page=1&limit=10", description="Permanent Failures")))
    
    # 12. Bank Response Codes: Create
    brc_data = {
        "response_code": "TEST-CODE-01",
        "bank_name": "Test Bank",
        "description": "Test temporary failure",
        "failure_type": "TEMPORARY",
        "recovery_potential": 0.80,
        "recommended_action": "Retry after 24 hours"
    }
    results.append(("Create Bank Code", run_endpoint_test("POST", "/api/bank-response-codes", data=brc_data, description="Create Bank Response Code")))
    
    # 13. Analytics: Failure Classifications
    results.append(("Failure Classifications", run_endpoint_test("GET", "/api/analytics/failure-classifications?page=1&limit=10", description="Failure Classifications")))
    
    # 14. Analytics: Response Code Analysis
    results.append(("Response Code Analysis", run_endpoint_test("GET", "/api/analytics/response-code-analysis?page=1&limit=10", description="Response Code Analysis")))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, success in results:
        status = "[PASS] PASSED" if success else "[FAIL] FAILED"
        print(f"{status:15} {name}")
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{total} endpoints passed")
    print("=" * 80)


if __name__ == "__main__":
    main()
