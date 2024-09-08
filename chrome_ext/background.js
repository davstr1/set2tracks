chrome.webNavigation.onCompleted.addListener(function (details) {
  if (details.frameId === 0) { // Ensures it's the main frame
    console.log('Page loaded:', details.url);
  }
}, { url: [{ urlMatches: 'http://*/*' }, { urlMatches: 'https://*/*' }] });

