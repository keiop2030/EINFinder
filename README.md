# EINFinder

Web app that searches public documents for EIN (Employer Identification Numbers) for businesses in order to generate 1099s for taxes.

## Overview

EINFinder is a Flask-based web application that helps users search for Employer Identification Numbers (EINs) from publicly available databases. This is particularly useful when preparing 1099 tax forms for contractors and vendors.

## Features

- 🔍 Search for EINs by business name and location
- 📊 Search multiple public data sources:
  - IRS Tax Exempt Organization Database (TEOS)
  - SEC EDGAR database for publicly traded companies
- ✅ EIN format validation
- 📱 Responsive web interface
- 🎨 Modern, user-friendly design

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/keiop2030/EINFinder.git
cd EINFinder
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

1. Start the Flask development server:
```bash
# For development (enables debug mode)
FLASK_ENV=development python app.py

# For production (debug mode disabled - default)
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:3000
```

3. Enter the business information in the search form:
   - **Business Name** (required): The name of the business
   - **City** (optional): The city where the business is located
   - **State** (optional): The state where the business is located

4. Click "Search EIN" to search public databases

### API Endpoints

The application provides REST API endpoints:

#### Search for EIN
```
POST /search
Content-Type: application/json

{
  "business_name": "Business Name",
  "city": "City Name",
  "state": "State"
}
```

#### Validate EIN Format
```
POST /validate
Content-Type: application/json

{
  "ein": "12-3456789"
}
```

## Project Structure

```
EINFinder/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Git ignore rules
├── templates/            # HTML templates
│   ├── index.html        # Main search page
│   └── about.html        # About page
└── static/               # Static files
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── app.js        # JavaScript for search functionality
```

## Data Sources

This application searches the following public databases:

1. **IRS Tax Exempt Organization Search (TEOS)**: Contains EINs for non-profit organizations
2. **SEC EDGAR**: Contains EINs for publicly traded companies in their SEC filings

## Important Notes

⚠️ **Privacy and Accuracy:**
- This tool only searches publicly available information
- Always verify EIN information directly with the business by requesting a W-9 form
- Not all businesses have publicly available EINs
- The most reliable way to obtain an EIN is to request a W-9 form from the business

## EIN Format

A valid EIN follows the format: **XX-XXXXXXX** (two digits, hyphen, seven digits)

Example: 12-3456789

## Use Cases

- Finding EINs for vendors and contractors when preparing 1099 forms
- Verifying business tax identification numbers
- Research on publicly available business information

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Data Sources**: IRS TEOS, SEC EDGAR
- **Libraries**: 
  - Flask 3.0.0
  - Requests 2.31.0
  - BeautifulSoup4 4.12.2

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

This tool is for informational purposes only. Always verify EIN information with the business directly using a W-9 form. The authors are not responsible for any inaccuracies or misuse of the information provided by this tool.
