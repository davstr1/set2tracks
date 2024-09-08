chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
  chrome.scripting.executeScript({
    target: { tabId: tabs[0].id },
    function: getVideoId
  }, (results) => {
    const videoId = results[0].result;
    if (videoId) {
      chrome.runtime.sendMessage({ action: 'checkVideoId', videoId: videoId }, response => {
        document.getElementById('statusText').textContent = response.message;
      });
    }
  });
});

function getVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}
