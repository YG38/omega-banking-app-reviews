# Ethiopian Banking App Reviews Analysis

A comprehensive pipeline for scraping, analyzing, and visualizing user reviews of Ethiopian banking applications from the Google Play Store.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Scraping Reviews](#scraping-reviews)
  - [Preprocessing](#preprocessing)
  - [Analysis](#analysis)
  - [Visualization](#visualization)
  - [Database Operations](#database-operations)
  - [Running the Full Pipeline](#running-the-full-pipeline)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Scraping**: Automated collection of app reviews from Google Play Store
- **Preprocessing**: Advanced NLP-based text cleaning and feature extraction
- **Sentiment Analysis**: Multi-level sentiment classification (positive/negative/neutral)
- **Thematic Analysis**: Topic modeling and keyword extraction
- **Visualization**: Interactive dashboards and static visualizations
- **Database Integration**: Store and query results in Oracle or PostgreSQL
- **Modular Design**: Easy to extend and customize

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Oracle Database 19c+ or PostgreSQL 13+ (optional, for database storage)
- Git (for version control)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/omega-banking-app-reviews.git
   cd omega-banking-app-reviews
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with your database credentials:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=bank_reviews
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_TYPE=postgresql  # or 'oracle'
   DB_SERVICE=XE  # For Oracle only
   ```

## Configuration

### Database Setup

1. **PostgreSQL**:
   ```bash
   createdb bank_reviews
   psql -U your_username -d bank_reviews -f src/db/schema/postgres_schema.sql
   ```

2. **Oracle**:
   ```bash
   sqlplus sys/your_password@//localhost:1521/XE as sysdba
   CREATE USER bank_reviews IDENTIFIED BY your_password;
   GRANTE CONNECT, RESOURCE, CREATE VIEW TO bank_reviews;
   ```
   Then run the Oracle schema script:
   ```bash
   sqlplus bank_reviews/your_password@//localhost:1521/XE @src/db/schema/oracle_schema.sql
   ```

## Usage

The pipeline can be run as a whole or step by step using the command-line interface.

### Scraping Reviews

Scrape reviews from Google Play Store:

```bash
python main.py scrape --count 500 --output-dir data/raw
```

### Preprocessing

Clean and preprocess the scraped reviews:

```bash
python main.py preprocess --input-dir data/raw --output-dir data/processed
```

### Analysis

Perform sentiment and thematic analysis:

```bash
python main.py analyze --input-file data/processed/processed_reviews.csv --output-dir data/analysis
```

### Visualization

Generate visualizations from analysis results:

```bash
python main.py visualize --input-dir data/analysis --output-dir reports/figures
```

### Database Operations

#### Initialize Database

```bash
python main.py db init --drop-tables
```

#### Load Data into Database

```bash
python main.py db load --input-dir data/processed --batch-size 100
```

#### Execute SQL Query

```bash
python main.py db query --sql "SELECT * FROM reviews LIMIT 10"
```

### Running the Full Pipeline

Run the entire pipeline (scrape → preprocess → analyze → visualize → load to DB):

```bash
python main.py all --count 500
```

## Project Structure

```
omega-banking-app-reviews/
├── data/                    # Data storage
│   ├── raw/                 # Raw scraped data
│   ├── processed/           # Processed and cleaned data
│   └── analysis_results/    # Analysis outputs
├── reports/                 # Generated reports and visualizations
│   └── figures/            # Saved visualizations
├── src/
│   ├── db/                 # Database module
│   │   ├── __init__.py
│   │   ├── database.py     # Database connection and operations
│   │   ├── init_db.py      # Database initialization
│   │   └── load_data.py    # Data loading utilities
│   │
│   ├── nlp/               # NLP analysis
│   │   ├── __init__.py
│   │   ├── sentiment_analysis.py
│   │   └── advanced_analysis.py
│   │
│   ├── preprocessing/     # Data cleaning and preparation
│   │   ├── __init__.py
│   │   └── clean_reviews.py
│   │
│   ├── scraping/          # Web scraping utilities
│   │   ├── __init__.py
│   │   └── scrape_reviews.py
│   │
│   └── visualization/     # Data visualization
│       ├── __init__.py
│       └── visualize_results.py
│
├── tests/                 # Unit and integration tests
├── .env.example           # Example environment variables
├── .gitignore
├── main.py                # Command-line interface
├── README.md
└── requirements.txt       # Project dependencies
```

## Database Schema

### Reviews Table
- `review_id`: Primary key
- `app_id`: App identifier
- `app_name`: Name of the banking app
- `reviewer_name`: Name of the reviewer
- `review_text`: Full text of the review
- `rating`: Star rating (1-5)
- `thumbs_up_count`: Number of helpful votes
- `review_date`: Date of the review
- `sentiment`: Sentiment classification (positive/negative/neutral)
- `sentiment_score`: Numeric sentiment score (-1 to 1)
- `keywords`: Extracted keywords (JSON array)
- `themes`: Identified themes (JSON array)
- `created_at`: Timestamp of when the record was created
- `updated_at`: Timestamp of when the record was last updated

### Apps Table
- `app_id`: Primary key
- `app_name`: Name of the app
- `package_name`: Package identifier
- `description`: App description
- `category`: App category
- `installs`: Number of installs
- `score`: Average rating
- `reviews_count`: Total number of reviews
- `last_updated`: When the app was last updated
- `version`: Current version
- `developer`: Developer name

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify database is running
   - Check credentials in `.env` file
   - Ensure the database user has correct permissions

2. **Missing Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Rate Limiting**:
   - If scraping fails, wait and try again later
   - Use proxies if needed

4. **Memory Issues**:
   - Process data in smaller batches
   - Increase system swap space if needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Overview
This project analyzes user reviews from mobile banking apps of three major Ethiopian banks to gain insights into customer satisfaction, identify pain points, and provide data-driven recommendations for improvement. The analysis includes sentiment analysis using DistilBERT and thematic analysis using TF-IDF and clustering techniques.

## Banks Analyzed
1. Commercial Bank of Ethiopia (CBE)
2. Bank of Abyssinia (BOA)
3. Dashen Bank

## Project Structure
```
omega-banking-app-reviews/
├── data/                   # Data storage
│   ├── raw/               # Original scraped data
│   ├── processed/         # Cleaned and processed data
│   └── analysis_results/  # Analysis results (sentiment, topics, etc.)
│
├── reports/               # Generated reports and visualizations
│   └── figures/           # Saved visualizations
│
├── src/                   # Source code
│   ├── scraping/         # Web scraping scripts
│   ├── preprocessing/    # Data cleaning and transformation
│   ├── nlp/             # Sentiment and thematic analysis
│   └── visualization/    # Plot generation
│
├── tests/               # Unit and integration tests
├── .gitignore
├── requirements.txt
├── main.py              # Command-line interface
└── README.md
```

## Features

- **Web Scraping**: Collect reviews from Google Play Store for multiple banks
- **Data Preprocessing**: Clean and prepare review data for analysis
- **Sentiment Analysis**: Use DistilBERT to determine sentiment (positive/negative/neutral)
- **Thematic Analysis**: Identify key topics and themes in the reviews
- **Visualization**: Generate insightful visualizations of the analysis results

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/omega-banking-app-reviews.git
   cd omega-banking-app-reviews
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Usage

The project provides a command-line interface through `main.py`. You can run the entire pipeline or individual steps.

### Run the entire pipeline

```bash
python main.py run_all --count 400
```

This will:
1. Scrape 400 reviews per bank (default)
2. Preprocess the data
3. Perform sentiment and thematic analysis
4. Generate visualizations

### Individual Commands

1. **Scrape reviews**
   ```bash
   python main.py scrape --count 400 --output-dir data/raw
   ```

2. **Preprocess the data**
   ```bash
   python main.py preprocess --input-dir data/raw --output-dir data/processed
   ```

3. **Run analysis**
   ```bash
   python main.py analyze --output-dir data/analysis_results
   ```

4. **Generate visualizations**
   ```bash
   python main.py visualize --input-dir data/analysis_results --output-dir reports/figures
   ```

## Output

The analysis will generate several output files:

- **Raw Data**: CSV files in `data/raw/` containing scraped reviews
- **Processed Data**: Cleaned and preprocessed data in `data/processed/`
- **Analysis Results**:
  - Sentiment analysis results
  - Extracted keywords
  - Discovered topics
- **Visualizations**: Various plots and charts in `reports/figures/`

## Customization

You can customize the analysis by modifying the following parameters:

- Number of reviews to scrape per bank (default: 400)
- Number of topics for LDA (in `advanced_analysis.py`)
- Number of clusters for K-means (in `advanced_analysis.py`)
- Visualization styles and colors (in `visualize_results.py`)

## Dependencies

- Python 3.8+
- See `requirements.txt` for a complete list of Python packages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

1. **Scrape reviews**
   ```bash
   python src/scraping/scrape_reviews.py
   ```

2. **Preprocess data**
   ```bash
   python src/preprocessing/clean_reviews.py
   ```

3. **Run analysis**
   ```bash
   python src/nlp/sentiment_analysis.py
   ```

## Key Features
- Web scraping of Google Play Store reviews
- Sentiment analysis of user feedback
- Theme extraction from reviews
- Data visualization
- Database integration

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Omega Consultancy for the project opportunity
- Google Play Store for the review data
- Open-source contributors of the Python libraries used
