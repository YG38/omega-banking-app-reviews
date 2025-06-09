"""
Advanced Sentiment and Thematic Analysis for Banking App Reviews

This script performs:
1. Sentiment analysis using DistilBERT
2. Thematic analysis using TF-IDF and clustering
3. Visualization of results
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict
import re
import string

# Text processing
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams

# NLP and ML
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
import pyLDAvis.sklearn

# Deep Learning
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Set style for visualizations
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class BankingReviewAnalyzer:
    def __init__(self, data_dir='../../data/processed'):
        """Initialize the analyzer with data directory."""
        self.data_dir = data_dir
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.sentiment_analyzer = None
        self.vectorizer = None
        self.lda_model = None
        self.kmeans = None
        
        # Download required NLTK data
        self._download_nltk_data()
        
    def _download_nltk_data(self):
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
    
    def load_data(self):
        """Load the most recent cleaned reviews file."""
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Directory {self.data_dir} does not exist.")
        
        # Find all cleaned review files
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith('cleaned_reviews_') and f.endswith('.csv')]
        
        if not files:
            raise FileNotFoundError("No cleaned review files found.")
        
        # Get the most recent file
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)))
        filepath = os.path.join(self.data_dir, latest_file)
        
        try:
            self.df = pd.read_csv(filepath, parse_dates=['date'], infer_datetime_format=True)
            print(f"Loaded {len(self.df)} reviews from {latest_file}")
            return self.df
        except Exception as e:
            raise Exception(f"Error loading {latest_file}: {str(e)}")
    
    def preprocess_text(self, text):
        """Preprocess text for analysis."""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word not in stop_words]
        
        # Lemmatization
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        
        return ' '.join(tokens)
    
    def initialize_sentiment_analyzer(self):
        """Initialize the DistilBERT sentiment analyzer."""
        print("Initializing DistilBERT sentiment analyzer...")
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                          model=model_name, 
                                          device=0 if self.device == 'cuda' else -1)
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of a text using DistilBERT."""
        if not self.sentiment_analyzer:
            self.initialize_sentiment_analyzer()
        
        if not text or not isinstance(text, str) or not text.strip():
            return {'label': 'NEUTRAL', 'score': 0.5}
        
        try:
            result = self.sentiment_analyzer(text[:512])[0]  # Truncate to max length
            return {
                'label': result['label'],
                'score': result['score'] if result['label'] == 'POSITIVE' else 1 - result['score']
            }
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return {'label': 'NEUTRAL', 'score': 0.5}
    
    def add_sentiment_columns(self):
        """Add sentiment analysis columns to the DataFrame."""
        print("Performing sentiment analysis...")
        sentiment_results = self.df['review'].apply(self.analyze_sentiment)
        self.df['sentiment_label'] = sentiment_results.apply(lambda x: x['label'])
        self.df['sentiment_score'] = sentiment_results.apply(lambda x: x['score'])
        return self.df
    
    def extract_keywords(self, n_top_words=10):
        """Extract keywords using TF-IDF."""
        print("Extracting keywords...")
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)  # Include unigrams and bigrams
        )
        
        # Fit and transform the text data
        tfidf_matrix = self.vectorizer.fit_transform(self.df['review'])
        
        # Get feature names (words/terms)
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get top keywords for each bank
        bank_keywords = {}
        for bank in self.df['bank'].unique():
            bank_indices = self.df[self.df['bank'] == bank].index
            bank_tfidf = tfidf_matrix[bank_indices]
            
            # Calculate average TF-IDF scores across all documents for this bank
            avg_tfidf = np.asarray(bank_tfidf.mean(axis=0)).flatten()
            
            # Get top n words with highest TF-IDF scores
            top_indices = avg_tfidf.argsort()[-n_top_words:][::-1]
            bank_keywords[bank] = [feature_names[i] for i in top_indices]
        
        return bank_keywords
    
    def perform_lda(self, n_topics=5, n_top_words=10):
        """Perform LDA topic modeling."""
        print("Performing LDA topic modeling...")
        
        # Create document-term matrix
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            dtm = self.vectorizer.fit_transform(self.df['review'])
        else:
            dtm = self.vectorizer.transform(self.df['review'])
        
        # Train LDA model
        self.lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            learning_method='online',
            max_iter=10
        )
        
        lda_output = self.lda_model.fit_transform(dtm)
        
        # Get top words for each topic
        feature_names = self.vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_words_idx = topic.argsort()[:-n_top_words - 1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topics.append({
                'topic_id': topic_idx,
                'top_words': ', '.join(top_words)
            })
        
        return pd.DataFrame(topics)
    
    def cluster_reviews(self, n_clusters=5):
        """Cluster reviews using K-means."""
        print("Clustering reviews...")
        
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            features = self.vectorizer.fit_transform(self.df['review'])
        else:
            features = self.vectorizer.transform(self.df['review'])
        
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = self.kmeans.fit_predict(features)
        
        # Get top terms per cluster
        order_centroids = self.kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = self.vectorizer.get_feature_names_out()
        
        cluster_terms = {}
        for i in range(n_clusters):
            cluster_terms[i] = [terms[ind] for ind in order_centroids[i, :10]]
        
        return cluster_terms
    
    def analyze(self):
        """Run the complete analysis pipeline."""
        # Load data
        self.load_data()
        
        # Preprocess text
        print("Preprocessing text...")
        self.df['cleaned_review'] = self.df['review'].apply(self.preprocess_text)
        
        # Sentiment analysis
        self.add_sentiment_columns()
        
        # Extract keywords
        bank_keywords = self.extract_keywords()
        
        # Topic modeling
        topics_df = self.perform_lda()
        
        # Clustering
        cluster_terms = self.cluster_reviews()
        
        return {
            'sentiment_analysis': self.df[['review', 'bank', 'rating', 'sentiment_label', 'sentiment_score']],
            'bank_keywords': bank_keywords,
            'topics': topics_df,
            'clusters': cluster_terms
        }
    
    def save_results(self, output_dir='../../data/analysis_results'):
        """Save analysis results to files."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save sentiment analysis results
        sentiment_file = os.path.join(output_dir, f'sentiment_analysis_{timestamp}.csv')
        self.df.to_csv(sentiment_file, index=False)
        
        # Save bank keywords
        bank_keywords = self.extract_keywords()
        bank_keywords_df = pd.DataFrame({
            'bank': bank_keywords.keys(),
            'top_keywords': [', '.join(keywords) for keywords in bank_keywords.values()]
        })
        keywords_file = os.path.join(output_dir, f'bank_keywords_{timestamp}.csv')
        bank_keywords_df.to_csv(keywords_file, index=False)
        
        # Save topics
        topics_df = self.perform_lda()
        topics_file = os.path.join(output_dir, f'topics_{timestamp}.csv')
        topics_df.to_csv(topics_file, index=False)
        
        print(f"Analysis results saved to {output_dir}")
        
        return {
            'sentiment_file': sentiment_file,
            'keywords_file': keywords_file,
            'topics_file': topics_file
        }

def main():
    """Main function to run the analysis."""
    try:
        analyzer = BankingReviewAnalyzer()
        results = analyzer.analyze()
        output_files = analyzer.save_results()
        
        print("\nAnalysis complete!")
        print(f"- Sentiment analysis saved to: {output_files['sentiment_file']}")
        print(f"- Bank keywords saved to: {output_files['keywords_file']}")
        print(f"- Topics saved to: {output_files['topics_file']}")
        
        # Print some summary statistics
        print("\nSentiment Distribution:")
        print(results['sentiment_analysis']['sentiment_label'].value_counts())
        
        print("\nTop Keywords by Bank:")
        for bank, keywords in results['bank_keywords'].items():
            print(f"\n{bank}:")
            print(", ".join(keywords))
        
        print("\nTopics Discovered:")
        print(results['topics'])
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
