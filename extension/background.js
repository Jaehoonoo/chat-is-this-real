// background.js - Handles extension icon clicks and communication

chrome.runtime.onInstalled.addListener(() => {
	console.log('Chat Is This Real extension installed');
});

// Handle extension icon clicks - toggle the widget
chrome.action.onClicked.addListener(async (tab) => {
	try {
		// Send message to content script to toggle widget
		await chrome.tabs.sendMessage(tab.id, {
			type: 'TOGGLE_WIDGET',
		});
	} catch (error) {
		console.log('Could not inject content script, trying to inject...');
		// If content script isn't loaded, inject it
		try {
			await chrome.scripting.executeScript({
				target: { tabId: tab.id },
				files: ['contentScript.js'],
			});
			await chrome.scripting.insertCSS({
				target: { tabId: tab.id },
				files: ['styles.css'],
			});
			// Try again after injection
			setTimeout(async () => {
				await chrome.tabs.sendMessage(tab.id, {
					type: 'TOGGLE_WIDGET',
				});
			}, 100);
		} catch (injectionError) {
			console.error('Failed to inject content script:', injectionError);
		}
	}
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (message.type === 'ANALYZE_PAGE') {
        analyzePage(message.url)
            .then( 
                (results) => {
                    sendResponse(
                        {
                            success: true, 
                            data: results
                        }
                    );
                }
            )
            .catch(
                (error) => {
                    console.error('API call failed:', error);
                    sendResponse(
                        {
                            success: false, 
                            error: error.message
                        }
                    )
                }
            )
		return true;
	}
});

// Simulate analysis (replace with real backend call)
async function simulateAnalysis() {
	await new Promise((resolve) => setTimeout(resolve, 2000));
	return {
		claims: [
			{
				claim_text:
					'Example potentially misleading claim detected on this page',
				confidence: '0.82',
				bias_score: '0.4',
				sources: ['BBC News', 'Reuters', 'Associated Press'],
			},
		],
	};
}

async function analyzePage(url) {
    const apiEndpoint = "http://localhost:8000/run";

    const response = await fetch(
        apiEndpoint,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(
                {
                    "input": { "url": url }
                }
            )
        }
    );

    if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
    }

    const results = await response.json();
    return results;
}
