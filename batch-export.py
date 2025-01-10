#!/usr/bin/env python3
"""
Script to export all markdown files to PDF files using Typora on MacOS
"""

import os
import glob
from pathlib import Path

def should_skip_file(file_path: str) -> bool:
    """Check if the file should be skipped based on certain conditions."""
    skip_patterns = [
        ".git",
        "README.md",
        "CONTRIBUTING.md",
        "mle_div.md",
        "reversed-bit-order.md",
        "mmcs/interpretions/src"
    ]
    return any(pattern in file_path for pattern in skip_patterns)

def main():
    count = 0
    # Find all markdown files in kzg10 directory
    markdown_files = []
    for ext in ['*.md', '*.markdown']:
        markdown_files.extend(glob.glob(f'./**/{ext}', recursive=True))
    
    # Sort the files for consistent processing order
    for file_path in sorted(markdown_files):
        if should_skip_file(file_path):
            continue
            
        print(f"Processing: {file_path}")
        # Uncomment the following line to actually process the files
        os.system(f'./export-pdf.sh "{file_path}"')
        count += 1
    
    print(f"Processed {count} markdown files.")

if __name__ == "__main__":
    main()
