# Wikipedia Category Word Frequency Analyzer

This script analyzes all pages in a Wikipedia category and outputs the cumulative frequency of non-common words across all pages using the MediaWiki API.

## Features

- Fetches all pages from a specified Wikipedia category
- Extracts plain text content from each page
- Filters out common English stop words
- Calculates word frequency across all pages
- Displays top N most frequent words
- Optional JSON output for further analysis

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python wikipedia_category_analyzer.py "Large_language_models"
```

With custom options:
```bash
python wikipedia_category_analyzer.py "Machine_learning" --top 100 --output results.json
```

## Arguments

- `category`: Wikipedia category name (without "Category:" prefix)
- `--top N`: Number of top words to display (default: 50)
- `--output FILE`: Save results to JSON file

## Examples

```bash
# Analyze Large Language Models category
python wikipedia_category_analyzer.py "Large_language_models"

# Analyze Machine Learning with top 100 words
python wikipedia_category_analyzer.py "Machine_learning" --top 100

# Save results to file
python wikipedia_category_analyzer.py "Artificial_intelligence" --output ai_words.json
```

## Output

The script provides:
- Progress information during processing
- Total unique words found
- Total word occurrences
- Top N most frequent words with their frequencies
- Optional JSON export of all word frequencies
