"""
Data Cleaning and Preprocessing for Banking App Reviews

This script processes raw review data by:
1. Loading scraped reviews
2. Cleaning and normalizing text
3. Handling missing values
4. Saving cleaned data
"""

import pandas as pd
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import os
from datetime import datetime

# Download required NLTK data
def download_nltk_data():
    """Download required NLTK data files."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')

def load_reviews(directory='../../data/raw'):
    """Load all review CSV files from the specified directory."""
    all_reviews = []
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return pd.DataFrame()
    
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                all_reviews.append(df)
                print(f"Loaded {len(df)} reviews from {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")
    
    if not all_reviews:
        print("No review files found.")
        return pd.DataFrame()
    
    return pd.concat(all_reviews, ignore_index=True)

def clean_text(text):
    """Clean and preprocess text data."""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Tokenization
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    # Join tokens back to text
    return ' '.join(tokens)

def preprocess_reviews(df):
    """Preprocess the reviews DataFrame."""
    if df.empty:
        return df
    
    print("\nStarting data preprocessing...")
    
    # Make a copy of the original data
    df_clean = df.copy()
    
    # Handle missing values
    print("Handling missing values...")
    df_clean.dropna(subset=['content', 'score'], inplace=True)
    
    # Clean text data
    print("Cleaning review text...")
    df_clean['cleaned_text'] = df_clean['content'].apply(clean_text)
    
    # Convert date to datetime
    print("Processing dates...")
    if 'at' in df_clean.columns:
        df_clean['review_date'] = pd.to_datetime(df_clean['at'], unit='s', errors='coerce')
    
    # Select and rename columns
    columns = {
        'content': 'original_text',
        'score': 'rating',
        'review_date': 'date',
        'userName': 'user_name',
        'thumbsUpCount': 'thumbs_up'
    }
    
    # Keep only the columns we need
    df_clean = df_clean.rename(columns=columns)
    final_columns = ['original_text', 'cleaned_text', 'rating', 'date', 'bank', 'source', 'user_name', 'thumbs_up']
    df_clean = df_clean[[col for col in final_columns if col in df_clean.columns]]
    
    # Drop any remaining duplicates
    df_clean.drop_duplicates(subset=['original_text', 'user_name', 'date'], inplace=True)
    
    print(f"Preprocessing complete. {len(df_clean)} reviews processed.")
    return df_clean

def save_cleaned_data(df, directory='../../data/processed'):
    """Save the cleaned data to a CSV file."""
    if df.empty:
        return
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'cleaned_reviews_{timestamp}.csv'
    filepath = os.path.join(directory, filename)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    print(f"\nSaved cleaned data to {filepath}")

def main():
    """Main function to run the preprocessing pipeline."""
    print("Starting review preprocessing...")
    
    # Download required NLTK data
    download_nltk_data()
    
    # Load raw reviews
    print("\nLoading raw review data...")
    df = load_reviews()
    
    if df.empty:
        print("No data to process. Exiting.")
        return
    
    # Preprocess the data
    df_clean = preprocess_reviews(df)
    
    # Save the cleaned data
    if not df_clean.empty:
        save_cleaned_data(df_clean)
    
    print("\nPreprocessing complete!")

if __name__ == "__main__":
    main()
