from playwright.sync_api import sync_playwright
import os

# Chrome path
chrome_path = r"C:\Users\Krish.Kumar\AppData\Local\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    # Try to use existing Chrome profile
    user_data_dir = os.path.expandvars(r"%APPDATA%\..\Local\Google\Chrome\User Data\Default")
    
    print(f"Chrome path: {chrome_path}")
    print(f"Profile path: {user_data_dir}")
    print(f"Profile exists: {os.path.exists(user_data_dir)}")
    
    if os.path.exists(user_data_dir):
        print("Launching Chrome with your profile...")
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            executable_path=chrome_path
        )
    else:
        print("No profile found, launching Chrome...")
        browser = p.chromium.launch(
            headless=False,
            executable_path=chrome_path
        )
        context = browser.new_context()
    
    page = context.new_page()
    
    # Go to GitHub new repo page
    page.goto('https://github.com/new')
    page.wait_for_load_state('networkidle')
    
    # Take screenshot
    page.screenshot(path='github_page.png')
    
    print(f"\nTitle: {page.title()}")
    print(f"URL: {page.url}")
    
    print("\n" + "="*50)
    print("Browser is now open!")
    print("Please create the repository:")
    print("1. Name: manika-dashboard")
    print("2. Select: Private")
    print("3. Don't add README")
    print("4. Click Create repository")
    print("\nTell me when done!")
    print("="*50)
    
    import time
    time.sleep(180)  # 3 minutes
    
    context.close()
