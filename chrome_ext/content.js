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

  displayS2tButton(videoStatus);
  // You can manipulate the DOM or display information as needed here
}

function displayS2tButton(videoStatus) {
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

      // Determine the button label and behavior based on videoStatus
      if (videoStatus.status === "not_found") {
        s2tButton.textContent = 'Add to Set2Tracks';
        s2tButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          window.open(SET2TRACK_URL + lastKnownVideoId, '_blank');
        });
      } else if (videoStatus.status === "published") {
        s2tButton.textContent = 'Check on Set2Tracks';
        s2tButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          window.open(SET2TRACK_URL + lastKnownVideoId, '_blank');
        });
      } else if (videoStatus.error) {
        // Display the error message without adding any button
        console.error("Error:", videoStatus.error);
      } else {
        // For any other status, just display it as a console log
        console.log("Status:", videoStatus.status);
      }

      // Only add the button if it's not an error scenario
      if (!videoStatus.error) {
        s2tButton.style.float = 'right';
        s2tButton.style.padding = '10px';
        s2tButton.style.borderRadius = '25px';  
        s2tButton.style.border = '1px solid #7480ff';
        s2tButton.style.cursor = 'pointer';

        parentEl.prepend(s2tButton);
        const videoTitle = parentEl.querySelector('#title');
        videoTitle.style.minHeight = '54px';
        console.log('Hello Square has been added.');
      }

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
