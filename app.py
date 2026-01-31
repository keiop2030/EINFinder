"""
EIN Finder - Web application to search for Employer Identification Numbers (EINs)
for businesses from public documents to help with 1099 tax form generation.
"""

from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

app = Flask(__name__)

class EINSearcher:
    """Class to search for EINs from various public sources"""
    
    def __init__(self):
        self.results = []
    
    def search_ein(self, business_name, city=None, state=None):
        """
        Search for EIN using business name and optional location
        Returns a list of potential matches with EIN information
        """
        results = []
        
        # Clean and prepare search query
        search_query = business_name.strip()
        if city:
            search_query += f" {city.strip()}"
        if state:
            search_query += f" {state.strip()}"
        
        # Search multiple sources
        results.extend(self._search_irs_exempt_organizations(business_name, city, state))
        results.extend(self._search_sec_edgar(business_name))
        
        return results
    
    def _search_irs_exempt_organizations(self, business_name, city=None, state=None):
        """
        Search IRS Tax Exempt Organization Database
        Note: This searches for non-profit organizations with publicly available EINs
        """
        results = []
        
        try:
            # IRS Tax Exempt Organization Search (TEOS)
            # This is a simplified simulation - in production, you'd use actual IRS API
            # The IRS provides a downloadable database of exempt organizations
            
            # For demonstration, we'll simulate some results
            # In production, this would query the actual IRS database
            results.append({
                'business_name': business_name,
                'ein': 'XX-XXXXXXX',  # Placeholder
                'city': city or 'N/A',
                'state': state or 'N/A',
                'source': 'IRS Tax Exempt Organization Database (Sample)',
                'note': 'This is a demonstration. Connect to actual IRS TEOS database for real data.'
            })
            
        except Exception as e:
            print(f"Error searching IRS database: {e}")
        
        return results
    
    def _search_sec_edgar(self, business_name):
        """
        Search SEC EDGAR database for publicly traded companies
        Public companies must disclose their EIN in certain filings
        """
        results = []
        
        try:
            # SEC EDGAR search
            # For demonstration purposes - in production would use SEC API
            
            results.append({
                'business_name': business_name,
                'ein': 'XX-XXXXXXX',  # Placeholder
                'city': 'N/A',
                'state': 'N/A',
                'source': 'SEC EDGAR Database (Sample)',
                'note': 'This is a demonstration. Connect to actual SEC EDGAR API for real data.'
            })
            
        except Exception as e:
            print(f"Error searching SEC EDGAR: {e}")
        
        return results
    
    def validate_ein(self, ein):
        """
        Validate EIN format (XX-XXXXXXX)
        """
        pattern = r'^\d{2}-\d{7}$'
        return bool(re.match(pattern, ein))

@app.route('/')
def index():
    """Main page with search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle EIN search requests"""
    try:
        data = request.get_json()
        business_name = data.get('business_name', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        
        if not business_name:
            return jsonify({
                'error': 'Business name is required'
            }), 400
        
        searcher = EINSearcher()
        results = searcher.search_ein(business_name, city, state)
        
        return jsonify({
            'success': True,
            'query': {
                'business_name': business_name,
                'city': city,
                'state': state
            },
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/validate', methods=['POST'])
def validate():
    """Validate EIN format"""
    try:
        data = request.get_json()
        ein = data.get('ein', '').strip()
        
        searcher = EINSearcher()
        is_valid = searcher.validate_ein(ein)
        
        return jsonify({
            'ein': ein,
            'valid': is_valid
        })
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/about')
def about():
    """About page with information on the app"""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
