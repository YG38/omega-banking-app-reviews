#!/usr/bin/env python3
"""
Banking App Reviews Analysis - Main Script

This script provides a command-line interface to run the banking app review analysis pipeline.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze banking app reviews from Google Play Store.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Database configuration arguments
    db_group = parser.add_argument_group('Database Options')
    db_group.add_argument('--db-type', choices=['oracle', 'postgresql'], default='postgresql',
                         help='Database type')
    db_group.add_argument('--db-host', default=os.getenv('DB_HOST', 'localhost'),
                         help='Database host')
    db_group.add_argument('--db-port', default=os.getenv('DB_PORT', '5432'),
                         help='Database port')
    db_group.add_argument('--db-name', default=os.getenv('DB_NAME', 'bank_reviews'),
                         help='Database name')
    db_group.add_argument('--db-user', default=os.getenv('DB_USER', 'postgres'),
                         help='Database user')
    db_group.add_argument('--db-password', default=os.getenv('DB_PASSWORD', 'postgres'),
                         help='Database password')
    db_group.add_argument('--db-service', default=os.getenv('DB_SERVICE', 'XE'),
                         help='Database service name (Oracle only)')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', 
                                        help='Scrape reviews from Google Play Store',
                                        parents=[db_group])
    scrape_parser.add_argument('--count', type=int, default=400,
                             help='Number of reviews to scrape per bank')
    scrape_parser.add_argument('--output-dir', default='data/raw',
                             help='Directory to save scraped data')
    scrape_parser.add_argument('--skip-existing', action='store_true',
                             help='Skip scraping if output file already exists')
    
    # Preprocess command
    preprocess_parser = subparsers.add_parser('preprocess', 
                                            help='Preprocess scraped reviews',
                                            parents=[db_group])
    preprocess_parser.add_argument('--input-dir', default='data/raw',
                                 help='Directory containing raw data')
    preprocess_parser.add_argument('--output-dir', default='data/processed',
                                 help='Directory to save processed data')
    preprocess_parser.add_argument('--clean', action='store_true',
                                 help='Clean existing processed files')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', 
                                         help='Perform sentiment and thematic analysis',
                                         parents=[db_group])
    analyze_parser.add_argument('--input-file', 
                              help='Path to cleaned reviews CSV file')
    analyze_parser.add_argument('--output-dir', default='data/analysis_results',
                              help='Directory to save analysis results')
    analyze_parser.add_argument('--batch-size', type=int, default=100,
                              help='Batch size for processing reviews')
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', 
                                           help='Generate visualizations from analysis results',
                                           parents=[db_group])
    visualize_parser.add_argument('--input-dir', default='data/analysis_results',
                                help='Directory containing analysis results')
    visualize_parser.add_argument('--output-dir', default='reports/figures',
                                help='Directory to save visualizations')
    visualize_parser.add_argument('--format', choices=['png', 'pdf', 'svg'], default='png',
                                help='Output format for visualizations')
    
    # Database commands
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_subparsers = db_parser.add_subparsers(dest='db_command', help='Database command')
    
    # DB init command
    init_parser = db_subparsers.add_parser('init', help='Initialize database')
    init_parser.add_argument('--drop-tables', action='store_true',
                           help='Drop existing tables before creating')
    
    # DB load command
    load_parser = db_subparsers.add_parser('load', help='Load data into database')
    load_parser.add_argument('--input-dir', default='data/processed',
                           help='Directory containing processed data')
    load_parser.add_argument('--batch-size', type=int, default=100,
                           help='Batch size for database inserts')
    
    # DB query command
    query_parser = db_subparsers.add_parser('query', help='Query database')
    query_parser.add_argument('--sql', help='SQL query to execute')
    query_parser.add_argument('--output', help='Output file for query results')
    
    # All-in-one command
    all_parser = subparsers.add_parser('all', 
                                      help='Run the entire pipeline',
                                      parents=[db_group])
    all_parser.add_argument('--skip-scrape', action='store_true',
                          help='Skip the scraping step')
    all_parser.add_argument('--skip-db', action='store_true',
                          help='Skip database operations')
    all_parser.add_argument('--skip-visualize', action='store_true',
                          help='Skip visualization step')
    all_parser.add_argument('--count', type=int, default=400,
                          help='Number of reviews to scrape per bank')
    
    # Add common arguments to all commands
    for subparser in [scrape_parser, preprocess_parser, analyze_parser, 
                     visualize_parser, all_parser]:
        subparser.add_argument('--log-level', 
                             choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                             default='INFO',
                             help='Set the logging level')
    
    return parser.parse_args()

def setup_logging(log_level='INFO'):
    """Configure logging with the specified log level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )

def ensure_directory(directory):
    """Ensure that the specified directory exists."""
    os.makedirs(directory, exist_ok=True)
    return directory

def get_db_params(args):
    """Extract database connection parameters from command line arguments."""
    return {
        'db_type': args.db_type,
        'host': args.db_host,
        'port': args.db_port,
        'database': getattr(args, 'db_name', None),
        'user': args.db_user,
        'password': args.db_password,
        'service_name': getattr(args, 'db_service', None)
    }

def run_scrape(args):
    """Run the scraping process."""
    from src.scraping.scrape_reviews import main as scrape_main
    
    logger.info(f"Starting to scrape up to {args.count} reviews per bank...")
    output_dir = ensure_directory(args.output_dir)
    
    try:
        scrape_main(count=args.count, output_dir=output_dir, skip_existing=args.skip_existing)
        logger.info("Scraping completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        return False

def run_preprocess(args):
    """Run the preprocessing pipeline."""
    from src.preprocessing.clean_reviews import main as preprocess_main
    
    logger.info("Starting preprocessing of scraped reviews...")
    output_dir = ensure_directory(args.output_dir)
    
    try:
        preprocess_main(input_dir=args.input_dir, output_dir=output_dir, clean=args.clean)
        logger.info("Preprocessing completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}", exc_info=True)
        return False

def run_analyze(args):
    """Run the analysis pipeline."""
    from src.nlp.sentiment_analysis import main as analyze_main
    
    logger.info("Starting sentiment and thematic analysis...")
    output_dir = ensure_directory(args.output_dir)
    
    try:
        analyze_main(input_file=args.input_file, output_dir=output_dir, batch_size=args.batch_size)
        logger.info("Analysis completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        return False

def run_visualize(args):
    """Run the visualization pipeline."""
    from src.visualization.visualize_results import main as visualize_main
    
    logger.info("Generating visualizations...")
    output_dir = ensure_directory(args.output_dir)
    
    try:
        visualize_main(input_dir=args.input_dir, output_dir=output_dir, format=args.format)
        logger.info("Visualization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during visualization: {str(e)}", exc_info=True)
        return False

def run_db_init(args):
    """Initialize the database."""
    from src.db.init_db import main as init_db_main
    
    logger.info("Initializing database...")
    
    try:
        init_db_main(
            db_type=args.db_type,
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            db_service=args.db_service,
            drop_tables=args.drop_tables
        )
        logger.info("Database initialization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        return False

def run_db_load(args):
    """Load data into the database."""
    from src.db.load_data import main as load_data_main
    
    logger.info(f"Loading data from {args.input_dir} into database...")
    
    try:
        load_data_main(
            db_type=args.db_type,
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            db_service=args.db_service,
            input_dir=args.input_dir,
            batch_size=args.batch_size
        )
        logger.info("Data loading completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error loading data into database: {str(e)}", exc_info=True)
        return False

def run_db_query(args):
    """Execute a database query."""
    from src.db.database import DatabaseManager
    import pandas as pd
    
    if not args.sql:
        logger.error("No SQL query provided. Use --sql option to specify a query.")
        return False
    
    logger.info(f"Executing query: {args.sql}")
    
    try:
        db = DatabaseManager(**get_db_params(args))
        if not db.connect():
            raise Exception("Failed to connect to database")
        
        # Execute the query
        db.cursor.execute(args.sql)
        
        # Fetch results
        columns = [col[0] for col in db.cursor.description] if db.cursor.description else []
        results = db.cursor.fetchall()
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(results, columns=columns)
        
        # Print or save results
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == '.csv':
                df.to_csv(output_path, index=False)
                logger.info(f"Query results saved to {output_path}")
            elif output_path.suffix.lower() == '.xlsx':
                df.to_excel(output_path, index=False)
                logger.info(f"Query results saved to {output_path}")
            else:
                # Default to CSV if format not recognized
                output_path = output_path.with_suffix('.csv')
                df.to_csv(output_path, index=False)
                logger.info(f"Query results saved to {output_path}")
        else:
            # Print to console
            print("\nQuery Results:")
            print(df.to_string())
        
        return True
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}", exc_info=True)
        return False
    finally:
        if 'db' in locals():
            db.disconnect()

def run_all(args):
    """Run the entire pipeline."""
    success = True
    
    # Scrape
    if not args.skip_scrape:
        logger.info("=== Starting Scraping Step ===")
        if not run_scrape(args):
            logger.error("Scraping failed. Check logs for details.")
            success = False
    
    # Preprocess
    logger.info("\n=== Starting Preprocessing Step ===")
    if not run_preprocess(args):
        logger.error("Preprocessing failed. Check logs for details.")
        success = False
    
    # Analyze
    logger.info("\n=== Starting Analysis Step ===")
    if not run_analyze(args):
        logger.error("Analysis failed. Check logs for details.")
        success = False
    
    # Database operations
    if not args.skip_db:
        logger.info("\n=== Starting Database Operations ===")
        # Initialize database
        if not run_db_init(args):
            logger.error("Database initialization failed. Check logs for details.")
            success = False
        
        # Load data
        if not run_db_load(args):
            logger.error("Data loading failed. Check logs for details.")
            success = False
    
    # Visualize
    if not args.skip_visualize:
        logger.info("\n=== Starting Visualization Step ===")
        if not run_visualize(args):
            logger.error("Visualization failed. Check logs for details.")
            success = False
    
    if success:
        logger.info("\n=== Pipeline completed successfully! ===")
    else:
        logger.warning("\n=== Pipeline completed with errors. Check logs for details. ===")
    
    return success

def main():
    """Main entry point for the application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set up logging
        log_level = getattr(args, 'log_level', 'INFO')
        setup_logging(log_level)
        
        logger.info(f"Starting Banking App Reviews Analysis (Log Level: {log_level})")
        
        # Execute the requested command
        if args.command == 'scrape':
            success = run_scrape(args)
        elif args.command == 'preprocess':
            success = run_preprocess(args)
        elif args.command == 'analyze':
            success = run_analyze(args)
        elif args.command == 'visualize':
            success = run_visualize(args)
        elif args.command == 'db':
            if args.db_command == 'init':
                success = run_db_init(args)
            elif args.db_command == 'load':
                success = run_db_load(args)
            elif args.db_command == 'query':
                success = run_db_query(args)
            else:
                logger.error(f"Unknown database command: {args.db_command}")
                success = False
        elif args.command == 'all':
            success = run_all(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

def run_scrape(args):
    """Run the scraping process."""
    from src.scraping.scrape_reviews import main as scrape_main
    
    print("\n=== Starting Review Scraping ===\n")
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Call the scraping function with the provided arguments
    scrape_main(count=args.count, output_dir=args.output_dir)
    print("\n=== Scraping Completed Successfully ===\n")

def run_preprocess(args):
    """Run the preprocessing pipeline."""
    from src.preprocessing.clean_reviews import main as preprocess_main
    
    print("\n=== Starting Data Preprocessing ===\n")
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Call the preprocessing function with the provided arguments
    preprocess_main(input_dir=args.input_dir, output_dir=args.output_dir)
    print("\n=== Preprocessing Completed Successfully ===\n")

def run_analyze(args):
    """Run the analysis pipeline."""
    from src.nlp.advanced_analysis import BankingReviewAnalyzer
    
    print("\n=== Starting Sentiment and Thematic Analysis ===\n")
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize the analyzer
    analyzer = BankingReviewAnalyzer(data_dir=os.path.dirname(args.input_file) if args.input_file else 'data/processed')
    
    # If a specific input file is provided, use it
    if args.input_file:
        if not os.path.exists(args.input_file):
            raise FileNotFoundError(f"Input file not found: {args.input_file}")
        analyzer.df = pd.read_csv(args.input_file, parse_dates=['date'], infer_datetime_format=True)
    
    # Run the analysis
    results = analyzer.analyze()
    output_files = analyzer.save_results(output_dir=args.output_dir)
    
    print("\n=== Analysis Completed Successfully ===\n")
    print("Output files:")
    for name, path in output_files.items():
        print(f"- {name}: {os.path.abspath(path)}")

def run_visualize(args):
    """Run the visualization pipeline."""
    from src.visualization.visualize_results import ReviewVisualizer
    
    print("\n=== Generating Visualizations ===\n")
    
    # Initialize the visualizer
    visualizer = ReviewVisualizer(data_dir=args.input_dir)
    
    # Generate and save all visualizations
    visualizer.generate_all_visualizations(output_dir=args.output_dir)
    
    print("\n=== Visualization Generation Completed Successfully ===\n")

def run_all(args):
    """Run the entire pipeline."""
    # Scrape
    scrape_args = type('Args', (), {'count': args.count, 'output_dir': 'data/raw'})
    run_scrape(scrape_args)
    
    # Preprocess
    preprocess_args = type('Args', (), {'input_dir': 'data/raw', 'output_dir': 'data/processed'})
    run_preprocess(preprocess_args)
    
    # Analyze
    analyze_args = type('Args', (), {'input_file': None, 'output_dir': 'data/analysis_results'})
    run_analyze(analyze_args)
    
    # Visualize
    visualize_args = type('Args', (), {'input_dir': 'data/analysis_results', 'output_dir': 'reports/figures'})
    run_visualize(visualize_args)
    
    print("\n=== Pipeline Completed Successfully ===\n")

def main():
    """Main function to run the selected command."""
    args = parse_arguments()
    
    try:
        if args.command == 'scrape':
            run_scrape(args)
        elif args.command == 'preprocess':
            run_preprocess(args)
        elif args.command == 'analyze':
            run_analyze(args)
        elif args.command == 'visualize':
            run_visualize(args)
        elif args.command == 'run_all':
            run_all(args)
        else:
            print("Please specify a valid command. Use --help for usage information.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
