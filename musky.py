#!/usr/bin/env python3
from os import environ
from playwright.sync_api import Playwright, sync_playwright, TimeoutError
import time

# BrightData Authentication credentials
AUTH = environ.get('AUTH', default='brd-customer-hl_13cbb6ef-zone-scraping_browser1:slx6x1wk2ag2')

# Target URL to navigate
TARGET_URL = 'https://nowshort.com/7nQD9'


def scrape(playwright: Playwright, url=TARGET_URL):
    """
    Main scraping function that:
    1. Connects to BrightData browser
    2. Navigates through redirects
    3. Takes screenshot of final page
    4. Waits for 10 seconds
    """
    
    print('Connecting to BrightData Browser...')
    endpoint_url = f'wss://{AUTH}@brd.superproxy.io:9222'
    
    # Connect to BrightData's browser
    browser = playwright.chromium.connect_over_cdp(endpoint_url)
    
    try:
        print(f'Connected! Creating new page...')
        page = browser.new_page()
        
        # Create CDP session for captcha solving
        client = page.context.new_cdp_session(page)
        
        # Step 0: Navigate to the URL and mark as main page
        print(f'Navigating to {url}...')
        try:
            # Use 'commit' wait_until for fastest navigation (100% ratio)
            # This waits only for navigation to be committed, not for full page load
            page.goto(url, wait_until='commit', timeout=30000)
            print('Initial navigation committed!')
        except TimeoutError:
            print('Navigation timeout after 30 seconds, continuing anyway...')
        
        # Wait for potential captcha and solve it
        print('Checking for captcha...')
        try:
            result = client.send('Captcha.waitForSolve', {
                'detectTimeout': 10 * 1000,  # 10 seconds to detect captcha
            })
            status = result.get('status', 'unknown')
            print(f'Captcha status: {status}')
        except Exception as e:
            print(f'Captcha check skipped or failed: {str(e)}')
        
        # Step 1: Wait for redirects to complete and final page to load
        print('Waiting for redirects to complete...')
        
        # Wait for network to be idle (no more redirects)
        try:
            # Wait for network idle with 30 second timeout
            page.wait_for_load_state('networkidle', timeout=30000)
            print('Page fully loaded after redirects!')
        except TimeoutError:
            print('Page load timeout after 30 seconds, continuing with current state...')
        
        # Get current URL after all redirects
        current_url = page.url
        print(f'Final page URL: {current_url}')
        
        # Take screenshot of the final page
        screenshot_path = f'screenshot_{int(time.time())}.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f'Screenshot saved: {screenshot_path}')
        
        # Wait for 10 seconds on the final page
        print('Waiting for 10 seconds...')
        time.sleep(10)
        
        print('Process completed successfully!')
        
    except Exception as e:
        print(f'Error occurred: {str(e)}')
        raise
    finally:
        print('Closing browser...')
        browser.close()


def main():
    """
    Main entry point of the script
    """
    with sync_playwright() as playwright:
        scrape(playwright)


if __name__ == '__main__':
    main()
