# Ethiopian Banking App Reviews Analysis

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
