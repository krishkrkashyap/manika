import requests
import json
import os

# Use new broker URLs (Broker provided)
HOST_LOOKUP_URL = "http://xts.achintya.net.in:3000/hostlookup"
MARKET_DATA_URL = "http://xts.achintya.net.in:3000/apimarketdata"
TRADING_URL = "http://xts.achintya.net.in:3000/interactive"

TRADING_APP_KEY = os.getenv("XTS_TRADING_APP_KEY", "0daeeb05bfd840e59a1116")
TRADING_SECRET_KEY = os.getenv("XTS_TRADING_SECRET_KEY", "Kftw578#@G")
MARKET_DATA_APP_KEY = os.getenv("XTS_MARKET_DATA_APP_KEY", "ddc9ca260dee67556bd436")
MARKET_DATA_SECRET_KEY = os.getenv("XTS_MARKET_DATA_SECRET_KEY", "Fixs437#W1")

print(f"\n  Using Broker URLs:")
print(f"    Trading: {TRADING_URL}")
print(f"    Market Data: {MARKET_DATA_URL}")


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(name, success, data=None, error=None):
    status = "[OK] SUCCESS" if success else "[FAIL] FAILED"
    print(f"\n  {name}: {status}")
    if success and data:
        print(f"  Response: {json.dumps(data, indent=2)[:300]}")
    elif error:
        print(f"  Error: {error}")


def test_host_lookup():
    """Test HostLookup endpoint"""
    print_section("1. HOST LOOKUP")

    try:
        response = requests.post(
            HOST_LOOKUP_URL,
            json={
                "accesspassword": "2021HostLookUpAccess",
                "version": "interactive_1.0.2",
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if data.get("type") is True:
            unique_key = data.get("result", {}).get("uniqueKey")
            if unique_key:
                print_result("HostLookup", True, {"uniqueKey": unique_key[:50] + "..."})
                return unique_key
            else:
                print_result("HostLookup", False, error="No uniqueKey in response")
                return None
        else:
            error_code = data.get("code", "UNKNOWN")
            error_desc = data.get("description", "Unknown error")
            print_result(
                "HostLookup", False, error=f"Code: {error_code} | {error_desc}"
            )
            return None

    except requests.exceptions.Timeout:
        print_result("HostLookup", False, error="Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print_result("HostLookup", False, error="Connection failed - check internet")
        return None
    except Exception as e:
        print_result("HostLookup", False, error=str(e))
        return None


def test_market_data_login():
    """Test Market Data API login - Official SDK Format"""
    print_section("2. MARKET DATA API LOGIN")

    try:
        # SDK format: POST JSON body with appKey, secretKey, source
        response = requests.post(
            f"{MARKET_DATA_URL}/auth/login",
            json={
                "appKey": MARKET_DATA_APP_KEY,
                "secretKey": MARKET_DATA_SECRET_KEY,
                "source": "WEBAPI",
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        # Check if it's a list (API returns array)
        if isinstance(data, list):
            data = data[0] if data else {}

        if data.get("type") == "success":
            token = data.get("result", {}).get("token", "")
            user_id = data.get("result", {}).get("userID", "")
            expiry = data.get("result", {}).get("application_expiry_date", "")
            print_result(
                "Market Data Login",
                True,
                {
                    "userID": user_id,
                    "token": token[:50] + "..." if token else "",
                    "expiry": expiry,
                },
            )
            return token
        else:
            error_code = data.get("code", "UNKNOWN")
            error_desc = data.get("description", "Unknown error")
            print_result(
                "Market Data Login", False, error=f"Code: {error_code} | {error_desc}"
            )
            return None

    except requests.exceptions.Timeout:
        print_result("Market Data Login", False, error="Request timed out")
    except requests.exceptions.ConnectionError:
        print_result("Market Data Login", False, error="Connection failed")
    except Exception as e:
        print_result("Market Data Login", False, error=str(e))


def test_trading_login(unique_key):
    """Test Trading API login - Official SDK Format"""
    print_section("3. TRADING API LOGIN")

    # Per the SDK example, we don't need uniqueKey for basic login
    # Just send appKey, secretKey, source
    try:
        response = requests.post(
            f"{TRADING_URL}/user/session",
            json={
                "appKey": TRADING_APP_KEY,
                "secretKey": TRADING_SECRET_KEY,
                "source": "WEBAPI",
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if data.get("type") == "success":
            token = data.get("result", {}).get("token", "")
            user_id = data.get("result", {}).get("userID", "")
            print_result(
                "Trading Login",
                True,
                {"userID": user_id, "token": token[:50] + "..." if token else ""},
            )
            return token
        else:
            error_code = data.get("code", "UNKNOWN")
            error_desc = data.get("description", "Unknown error")

            # Check for specific error codes
            if "accessToken" in str(data):
                error_desc += " | Requires OAuth accessToken from broker"

            print_result(
                "Trading Login", False, error=f"Code: {error_code} | {error_desc}"
            )
            return None

    except requests.exceptions.Timeout:
        print_result("Trading Login", False, error="Request timed out")
    except requests.exceptions.ConnectionError:
        print_result("Trading Login", False, error="Connection failed")
    except Exception as e:
        print_result("Trading Login", False, error=str(e))
        return None


def test_positions(trading_token):
    """Test getting positions"""
    print_section("4. GET POSITIONS")

    if not trading_token:
        print_result("Get Positions", False, error="Not logged in to Trading API")
        return

    try:
        response = requests.get(
            f"{TRADING_URL}/portfolio/positions",
            headers={"Authorization": trading_token},
            params={"dayOrNet": "DayWise"},
            timeout=10,
        )

        data = response.json()

        if data.get("type") == "success":
            positions = data.get("result", {}).get("listPositions", [])
            print_result("Get Positions", True, {"positions_count": len(positions)})
        else:
            error_code = data.get("code", "UNKNOWN")
            error_desc = data.get("description", "Unknown error")
            print_result(
                "Get Positions", False, error=f"Code: {error_code} | {error_desc}"
            )

    except requests.exceptions.Timeout:
        print_result("Get Positions", False, error="Request timed out")
    except Exception as e:
        print_result("Get Positions", False, error=str(e))


def test_quotes(market_data_token):
    """Test getting quotes"""
    print_section("5. GET QUOTES")

    if not market_data_token:
        print_result("Get Quotes", False, error="Not logged in to Market Data API")
        return

    try:
        response = requests.post(
            f"{MARKET_DATA_URL}/instruments/quotes",
            json={
                "instruments": [
                    {"exchangeSegment": 2, "exchangeInstrumentID": 52687}  # BEL FUT
                ],
                "xtsMessageCode": 1501,
                "publishFormat": "JSON",
            },
            headers={
                "Authorization": market_data_token,
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        data = response.json()

        if isinstance(data, list):
            data = data[0] if data else {}

        if data.get("type") == "success":
            print_result("Get Quotes", True, {"status": "Quotes received"})
        else:
            error_code = data.get("code", "UNKNOWN")
            error_desc = data.get("description", "Unknown error")
            print_result(
                "Get Quotes", False, error=f"Code: {error_code} | {error_desc}"
            )

    except requests.exceptions.Timeout:
        print_result("Get Quotes", False, error="Request timed out")
    except Exception as e:
        print_result("Get Quotes", False, error=str(e))


def main():
    print("\n" + "=" * 60)
    print("  XTS API CONNECTION DIAGNOSTIC")
    print("=" * 60)
    print(f"\n  Trading App Key: {TRADING_APP_KEY[:10]}...")
    print(f"  Market Data App Key: {MARKET_DATA_APP_KEY[:10]}...")
    print(f"\n  Testing all endpoints...")

    # Test 1: HostLookup (skip - try direct login for broker)
    unique_key = None

    # Test 2: Market Data Login (try first)
    market_data_token = test_market_data_login()

    # Test 3: Trading Login (try directly without uniqueKey)
    trading_token = test_trading_login(unique_key)

    # Test 4: Get Positions (if trading connected)
    test_positions(trading_token)

    # Test 5: Get Quotes (if market data connected)
    test_quotes(market_data_token)

    # Summary
    print_section("CONNECTION SUMMARY")

    connected = []
    failed = []

    if unique_key or market_data_token:
        connected.append("Market Lookup")  # Either works

    if market_data_token:
        connected.append("Market Data API")
    else:
        failed.append("Market Data API")

    if trading_token:
        connected.append("Trading API")
    else:
        failed.append("Trading API")

    print(f"\n  [OK] Connected: {', '.join(connected) if connected else 'None'}")
    print(f"  [FAIL] Failed: {', '.join(failed) if failed else 'None'}")

    if not failed:
        print(f"\n  ALL APIs CONNECTED!")
    else:
        print(f"\n  WARNING: {len(failed)} API(s) failed. Check error codes above.")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
