// contentScript.js - Expandable overlay widget

class FactCheckerWidget {
	constructor() {
		this.isExpanded = false;
		this.isAnalyzing = false;
		this.widget = null;
		this.init();
	}

	init() {
		// Only inject if not already present
		if (document.getElementById('fact-checker-widget')) return;

		this.createWidget();
		this.attachEventListeners();
	}

	createWidget() {
		this.widget = document.createElement('div');
		this.widget.id = 'fact-checker-widget';
		this.widget.className = 'fact-checker-minimized';

		this.widget.innerHTML = `
            <div class="widget-minimized" id="widget-minimized">
                <div class="widget-icon">🤖</div>
                <div class="widget-label">Fact Check</div>
            </div>
            
            <div class="widget-expanded" id="widget-expanded" style="display: none;">
                <div class="widget-header">
                    <div class="widget-title">
                        <span class="widget-icon">🤖</span>
                        Chat, Is This Real?
                    </div>
                    <button class="widget-close" id="widget-close">×</button>
                </div>
                
                <div class="widget-content">
                    <div class="widget-status" id="widget-status">
                        Ready to analyze: ${window.location.hostname}
                    </div>
                    
                    <button class="widget-analyze-btn" id="widget-analyze-btn">
                        Analyze Current Page
                    </button>
                    
                    <div class="widget-loading" id="widget-loading" style="display: none;">
                        <div class="loading-spinner"></div>
                        <p>🔍 Analyzing content...</p>
                    </div>
                    
                    <div class="widget-results" id="widget-results">
                        <!-- Results will be populated here -->
                    </div>
                </div>
            </div>
        `;

		document.body.appendChild(this.widget);
	}

	attachEventListeners() {
		// Toggle expansion when clicking minimized widget
		const minimized = this.widget.querySelector('#widget-minimized');
		minimized.addEventListener('click', () => this.expand());

		// Close button
		const closeBtn = this.widget.querySelector('#widget-close');
		closeBtn.addEventListener('click', () => this.minimize());

		// Analyze button
		const analyzeBtn = this.widget.querySelector('#widget-analyze-btn');
		analyzeBtn.addEventListener('click', () => this.analyzeCurrentPage());

		// Prevent clicks on expanded widget from bubbling
		const expanded = this.widget.querySelector('#widget-expanded');
		expanded.addEventListener('click', (e) => e.stopPropagation());
	}

	expand() {
		this.isExpanded = true;
		this.widget.className = 'fact-checker-expanded';
		this.widget.querySelector('#widget-minimized').style.display = 'none';
		this.widget.querySelector('#widget-expanded').style.display = 'block';
	}

	minimize() {
		this.isExpanded = false;
		this.widget.className = 'fact-checker-minimized';
		this.widget.querySelector('#widget-minimized').style.display = 'flex';
		this.widget.querySelector('#widget-expanded').style.display = 'none';
	}

	async analyzeCurrentPage() {
		if (this.isAnalyzing) return;

		this.isAnalyzing = true;
		const analyzeBtn = this.widget.querySelector('#widget-analyze-btn');
		const loading = this.widget.querySelector('#widget-loading');
		const status = this.widget.querySelector('#widget-status');
		const results = this.widget.querySelector('#widget-results');

		// Show loading state
		analyzeBtn.disabled = true;
		loading.style.display = 'block';
		results.innerHTML = '';
		status.textContent = 'Analyzing content...';

		try {
			// For now, simulate analysis
			// TODO: Replace with real API call
			const analysisResults = await this.simulateAnalysis();
			this.renderResults(analysisResults);
			status.textContent = 'Analysis complete';
		} catch (error) {
			console.error('Analysis failed:', error);
			status.textContent = 'Analysis failed';
			results.innerHTML =
				'<div class="error-message">Analysis failed. Please try again.</div>';
		} finally {
			this.isAnalyzing = false;
			analyzeBtn.disabled = false;
			loading.style.display = 'none';
		}
	}

	async simulateAnalysis() {
		// Simulate API delay
		await new Promise((resolve) => setTimeout(resolve, 2000));

		return {
			claims: [
				{
					claim_text: 'Example claim detected on this page',
					confidence: '0.75',
					bias_score: '0.3',
					sources: ['Source 1', 'Source 2', 'Source 3'],
				},
				{
					claim_text: 'Example claim detected on this page',
					confidence: '0.75',
					bias_score: '0.3',
					sources: ['Source 1', 'Source 2', 'Source 3'],
				},
				{
					claim_text: 'Another potentially misleading statement',
					confidence: '0.62',
					bias_score: '0.5',
					sources: ['Source A', 'Source B'],
				},
			],
		};
	}

	renderResults(data) {
		const results = this.widget.querySelector('#widget-results');
		results.innerHTML = '';

		if (!data || !data.claims || data.claims.length === 0) {
			results.innerHTML = `
                <div class="claim-card success">
                    <div class="claim-title">✅ No misleading claims detected!</div>
                    <div class="claim-description">This page appears to contain reliable information.</div>
                </div>
            `;
			return;
		}

		data.claims.forEach((claim, index) => {
			const claimCard = document.createElement('div');
			claimCard.className = 'claim-card';

			const confidenceClass =
				parseFloat(claim.confidence) > 0.7
					? 'high-confidence'
					: 'low-confidence';

			claimCard.innerHTML = `
                <div class="claim-title">
                    🔍 Claim ${index + 1}: ${claim.claim_text}
                </div>
                <div class="claim-score ${confidenceClass}">
                    Confidence: ${(parseFloat(claim.confidence) * 100).toFixed(
											0
										)}% 
                    | Bias: ${(parseFloat(claim.bias_score) * 100).toFixed(0)}%
                </div>
                <div class="claim-sources">
                    <div class="sources-label">Sources:</div>
                    <div class="chip-container">
                        ${claim.sources
													.map(
														(source) =>
															`<span class="chip" onclick="alert('Source: ${source}')">${source}</span>`
													)
													.join('')}
                    </div>
                </div>
            `;

			results.appendChild(claimCard);
		});
	}
}

// Initialize the widget when page loads
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', () => new FactCheckerWidget());
} else {
	new FactCheckerWidget();
}
