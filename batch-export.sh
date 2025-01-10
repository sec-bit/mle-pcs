#!/bin/bash
# Will export all markdown files to PDF files using Typora on MacOS

count=0

# Find all markdown files (both .md and .markdown extensions) and sort them
for file in $(find . -type f \( -name "*.md" -o -name "*.markdown" \) | sort); do
    # Skip files in .git directory
    if [[ "$file" == *".git"* ]]; then
        continue
    fi

    # Skip some files
    if [[ "$file" == *"README.md"* ||
          "$file" == *"CONTRIBUTING.md"* ||
          "$file" == *"mle_div.md"* ||
          "$file" == *"reversed-bit-order.md"* ||
          "$file" == *"mmcs/interpretions/src"* ]]; then
        continue
    fi

    echo "Processing: $file"
    ./export-pdf.sh "$file"
    ((count++))
done

echo "Processed $count markdown files."
