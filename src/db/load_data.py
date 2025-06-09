"""
Data Loading Script for Banking App Reviews

This script loads processed review data from CSV/JSON files into the database.
It handles data validation, transformation, and batch insertion.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_loading.log')
    ]
)
logger = logging.getLogger(__name__)

# Import database module
from .database import DatabaseManager

class DataLoader:
    """Handles loading of processed review data into the database."""
    
    def __init__(self, db_type: str = 'oracle', **db_params):
        """
        Initialize the DataLoader.
        
        Args:
            db_type: Type of database ('oracle' or 'postgresql')
            **db_params: Additional database connection parameters
        """
        self.db = DatabaseManager(db_type=db_type, **db_params)
        self.processed_data_dir = Path('data/processed')
        self.supported_formats = ['.csv', '.json']
    
    def connect(self) -> bool:
        """Establish database connection."""
        return self.db.connect()
    
    def disconnect(self):
        """Close database connection."""
        self.db.disconnect()
    
    def ensure_tables_exist(self) -> bool:
        """Ensure required database tables exist."""
        return self.db.create_tables()
    
    def load_file(self, file_path: Union[str, Path]) -> Optional[pd.DataFrame]:
        """
        Load data from a file (CSV or JSON).
        
        Args:
            file_path: Path to the input file
            
        Returns:
            pd.DataFrame: Loaded data, or None if loading failed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            if file_path.suffix.lower() == '.csv':
                return pd.read_csv(file_path, parse_dates=['date'], infer_datetime_format=True)
            elif file_path.suffix.lower() == '.json':
                return pd.read_json(file_path, convert_dates=['date'])
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return None
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return None
    
    def transform_review_data(self, df: pd.DataFrame, bank_id: str) -> List[Dict[str, Any]]:
        """
        Transform review data for database insertion.
        
        Args:
            df: DataFrame containing review data
            bank_id: ID of the bank
            
        Returns:
            List of dictionaries ready for database insertion
        """
        if df.empty:
            return []
        
        # Ensure required columns exist
        required_columns = ['review_id', 'content', 'score', 'at', 'userName', 'thumbsUpCount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {', '.join(missing_columns)}")
            return []
        
        # Handle potentially missing NLP columns
        df['processed_text'] = df.get('processed_text', df['content'])
        df['tokens'] = df.get('tokens', '').apply(lambda x: x if isinstance(x, (list, dict)) else [])
        df['sentiment_label'] = df.get('sentiment_label', '')
        df['sentiment_score'] = pd.to_numeric(df.get('sentiment_score', 0), errors='coerce').fillna(0)
        df['theme'] = df.get('theme', '').apply(lambda x: [x] if isinstance(x, str) else (x if isinstance(x, list) else []))
        df['keywords'] = df.get('keywords', '').apply(lambda x: x if isinstance(x, list) else [])
        
        # Transform data
        reviews = []
        for _, row in df.iterrows():
            review = {
                'review_id': str(row['review_id']),
                'bank': bank_id,
                'original_text': str(row['content'])[:4000],  # Truncate to avoid CLOB overflow
                'processed_text': str(row['processed_text'])[:4000],
                'tokens': row['tokens'],
                'sentiment_label': str(row['sentiment_label']).lower()[:10],
                'sentiment_score': float(row['sentiment_score']),
                'theme': row['theme'],
                'keywords': row['keywords'],
                'rating': float(row['score']),
                'date': pd.to_datetime(row['at']).to_pydatetime(),
                'user_name': str(row['userName'])[:100],
                'thumbs_up': int(row['thumbsUpCount']),
                'source': 'google_play'
            }
            reviews.append(review)
        
        return reviews
    
    def process_directory(self, directory: Union[str, Path] = None) -> bool:
        """
        Process all data files in a directory.
        
        Args:
            directory: Directory containing processed data files
            
        Returns:
            bool: True if all files were processed successfully, False otherwise
        """
        if directory is None:
            directory = self.processed_data_dir
        
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory not found: {directory}")
            return False
        
        # Ensure database connection and tables exist
        if not self.db.connect():
            return False
        
        if not self.ensure_tables_exist():
            return False
        
        # Process each file in the directory
        success = True
        processed_files = 0
        
        for file_path in directory.glob('*'):
            if file_path.suffix.lower() not in self.supported_formats:
                continue
                
            logger.info(f"Processing file: {file_path.name}")
            
            # Extract bank ID from filename (format: {bank_name}_reviews_*.{ext})
            bank_id = file_path.stem.split('_reviews_')[0].upper()
            if not bank_id:
                logger.warning(f"Could not determine bank ID from filename: {file_path.name}")
                bank_id = 'UNKNOWN'
            
            # Load and transform data
            df = self.load_file(file_path)
            if df is None or df.empty:
                logger.warning(f"No data loaded from {file_path.name}")
                success = False
                continue
            
            reviews = self.transform_review_data(df, bank_id)
            if not reviews:
                logger.warning(f"No valid reviews found in {file_path.name}")
                success = False
                continue
            
            # Insert data in batches
            if not self.db.batch_insert_reviews(reviews):
                logger.error(f"Failed to insert reviews from {file_path.name}")
                success = False
                continue
            
            processed_files += 1
            logger.info(f"Successfully processed {len(reviews)} reviews from {file_path.name}")
        
        # Log summary
        if processed_files > 0:
            logger.info(f"Processed {processed_files} files successfully")
        else:
            logger.warning("No files were processed")
            success = False
            
        return success
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.
        
        Returns:
            Dictionary containing loading statistics
        """
        if not self.db.connect():
            return {}
        
        try:
            stats = {}
            
            # Get total reviews count
            self.db.cursor.execute("SELECT COUNT(*) FROM reviews")
            stats['total_reviews'] = self.db.cursor.fetchone()[0]
            
            # Get reviews by bank
            self.db.cursor.execute("""
                SELECT b.bank_name, COUNT(*) as count 
                FROM reviews r 
                JOIN banks b ON r.bank_id = b.bank_id 
                GROUP BY b.bank_name
            """)
            stats['reviews_by_bank'] = dict(self.db.cursor.fetchall())
            
            # Get sentiment distribution
            self.db.cursor.execute("""
                SELECT sentiment_label, COUNT(*) as count 
                FROM reviews 
                GROUP BY sentiment_label
            """)
            stats['sentiment_distribution'] = dict(self.db.cursor.fetchall())
            
            # Get average rating
            self.db.cursor.execute("SELECT AVG(rating) FROM reviews")
            stats['average_rating'] = round(float(self.db.cursor.fetchone()[0] or 0), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting loading stats: {str(e)}")
            return {}

def main():
    """Main function to run the data loading process."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load processed review data into the database.')
    parser.add_argument('--db-type', type=str, default='oracle',
                       choices=['oracle', 'postgresql'],
                       help='Database type (default: oracle)')
    parser.add_argument('--db-host', type=str, default=None,
                       help='Database host')
    parser.add_argument('--db-port', type=str, default=None,
                       help='Database port')
    parser.add_argument('--db-name', type=str, default=None,
                       help='Database name (for PostgreSQL)')
    parser.add_argument('--db-service', type=str, default=None,
                       help='Database service name (for Oracle)')
    parser.add_argument('--db-user', type=str, default=None,
                       help='Database username')
    parser.add_argument('--db-password', type=str, default=None,
                       help='Database password')
    parser.add_argument('--input-dir', type=str, default='data/processed',
                       help='Directory containing processed data files')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (does not modify database)')
    
    args = parser.parse_args()
    
    # Initialize data loader
    db_params = {
        'host': args.db_host,
        'port': args.db_port,
        'user': args.db_user,
        'password': args.db_password,
    }
    
    if args.db_type == 'oracle':
        db_params['service_name'] = args.db_service or 'XE'
    else:  # postgresql
        db_params['database'] = args.db_name or 'bank_reviews'
    
    data_loader = DataLoader(db_type=args.db_type, **db_params)
    
    if args.test:
        # Test database connection and table creation
        print("Running in test mode...")
        if not data_loader.connect():
            print("❌ Database connection failed")
            return 1
            
        if not data_loader.ensure_tables_exist():
            print("❌ Table creation failed")
            return 1
            
        print("✅ Database connection and table creation successful")
        print("\nSample data loading test:")
        
        # Create a test DataFrame
        test_data = {
            'review_id': ['test1', 'test2'],
            'content': ['Great app!', 'Needs improvement'],
            'score': [5, 2],
            'at': [pd.Timestamp.now()] * 2,
            'userName': ['user1', 'user2'],
            'thumbsUpCount': [10, 2],
            'processed_text': ['great app', 'needs improvement'],
            'sentiment_label': ['positive', 'negative'],
            'sentiment_score': [0.9, -0.3],
            'theme': [['usability'], ['bugs']],
            'keywords': [['great', 'app'], ['needs', 'improvement']]
        }
        
        test_df = pd.DataFrame(test_data)
        test_reviews = data_loader.transform_review_data(test_df, 'TEST')
        
        if not test_reviews:
            print("❌ Test data transformation failed")
            return 1
            
        print("✅ Test data transformation successful")
        print("\nTest reviews to be inserted:")
        for i, review in enumerate(test_reviews, 1):
            print(f"{i}. {review['review_id']}: {review['original_text'][:50]}...")
        
        # Don't actually insert in test mode
        print("\n✅ Test completed successfully (no data was actually inserted)")
        return 0
    
    # Process the directory
    print(f"Loading data from: {args.input_dir}")
    success = data_loader.process_directory(args.input_dir)
    
    if success:
        print("\n✅ Data loading completed successfully!")
        
        # Print loading statistics
        stats = data_loader.get_loading_stats()
        if stats:
            print("\nLoading Statistics:")
            print(f"- Total reviews loaded: {stats.get('total_reviews', 0)}")
            print("- Reviews by bank:")
            for bank, count in stats.get('reviews_by_bank', {}).items():
                print(f"  - {bank}: {count}")
            print("- Sentiment distribution:")
            for sentiment, count in stats.get('sentiment_distribution', {}).items():
                print(f"  - {sentiment}: {count}")
            print(f"- Average rating: {stats.get('average_rating', 0)}/5")
    else:
        print("\n❌ Data loading completed with errors. Please check the logs for details.")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
