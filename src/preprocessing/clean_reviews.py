"""
Advanced Data Preprocessing Pipeline for Banking App Reviews

This script processes raw review data by:
1. Loading scraped reviews
2. Cleaning and normalizing text
3. Performing advanced NLP preprocessing (tokenization, stop-word removal, lemmatization)
4. Extracting keywords and identifying themes
5. Saving processed data with sentiment analysis

Output format:
- review_id: Unique identifier for each review
- review_text: Original review text
- processed_text: Cleaned and preprocessed text
- tokens: List of processed tokens
- sentiment_label: Sentiment classification (positive/negative/neutral)
- sentiment_score: Sentiment polarity score
- theme: Identified theme category
- keywords: Extracted keywords
- bank: Source bank
- rating: Star rating
- date: Review date
"""

import pandas as pd
import re
import string
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from collections import Counter
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import spacy

# Load spaCy model for advanced NLP
nlp = spacy.load('en_core_web_sm')

# Define theme categories
THEME_CATEGORIES = {
    'ui_ux': ['interface', 'design', 'layout', 'theme', 'color', 'button', 'menu', 'navigation', 'experience'],
    'performance': ['slow', 'fast', 'lag', 'crash', 'freeze', 'response', 'speed', 'performance', 'optimization'],
    'functionality': ['feature', 'function', 'tool', 'option', 'setting', 'capability', 'work', 'operation'],
    'security': ['login', 'password', 'pin', 'security', 'authentication', 'verification', 'biometric', 'faceid'],
    'customer_service': ['support', 'service', 'help', 'response', 'assistance', 'representative', 'contact'],
    'transactions': ['transfer', 'payment', 'transaction', 'send', 'receive', 'bill', 'deposit', 'withdrawal']
}

# Download required NLTK data
def download_nltk_data():
    """Download required NLTK data files."""
    required_data = {
        'tokenizers/punkt': 'punkt',
        'corpora/stopwords': 'stopwords',
        'corpora/wordnet': 'wordnet',
        'taggers/averaged_perceptron_tagger': 'averaged_perceptron_tagger',
        'tokenizers/punkt': 'punkt',
        'corpora/omw-1.4': 'omw-1.4'
    }
    
    for path, package in required_data.items():
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"Downloading NLTK data: {package}")
            nltk.download(package, quiet=True)

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

def clean_text(text, return_tokens=True):
    """
    Advanced text cleaning and preprocessing pipeline.
    
    Args:
        text (str): Input text to clean
        return_tokens (bool): If True, return tokens; if False, return joined text
        
    Returns:
        list or str: Cleaned tokens or text
    """
    if not isinstance(text, str) or not text.strip():
        return [] if return_tokens else ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs, mentions, and special patterns
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # URLs
    text = re.sub(r'@\w+', '', text)  # Mentions
    text = re.sub(r'#\w+', '', text)  # Hashtags
    text = re.sub(r'\b\w{20,}\b', '', text)  # Long words (likely garbage)
    
    # Remove HTML tags and special characters
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)  # Keep only alphanumeric and whitespace
    
    # Tokenization with NLTK
    tokens = word_tokenize(text)
    
    # Remove stopwords and short tokens
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    # Lemmatization with POS tagging
    lemmatizer = WordNetLemmatizer()
    pos_tags = nltk.pos_tag(tokens)
    tokens = []
    
    for word, tag in pos_tags:
        if tag.startswith('NN'):  # Noun
            pos = 'n'
        elif tag.startswith('VB'):  # Verb
            pos = 'v'
        elif tag.startswith('JJ'):  # Adjective
            pos = 'a'
        elif tag.startswith('R'):  # Adverb
            pos = 'r'
        else:
            pos = 'n'  # Default to noun
            
        lemma = lemmatizer.lemmatize(word, pos=pos)
        tokens.append(lemma)
    
    # Remove any remaining non-alphabetic tokens
    tokens = [word for word in tokens if word.isalpha()]
    
    if return_tokens:
        return tokens
    return ' '.join(tokens)

def analyze_sentiment(text):
    """
    Analyze sentiment of a text using TextBlob.
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        tuple: (sentiment_label, sentiment_score)
    """
    if not isinstance(text, str) or not text.strip():
        return 'neutral', 0.0
    
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0.1:
        return 'positive', polarity
    elif polarity < -0.1:
        return 'negative', polarity
    else:
        return 'neutral', polarity

def extract_keywords(text, top_n=10):
    """
    Extract top keywords using TF-IDF.
    
    Args:
        text (str): Input text
        top_n (int): Number of keywords to extract
        
    Returns:
        list: Top keywords
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Use spaCy for keyword extraction
    doc = nlp(text)
    
    # Extract noun chunks and named entities
    keywords = [chunk.text.lower() for chunk in doc.noun_chunks]
    keywords.extend([ent.text.lower() for ent in doc.ents])
    
    # Extract meaningful tokens (nouns and adjectives)
    keywords.extend([token.lemma_ for token in doc 
                    if token.pos_ in ['NOUN', 'ADJ'] 
                    and not token.is_stop 
                    and len(token.text) > 2])
    
    # Count and get top keywords
    keyword_counts = Counter(keywords)
    return [word for word, _ in keyword_counts.most_common(top_n)]

def identify_theme(text, top_n=2):
    """
    Identify the most relevant themes for a given text.
    
    Args:
        text (str): Input text
        top_n (int): Number of themes to return
        
    Returns:
        list: Identified themes
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Clean and tokenize the text
    tokens = clean_text(text)
    text = ' '.join(tokens)
    
    # Calculate theme scores
    theme_scores = {}
    for theme, keywords in THEME_CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            theme_scores[theme] = score
    
    # Sort themes by score and get top N
    sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
    return [theme for theme, _ in sorted_themes[:top_n]]

def preprocess_reviews(df):
    """
    Advanced preprocessing pipeline for bank reviews.
    
    Args:
        df (pd.DataFrame): Raw review data
        
    Returns:
        pd.DataFrame: Processed data with NLP features
    """
    if df.empty:
        return df
    
    print("\nStarting advanced data preprocessing...")
    
    # Make a copy of the original data
    df_clean = df.copy()
    
    # Handle missing values
    print("1/6 Handling missing values...")
    df_clean.dropna(subset=['content', 'score'], inplace=True)
    
    # Standardize column names and types
    print("2/6 Standardizing columns...")
    df_clean['review_id'] = range(1, len(df_clean) + 1)  # Add unique ID
    df_clean['rating'] = df_clean['score'].astype(float)
    df_clean['date'] = pd.to_datetime(df_clean['at'], unit='s', errors='coerce')
    
    # Clean and preprocess text
    print("3/6 Cleaning and tokenizing text...")
    df_clean['tokens'] = df_clean['content'].apply(clean_text, return_tokens=True)
    df_clean['processed_text'] = df_clean['tokens'].apply(lambda x: ' '.join(x) if x else '')
    
    # Sentiment analysis
    print("4/6 Analyzing sentiment...")
    sentiment_results = df_clean['content'].apply(analyze_sentiment)
    df_clean['sentiment_label'] = sentiment_results.apply(lambda x: x[0])
    df_clean['sentiment_score'] = sentiment_results.apply(lambda x: x[1])
    
    # Extract keywords and identify themes
    print("5/6 Extracting keywords and identifying themes...")
    df_clean['keywords'] = df_clean['content'].apply(lambda x: extract_keywords(x, top_n=5))
    df_clean['theme'] = df_clean['content'].apply(lambda x: identify_theme(x, top_n=2))
    
    # Select and rename columns
    print("6/6 Finalizing data structure...")
    columns = {
        'review_id': 'review_id',
        'content': 'original_text',
        'score': 'rating',
        'date': 'date',
        'userName': 'user_name',
        'thumbsUpCount': 'thumbs_up',
        'app_name': 'bank',
        'source': 'source'
    }
    
    # Keep only the columns we need
    df_clean = df_clean.rename(columns=columns)
    final_columns = [
        'review_id', 'original_text', 'processed_text', 'tokens',
        'sentiment_label', 'sentiment_score', 'theme', 'keywords',
        'rating', 'date', 'bank', 'source', 'user_name', 'thumbs_up'
    ]
    
    df_clean = df_clean[[col for col in final_columns if col in df_clean.columns]]
    
    # Drop any remaining duplicates
    df_clean.drop_duplicates(subset=['original_text', 'user_name', 'date'], inplace=True)
    
    print(f"Preprocessing complete. {len(df_clean)} reviews processed.")
    return df_clean

def save_cleaned_data(df, directory='../../data/processed'):
    """
    Save the processed data to CSV and JSON files.
    
    Args:
        df (pd.DataFrame): Processed data
        directory (str): Output directory
    """
    if df.empty:
        print("No data to save.")
        return
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to CSV (flatten lists)
        csv_df = df.copy()
        for col in ['tokens', 'keywords', 'theme']:
            if col in csv_df.columns:
                csv_df[col] = csv_df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else '')
        
        csv_filename = f'bank_reviews_processed_{timestamp}.csv'
        csv_path = os.path.join(directory, csv_filename)
        csv_df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Save to JSON (preserves data types better)
        json_filename = f'bank_reviews_processed_{timestamp}.json'
        json_path = os.path.join(directory, json_filename)
        df.to_json(json_path, orient='records', lines=True, force_ascii=False)
        
        # Save a sample for testing
        sample_size = min(100, len(df))
        sample_df = df.sample(sample_size, random_state=42)
        sample_path = os.path.join(directory, f'sample_processed_reviews_{timestamp}.csv')
        sample_df.to_csv(sample_path, index=False, encoding='utf-8')
        
        print(f"\nSuccessfully saved processed data to:")
        print(f"- CSV: {os.path.abspath(csv_path)}")
        print(f"- JSON: {os.path.abspath(json_path)}")
        print(f"- Sample: {os.path.abspath(sample_path)}")
        
        return csv_path, json_path
    
    except Exception as e:
        print(f"Error saving processed data: {str(e)}")
        return None, None

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
