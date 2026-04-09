// Create context menu when extension is installed
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
      id: "checkSpam",
      title: "Check if spam",
      contexts: ["selection"]
    });
  });
  
  // Handle context menu click
  chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "checkSpam") {
      const selectedText = info.selectionText;
      
      // Send to API
      fetch('http://127.0.0.1:8000/classify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: selectedText })
      })
      .then(response => response.json())
      .then(data => {
        // Show result as notification or alert
        const result = data.is_spam ? "SPAM" : "NOT SPAM";
        const confidence = (data.confidence * 100).toFixed(1);
        
        // Inject content script to show result on page
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: showResult,
          args: [result, confidence, data.processing_time_ms]
        });
      })
      .catch(error => {
        console.error('Error:', error);
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: showError
        });
      });
    }
  });
  
  // Function that will be injected into the page
  function showResult(result, confidence, timeMs) {
    // Remove any existing result box
    const existing = document.getElementById('spam-detector-result');
    if (existing) existing.remove();
    
    // Create result box
    const resultBox = document.createElement('div');
    resultBox.id = 'spam-detector-result';
    resultBox.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 20px;
      background: ${result === 'SPAM' ? '#fee' : '#efe'};
      border: 2px solid ${result === 'SPAM' ? '#f44336' : '#4caf50'};
      border-radius: 10px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      font-family: Arial, sans-serif;
      min-width: 250px;
    `;
    
    resultBox.innerHTML = `
      <div style="font-size: 18px; font-weight: bold; color: ${result === 'SPAM' ? '#d32f2f' : '#388e3c'}; margin-bottom: 8px;">
        ${result === 'SPAM' ? '⚠️ SPAM Detected!' : '✅ Not Spam'}
      </div>
      <div style="font-size: 14px; color: #666;">
        Confidence: ${confidence}%<br>
        Processing: ${timeMs}ms
      </div>
      <button onclick="this.parentElement.remove()" style="
        margin-top: 10px;
        padding: 5px 15px;
        background: #666;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
      ">Close</button>
    `;
    
    document.body.appendChild(resultBox);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (resultBox.parentElement) {
        resultBox.remove();
      }
    }, 5000);
  }
  
  function showError() {
    const resultBox = document.createElement('div');
    resultBox.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 20px;
      background: #fff3cd;
      border: 2px solid #ffc107;
      border-radius: 10px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    resultBox.innerHTML = `
      <div style="color: #856404;">
        Failed to connect to API. Make sure the backend is running.
      </div>
    `;
    document.body.appendChild(resultBox);
    setTimeout(() => resultBox.remove(), 3000);
  }