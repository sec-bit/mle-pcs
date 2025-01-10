#!/bin/bash

# Script to update PDF files in gh-pages branch

# Create a temporary directory for PDFs
tmp_dir=$(mktemp -d)
echo "Created temporary directory: $tmp_dir"

# Move all PDF files (except publications/) to temporary directory while preserving directory structure
find . -name "*.pdf" -type f ! -path "./publications/*" | while read file; do
    # Create target directory in tmp_dir
    mkdir -p "$tmp_dir/$(dirname "$file")"
    # Move file preserving path structure
    mv "$file" "$tmp_dir/$file"
done
echo "Moved PDF files to temporary directory"

# Switch to gh-pages branch
git checkout gh-pages

echo "Switched to gh-pages branch"

# Copy all PDF files from temporary directory preserving structure
echo "Restoring PDF files from temporary directory"
echo "You may need to delete some old files manually if directory structure or filename has changed"
cp -r "$tmp_dir"/. .

echo "Restored PDF files from temporary directory"

echo "Now commit those PDF files yourself"
