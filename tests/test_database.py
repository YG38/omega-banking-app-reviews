"""
Tests for the database module.

These tests verify that the database connection, table creation, and basic CRUD operations work as expected.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import DatabaseManager

class TestDatabase(unittest.TestCase):
    """Test cases for the database module."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for test data
        cls.test_dir = tempfile.mkdtemp()
        
        # Initialize database connection
        cls.db_type = os.getenv('TEST_DB_TYPE', 'postgresql')
        
        if cls.db_type == 'postgresql':
            # Use a test database for PostgreSQL
            cls.db_params = {
                'host': os.getenv('TEST_DB_HOST', 'localhost'),
                'port': os.getenv('TEST_DB_PORT', '5432'),
                'database': os.getenv('TEST_DB_NAME', 'test_bank_reviews'),
                'user': os.getenv('TEST_DB_USER', 'postgres'),
                'password': os.getenv('TEST_DB_PASSWORD', 'postgres')
            }
        else:  # oracle
            # Use the default Oracle XE configuration
            cls.db_params = {
                'host': os.getenv('TEST_DB_HOST', 'localhost'),
                'port': os.getenv('TEST_DB_PORT', '1521'),
                'service_name': os.getenv('TEST_DB_SERVICE', 'XE'),
                'user': os.getenv('TEST_DB_USER', 'system'),
                'password': os.getenv('TEST_DB_PASSWORD', 'oracle')
            }
        
        # Initialize the database manager
        cls.db = DatabaseManager(db_type=cls.db_type, **cls.db_params)
        
        # Create test data
        cls.test_bank = {
            'bank_id': 'TEST',
            'bank_name': 'Test Bank',
            'app_name': 'Test Bank App'
        }
        
        cls.test_review = {
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
    
    def setUp(self):
        """Set up test fixtures."""
        # Connect to the database
        self.assertTrue(self.db.connect(), "Failed to connect to the database")
        
        # Create tables
        self.assertTrue(self.db.create_tables(), "Failed to create tables")
    
    def tearDown(self):
        """Clean up after each test."""
        # Drop all tables
        if self.db.connection:
            try:
                if self.db.db_type == 'postgresql':
                    self.db.cursor.execute("DROP TABLE IF EXISTS reviews CASCADE")
                    self.db.cursor.execute("DROP TABLE IF EXISTS banks CASCADE")
                else:  # oracle
                    self.db.cursor.execute("BEGIN EXECUTE IMMEDIATE 'DROP TABLE reviews CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;")
                    self.db.cursor.execute("BEGIN EXECUTE IMMEDIATE 'DROP TABLE banks CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;")
                self.db.connection.commit()
            except Exception as e:
                print(f"Error dropping tables: {e}")
                if self.db.connection:
                    self.db.connection.rollback()
        
        # Disconnect
        self.db.disconnect()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        # Remove temporary directory
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def test_connection(self):
        """Test database connection."""
        self.assertTrue(self.db.connect(), "Failed to connect to the database")
        self.assertIsNotNone(self.db.connection, "Database connection is None")
        self.assertIsNotNone(self.db.cursor, "Database cursor is None")
    
    def test_table_creation(self):
        """Test table creation."""
        # Check if tables exist
        if self.db.db_type == 'postgresql':
            self.db.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('banks', 'reviews')
            """)
        else:  # oracle
            self.db.cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE table_name IN ('BANKS', 'REVIEWS')
            """)
        
        tables = [row[0].lower() for row in self.db.cursor.fetchall()]
        self.assertIn('banks', tables, "Banks table was not created")
        self.assertIn('reviews', tables, "Reviews table was not created")
    
    def test_insert_bank(self):
        """Test inserting a bank."""
        # Insert a test bank
        result = self.db.insert_bank(
            bank_id=self.test_bank['bank_id'],
            bank_name=self.test_bank['bank_name'],
            app_name=self.test_bank['app_name']
        )
        
        self.assertTrue(result, "Failed to insert bank")
        
        # Verify the bank was inserted
        if self.db.db_type == 'postgresql':
            self.db.cursor.execute("SELECT * FROM banks WHERE bank_id = %s", (self.test_bank['bank_id'],))
        else:  # oracle
            self.db.cursor.execute("SELECT * FROM banks WHERE bank_id = :1", (self.test_bank['bank_id'],))
        
        bank = self.db.cursor.fetchone()
        self.assertIsNotNone(bank, "Bank was not inserted")
        self.assertEqual(bank[0], self.test_bank['bank_id'], "Bank ID does not match")
        self.assertEqual(bank[1], self.test_bank['bank_name'], "Bank name does not match")
    
    def test_insert_review(self):
        """Test inserting a review."""
        # First insert the bank
        self.test_insert_bank()
        
        # Insert a test review
        result = self.db.insert_review(self.test_review)
        self.assertTrue(result, "Failed to insert review")
        
        # Verify the review was inserted
        if self.db.db_type == 'postgresql':
            self.db.cursor.execute("SELECT * FROM reviews WHERE review_id = %s", (self.test_review['review_id'],))
        else:  # oracle
            self.db.cursor.execute("SELECT * FROM reviews WHERE review_id = :1", (self.test_review['review_id'],))
        
        review = self.db.cursor.fetchone()
        self.assertIsNotNone(review, "Review was not inserted")
        self.assertEqual(review[0], self.test_review['review_id'], "Review ID does not match")
        self.assertEqual(review[1], self.test_review['bank'], "Bank ID does not match")
    
    def test_batch_insert_reviews(self):
        """Test batch inserting multiple reviews."""
        # First insert the bank
        self.test_insert_bank()
        
        # Create test reviews
        reviews = [
            {
                'review_id': f'test_review_{i}',
                'bank': 'TEST',
                'original_text': f'Test review {i}',
                'processed_text': f'test review {i}',
                'tokens': ['test', 'review', str(i)],
                'sentiment_label': 'positive' if i % 2 == 0 else 'negative',
                'sentiment_score': 0.8 if i % 2 == 0 else -0.5,
                'theme': 'testing',
                'keywords': ['test', 'review', str(i)],
                'rating': 5.0 if i % 2 == 0 else 2.0,
                'date': datetime.now(),
                'user_name': f'tester_{i}',
                'thumbs_up': i,
                'source': 'test'
            }
            for i in range(5)  # Create 5 test reviews
        ]
        
        # Insert the reviews in a batch
        result = self.db.batch_insert_reviews(reviews, batch_size=2)  # Test with batch size of 2
        self.assertTrue(result, "Batch insert failed")
        
        # Verify the reviews were inserted
        if self.db.db_type == 'postgresql':
            self.db.cursor.execute("SELECT COUNT(*) FROM reviews WHERE bank_id = %s", ('TEST',))
        else:  # oracle
            self.db.cursor.execute("SELECT COUNT(*) FROM reviews WHERE bank_id = :1", ('TEST',))
        
        count = self.db.cursor.fetchone()[0]
        self.assertEqual(count, 5, f"Expected 5 reviews, got {count}")
    
    def test_get_reviews_by_bank(self):
        """Test retrieving reviews by bank ID."""
        # First insert test data
        self.test_batch_insert_reviews()
        
        # Get reviews for the test bank
        reviews_df = self.db.get_reviews_by_bank('TEST')
        
        # Verify the results
        self.assertIsNotNone(reviews_df, "Failed to get reviews")
        self.assertFalse(reviews_df.empty, "No reviews returned")
        self.assertEqual(len(reviews_df), 5, "Incorrect number of reviews")
        self.assertIn('review_id', reviews_df.columns, "Missing review_id column")
        self.assertIn('sentiment_label', reviews_df.columns, "Missing sentiment_label column")
    
    def test_get_sentiment_summary(self):
        """Test getting sentiment summary."""
        # First insert test data
        self.test_batch_insert_reviews()
        
        # Get sentiment summary
        summary_df = self.db.get_sentiment_summary()
        
        # Verify the results
        self.assertIsNotNone(summary_df, "Failed to get sentiment summary")
        self.assertFalse(summary_df.empty, "No summary data returned")
        self.assertIn('sentiment_label', summary_df.columns, "Missing sentiment_label column")
        self.assertIn('review_count', summary_df.columns, "Missing review_count column")
        
        # Verify the sentiment distribution
        positive_count = summary_df[summary_df['sentiment_label'] == 'positive']['review_count'].sum()
        negative_count = summary_df[summary_df['sentiment_label'] == 'negative']['review_count'].sum()
        self.assertEqual(positive_count + negative_count, 5, "Incorrect total review count")


if __name__ == '__main__':
    unittest.main()
