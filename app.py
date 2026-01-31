"""
EIN Finder - Web application to search for Employer Identification Numbers (EINs)
for businesses from public documents to help with 1099 tax form generation.
"""

from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

app = Flask(__name__)

# SEC EDGAR requires a User-Agent header with contact info
SEC_USER_AGENT = os.environ.get('SEC_USER_AGENT', 'EINFinder/1.0 (contact@example.com)')

class EINSearcher:
    """Class to search for EINs from various public sources"""
    
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SEC_USER_AGENT,
            'Accept': 'application/json, application/xml, text/html'
        })
    
    def search_ein(self, business_name, city=None, state=None):
        """
        Search for EIN using business name and optional location
        Returns a list of potential matches with EIN information
        """
        results = []
        
        # Search multiple sources
        results.extend(self._search_irs_exempt_organizations(business_name, city, state))
        results.extend(self._search_sec_edgar(business_name))
        
        return results
    
    def _search_irs_exempt_organizations(self, business_name, city=None, state=None):
        """
        Search IRS Tax Exempt Organization Database (TEOS)
        Uses the IRS EOS web search to find non-profit organizations
        """
        results = []
        
        try:
            # IRS Tax Exempt Organization Search API endpoint
            search_url = "https://apps.irs.gov/app/eos/allSearch"
            
            # Build search parameters
            params = {
                'ein': '',
                'names': business_name,
                'city': city or '',
                'state': state or '',
                'country': 'US',
                'deductibility': 'all',
                'dispatchMethod': 'searchAll',
                'postDateFrom': '',
                'postDateTo': '',
                'exemptTypeCode': '',
                'indexOfFirstRow': '0',
                'sortColumn': 'orgName',
                'resultsPerPage': '25',
                'isDescending': 'false'
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                # Parse the HTML response
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find results table rows
                table = soup.find('table', {'id': 'searchResults'})
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows[:10]:  # Limit to first 10 results
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            ein_raw = cells[0].get_text(strip=True)
                            org_name = cells[1].get_text(strip=True)
                            org_city = cells[2].get_text(strip=True)
                            org_state = cells[3].get_text(strip=True)
                            org_country = cells[4].get_text(strip=True)
                            
                            # Format EIN as XX-XXXXXXX
                            ein_formatted = self._format_ein(ein_raw)
                            
                            results.append({
                                'business_name': org_name,
                                'ein': ein_formatted,
                                'city': org_city,
                                'state': org_state,
                                'source': 'IRS Tax Exempt Organization Database',
                                'note': 'Tax-exempt organization'
                            })
                
                # Alternative: Try parsing JSON if available
                if not results:
                    try:
                        data = response.json()
                        if 'searchResults' in data:
                            for org in data['searchResults'][:10]:
                                ein_formatted = self._format_ein(org.get('ein', ''))
                                results.append({
                                    'business_name': org.get('name', 'N/A'),
                                    'ein': ein_formatted,
                                    'city': org.get('city', 'N/A'),
                                    'state': org.get('state', 'N/A'),
                                    'source': 'IRS Tax Exempt Organization Database',
                                    'note': 'Tax-exempt organization'
                                })
                    except:
                        pass
                        
        except requests.exceptions.Timeout:
            results.append({
                'business_name': business_name,
                'ein': 'N/A',
                'city': city or 'N/A',
                'state': state or 'N/A',
                'source': 'IRS Tax Exempt Organization Database',
                'note': 'Search timed out. Please try again.'
            })
        except Exception as e:
            print(f"Error searching IRS database: {e}")
            results.append({
                'business_name': business_name,
                'ein': 'N/A',
                'city': city or 'N/A',
                'state': state or 'N/A',
                'source': 'IRS Tax Exempt Organization Database',
                'note': f'Search error: Unable to connect to IRS database'
            })
        
        return results
    
    def _search_sec_edgar(self, business_name):
        """
        Search SEC EDGAR database for publicly traded companies
        Public companies must disclose their EIN in certain filings
        """
        results = []
        
        try:
            # Step 1: Search for company by name using SEC full-text search
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'company': business_name,
                'type': '10-K',  # Annual reports contain EIN
                'dateb': '',
                'owner': 'include',
                'count': '10',
                'output': 'atom'
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                # Parse Atom feed response
                root = ET.fromstring(response.content)
                
                # Define namespace
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entries = root.findall('.//atom:entry', ns)
                
                for entry in entries[:5]:  # Limit to first 5 companies
                    title = entry.find('atom:title', ns)
                    company_info = entry.find('atom:content', ns)
                    
                    if title is not None:
                        company_name = title.text.split(' - ')[0] if title.text else 'N/A'
                        cik = self._extract_cik_from_entry(entry, ns)
                        
                        if cik:
                            # Step 2: Get company details including EIN
                            ein = self._get_ein_from_sec_filings(cik)
                            
                            if ein and ein != 'N/A':
                                results.append({
                                    'business_name': company_name,
                                    'ein': ein,
                                    'city': 'N/A',
                                    'state': 'N/A',
                                    'source': 'SEC EDGAR Database',
                                    'note': f'CIK: {cik} - Publicly traded company'
                                })
                
                # If no results with EIN found, still show companies found
                if not results and entries:
                    for entry in entries[:3]:
                        title = entry.find('atom:title', ns)
                        if title is not None:
                            company_name = title.text.split(' - ')[0] if title.text else 'N/A'
                            cik = self._extract_cik_from_entry(entry, ns)
                            results.append({
                                'business_name': company_name,
                                'ein': 'Check SEC filings',
                                'city': 'N/A',
                                'state': 'N/A',
                                'source': 'SEC EDGAR Database',
                                'note': f'CIK: {cik} - Review 10-K filing for EIN'
                            })
                            
        except requests.exceptions.Timeout:
            results.append({
                'business_name': business_name,
                'ein': 'N/A',
                'city': 'N/A',
                'state': 'N/A',
                'source': 'SEC EDGAR Database',
                'note': 'Search timed out. Please try again.'
            })
        except Exception as e:
            print(f"Error searching SEC EDGAR: {e}")
            results.append({
                'business_name': business_name,
                'ein': 'N/A',
                'city': 'N/A',
                'state': 'N/A',
                'source': 'SEC EDGAR Database',
                'note': 'Unable to connect to SEC EDGAR'
            })
        
        return results
    
    def _extract_cik_from_entry(self, entry, ns):
        """Extract CIK number from SEC EDGAR Atom entry"""
        try:
            # CIK is usually in the id or link
            link = entry.find('atom:link', ns)
            if link is not None:
                href = link.get('href', '')
                # Extract CIK from URL like /cgi-bin/browse-edgar?action=getcompany&CIK=0000320193
                match = re.search(r'CIK[=]?(\d+)', href, re.IGNORECASE)
                if match:
                    return match.group(1).lstrip('0') or '0'
            
            # Try from id
            entry_id = entry.find('atom:id', ns)
            if entry_id is not None:
                match = re.search(r'(\d{7,10})', entry_id.text or '')
                if match:
                    return match.group(1)
        except:
            pass
        return None
    
    def _get_ein_from_sec_filings(self, cik):
        """
        Get EIN from SEC company filings
        EIN is typically found in 10-K annual reports
        """
        try:
            # Pad CIK to 10 digits
            cik_padded = cik.zfill(10)
            
            # Get company submission data
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
            response = self.session.get(submissions_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # EIN is sometimes directly in the company info
                ein = data.get('ein')
                if ein:
                    return self._format_ein(ein)
                
                # Look in recent filings for 10-K with EIN
                filings = data.get('filings', {}).get('recent', {})
                forms = filings.get('form', [])
                accession_numbers = filings.get('accessionNumber', [])
                
                # Find most recent 10-K
                for i, form in enumerate(forms):
                    if form in ['10-K', '10-K/A']:
                        if i < len(accession_numbers):
                            accession = accession_numbers[i].replace('-', '')
                            ein = self._extract_ein_from_filing(cik_padded, accession)
                            if ein:
                                return ein
                        break  # Only check most recent 10-K
                        
        except Exception as e:
            print(f"Error getting EIN from SEC filings: {e}")
        
        return 'N/A'
    
    def _extract_ein_from_filing(self, cik, accession_number):
        """Extract EIN from a specific SEC filing document"""
        try:
            # Try to get the filing index
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
            response = self.session.get(f"{filing_url}/index.json", timeout=10)
            
            if response.status_code == 200:
                index_data = response.json()
                
                # Look for the main 10-K document
                for item in index_data.get('directory', {}).get('item', []):
                    name = item.get('name', '')
                    if name.endswith('.htm') or name.endswith('.html'):
                        doc_url = f"{filing_url}/{name}"
                        doc_response = self.session.get(doc_url, timeout=15)
                        
                        if doc_response.status_code == 200:
                            # Search for EIN pattern in document
                            ein_match = re.search(
                                r'I\.?R\.?S\.?\s*(?:Employer\s*)?(?:Identification\s*)?(?:Number|No\.?|#)?\s*[:\-]?\s*(\d{2}[-\s]?\d{7})',
                                doc_response.text,
                                re.IGNORECASE
                            )
                            if ein_match:
                                return self._format_ein(ein_match.group(1))
                            
                            # Alternative pattern
                            ein_match = re.search(r'EIN[:\s]+(\d{2}[-\s]?\d{7})', doc_response.text, re.IGNORECASE)
                            if ein_match:
                                return self._format_ein(ein_match.group(1))
                        break  # Only check first HTML document
                        
        except Exception as e:
            print(f"Error extracting EIN from filing: {e}")
        
        return None
    
    def _format_ein(self, ein_raw):
        """Format EIN to standard XX-XXXXXXX format"""
        if not ein_raw:
            return 'N/A'
        
        # Remove any non-digit characters
        digits = re.sub(r'\D', '', str(ein_raw))
        
        if len(digits) == 9:
            return f"{digits[:2]}-{digits[2:]}"
        elif len(digits) > 0:
            return ein_raw  # Return as-is if not 9 digits
        
        return 'N/A'
    
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
    # Only enable debug mode in development
    # In production, set FLASK_ENV to 'production'
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=3000)
