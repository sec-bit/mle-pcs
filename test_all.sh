#!/bin/bash

# Find all Python files containing 'test' in their name from src and tests directories
test_files=$(find src tests -name '*test*.py')

# Loop through each test file and run it with sage
for file in $test_files; do
    echo "Running tests in $file"
    sage "$file"
    echo "----------------------------------------"
done

echo "All tests completed."
