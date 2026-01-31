// EIN Finder - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');

    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleSearch();
        });
    }

    function handleSearch() {
        // Get form values
        const businessName = document.getElementById('business_name').value.trim();
        const city = document.getElementById('city').value.trim();
        const state = document.getElementById('state').value.trim();

        if (!businessName) {
            showError('Please enter a business name');
            return;
        }

        // Show loading state
        showLoading();

        // Prepare request data
        const searchData = {
            business_name: businessName,
            city: city,
            state: state
        };

        // Make API request
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                displayResults(data);
            }
        })
        .catch(error => {
            showError('An error occurred while searching. Please try again.');
            console.error('Error:', error);
        });
    }

    function showLoading() {
        resultsSection.style.display = 'block';
        resultsContainer.innerHTML = `
            <div class="loading">
                <p>🔍 Searching public databases...</p>
            </div>
        `;
    }

    function showError(message) {
        resultsSection.style.display = 'block';
        resultsContainer.innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    function displayResults(data) {
        resultsSection.style.display = 'block';

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <h3>No Results Found</h3>
                    <p>No EIN information was found for "${data.query.business_name}" in the public databases.</p>
                    <p><strong>Suggestions:</strong></p>
                    <ul style="text-align: left; max-width: 500px; margin: 1rem auto;">
                        <li>Try different variations of the business name</li>
                        <li>Add or remove location information</li>
                        <li>Request a W-9 form directly from the business (most reliable method)</li>
                        <li>Check if the business is a non-profit or publicly traded company</li>
                    </ul>
                </div>
            `;
            return;
        }

        let resultsHTML = `
            <div style="margin-bottom: 1rem;">
                <strong>Search Query:</strong> ${data.query.business_name}
                ${data.query.city ? `, ${data.query.city}` : ''}
                ${data.query.state ? `, ${data.query.state}` : ''}
            </div>
            <div style="margin-bottom: 1rem;">
                <strong>Results found:</strong> ${data.count}
            </div>
        `;

        data.results.forEach((result, index) => {
            resultsHTML += `
                <div class="result-card">
                    <h3>${result.business_name}</h3>
                    <div class="result-info">
                        <div class="result-field">
                            <strong>EIN:</strong>
                            <span>${result.ein}</span>
                        </div>
                        <div class="result-field">
                            <strong>City:</strong>
                            <span>${result.city || 'N/A'}</span>
                        </div>
                        <div class="result-field">
                            <strong>State:</strong>
                            <span>${result.state || 'N/A'}</span>
                        </div>
                        <div class="result-field">
                            <strong>Source:</strong>
                            <span>${result.source}</span>
                        </div>
                    </div>
                    ${result.note ? `
                        <div class="result-note">
                            <strong>Note:</strong> ${result.note}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        resultsHTML += `
            <div class="warning-box" style="margin-top: 2rem;">
                <strong>⚠️ Important:</strong>
                <ul>
                    <li>Always verify EIN information directly with the business by requesting a W-9 form</li>
                    <li>This tool only searches publicly available information</li>
                    <li>Use this information at your own discretion for tax reporting purposes</li>
                </ul>
            </div>
        `;

        resultsContainer.innerHTML = resultsHTML;
    }
});
