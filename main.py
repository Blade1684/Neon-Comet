
import os
from dotenv import load_dotenv
from src.scraper import Scraper
from src.notifier import Notifier
import sys

def main():
    load_dotenv()
    
    print("--- Online Price Tracker ---")
    
    # Get interactive input or use args
    if len(sys.argv) > 1:
        url = sys.argv[1]
        target_price = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        email = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        url = input("Enter Product URL: ").strip()
        try:
            target_price = float(input("Enter Target Price: ").strip())
        except ValueError:
            print("Invalid price. Using 0.")
            target_price = 0.0
        email = input("Enter Email for notification (optional): ").strip()
    
    scraper = Scraper()
    notifier = Notifier()
    
    print(f"\nChecking price for: {url}...")
    current_price = scraper.get_price(url)
    
    if current_price:
        print(f"Current Price: {current_price}")
        
        if current_price < target_price:
            print(f"ALERT: Price is below {target_price}!")
            if email:
                notifier.send_notification(url, current_price, target_price, email)
        else:
            print(f"Price is still above {target_price}. No alert.")
    else:
        print("Failed to retrieve price.")

if __name__ == "__main__":
    main()
