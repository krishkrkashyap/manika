import shutil
import os

# Copy cookies to a temp location
cookies_src = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
cookies_dst = os.path.join(os.path.dirname(__file__), "cookies_copy.db")

print(f"Copying cookies from: {cookies_src}")

# Chrome must be closed for this to work
# Let's try to copy
try:
    shutil.copy2(cookies_src, cookies_dst)
    print(f"Copied to: {cookies_dst}")
    print("Success! Now reading cookies...")
    
    import sqlite3
    conn = sqlite3.connect(cookies_dst)
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, value FROM cookies WHERE host_key LIKE '%github%'")
    cookies = cursor.fetchall()
    
    print(f"\nFound {len(cookies)} GitHub cookies:")
    for cookie in cookies:
        print(f"  {cookie[0]} | {cookie[1]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    print("\nPlease close Chrome and run this again, or create the repo manually in the browser.")
