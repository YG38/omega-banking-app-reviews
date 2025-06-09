"""
Database Initialization Script for Banking App Reviews

This script initializes the database schema and performs any necessary setup.
It can be used to create tables, indexes, and initial data.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_init.log')
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow importing from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database module
from db.database import DatabaseManager

class DatabaseInitializer:
    """Handles database initialization and setup."""
    
    def __init__(self, db_type: str = 'oracle', **db_params):
        """
        Initialize the DatabaseInitializer.
        
        Args:
            db_type: Type of database ('oracle' or 'postgresql')
            **db_params: Additional database connection parameters
        """
        self.db = DatabaseManager(db_type=db_type, **db_params)
    
    def connect(self) -> bool:
        """Establish database connection."""
        return self.db.connect()
    
    def disconnect(self):
        """Close database connection."""
        self.db.disconnect()
    
    def drop_tables(self) -> bool:
        """
        Drop all database tables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db.connect():
            return False
        
        try:
            # Drop tables in the correct order to respect foreign key constraints
            self.db.cursor.execute("""
                BEGIN
                    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS reviews CASCADE CONSTRAINTS';
                    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS banks CASCADE CONSTRAINTS';
                    DBMS_OUTPUT.PUT_LINE('Tables dropped successfully');
                EXCEPTION
                    WHEN OTHERS THEN
                        DBMS_OUTPUT.PUT_LINE('Error dropping tables: ' || SQLERRM);
                        RAISE;
                END;
            """)
            
            if self.db.db_type == 'postgresql':
                self.db.cursor.execute("""
                    DROP TABLE IF EXISTS reviews CASCADE;
                    DROP TABLE IF EXISTS banks CASCADE;
                """)
            
            self.db.connection.commit()
            logger.info("Dropped all tables")
            return True
            
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            if self.db.connection:
                self.db.connection.rollback()
            return False
    
    def create_tables(self) -> bool:
        """
        Create database tables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.db.create_tables()
    
    def create_indexes(self) -> bool:
        """
        Create additional indexes for better query performance.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db.connect():
            return False
        
        try:
            # Create indexes for common query patterns
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_theme ON reviews(theme)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_rating ON reviews(sentiment_label, rating)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_bank_sentiment ON reviews(bank_id, sentiment_label)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_rating_sentiment ON reviews(rating, sentiment_label)"
            ]
            
            for index_sql in indexes:
                self.db.cursor.execute(index_sql)
            
            self.db.connection.commit()
            logger.info("Created additional indexes")
            return True
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            if self.db.connection:
                self.db.connection.rollback()
            return False
    
    def create_views(self) -> bool:
        """
        Create useful database views.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db.connect():
            return False
        
        try:
            # View for sentiment analysis results
            self.db.cursor.execute("""
                CREATE OR REPLACE VIEW vw_sentiment_analysis AS
                SELECT 
                    b.bank_name,
                    r.sentiment_label,
                    COUNT(*) as review_count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY b.bank_name), 2) as percentage,
                    ROUND(AVG(r.sentiment_score), 4) as avg_sentiment,
                    ROUND(AVG(r.rating), 2) as avg_rating
                FROM reviews r
                JOIN banks b ON r.bank_id = b.bank_id
                GROUP BY b.bank_name, r.sentiment_label
                ORDER BY b.bank_name, 
                         CASE r.sentiment_label 
                             WHEN 'positive' THEN 1 
                             WHEN 'neutral' THEN 2 
                             WHEN 'negative' THEN 3 
                             ELSE 4 
                         END
            """)
            
            # View for theme analysis
            self.db.cursor.execute("""
                CREATE OR REPLACE VIEW vw_theme_analysis AS
                SELECT 
                    b.bank_name,
                    r.theme,
                    r.sentiment_label,
                    COUNT(*) as review_count,
                    ROUND(AVG(r.rating), 2) as avg_rating
                FROM reviews r
                JOIN banks b ON r.bank_id = b.bank_id
                WHERE r.theme IS NOT NULL
                GROUP BY b.bank_name, r.theme, r.sentiment_label
                ORDER BY b.bank_name, review_count DESC
            """)
            
            # View for rating distribution
            self.db.cursor.execute("""
                CREATE OR REPLACE VIEW vw_rating_distribution AS
                SELECT 
                    b.bank_name,
                    r.rating,
                    COUNT(*) as review_count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY b.bank_name), 2) as percentage
                FROM reviews r
                JOIN banks b ON r.bank_id = b.bank_id
                GROUP BY b.bank_name, r.rating
                ORDER BY b.bank_name, r.rating
            """)
            
            self.db.connection.commit()
            logger.info("Created database views")
            return True
            
        except Exception as e:
            logger.error(f"Error creating views: {str(e)}")
            if self.db.connection:
                self.db.connection.rollback()
            return False
    
    def initialize_reference_data(self) -> bool:
        """
        Initialize reference data in the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db.connect():
            return False
        
        try:
            # Insert default banks
            banks = [
                ('CBE', 'Commercial Bank of Ethiopia', 'CBE Birr'),
                ('BOA', 'Bank of Abyssinia', 'BOA Mobile Banking'),
                ('DASHEN', 'Dashen Bank', 'Dashen Bank Mobile')
            ]
            
            for bank_id, bank_name, app_name in banks:
                self.db.insert_bank(bank_id=bank_id, bank_name=bank_name, app_name=app_name)
            
            self.db.connection.commit()
            logger.info("Initialized reference data")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing reference data: {str(e)}")
            if self.db.connection:
                self.db.connection.rollback()
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.
        
        Returns:
            Dictionary containing database information
        """
        if not self.db.connect():
            return {}
        
        try:
            info = {}
            
            # Get database version
            if self.db.db_type == 'oracle':
                self.db.cursor.execute("SELECT * FROM v$version")
                info['version'] = self.db.cursor.fetchone()[0]
            else:  # postgresql
                self.db.cursor.execute("SELECT version()")
                info['version'] = self.db.cursor.fetchone()[0]
            
            # Get table counts
            self.db.cursor.execute("SELECT COUNT(*) FROM banks")
            info['banks_count'] = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT COUNT(*) FROM reviews")
            info['reviews_count'] = self.db.cursor.fetchone()[0]
            
            # Get table sizes (approximate for Oracle, exact for PostgreSQL)
            if self.db.db_type == 'postgresql':
                self.db.cursor.execute("""
                    SELECT 
                        table_name, 
                        pg_size_pretty(pg_total_relation_size(table_name)) as size
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY pg_total_relation_size(table_name) DESC
                """)
                info['table_sizes'] = dict(self.db.cursor.fetchall())
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {}

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Initialize the banking reviews database.')
    
    # Database connection parameters
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
    
    # Actions
    parser.add_argument('--drop-tables', action='store_true',
                       help='Drop all tables before creating them')
    parser.add_argument('--create-tables', action='store_true',
                       help='Create database tables')
    parser.add_argument('--create-indexes', action='store_true',
                       help='Create additional indexes')
    parser.add_argument('--create-views', action='store_true',
                       help='Create database views')
    parser.add_argument('--init-data', action='store_true',
                       help='Initialize reference data')
    parser.add_argument('--all', action='store_true',
                       help='Perform all initialization steps')
    parser.add_argument('--info', action='store_true',
                       help='Show database information')
    
    return parser.parse_args()

def main():
    """Main function to run the database initialization."""
    args = parse_arguments()
    
    # Prepare database parameters
    db_params = {
        'host': args.db_host or os.getenv('DB_HOST'),
        'port': args.db_port or os.getenv('DB_PORT'),
        'user': args.db_user or os.getenv('DB_USER'),
        'password': args.db_password or os.getenv('DB_PASSWORD'),
    }
    
    if args.db_type == 'oracle':
        db_params['service_name'] = args.db_service or os.getenv('DB_SERVICE', 'XE')
    else:  # postgresql
        db_params['database'] = args.db_name or os.getenv('DB_NAME', 'bank_reviews')
    
    # Initialize the database initializer
    initializer = DatabaseInitializer(db_type=args.db_type, **db_params)
    
    # Connect to the database
    if not initializer.connect():
        logger.error("Failed to connect to the database")
        return 1
    
    try:
        # Show database info if requested
        if args.info:
            info = initializer.get_database_info()
            print("\nDatabase Information:")
            print(f"Type: {args.db_type.upper()}")
            print(f"Version: {info.get('version', 'N/A')}")
            print(f"Number of banks: {info.get('banks_count', 0)}")
            print(f"Number of reviews: {info.get('reviews_count', 0)}")
            
            if 'table_sizes' in info:
                print("\nTable Sizes:")
                for table, size in info['table_sizes'].items():
                    print(f"  - {table}: {size}")
            
            return 0
        
        # Determine which actions to perform
        drop_tables = args.drop_tables or args.all
        create_tables = args.create_tables or args.all
        create_indexes = args.create_indexes or args.all
        create_views = args.create_views or args.all
        init_data = args.init_data or args.all
        
        # Execute the requested actions
        success = True
        
        if drop_tables:
            print("Dropping existing tables...")
            success = success and initializer.drop_tables()
        
        if create_tables:
            print("Creating tables...")
            success = success and initializer.create_tables()
        
        if create_indexes:
            print("Creating indexes...")
            success = success and initializer.create_indexes()
        
        if create_views:
            print("Creating views...")
            success = success and initializer.create_views()
        
        if init_data:
            print("Initializing reference data...")
            success = success and initializer.initialize_reference_data()
        
        if success:
            print("\n✅ Database initialization completed successfully!")
            
            # Show summary
            info = initializer.get_database_info()
            print(f"\nSummary:")
            print(f"- Number of banks: {info.get('banks_count', 0)}")
            print(f"- Number of reviews: {info.get('reviews_count', 0)}")
            
            if args.db_type == 'postgresql' and 'table_sizes' in info:
                print("\nTable Sizes:")
                for table, size in info['table_sizes'].items():
                    print(f"  - {table}: {size}")
            
            return 0
        else:
            print("\n❌ Database initialization completed with errors. Please check the logs for details.")
            return 1
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1
    finally:
        initializer.disconnect()


if __name__ == "__main__":
    sys.exit(main())
