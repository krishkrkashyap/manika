# This script will try to extract cookies from Chrome to authenticate with GitHub
import sqlite3
import os
import json

# Path to Chrome cookies
cookies_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")

if not os.path.exists(cookies_path):
    # Try alternate path
    cookies_path = os.path.expandvars(r"%APPDATA%\..\Local\Google\Chrome\User Data\Default\Cookies")

print(f"Cookies path: {cookies_path}")
print(f"Exists: {os.path.exists(cookies_path)}")

if os.path.exists(cookies_path):
    try:
        conn = sqlite3.connect(cookies_path)
        cursor = conn.cursor()
        
        # Query for github.com cookies
        cursor.execute("SELECT host_key, name, value FROM cookies WHERE host_key LIKE '%github%'")
        cookies = cursor.fetchall()
        
        print(f"\nFound {len(cookies)} GitHub cookies:")
        for cookie in cookies:
            print(f"  {cookie[1]}: {cookie[2][:20]}...")
        
        conn.close()
    except Exception as e:
        print(f"Error reading cookies: {e}")
else:
    print("Cookies file not found")
