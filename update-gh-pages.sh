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

# Stash any changes in current branch
git stash push

# Switch to gh-pages branch
git checkout gh-pages

# Copy all PDF files from temporary directory preserving structure
cp -r "$tmp_dir"/. .

# Add all PDFs
git add ./**/*.pdf

# Move back PDF files from temporary directory preserving structure
cp -r "$tmp_dir"/. .
rm -rf "$tmp_dir"
echo "Restored PDF files from temporary directory"

# # Create commit with timestamp
# git commit -m "Update PDFs from main branch ($(date '+%Y-%m-%d %H:%M:%S'))"

# # Switch back to original branch
# git checkout -

# # Pop stashed changes if any
# git stash pop

# echo "PDF files have been updated in gh-pages branch"
