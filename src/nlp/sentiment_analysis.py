"""
Sentiment Analysis for Banking App Reviews

This script performs sentiment analysis on preprocessed banking app reviews
using TextBlob for polarity and subjectivity scores.
"""

import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

def load_cleaned_data(directory='../../data/processed'):
    """Load the most recent cleaned reviews file."""
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return pd.DataFrame()
    
    # Find all cleaned review files
    files = [f for f in os.listdir(directory) if f.startswith('cleaned_reviews_') and f.endswith('.csv')]
    if not files:
        print("No cleaned review files found.")
        return pd.DataFrame()
    
    # Get the most recent file
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(directory, x)))
    filepath = os.path.join(directory, latest_file)
    
    try:
        df = pd.read_csv(filepath, parse_dates=['date'], infer_datetime_format=True)
        print(f"Loaded {len(df)} reviews from {latest_file}")
        return df
    except Exception as e:
        print(f"Error loading {latest_file}: {str(e)}")
        return pd.DataFrame()

def analyze_sentiment(text):
    """
    Perform sentiment analysis using TextBlob.
    Returns polarity (-1 to 1) and sentiment label.
    """
    if not isinstance(text, str) or not text.strip():
        return 0.0, 'neutral'
    
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    # Categorize sentiment
    if polarity > 0.1:
        sentiment = 'positive'
    elif polarity < -0.1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return polarity, sentiment

def add_sentiment_columns(df):
    """Add sentiment analysis columns to the DataFrame."""
    if df.empty:
        return df
    
    print("Performing sentiment analysis...")
    
    # Apply sentiment analysis
    sentiment_results = df['cleaned_text'].apply(analyze_sentiment)
    df[['polarity', 'sentiment']] = pd.DataFrame(sentiment_results.tolist(), index=df.index)
    
    # Map numeric ratings to sentiment categories for comparison
    rating_to_sentiment = {
        1: 'negative',
        2: 'negative',
        3: 'neutral',
        4: 'positive',
        5: 'positive'
    }
    df['rating_sentiment'] = df['rating'].map(rating_to_sentiment)
    
    return df

def generate_visualizations(df, output_dir='../../data/processed/visualizations'):
    """Generate and save visualizations for sentiment analysis."""
    if df.empty:
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    sns.set(style="whitegrid")
    
    # 1. Sentiment distribution
    plt.figure(figsize=(10, 6))
    ax = sns.countplot(x='sentiment', data=df, 
                      order=['positive', 'neutral', 'negative'])
    plt.title('Distribution of Sentiments in Reviews')
    plt.xlabel('Sentiment')
    plt.ylabel('Number of Reviews')
    
    # Add count labels on top of bars
    for p in ax.patches:
        ax.annotate(f'{p.get_height()}', 
                   (p.get_x() + p.get_width() / 2., p.get_height()),
                   ha='center', va='center', 
                   xytext=(0, 10), 
                   textcoords='offset points')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sentiment_distribution.png'))
    plt.close()
    
    # 2. Sentiment by bank
    plt.figure(figsize=(12, 6))
    bank_sentiment = pd.crosstab(df['bank'], df['sentiment'])
    bank_sentiment = bank_sentiment[['positive', 'neutral', 'negative']]
    bank_sentiment.plot(kind='bar', stacked=True, colormap='viridis')
    plt.title('Sentiment Distribution by Bank')
    plt.xlabel('Bank')
    plt.ylabel('Number of Reviews')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Sentiment')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sentiment_by_bank.png'))
    plt.close()
    
    # 3. Average sentiment score by bank
    plt.figure(figsize=(10, 6))
    avg_sentiment = df.groupby('bank')['polarity'].mean().sort_values()
    sns.barplot(x=avg_sentiment.index, y=avg_sentiment.values, palette='coolwarm')
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.title('Average Sentiment Score by Bank')
    plt.xlabel('Bank')
    plt.ylabel('Average Sentiment Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'avg_sentiment_by_bank.png'))
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")

def save_analysis_results(df, output_dir='../../data/processed'):
    """Save the analysis results to a CSV file."""
    if df.empty:
        return
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'reviews_with_sentiment_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    print(f"\nSaved analysis results to {filepath}")

def main():
    """Main function to run the sentiment analysis pipeline."""
    print("Starting sentiment analysis...")
    
    # Load cleaned data
    print("\nLoading cleaned review data...")
    df = load_cleaned_data()
    
    if df.empty:
        print("No data to analyze. Exiting.")
        return
    
    # Perform sentiment analysis
    df = add_sentiment_columns(df)
    
    # Generate visualizations
    generate_visualizations(df)
    
    # Save results
    save_analysis_results(df)
    
    # Print summary
    print("\n--- Analysis Summary ---")
    print(f"Total reviews analyzed: {len(df)}")
    print("\nSentiment distribution:")
    print(df['sentiment'].value_counts())
    print("\nAverage sentiment by bank:")
    print(df.groupby('bank')['polarity'].mean().sort_values(ascending=False))
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
