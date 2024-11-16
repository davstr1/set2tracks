console.log("Content script has loaded and is running.");

let lastKnownVideoId = '';
SERVER_URL = 'http://localhost:50001'
SET2TRACK_URL = SERVER_URL + '/insert_set/'
VIDEO_STATUS_URL = SERVER_URL + '/jax/check_set_status/'

// Function to check and log URL changes
async function checkForURLChange() {
  const currentURL = window.location.href;
  const urlParams = new URLSearchParams(new URL(currentURL).search);
  const videoId = urlParams.get('v') || '';
  if (videoId && videoId !== lastKnownVideoId) {
    console.log('Video id changed to:', videoId);
    lastKnownVideoId = videoId; // Update the last known URL
    displayVideoInfo(videoId);
  }
}

async function fetchVideoStatus(videoId) {
  try {
    const response = await fetch(VIDEO_STATUS_URL + videoId);
    const data = await response.json();
    console.log('Video status:', data);
    return data;
  } catch (error) {
    return { error: error.message };
  }
}
// Define the display function
async function displayVideoInfo(videoId) {
  // Example: Update the DOM, or log to console
  console.log('Displaying info for video id:', videoId);
  videoStatus = await fetchVideoStatus(videoId);

  // Analyse the videoStatus and display the button accordingly
  const videoStatusInfo = analyseVideoStatus(videoStatus);
  displayS2tButton(videoStatusInfo);
  // You can manipulate the DOM or display information as needed here
}

function analyseVideoStatus(videoStatus) {

  const status = videoStatus.status;
  const error = videoStatus.discarded_reason;

  const queuedStatuses = ["prequeued", "queued", "processing"];

  const isProcessing = queuedStatuses.some(str => status.includes(str));

  if (isProcessing) {
    return {'action': 'wait', 'label': 'Processing on Set2Tracks...'};
  }

  if (status === "not_found") {
    return {'action': 'add', 'label': 'Add to Set2Tracks'};
  }

  if (status === "published") {
    return {'action': 'check', 'label': 'Check on Set2Tracks'};
  }

  if (error) {
    if (error.includes("live")) {
      return {'action': 'add', 'label': 'Add to Set2Tracks'};
    }
    return {'action': 'error', 'label': error};
  }

}

function displayS2tButton(videoStatusInfo) {
  const tryAddS2tButton = setInterval(() => {
    //const parentEl = document.querySelector('.html5-video-container');
    const parentEl = document.querySelector('#above-the-fold');
    const s2tButtonAlreadyExists = document.querySelector('#set2Tracks_button');
    if(s2tButtonAlreadyExists) {
      s2tButtonAlreadyExists.remove();
    }
    if (parentEl) {
      const s2tButton = document.createElement('span');
      s2tButton.id = 'set2Tracks_button';
      console.log('Video status:', videoStatusInfo);
      const action = videoStatusInfo.action;

      if (action !== 'error' && action !== 'wait') {
        s2tButton.textContent = videoStatusInfo.label;
        s2tButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          window.open(SET2TRACK_URL + lastKnownVideoId, '_blank');
        });

      }

      
        s2tButton.textContent = videoStatusInfo.label;
      
      
        

      // Determine the button label and behavior based on videoStatus
     

      
    
        s2tButton.style.float = 'right';
        s2tButton.style.padding = '10px';
        s2tButton.style.borderRadius = '25px';  
        if(action !== 'error' && action !== 'wait') {
        s2tButton.style.border = '1px solid #7480ff';
        s2tButton.style.cursor = 'pointer';
        } else {
          s2tButton.style.border = '1px solid #ff0000';
        }

        parentEl.prepend(s2tButton);
        const videoTitle = parentEl.querySelector('#title');
        videoTitle.style.minHeight = '54px';
        console.log('Set2Tracks button has been added.');
      

      clearInterval(tryAddS2tButton); // Stop the interval after successfully adding the button
    } else {
      console.log('Waiting for YouTube video parentEl...');
    }
  }, 1000); // checks every 1000 milliseconds (1 second)
}


// Function to setup MutationObserver
function setupObserver() {
  if (document.body) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        // Check for URL change on each mutation
        checkForURLChange();
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['href']
    });

    console.log("Observer has been set up.");
  } else {
    console.log("document.body is not available.");
  }
}

// Check URL change on page load
checkForURLChange();

// Wait for the DOM to be fully loaded to setup the observer
document.addEventListener('DOMContentLoaded', setupObserver);
window.addEventListener('DOMContentLoaded', checkForURLChange);

// Listen to history API updates
window.addEventListener('popstate', checkForURLChange);
window.addEventListener('pushstate', checkForURLChange);
window.addEventListener('replacestate', checkForURLChange);

// Setup to catch manual URL changes (e.g., user enters a new URL)
window.addEventListener('load', checkForURLChange);
