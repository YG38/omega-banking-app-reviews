#!/usr/bin/env python3
"""
Script to validate the project structure and required files.
"""

import os
import sys
from pathlib import Path

def check_directory(path, required=True):
    """Check if directory exists and return status."""
    exists = path.exists() and path.is_dir()
    status = "[OK]" if exists else "[MISSING]"
    print(f"{status} {path}")
    if not exists and required:
        print(f"  -> Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
    return exists

def check_file(path, required=True):
    """Check if file exists and return status."""
    exists = path.exists() and path.is_file()
    status = "✓" if exists else "✗"
    print(f"{status} {path}")
    return exists

def main():
    """Main function to validate project structure."""
    root = Path(__file__).parent.parent
    print("\nValidating project structure...\n")
    
    # Required directories
    print("Checking required directories:")
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "analysis_results",
        root / "reports" / "figures",
        root / "src" / "db",
        root / "src" / "nlp",
        root / "src" / "preprocessing",
        root / "src" / "scraping",
        root / "src" / "visualization",
        root / "tests",
        root / "scripts"
    ]
    
    for d in dirs:
        check_directory(d)
    
    # Required files
    print("\nChecking required files:")
    files = [
        root / ".env.example",
        root / "requirements.txt",
        root / "main.py",
        root / "README.md",
        root / "src" / "db" / "database.py",
        root / "src" / "db" / "init_db.py",
        root / "src" / "db" / "load_data.py",
        root / "src" / "nlp" / "sentiment_analysis.py",
        root / "src" / "nlp" / "advanced_analysis.py",
        root / "src" / "preprocessing" / "clean_reviews.py",
        root / "src" / "scraping" / "scrape_reviews.py",
        root / "src" / "visualization" / "visualize_results.py",
        root / "tests" / "test_database.py",
        root / "tests" / "test_database_connection.py"
    ]
    
    missing_files = []
    for f in files:
        if not check_file(f):
            missing_files.append(str(f))
    
    if missing_files:
        print("\nMissing required files:")
        for f in missing_files:
            print(f"- {f}")
        sys.exit(1)
    
    print("\nProject structure is valid!")
    sys.exit(0)

if __name__ == "__main__":
    main()
