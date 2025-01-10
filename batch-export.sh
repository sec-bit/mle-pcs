#!/bin/bash
# Will export all markdown files to PDF files using Typora on MacOS
# Find all markdown files (both .md and .markdown extensions) and sort them
find . -type f \( -name "*.md" -o -name "*.markdown" \) | sort | while read -r file; do
    # Skip files in .git directory
    if [[ "$file" == *".git"* ]]; then
        continue
    fi

    # Skip blacklisted files
    if [[ "$file" == *"README.md"* ||
          "$file" == *"CONTRIBUTING.md"* ||
          "$file" == *"mle_div.md"* ||
          "$file" == *"mmcs/interpretions/src"* ]]; then
        continue
    fi

    echo "Processing: $file"
    ./export-pdf.sh "$file"
done

echo "All markdown files have been processed."
