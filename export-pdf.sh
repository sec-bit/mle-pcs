#!/bin/bash
# Will export a markdown file to a PDF file using Typora on MacOS

# Get the input markdown file path
md_file="$(realpath "$1")"
# Construct the PDF file path by replacing .md with .pdf
pdf_file="${md_file%.md}.pdf"

# Check if PDF exists and remove it
if [ -f "$pdf_file" ]; then
    echo "Removing existing PDF file: $pdf_file"
    rm "$pdf_file"
fi

# Export to PDF using Typora
echo "Exporting $md_file"
osascript typora-export-pdf.applescript "$md_file"
echo "Exported to $pdf_file"
# Check PDF file
ls -lh "$pdf_file"

# Open the PDF file if flag is set
if [ "$2" == "open" ]; then
    echo "Opening $pdf_file"
    open "$pdf_file"
fi