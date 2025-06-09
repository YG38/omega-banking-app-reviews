#!/usr/bin/env python3
"""
Test script to verify database connection and basic operations.
"""

import os
import sys
import unittest
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

class TestDatabaseConnection(unittest.TestCase):    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Load environment variables from .env file
        dotenv_path = Path(__file__).parent.parent / '.env'
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
        
        # Import database module after setting up environment
        from db.database import DatabaseManager
        
        # Initialize database connection
        cls.db_params = {
            'db_type': os.getenv('DB_TYPE', 'postgresql'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'bank_reviews'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'service_name': os.getenv('DB_SERVICE', 'XE')
        }
        
        cls.db = DatabaseManager(**cls.db_params)
    
    def test_connection(self):
        """Test database connection."""
        self.assertTrue(self.db.connect(), "Failed to connect to database")
        self.assertIsNotNone(self.db.connection, "Database connection is None")
        self.assertIsNotNone(self.db.cursor, "Database cursor is None")
    
    def test_table_exists(self):
        """Test if required tables exist."""
        self.db.connect()
        
        # Check if reviews table exists
        if self.db.db_type == 'oracle':
            query = """
                SELECT table_name 
                FROM all_tables 
                WHERE owner = :owner 
                AND table_name = 'REVIEWS'
            """
            params = {'owner': self.db.user.upper()}
        else:  # postgresql
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'reviews';
            """
            params = {}
        
        self.db.cursor.execute(query, params)
        result = self.db.cursor.fetchone()
        self.assertIsNotNone(result, "Reviews table does not exist")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        if hasattr(cls, 'db') and cls.db.connection:
            cls.db.disconnect()

if __name__ == '__main__':
    unittest.main()
