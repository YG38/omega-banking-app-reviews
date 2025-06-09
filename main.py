#!/usr/bin/env python3
"""
Banking App Reviews Analysis - Main Script

This script provides a command-line interface to run the banking app review analysis pipeline.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze banking app reviews.')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape reviews from Google Play Store')
    scrape_parser.add_argument('--count', type=int, default=400,
                             help='Number of reviews to scrape per bank (default: 400)')
    scrape_parser.add_argument('--output-dir', default='data/raw',
                             help='Directory to save scraped data (default: data/raw)')
    
    # Preprocess command
    preprocess_parser = subparsers.add_parser('preprocess', 
                                            help='Preprocess scraped reviews')
    preprocess_parser.add_argument('--input-dir', default='data/raw',
                                 help='Directory containing raw data (default: data/raw)')
    preprocess_parser.add_argument('--output-dir', default='data/processed',
                                 help='Directory to save processed data (default: data/processed)')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', 
                                         help='Perform sentiment and thematic analysis')
    analyze_parser.add_argument('--input-file', 
                              help='Path to cleaned reviews CSV file. If not provided, the most recent file in the processed directory will be used.')
    analyze_parser.add_argument('--output-dir', default='data/analysis_results',
                              help='Directory to save analysis results (default: data/analysis_results)')
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', 
                                           help='Generate visualizations from analysis results')
    visualize_parser.add_argument('--input-dir', default='data/analysis_results',
                                help='Directory containing analysis results (default: data/analysis_results)')
    visualize_parser.add_argument('--output-dir', default='reports/figures',
                                help='Directory to save visualizations (default: reports/figures)')
    
    # Run all command
    all_parser = subparsers.add_parser('run_all', 
                                      help='Run the entire pipeline: scrape -> preprocess -> analyze -> visualize')
    all_parser.add_argument('--count', type=int, default=400,
                          help='Number of reviews to scrape per bank (default: 400)')
    
    return parser.parse_args()

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
