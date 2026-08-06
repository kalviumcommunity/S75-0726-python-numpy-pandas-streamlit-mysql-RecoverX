import time
import requests

headers = {
    "X-API-Key": "recoverx123"
}

BASE_URL = "http://127.0.0.1:8000"


def test_endpoint(method, endpoint, json_data=None):
    url = BASE_URL + endpoint

    start = time.perf_counter()

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)

        elif method == "POST":
            response = requests.post(
                url,
                json=json_data,
                headers=headers
                )

        else:
            print(f"Unsupported method: {method}")
            return

        end = time.perf_counter()

        elapsed = (end - start) * 1000

        print("=" * 60)
        print(f"{method} {endpoint}")
        print(f"Status Code : {response.status_code}")
        print(f"Response Time : {elapsed:.2f} ms")

        if response.status_code < 400:
            print("Result : ✅ PASS")
        else:
            print("Result : ❌ FAIL")

    except Exception as e:
        print("=" * 60)
        print(f"{method} {endpoint}")
        print("Result : ❌ ERROR")
        print(e)

if __name__ == "__main__":

    print("\nRecoverX API Performance Test\n")

    test_endpoint(
        "GET",
        "/api/transactions"
    )

    test_endpoint(
    "GET",
    "/api/transactions/TXN-BZK1NZTVWVJI"
)
    test_endpoint(
    "GET",
    "/api/transactions/TXN-BZK1NZTVWVJI/retries"
)