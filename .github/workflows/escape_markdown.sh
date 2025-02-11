#!/bin/bash

# This script escapes special Markdown characters for Telegram API
# Usage:
#   cat input.txt | ./escape_markdown.sh > output.txt
#   OR
#   echo "Your text here" | ./escape_markdown.sh

perl -pe 's/([_*[\]()~`>#+\-=\|{}.!])/\\$1/g'