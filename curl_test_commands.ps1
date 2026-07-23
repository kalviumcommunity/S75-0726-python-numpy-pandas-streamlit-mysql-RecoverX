# RecoverX API Test Script (PowerShell)

$API_KEY = "recoverx-secret-key"
$BASE_URL = "http://localhost:8000"

Write-Host "=== RecoverX API Test Script ===" -ForegroundColor Cyan
Write-Host ""

# Helper function for REST calls
function Invoke-APICall {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    $fullUrl = "${BASE_URL}${Endpoint}"
    $headers = @{} + $Headers
    $headers["X-API-Key"] = $API_KEY
    
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Uri $fullUrl -Method $Method -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10) -ContentType "application/json"
        } else {
            $response = Invoke-RestMethod -Uri $fullUrl -Method $Method -Headers $headers
        }
        Write-Host "✓ Success!" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "✗ Failed! Error: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Test 1: Root Health Check
Write-Host "1. Testing Root Health Check" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/"

# Test 2: Get Overview Analytics
Write-Host "2. Getting Overview Analytics" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/analytics/overview"

# Test 3: List Transactions
Write-Host "3. Listing Transactions" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/transactions?page=1&limit=10"

# Test 4: List Bank Response Codes
Write-Host "4. Listing Bank Response Codes" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/bank-response-codes?page=1&limit=10"

# Test 5: List Temporary Failures
Write-Host "5. Listing Temporary Failures" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/bank-response-codes/temporary?page=1&limit=10"

# Test 6: List Payment Lifecycle
Write-Host "6. Getting Payment Lifecycle Data" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/payment-lifecycle?page=1&limit=10"

# Test 7: Create a Transaction
Write-Host "7. Creating a Test Transaction" -ForegroundColor Yellow
$transactionBody = @{
    transaction_id = "TEST-TXN-001"
    customer_id = "TEST-CUST-001"
    amount = 100.50
    currency = "USD"
    payment_method = "Credit Card"
    gateway = "Stripe"
    initial_status = "Pending"
    final_status = "Success"
    created_at = "2024-07-23T10:00:00Z"
}
Invoke-APICall -Method POST -Endpoint "/api/transactions" -Body $transactionBody

# Test 8: Get Transaction by ID
Write-Host "8. Getting Test Transaction" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/transactions/TEST-TXN-001"

# Test 9: Create a Payment Retry
Write-Host "9. Creating a Test Payment Retry" -ForegroundColor Yellow
$retryBody = @{
    transaction_id = "TEST-TXN-001"
    attempt_number = 1
    retry_timestamp = "2024-07-23T10:05:00Z"
    retry_status = "Failed"
    response_code = "51"
    response_message = "Insufficient Funds"
}
Invoke-APICall -Method POST -Endpoint "/api/transactions/TEST-TXN-001/retries" -Body $retryBody

# Test 10: List Retries for Transaction
Write-Host "10. Listing Retries for Test Transaction" -ForegroundColor Yellow
Invoke-APICall -Method GET -Endpoint "/api/transactions/TEST-TXN-001/retries?page=1&limit=10"

Write-Host "=== Test Script Complete ===" -ForegroundColor Cyan
