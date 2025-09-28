// background.js - Handles extension icon clicks and communication

// --- Configuration ---
const HOST = 'http://localhost:8000';
// const AGENT_NAME = 'extractor_agent';
const AGENT_NAME = 'master_agent';
const USER_ID = 'user_123';

// Session ID will be stored here. A more robust solution would use chrome.storage.
let sessionId = null;
// --- End Configuration ---

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
		console.log('Content script not ready, attempting to inject...');
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

// Handle messages from the content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (message.type === 'ANALYZE_PAGE') {
		console.log(`Received ANALYZE_PAGE dispatch req for URL: ${message.url}`);
		analyzePage(message.url)
			.then((results) => {
				sendResponse({ success: true, data: results });
			})
			.catch((error) => {
				console.error('API call failed:', error);
				sendResponse({ success: false, error: error.message });
			});
		return true; // Indicates that the response is sent asynchronously
	}
});

// Generates a simple unique ID
function generateUUID() {
	return (
		'ext-' + Date.now() + '-' + Math.random().toString(36).substring(2, 15)
	);
}

async function analyzePage(url) {
	// 1. Ensure a session exists
	if (!sessionId) {
		sessionId = generateUUID();
		const sessionUrl = `${HOST}/apps/${AGENT_NAME}/users/${USER_ID}/sessions/${sessionId}`;
		console.log(`Creating new session: ${sessionId}`);

		const sessionResponse = await fetch(sessionUrl, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
		});

		if (!sessionResponse.ok) {
			// If session exists, server might return an error. We can ignore it
			// unless it's a server error.
			if (sessionResponse.status !== 400) {
				const errorText = await sessionResponse.text();
				throw new Error(
					`Session creation failed with status ${sessionResponse.status}: ${errorText}`
				);
			}
			console.log('Session likely already exists, proceeding.');
		}
	}

	// 2. Run the Agent
	const runUrl = `${HOST}/run`;
	const runData = {
		app_name: AGENT_NAME,
		user_id: USER_ID,
		session_id: sessionId,
		new_message: {
			role: 'user',
			parts: [
				{
					text: `${url}`,
				},
			],
		},
	};

	console.log('Sending prompt to agent...');
	const runResponse = await fetch(runUrl, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(runData),
	});

	if (!runResponse.ok) {
		const errorText = await runResponse.text();
		throw new Error(
			`API request failed with status ${runResponse.status}: ${errorText}`
		);
	}

	const events = await runResponse.json();

	// 3. Process the final result
	if (Array.isArray(events) && events.length > 0) {
		const finalEvent = events[events.length - 1];
		return finalEvent.content;
	} else {
		throw new Error('Received an empty or invalid response from the agent.');
	}
}
