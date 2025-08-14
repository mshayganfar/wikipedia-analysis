#!/usr/bin/env python3
"""
Wikipedia Category Word Frequency Analyzer

This script analyzes all pages in a Wikipedia category and outputs the cumulative
frequency of non-common words across all pages using the MediaWiki API.

Usage:
    python wikipedia_category_analyzer.py <category_name>

Example:
    python wikipedia_category_analyzer.py "Large_language_models"
"""

import argparse
import requests
import re
import sys
from collections import Counter
from typing import List, Dict, Set
import time
import json
import urllib3
import os
import hashlib
from datetime import datetime, timedelta

# Disable urllib3 warnings about SSL
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Common English stop words to filter out
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with',
    'or', 'but', 'not', 'this', 'they', 'their', 'them', 'these', 'those', 'then',
    'than', 'there', 'where', 'when', 'who', 'what', 'which', 'why', 'how', 'can',
    'could', 'would', 'should', 'may', 'might', 'must', 'shall', 'will', 'do', 'did',
    'does', 'have', 'had', 'having', 'been', 'being', 'am', 'is', 'are', 'was', 'were',
    'i', 'you', 'we', 'they', 'me', 'him', 'her', 'us', 'my', 'your', 'his', 'her',
    'our', 'also', 'all', 'any', 'some', 'each', 'every', 'no', 'none', 'one', 'two',
    'first', 'last', 'other', 'another', 'more', 'most', 'many', 'much', 'few', 'less',
    'such', 'same', 'different', 'new', 'old', 'good', 'bad', 'big', 'small', 'long',
    'short', 'high', 'low', 'right', 'left', 'up', 'down', 'here', 'there', 'now',
    'then', 'today', 'tomorrow', 'yesterday', 'always', 'never', 'sometimes', 'often',
    'usually', 'again', 'once', 'twice', 'very', 'too', 'so', 'just', 'only', 'even',
    'still', 'yet', 'already', 'almost', 'quite', 'rather', 'really', 'actually',
    'probably', 'perhaps', 'maybe', 'certainly', 'definitely', 'absolutely', 'exactly',
    'completely', 'totally', 'entirely', 'particularly', 'especially', 'generally',
    'specifically', 'basically', 'essentially', 'mainly', 'mostly', 'largely',
    'partly', 'slightly', 'somewhat', 'fairly', 'pretty', 'enough', 'too', 'very'
}

class WikipediaAnalyzer:
    def __init__(self, cache_dir: str = "cache", cache_expiry_days: int = 7):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikipediaAnalyzer/1.0 (Educational Purpose)'
        })
        self.cache_dir = cache_dir
        self.cache_expiry_days = cache_expiry_days
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_filename(self, category: str, cache_type: str) -> str:
        """Generate cache filename for a category."""
        # Create a hash of the category name for safe filename
        category_hash = hashlib.md5(category.encode()).hexdigest()[:8]
        safe_category = re.sub(r'[^a-zA-Z0-9_-]', '_', category)
        return os.path.join(self.cache_dir, f"{safe_category}_{category_hash}_{cache_type}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache file exists and is not expired."""
        if not os.path.exists(cache_file):
            return False
        
        # Check if cache is expired
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        expiry_time = datetime.now() - timedelta(days=self.cache_expiry_days)
        
        return file_time > expiry_time
    
    def _load_cache(self, cache_file: str) -> dict:
        """Load data from cache file."""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_cache(self, cache_file: str, data: dict):
        """Save data to cache file."""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def get_category_members(self, category: str) -> List[str]:
        """
        Get all page titles in a Wikipedia category.
        
        Args:
            category: Category name (without "Category:" prefix)
            
        Returns:
            List of page titles in the category
        """
        # Check cache first
        cache_file = self._get_cache_filename(category, "members")
        if self._is_cache_valid(cache_file):
            cached_data = self._load_cache(cache_file)
            if cached_data.get('pages'):
                print(f"Loading pages from cache for category: {category}")
                print(f"Found {len(cached_data['pages'])} cached pages")
                return cached_data['pages']
        
        print(f"Fetching pages from category: {category}")
        
        pages = []
        continue_token = None
        
        while True:
            params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{category}',
                'cmlimit': 500,  # Maximum allowed
                'cmtype': 'page',  # Only get pages, not subcategories
                'format': 'json'
            }
            
            if continue_token:
                params['cmcontinue'] = continue_token
            
            try:
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    print(f"API Error: {data['error']['info']}")
                    break
                
                members = data.get('query', {}).get('categorymembers', [])
                page_titles = [member['title'] for member in members]
                pages.extend(page_titles)
                
                print(f"Found {len(page_titles)} pages in this batch (total: {len(pages)})")
                
                # Check if there are more pages
                if 'continue' not in data:
                    break
                continue_token = data['continue']['cmcontinue']
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
                
            except requests.RequestException as e:
                print(f"Request error: {e}")
                break
        
        print(f"Total pages found: {len(pages)}")
        
        # Save to cache
        cache_data = {
            'category': category,
            'pages': pages,
            'fetched_at': datetime.now().isoformat(),
            'total_pages': len(pages)
        }
        self._save_cache(cache_file, cache_data)
        print(f"Saved {len(pages)} pages to cache")
        
        return pages

    def get_page_content(self, title: str) -> str:
        """
        Get the plain text content of a Wikipedia page.
        
        Args:
            title: Page title
            
        Returns:
            Plain text content of the page
        """
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            'exintro': False,  # Get full content, not just intro
            'explaintext': True,  # Get plain text, not HTML
            'exsectionformat': 'plain',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'extract' in page_data:
                    return page_data['extract']
            
            return ""
            
        except requests.RequestException as e:
            print(f"Error fetching content for '{title}': {e}")
            return ""

    def extract_words(self, text: str) -> List[str]:
        """
        Extract words from text, filtering out non-alphabetic tokens and stop words.
        
        Args:
            text: Input text
            
        Returns:
            List of filtered words
        """
        if not text:
            return []
        
        # Convert to lowercase and extract words (alphabetic only)
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter out stop words and short words (less than 3 characters)
        filtered_words = [
            word for word in words 
            if word not in STOP_WORDS and len(word) >= 3
        ]
        
        return filtered_words

    def analyze_category(self, category: str) -> Dict[str, int]:
        """
        Analyze all pages in a category and return word frequency.
        
        Args:
            category: Category name
            
        Returns:
            Dictionary of word frequencies
        """
        # Check if we have cached analysis results
        analysis_cache_file = self._get_cache_filename(category, "analysis")
        if self._is_cache_valid(analysis_cache_file):
            cached_analysis = self._load_cache(analysis_cache_file)
            if cached_analysis.get('word_frequencies'):
                print(f"Loading analysis results from cache for category: {category}")
                print(f"Found {len(cached_analysis['word_frequencies'])} unique words in cache")
                print(f"Total word occurrences: {sum(cached_analysis['word_frequencies'].values())}")
                return cached_analysis['word_frequencies']
        
        # Get all pages in the category
        page_titles = self.get_category_members(category)
        
        if not page_titles:
            print("No pages found in the category.")
            return {}
        
        # Collect all words from all pages
        all_words = []
        processed_pages = 0
        
        print(f"\nProcessing {len(page_titles)} pages...")
        
        for i, title in enumerate(page_titles, 1):
            print(f"Processing page {i}/{len(page_titles)}: {title}")
            
            content = self.get_page_content(title)
            if content:
                words = self.extract_words(content)
                all_words.extend(words)
                processed_pages += 1
                print(f"  Found {len(words)} non-common words")
            else:
                print(f"  No content found")
            
            # Small delay to be respectful to the API
            time.sleep(0.1)
        
        print(f"\nProcessed {processed_pages} pages successfully")
        print(f"Total non-common words collected: {len(all_words)}")
        
        # Count word frequencies
        word_freq = Counter(all_words)
        word_freq_dict = dict(word_freq)
        
        # Save analysis results to cache
        analysis_data = {
            'category': category,
            'word_frequencies': word_freq_dict,
            'analyzed_at': datetime.now().isoformat(),
            'total_pages_processed': processed_pages,
            'total_unique_words': len(word_freq_dict),
            'total_word_occurrences': sum(word_freq_dict.values())
        }
        self._save_cache(analysis_cache_file, analysis_data)
        print(f"Saved analysis results to cache")
        
        return word_freq_dict

    def print_results(self, word_freq: Dict[str, int], top_n: int = 50):
        """
        Print the word frequency results.
        
        Args:
            word_freq: Dictionary of word frequencies
            top_n: Number of top words to display
        """
        if not word_freq:
            print("No words to analyze.")
            return
        
        print(f"\n{'='*60}")
        print(f"WORD FREQUENCY ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"Total unique words: {len(word_freq)}")
        print(f"Total word occurrences: {sum(word_freq.values())}")
        
        # Sort by frequency (descending)
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nTop {min(top_n, len(sorted_words))} most frequent words:")
        print(f"{'Rank':<6} {'Word':<20} {'Frequency':<10}")
        print("-" * 40)
        
        for i, (word, freq) in enumerate(sorted_words[:top_n], 1):
            print(f"{i:<6} {word:<20} {freq:<10}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze word frequency in Wikipedia category pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wikipedia_category_analyzer.py "Large_language_models"
  python wikipedia_category_analyzer.py "Machine_learning"
  python wikipedia_category_analyzer.py "Artificial_intelligence"
        """
    )
    
    parser.add_argument(
        'category',
        help='Wikipedia category name (without "Category:" prefix)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=50,
        help='Number of top words to display (default: 50)'
    )
    
    parser.add_argument(
        '--output',
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--cache-dir',
        default='cache',
        help='Directory to store cache files (default: cache)'
    )
    
    parser.add_argument(
        '--cache-expiry',
        type=int,
        default=7,
        help='Cache expiry in days (default: 7)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching and fetch fresh data'
    )
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    if args.no_cache:
        # Use a temporary directory that gets cleaned up
        import tempfile
        cache_dir = tempfile.mkdtemp()
        cache_expiry = 0  # Immediate expiry
    else:
        cache_dir = args.cache_dir
        cache_expiry = args.cache_expiry
    
    analyzer = WikipediaAnalyzer(cache_dir=cache_dir, cache_expiry_days=cache_expiry)
    
    try:
        word_freq = analyzer.analyze_category(args.category)
        
        # Print results
        analyzer.print_results(word_freq, args.top)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(word_freq, f, indent=2, sort_keys=True)
            print(f"\nResults saved to: {args.output}")
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
