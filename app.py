#!/usr/bin/env python3
"""
Flask Web Application for Wikipedia Word Cloud Visualization

This web app displays word frequency data from Wikipedia categories as interactive word clouds.
It uses cached data when available, otherwise computes frequencies from scratch.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from wikipedia_category_analyzer import WikipediaAnalyzer
from color_palette import get_all_color_palettes
import traceback
import random

app = Flask(__name__)

# Global analyzer instance
analyzer = WikipediaAnalyzer()

@app.route('/')
def index():
    """Main page with word cloud visualization."""
    return render_template('index.html')

@app.route('/api/categories')
def get_cached_categories():
    """Get list of cached categories."""
    try:
        cache_dir = analyzer.cache_dir
        if not os.path.exists(cache_dir):
            return jsonify([])
        
        categories = []
        for filename in os.listdir(cache_dir):
            if filename.endswith('_analysis.json'):
                # Extract category name from filename
                parts = filename.replace('_analysis.json', '').split('_')
                if len(parts) >= 2:
                    # Remove hash part (last 8 characters)
                    category_parts = parts[:-1]
                    category = '_'.join(category_parts)
                    
                    # Load cache to get metadata
                    cache_path = os.path.join(cache_dir, filename)
                    try:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                            categories.append({
                                'name': cache_data.get('category', category),
                                'display_name': cache_data.get('category', category).replace('_', ' '),
                                'total_words': cache_data.get('total_unique_words', 0),
                                'total_occurrences': cache_data.get('total_word_occurrences', 0),
                                'analyzed_at': cache_data.get('analyzed_at', 'Unknown')
                            })
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue
        
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<category>')
def analyze_category(category):
    """Analyze a Wikipedia category and return word frequency data."""
    try:
        # Replace spaces with underscores for Wikipedia category format
        category = category.replace(' ', '_')
        
        # Get word frequencies (will use cache if available)
        word_freq = analyzer.analyze_category(category)
        
        if not word_freq:
            return jsonify({'error': 'No data found for this category'}), 404
        
        # Convert to list of dictionaries for easier frontend handling
        word_data = [
            {'word': word, 'frequency': freq}
            for word, freq in word_freq.items()
        ]
        
        # Sort by frequency (descending)
        word_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Calculate statistics
        total_words = len(word_data)
        total_occurrences = sum(item['frequency'] for item in word_data)
        max_frequency = word_data[0]['frequency'] if word_data else 0
        min_frequency = word_data[-1]['frequency'] if word_data else 0
        
        return jsonify({
            'category': category,
            'words': word_data,
            'stats': {
                'total_unique_words': total_words,
                'total_occurrences': total_occurrences,
                'max_frequency': max_frequency,
                'min_frequency': min_frequency
            }
        })
        
    except Exception as e:
        print(f"Error analyzing category '{category}': {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/color-palettes')
def get_color_palettes():
    """Get all available color palettes."""
    try:
        palettes = get_all_color_palettes()
        palette_data = {}
        for name, palette in palettes.items():
            palette_data[name] = {
                'name': name.title(),
                'colors': palette.colors
            }
        return jsonify(palette_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/word-cloud/<category>')
@app.route('/api/word-cloud/<category>/<palette_name>')
def get_word_cloud_data(category, palette_name='pastel'):
    """Get word cloud data for a specific category."""
    try:
        # Replace spaces with underscores for Wikipedia category format
        category = category.replace(' ', '_')
        
        # Get word frequencies
        word_freq = analyzer.analyze_category(category)
        
        if not word_freq:
            return jsonify({'error': 'No data found for this category'}), 404
        
        # Get the selected color palette
        palettes = get_all_color_palettes()
        if palette_name not in palettes:
            palette_name = 'pastel'  # Default fallback
        selected_palette = palettes[palette_name]
        
        # Prepare data for word cloud (limit to top 100 words for performance)
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_words = sorted_words[:100]
        
        # Calculate relative sizes (normalize to 10-100 range for better visualization)
        if top_words:
            max_freq = top_words[0][1]
            min_freq = top_words[-1][1]
            freq_range = max_freq - min_freq if max_freq != min_freq else 1
            
            word_cloud_data = []
            for i, (word, freq) in enumerate(top_words):
                # Normalize frequency to 10-100 range
                normalized_size = 10 + (90 * (freq - min_freq) / freq_range)
                # Assign color from palette (cycle through colors)
                color = selected_palette.colors[i % len(selected_palette.colors)]
                word_cloud_data.append({
                    'text': word,
                    'size': int(normalized_size),
                    'frequency': freq,
                    'color': color
                })
        else:
            word_cloud_data = []
        
        return jsonify({
            'category': category,
            'words': word_cloud_data,
            'total_words': len(word_freq),
            'displayed_words': len(word_cloud_data)
        })
        
    except Exception as e:
        print(f"Error getting word cloud data for '{category}': {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("Starting Wikipedia Word Cloud Web App...")
    print("Visit http://localhost:8080 to view the application")
    app.run(debug=True, host='0.0.0.0', port=8080)
