"""
Database Operations for Banking App Reviews

This module handles all database operations including:
1. Connecting to Oracle/PostgreSQL databases
2. Creating necessary tables
3. Inserting processed review data
4. Running queries
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Union
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for the reviews database."""
    
    def __init__(self, db_type: str = 'oracle', **kwargs):
        """
        Initialize the database manager.
        
        Args:
            db_type: Type of database ('oracle' or 'postgresql')
            **kwargs: Database connection parameters
        """
        self.db_type = db_type.lower()
        self.connection = None
        self.cursor = None
        self.params = kwargs
        
        # Default connection parameters
        self.default_params = {
            'oracle': {
                'user': os.getenv('ORACLE_USER', 'system'),
                'password': os.getenv('ORACLE_PASSWORD', 'oracle'),
                'dsn': os.getenv('ORACLE_DSN', 'localhost:1521/XE'),
                'service_name': os.getenv('ORACLE_SERVICE', 'XE')
            },
            'postgresql': {
                'host': os.getenv('PGHOST', 'localhost'),
                'port': os.getenv('PGPORT', '5432'),
                'database': os.getenv('PGDATABASE', 'bank_reviews'),
                'user': os.getenv('PGUSER', 'postgres'),
                'password': os.getenv('PGPASSWORD', 'postgres')
            }
        }
        
        # Update with provided parameters
        if self.db_type in self.default_params:
            self.default_params[self.db_type].update(kwargs)
    
    def connect(self) -> bool:
        """
        Establish a database connection.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if self.db_type == 'oracle':
                import oracledb
                
                # Set up the connection parameters
                dsn = self.params.get('dsn') or f"{self.params.get('host', 'localhost')}:{self.params.get('port', '1521')}/{self.params.get('service_name', 'XE')}"
                
                # Connect to Oracle
                self.connection = oracledb.connect(
                    user=self.params.get('user'),
                    password=self.params.get('password'),
                    dsn=dsn
                )
                logger.info(f"Connected to Oracle Database: {self.connection.version}")
                
            elif self.db_type == 'postgresql':
                import psycopg2
                
                # Connect to PostgreSQL
                self.connection = psycopg2.connect(
                    host=self.params.get('host'),
                    port=self.params.get('port'),
                    database=self.params.get('database'),
                    user=self.params.get('user'),
                    password=self.params.get('password')
                )
                self.connection.autocommit = True
                logger.info("Connected to PostgreSQL database")
                
            self.cursor = self.connection.cursor()
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            self.connection = None
            self.cursor = None
            return False
    
    def disconnect(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def create_tables(self) -> bool:
        """
        Create necessary tables in the database.
        
        Returns:
            bool: True if tables were created successfully, False otherwise
        """
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            # Create banks table
            banks_table_sql = """
            CREATE TABLE IF NOT EXISTS banks (
                bank_id VARCHAR2(10) PRIMARY KEY,
                bank_name VARCHAR2(100) NOT NULL,
                app_name VARCHAR2(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # Create reviews table
            reviews_table_sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                review_id VARCHAR2(50) PRIMARY KEY,
                bank_id VARCHAR2(10) NOT NULL,
                original_text CLOB,
                processed_text CLOB,
                tokens CLOB,
                sentiment_label VARCHAR2(10),
                sentiment_score FLOAT,
                theme VARCHAR2(100),
                keywords CLOB,
                rating NUMBER(2,1),
                review_date TIMESTAMP,
                user_name VARCHAR2(100),
                thumbs_up NUMBER(10),
                source VARCHAR2(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bank_id) REFERENCES banks(bank_id)
            )
            """
            
            # Modify SQL for PostgreSQL
            if self.db_type == 'postgresql':
                banks_table_sql = banks_table_sql.replace('VARCHAR2', 'VARCHAR')
                banks_table_sql = banks_table_sql.replace('NUMBER', 'INTEGER')
                reviews_table_sql = reviews_table_sql.replace('VARCHAR2', 'VARCHAR')
                reviews_table_sql = reviews_table_sql.replace('NUMBER(2,1)', 'NUMERIC(2,1)')
                reviews_table_sql = reviews_table_sql.replace('NUMBER(10)', 'INTEGER')
                reviews_table_sql = reviews_table_sql.replace('CLOB', 'TEXT')
            
            # Execute table creation
            self.cursor.execute(banks_table_sql)
            self.cursor.execute(reviews_table_sql)
            
            # Create indexes
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON reviews(bank_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)")
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_bank(self, bank_id: str, bank_name: str, app_name: str = None) -> bool:
        """
        Insert a new bank into the database.
        
        Args:
            bank_id: Unique identifier for the bank
            bank_name: Name of the bank
            app_name: Name of the bank's app (optional)
            
        Returns:
            bool: True if insertion was successful, False otherwise
        """
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            sql = """
            INSERT INTO banks (bank_id, bank_name, app_name)
            VALUES (:1, :2, :3)
            ON CONFLICT (bank_id) DO NOTHING
            """
            
            if self.db_type == 'postgresql':
                sql = sql.replace(':1', '%s').replace(':2', '%s').replace(':3', '%s')
                
            self.cursor.execute(sql, (bank_id, bank_name, app_name))
            self.connection.commit()
            logger.info(f"Inserted/updated bank: {bank_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting bank: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_review(self, review_data: Dict[str, Any]) -> bool:
        """
        Insert a review into the database.
        
        Args:
            review_data: Dictionary containing review data
            
        Returns:
            bool: True if insertion was successful, False otherwise
        """
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            # Prepare data
            bank_id = review_data.get('bank')
            if not bank_id:
                logger.error("Missing bank_id in review data")
                return False
            
            # Insert bank if not exists
            self.insert_bank(bank_id=bank_id, bank_name=bank_id)
            
            # Handle list/tuple fields
            tokens = review_data.get('tokens', [])
            if isinstance(tokens, (list, tuple)):
                tokens = json.dumps(tokens)
                
            keywords = review_data.get('keywords', [])
            if isinstance(keywords, (list, tuple)):
                keywords = json.dumps(keywords)
                
            theme = review_data.get('theme', [])
            if isinstance(theme, (list, tuple)):
                theme = ', '.join(theme)
            
            # Prepare SQL and parameters
            sql = """
            INSERT INTO reviews (
                review_id, bank_id, original_text, processed_text, tokens,
                sentiment_label, sentiment_score, theme, keywords, rating,
                review_date, user_name, thumbs_up, source
            ) VALUES (
                :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14
            )
            ON CONFLICT (review_id) DO UPDATE SET
                sentiment_label = EXCLUDED.sentiment_label,
                sentiment_score = EXCLUDED.sentiment_score,
                theme = EXCLUDED.theme,
                keywords = EXCLUDED.keywords,
                thumbs_up = EXCLUDED.thumbs_up
            """
            
            # Handle parameter style for PostgreSQL
            if self.db_type == 'postgresql':
                sql = sql.replace(':1', '%s').replace(':2', '%s').replace(':3', '%s')\
                    .replace(':4', '%s').replace(':5', '%s').replace(':6', '%s')\
                    .replace(':7', '%s').replace(':8', '%s').replace(':9', '%s')\
                    .replace(':10', '%s').replace(':11', '%s').replace(':12', '%s')\
                    .replace(':13', '%s').replace(':14', '%s')
            
            # Execute the query
            self.cursor.execute(sql, (
                review_data.get('review_id'),
                bank_id,
                review_data.get('original_text'),
                review_data.get('processed_text'),
                tokens,
                review_data.get('sentiment_label'),
                review_data.get('sentiment_score'),
                theme,
                keywords,
                review_data.get('rating'),
                review_data.get('date'),
                review_data.get('user_name'),
                review_data.get('thumbs_up'),
                review_data.get('source')
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting review: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def batch_insert_reviews(self, reviews_data: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """
        Insert multiple reviews in batches.
        
        Args:
            reviews_data: List of review dictionaries
            batch_size: Number of reviews to insert in each batch
            
        Returns:
            bool: True if all batches were inserted successfully, False otherwise
        """
        if not reviews_data:
            return True
            
        success = True
        total_reviews = len(reviews_data)
        
        for i in range(0, total_reviews, batch_size):
            batch = reviews_data[i:i + batch_size]
            batch_success = all(self.insert_review(review) for review in batch)
            success = success and batch_success
            
            if not batch_success:
                logger.warning(f"Failed to insert batch {i//batch_size + 1}")
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(total_reviews + batch_size - 1)//batch_size}")
        
        return success
    
    def get_reviews_by_bank(self, bank_id: str, limit: int = 100) -> pd.DataFrame:
        """
        Retrieve reviews for a specific bank.
        
        Args:
            bank_id: ID of the bank
            limit: Maximum number of reviews to return
            
        Returns:
            pd.DataFrame: DataFrame containing the reviews
        """
        if not self.connection:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            sql = """
            SELECT r.*, b.bank_name
            FROM reviews r
            JOIN banks b ON r.bank_id = b.bank_id
            WHERE r.bank_id = :1
            ORDER BY r.review_date DESC
            LIMIT :2
            """
            
            if self.db_type == 'oracle':
                sql = sql.replace('LIMIT :2', 'AND ROWNUM <= :2')
            
            if self.db_type == 'postgresql':
                sql = sql.replace(':1', '%s').replace(':2', '%s')
            
            self.cursor.execute(sql, (bank_id, limit))
            columns = [col[0] for col in self.cursor.description]
            data = self.cursor.fetchall()
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            logger.error(f"Error retrieving reviews: {str(e)}")
            return pd.DataFrame()
    
    def get_sentiment_summary(self, bank_id: str = None) -> pd.DataFrame:
        """
        Get sentiment summary statistics.
        
        Args:
            bank_id: Optional bank ID to filter by
            
        Returns:
            pd.DataFrame: Sentiment summary statistics
        """
        if not self.connection:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            sql = """
            SELECT 
                b.bank_name,
                r.sentiment_label,
                COUNT(*) as review_count,
                ROUND(AVG(r.sentiment_score), 4) as avg_sentiment,
                ROUND(AVG(r.rating), 2) as avg_rating
            FROM reviews r
            JOIN banks b ON r.bank_id = b.bank_id
            {}
            GROUP BY b.bank_name, r.sentiment_label
            ORDER BY b.bank_name, r.sentiment_label
            """
            
            where_clause = "WHERE r.bank_id = :1" if bank_id else ""
            sql = sql.format(where_clause)
            
            params = (bank_id,) if bank_id else ()
            
            if self.db_type == 'postgresql':
                sql = sql.replace(':1', '%s')
            
            self.cursor.execute(sql, params)
            columns = [col[0] for col in self.cursor.description]
            data = self.cursor.fetchall()
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            logger.error(f"Error retrieving sentiment summary: {str(e)}")
            return pd.DataFrame()


def test_database_connection():
    """Test database connection and basic operations."""
    # Try Oracle first, fall back to PostgreSQL if Oracle fails
    db = DatabaseManager(db_type='oracle')
    
    if not db.connect():
        print("Oracle connection failed, trying PostgreSQL...")
        db = DatabaseManager(db_type='postgresql')
        if not db.connect():
            print("PostgreSQL connection also failed.")
            return False
    
    try:
        # Test table creation
        if not db.create_tables():
            print("Table creation failed")
            return False
        
        # Test bank insertion
        test_bank = {
            'bank_id': 'TEST',
            'bank_name': 'Test Bank',
            'app_name': 'Test Bank App'
        }
        
        if not db.insert_bank(**test_bank):
            print("Bank insertion failed")
            return False
        
        # Test review insertion
        test_review = {
            'review_id': 'test_review_1',
            'bank': 'TEST',
            'original_text': 'This is a test review',
            'processed_text': 'test review',
            'tokens': ['test', 'review'],
            'sentiment_label': 'positive',
            'sentiment_score': 0.8,
            'theme': 'testing',
            'keywords': ['test', 'review'],
            'rating': 5.0,
            'date': datetime.now(),
            'user_name': 'tester',
            'thumbs_up': 0,
            'source': 'test'
        }
        
        if not db.insert_review(test_review):
            print("Review insertion failed")
            return False
        
        # Test query
        reviews = db.get_reviews_by_bank('TEST')
        if reviews.empty:
            print("No reviews found")
            return False
            
        print("\nTest review inserted successfully:")
        print(reviews[['review_id', 'original_text', 'sentiment_label', 'rating']].to_string())
        
        # Clean up
        db.cursor.execute("DELETE FROM reviews WHERE bank_id = :1", ('TEST',))
        db.cursor.execute("DELETE FROM banks WHERE bank_id = :1", ('TEST',))
        db.connection.commit()
        
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("Testing database connection and operations...")
    if test_database_connection():
        print("\n✅ Database test completed successfully!")
    else:
        print("\n❌ Database test failed. Please check the error messages above.")
