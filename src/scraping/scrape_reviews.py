"""
Google Play Store Review Scraper for Ethiopian Banking Apps

This script scrapes user reviews from the Google Play Store for three Ethiopian banks:
1. Commercial Bank of Ethiopia (CBE)
2. Bank of Abyssinia (BOA)
3. Dashen Bank
"""

import pandas as pd
from google_play_scraper import app, Sort, reviews, reviews_all
import time
from datetime import datetime
import os

# Bank app details - Using package names from Google Play Store
BANK_APPS = {
    "CBE": "com.combanketh.mobilebanking.ethiopia",  # CBE Birr
    "BOA": "com.bankofabyssinia.bankofabyssiniamobilebanking",  # BOA Mobile
    "DASHEN": "com.dashen.mobilebanking"  # Dashen Bank
}

def get_app_info(app_id):
    """Get basic app information from Google Play Store."""
    try:
        app_info = app(app_id)
        return {
            'app_name': app_info.get('title', ''),
            'install_count': app_info.get('installs', ''),
            'score': app_info.get('score', 0),
            'reviews': app_info.get('reviews', 0)
        }
    except Exception as e:
        print(f"Error fetching app info for {app_id}: {str(e)}")
        return None

def scrape_reviews(app_id, bank_name, count=400):
    """Scrape reviews for a given app ID."""
    print(f"Scraping {count} reviews for {bank_name}...")
    
    try:
        # Scrape reviews with pagination
        result, continuation_token = reviews(
            app_id,
            lang='en',
            country='et',
            sort=Sort.NEWEST,
            count=min(100, count),  # Scrape in batches of 100
            filter_score_with=None  # Get all scores
        )
        
        all_reviews = result
        
        # Continue scraping until we have enough reviews
        while continuation_token and len(all_reviews) < count:
            result, continuation_token = reviews(
                app_id,
                continuation_token=continuation_token,
                lang='en',
                country='et',
                sort=Sort.NEWEST,
                count=min(100, count - len(all_reviews))
            )
            all_reviews.extend(result)
            
            # Be nice to Google's servers
            time.sleep(2)
            
        print(f"Successfully scraped {len(all_reviews)} reviews for {bank_name}")
        return all_reviews
    except Exception as e:
        print(f"Error scraping reviews for {bank_name}: {str(e)}")
        return []

def save_reviews(reviews_data, bank_name):
    """Save reviews to a CSV file."""
    if not reviews_data:
        return
        
    # Create data directory if it doesn't exist
    os.makedirs('../../data/raw', exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews_data)
    
    # Add bank name and source
    df['bank'] = bank_name
    df['source'] = 'Google Play Store'
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'../../data/raw/{bank_name.lower()}_reviews_{timestamp}.csv'
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} reviews to {filename}")

def main():
    """Main function to scrape reviews for all bank apps."""
    all_reviews = []
    
    for bank_name, app_id in BANK_APPS.items():
        # Get app info
        app_info = get_app_info(app_id)
        if app_info:
            print(f"\n--- {bank_name} ---")
            print(f"App Name: {app_info['app_name']}")
            print(f"Rating: {app_info['score']} ({app_info['reviews']} reviews)")
            print(f"Installs: {app_info['install_count']}")
        
        # Scrape reviews
        reviews_data = scrape_reviews(app_id, bank_name, count=400)
        
        # Save reviews to file
        save_reviews(reviews_data, bank_name)
        
        # Add to combined reviews
        if reviews_data:
            all_reviews.extend(reviews_data)
        
        # Add delay between different apps
        time.sleep(5)
    
    # Save combined reviews
    if all_reviews:
        df_all = pd.DataFrame(all_reviews)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        combined_filename = f'../../data/raw/all_banks_reviews_{timestamp}.csv'
        df_all.to_csv(combined_filename, index=False)
        print(f"\nSaved combined reviews to {combined_filename}")

if __name__ == "__main__":
    main()
