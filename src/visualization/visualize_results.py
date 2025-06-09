"""
Visualization Module for Banking App Reviews Analysis

This module provides functions to visualize the results of the sentiment and thematic analysis.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set style for visualizations
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 12

class ReviewVisualizer:
    def __init__(self, data_dir='../../data/analysis_results'):
        """Initialize the visualizer with data directory."""
        self.data_dir = data_dir
        self.sentiment_df = None
        self.bank_keywords = None
        self.topics_df = None
        
    def load_latest_results(self):
        """Load the most recent analysis results."""
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Directory {self.data_dir} does not exist.")
        
        # Find the most recent sentiment analysis file
        sentiment_files = [f for f in os.listdir(self.data_dir) 
                         if f.startswith('sentiment_analysis_') and f.endswith('.csv')]
        
        if not sentiment_files:
            raise FileNotFoundError("No sentiment analysis files found.")
        
        # Get the most recent file
        latest_sentiment = max(sentiment_files, 
                             key=lambda x: datetime.strptime(x.split('_')[-1].split('.')[0], '%Y%m%d_%H%M%S'))
        
        # Load sentiment data
        self.sentiment_df = pd.read_csv(os.path.join(self.data_dir, latest_sentiment), 
                                       parse_dates=['date'])
        
        # Load bank keywords
        bank_keywords_file = latest_sentiment.replace('sentiment_analysis_', 'bank_keywords_')
        if os.path.exists(os.path.join(self.data_dir, bank_keywords_file)):
            self.bank_keywords = pd.read_csv(os.path.join(self.data_dir, bank_keywords_file))
        
        # Load topics
        topics_file = latest_sentiment.replace('sentiment_analysis_', 'topics_')
        if os.path.exists(os.path.join(self.data_dir, topics_file)):
            self.topics_df = pd.read_csv(os.path.join(self.data_dir, topics_file))
    
    def plot_sentiment_distribution(self, save_path=None):
        """Plot the distribution of sentiment labels."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        plt.figure(figsize=(12, 6))
        ax = sns.countplot(data=self.sentiment_df, x='sentiment_label', 
                          order=['POSITIVE', 'NEUTRAL', 'NEGATIVE'])
        
        plt.title('Distribution of Sentiment in Reviews')
        plt.xlabel('Sentiment')
        plt.ylabel('Number of Reviews')
        
        # Add percentage labels
        total = len(self.sentiment_df)
        for p in ax.patches:
            height = p.get_height()
            ax.text(p.get_x() + p.get_width()/2., height + 10,
                   f'{height/total:.1%}'
                   f'\n({int(height)})',
                   ha='center')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved sentiment distribution plot to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def plot_sentiment_by_bank(self, save_path=None):
        """Plot sentiment distribution by bank."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        # Calculate percentages
        sentiment_by_bank = (self.sentiment_df.groupby(['bank', 'sentiment_label'])
                            .size()
                            .unstack()
                            .apply(lambda x: x/x.sum()*100, axis=1))
        
        # Reorder columns for consistent display
        sentiment_by_bank = sentiment_by_bank[['NEGATIVE', 'NEUTRAL', 'POSITIVE']]
        
        # Plot
        ax = sentiment_by_bank.plot(kind='barh', stacked=True, 
                                  color=['#e74c3c', '#f39c12', '#2ecc71'])
        
        plt.title('Sentiment Distribution by Bank')
        plt.xlabel('Percentage of Reviews')
        plt.ylabel('Bank')
        plt.legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add percentage labels
        for bank in sentiment_by_bank.index:
            pos = 0
            for sentiment in ['NEGATIVE', 'NEUTRAL', 'POSITIVE']:
                value = sentiment_by_bank.loc[bank, sentiment]
                if value > 5:  # Only show labels for values > 5%
                    ax.text(pos + value/2, bank, f'{value:.0f}%', 
                           va='center', ha='center', color='white', fontweight='bold')
                pos += value
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved sentiment by bank plot to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def plot_rating_distribution(self, save_path=None):
        """Plot the distribution of star ratings."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        # Count ratings
        rating_counts = self.sentiment_df['rating'].value_counts().sort_index()
        
        # Create bar plot
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=rating_counts.index, y=rating_counts.values, 
                        palette='viridis')
        
        plt.title('Distribution of Star Ratings')
        plt.xlabel('Star Rating')
        plt.ylabel('Number of Reviews')
        
        # Add count labels on top of bars
        for p in ax.patches:
            ax.annotate(f'{int(p.get_height())}', 
                       (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='center', 
                       xytext=(0, 10), 
                       textcoords='offset points')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved rating distribution plot to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def plot_rating_vs_sentiment(self, save_path=None):
        """Plot the relationship between star ratings and sentiment scores."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        plt.figure(figsize=(12, 6))
        
        # Create a box plot
        ax = sns.boxplot(x='rating', y='sentiment_score', 
                        data=self.sentiment_df, 
                        palette='viridis')
        
        plt.title('Sentiment Score Distribution by Star Rating')
        plt.xlabel('Star Rating')
        plt.ylabel('Sentiment Score')
        
        # Add median line
        medians = self.sentiment_df.groupby('rating')['sentiment_score'].median()
        for i, (rating, median) in enumerate(medians.items()):
            ax.text(i, median, f'{median:.2f}', 
                   horizontalalignment='center', 
                   size='medium', color='w', weight='semibold')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved rating vs sentiment plot to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def generate_word_cloud(self, bank_name=None, save_path=None):
        """Generate a word cloud for reviews of a specific bank or all banks."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        # Filter by bank if specified
        if bank_name:
            text = ' '.join(self.sentiment_df[self.sentiment_df['bank'] == bank_name]['review'].dropna())
            title = f'Word Cloud for {bank_name} Reviews'
        else:
            text = ' '.join(self.sentiment_df['review'].dropna())
            title = 'Word Cloud for All Bank Reviews'
        
        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, 
                             background_color='white',
                             max_words=100,
                             contour_width=3, 
                             contour_color='steelblue')
        
        wordcloud.generate(text)
        
        # Display the word cloud
        plt.figure(figsize=(14, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.title(title, fontsize=20)
        plt.axis('off')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved word cloud to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def plot_topics(self, save_path=None):
        """Visualize the topics discovered through LDA."""
        if self.topics_df is None:
            self.load_latest_results()
        
        if self.topics_df is None or self.topics_df.empty:
            print("No topic data available.")
            return
        
        # Create a bar plot for each topic
        n_topics = len(self.topics_df)
        n_cols = min(3, n_topics)
        n_rows = (n_topics + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4 * n_rows))
        if n_rows == 1:
            axes = [axes]
        
        for idx, (_, row) in enumerate(self.topics_df.iterrows()):
            ax = axes[idx // n_cols][idx % n_cols]
            
            # Split top words and their weights
            words = [w.strip() for w in row['top_words'].split(',')]
            weights = [1.0] * len(words)  # Equal weights for simplicity
            
            # Plot horizontal bar chart
            y_pos = range(len(words))
            ax.barh(y_pos, weights[::-1], align='center', color='skyblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(words[::-1])
            ax.set_title(f'Topic {row["topic_id"] + 1}')
            ax.set_xlim(0, 1.1)
            
            # Remove x-axis labels
            ax.set_xticks([])
        
        # Remove empty subplots
        for i in range(n_topics, n_rows * n_cols):
            fig.delaxes(axes[i // n_cols][i % n_cols])
        
        plt.suptitle('Discovered Topics', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust layout to make room for suptitle
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"Saved topics plot to {save_path}")
        
        plt.show()
    
    def generate_all_visualizations(self, output_dir='../../reports/figures'):
        """Generate all visualizations and save them to files."""
        if self.sentiment_df is None:
            self.load_latest_results()
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate and save all visualizations
        self.plot_sentiment_distribution(
            os.path.join(output_dir, 'sentiment_distribution.png'))
        
        self.plot_sentiment_by_bank(
            os.path.join(output_dir, 'sentiment_by_bank.png'))
        
        self.plot_rating_distribution(
            os.path.join(output_dir, 'rating_distribution.png'))
        
        self.plot_rating_vs_sentiment(
            os.path.join(output_dir, 'rating_vs_sentiment.png'))
        
        # Word clouds for each bank and overall
        banks = list(self.sentiment_df['bank'].unique()) + [None]
        for bank in banks:
            bank_name = bank if bank else 'all_banks'
            self.generate_word_cloud(
                bank,
                os.path.join(output_dir, f'wordcloud_{bank_name.lower().replace(" ", "_")}.png')
            )
        
        # Topics visualization if available
        if self.topics_df is not None and not self.topics_df.empty:
            self.plot_topics(os.path.join(output_dir, 'topics.png'))
        
        print(f"\nAll visualizations have been saved to: {os.path.abspath(output_dir)}")

def main():
    """Main function to generate all visualizations."""
    try:
        visualizer = ReviewVisualizer()
        visualizer.generate_all_visualizations()
        print("\nVisualization generation complete!")
    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        raise

if __name__ == "__main__":
    main()
