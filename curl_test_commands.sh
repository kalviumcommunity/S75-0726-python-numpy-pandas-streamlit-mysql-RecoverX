#!/bin/bash
# RecoverX API Test Script

API_KEY="recoverx-secret-key"
BASE_URL="http://localhost:8000"

echo "=== RecoverX API Test Script ==="
echo

# Test 1: Root Health Check
echo "1. Testing Root Health Check"
curl -X GET "${BASE_URL}/"
echo -e "\n"

# Test 2: Get Overview Analytics
echo "2. Getting Overview Analytics"
curl -X GET "${BASE_URL}/api/analytics/overview" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 3: List Transactions
echo "3. Listing Transactions"
curl -X GET "${BASE_URL}/api/transactions?page=1&limit=10" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 4: List Bank Response Codes
echo "4. Listing Bank Response Codes"
curl -X GET "${BASE_URL}/api/bank-response-codes?page=1&limit=10" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 5: List Temporary Failures
echo "5. Listing Temporary Failures"
curl -X GET "${BASE_URL}/api/bank-response-codes/temporary?page=1&limit=10" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 6: List Payment Lifecycle
echo "6. Getting Payment Lifecycle Data"
curl -X GET "${BASE_URL}/api/payment-lifecycle?page=1&limit=10" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 7: Create a Transaction
echo "7. Creating a Test Transaction"
curl -X POST "${BASE_URL}/api/transactions" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d '{
    "transaction_id": "TEST-TXN-001",
    "customer_id": "TEST-CUST-001",
    "amount": 100.50,
    "currency": "USD",
    "payment_method": "Credit Card",
    "gateway": "Stripe",
    "initial_status": "Pending",
    "final_status": "Success",
    "created_at": "2024-07-23T10:00:00Z"
}'
echo -e "\n"

# Test 8: Get Transaction by ID
echo "8. Getting Test Transaction"
curl -X GET "${BASE_URL}/api/transactions/TEST-TXN-001" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

# Test 9: Create a Payment Retry
echo "9. Creating a Test Payment Retry"
curl -X POST "${BASE_URL}/api/transactions/TEST-TXN-001/retries" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d '{
    "transaction_id": "TEST-TXN-001",
    "attempt_number": 1,
    "retry_timestamp": "2024-07-23T10:05:00Z",
    "retry_status": "Failed",
    "response_code": "51",
    "response_message": "Insufficient Funds"
}'
echo -e "\n"

# Test 10: List Retries for Transaction
echo "10. Listing Retries for Test Transaction"
curl -X GET "${BASE_URL}/api/transactions/TEST-TXN-001/retries?page=1&limit=10" -H "X-API-Key: ${API_KEY}"
echo -e "\n"

echo "=== Test Script Complete ==="
