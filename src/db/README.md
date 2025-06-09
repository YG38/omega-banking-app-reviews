# Database Module

This module handles all database operations for the Banking App Reviews project, including schema management, data loading, and querying.

## Features

- **Database Connection Management**: Supports both Oracle and PostgreSQL databases
- **Schema Management**: Create and drop database tables
- **Data Loading**: Load processed review data from CSV/JSON files into the database
- **Querying**: Execute common queries for analysis and reporting
- **Migrations**: Support for database schema migrations

## Prerequisites

- Python 3.8+
- Oracle Database XE (or another Oracle database) or PostgreSQL
- Required Python packages (see `requirements.txt` in the project root)

## Database Schema

The database consists of the following tables:

### `banks`
- `bank_id` (PK): Unique identifier for the bank
- `bank_name`: Name of the bank
- `app_name`: Name of the bank's mobile app
- `created_at`: Timestamp when the record was created

### `reviews`
- `review_id` (PK): Unique identifier for the review
- `bank_id` (FK): Reference to the bank
- `original_text`: Original review text
- `processed_text`: Processed/cleaned review text
- `tokens`: Tokenized text (stored as JSON)
- `sentiment_label`: Sentiment classification (positive/neutral/negative)
- `sentiment_score`: Sentiment score (-1.0 to 1.0)
- `theme`: Identified theme of the review
- `keywords`: Extracted keywords (stored as JSON)
- `rating`: Star rating (1-5)
- `review_date`: Date of the review
- `user_name`: Name of the reviewer
- `thumbs_up`: Number of thumbs up
- `source`: Source of the review (e.g., 'google_play')
- `created_at`: Timestamp when the record was created

## Usage

### 1. Initialize the Database

```bash
# Initialize the database with all tables and sample data
python -m src.db.init_db --all

# For PostgreSQL
python -m src.db.init_db --all --db-type postgresql --db-host localhost --db-port 5432 --db-name bank_reviews --db-user postgres --db-password yourpassword

# For Oracle
python -m src.db.init_db --all --db-type oracle --db-host localhost --db-port 1521 --db-service XE --db-user system --db-password oracle
```

### 2. Load Data into the Database

```bash
# Load processed data from the default directory (data/processed/)
python -m src.db.load_data

# Specify a custom input directory
python -m src.db.load_data --input-dir /path/to/processed/data

# Test the data loading without modifying the database
python -m src.db.load_data --test
```

### 3. Query the Database

You can use the `DatabaseManager` class to query the database in your Python code:

```python
from db.database import DatabaseManager

# Initialize the database manager
db = DatabaseManager(db_type='oracle')  # or 'postgresql'

# Connect to the database
if db.connect():
    # Get reviews for a specific bank
    reviews = db.get_reviews_by_bank('CBE', limit=10)
    print(reviews[['review_id', 'sentiment_label', 'rating']].to_string())
    
    # Get sentiment summary
    summary = db.get_sentiment_summary()
    print(summary.to_string())
    
    # Disconnect
    db.disconnect()
```

## Environment Variables

You can set the following environment variables instead of passing them as command-line arguments:

- `DB_TYPE`: Database type ('oracle' or 'postgresql')
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name (PostgreSQL)
- `DB_SERVICE`: Database service name (Oracle)
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

## Testing

To run the database tests:

```bash
# Test database connection and basic operations
python -m src.db.database

# Test data loading
python -m src.db.load_data --test
```

## Database Views

The following views are created for common analysis tasks:

1. `vw_sentiment_analysis`: Shows sentiment distribution by bank
2. `vw_theme_analysis`: Shows theme distribution by bank and sentiment
3. `vw_rating_distribution`: Shows rating distribution by bank

## Troubleshooting

### Oracle Database Issues

- **ORA-12541: TNS:no listener**: Make sure the Oracle database service is running
- **ORA-12154: TNS:could not resolve the connect identifier specified**: Check your TNS configuration or use the full connection string
- **ORA-01017: invalid username/password**: Verify the username and password

### PostgreSQL Database Issues

- **Connection refused**: Make sure PostgreSQL is running and accessible
- **Database does not exist**: Create the database first: `createdb bank_reviews`
- **Permission denied**: Check the database user permissions

### Common Issues

- **Encoding errors**: Make sure your database uses UTF-8 encoding
- **Connection timeouts**: Check your network connection and firewall settings
- **Insufficient privileges**: Make sure the database user has the necessary permissions
