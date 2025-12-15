// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

// DEBUG_MODE: Set to true for verbose debugging with minimal initialization
const DEBUG_MODE = false;

let markerArea = null;
let imageLoaded = false;
let lastImageData = null;

// Enhanced status logging with stack traces
const statusLogs = [];

function setStatus(msg) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusLogs.push(`[${new Date().toISOString().split('T')[1].slice(0, -1)}] ${msg}`);
        statusText.textContent = statusLogs.join('\n');
        statusText.classList.add('active');
    }
    console.log(msg);
}

// Add global error handlers with detailed stack traces
window.addEventListener("error", (e) => {
    setStatus("WINDOW ERROR: " + e.message);
    if (e.error && e.error.stack) {
        setStatus(e.error.stack);
    } else {
        setStatus("no stack trace available");
    }
    return false;
});

window.addEventListener("unhandledrejection", (e) => {
    setStatus("PROMISE REJECTION: " + (e.reason || "unknown reason"));
    if (e.reason && e.reason.stack) {
        setStatus(e.reason.stack);
    } else {
        setStatus("no stack trace available");
    }
});

function onRender(event) {
    const data = event.detail;
    
    if (!data || !data.args || !data.args.image_data) {
        console.error('No image data received');
        return;
    }

    const imageData = data.args.image_data;
    
    // If image hasn't changed, just set frame height and return
    if (imageData === lastImageData) {
        Streamlit.setFrameHeight();
        return;
    }
    
    // Image has changed - close existing editor and prepare for new one
    lastImageData = imageData;
    
    if (markerArea) {
        try {
            markerArea.close();
        } catch (e) {
            console.log('Error closing existing marker area:', e);
        }
        markerArea = null;
    }
    
    const targetImage = document.getElementById('targetImage');
    
    // Wait for image to load before auto-opening editor
    targetImage.onload = function() {
        imageLoaded = true;
        console.log('Image loaded successfully');
        
        const h = Math.max(700, targetImage.getBoundingClientRect().height + 200);
        Streamlit.setFrameHeight(h);
        
        // Use requestAnimationFrame + setTimeout for proper timing
        // Ensures layout is calculated and DOM is ready before showing editor
        requestAnimationFrame(() => {
            setTimeout(() => {
                showMarkerArea();
            }, 50); // Small delay allows Streamlit iframe to stabilize
        });
    };
    
    targetImage.onerror = function() {
        console.error('Failed to load image');
        imageLoaded = false;
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = 'Failed to load image';
            statusText.classList.add('active');
        }
    };
    
    // Set image source (should be base64 data URL)
    targetImage.src = imageData;
}

function showMarkerArea() {
    try {
        if (!imageLoaded) {
            if (DEBUG_MODE) setStatus("showMarkerArea: image not loaded yet");
            return;
        }

        const targetImage = document.getElementById('targetImage');
        const loadingText = document.getElementById('loadingText');
        loadingText.classList.add('active');

        // Check if image has naturalWidth/naturalHeight
        if (!targetImage.naturalWidth || !targetImage.naturalHeight) {
            setStatus("Image not ready: naturalWidth=" + targetImage.naturalWidth + ", naturalHeight=" + targetImage.naturalHeight);
            loadingText.classList.remove('active');
            return;
        }

        if (DEBUG_MODE) setStatus("Image ready: " + targetImage.naturalWidth + "x" + targetImage.naturalHeight);

        const mj = window.markerjs2 || window.markerjs;
        if (!mj) {
            loadingText.classList.remove('active');
            loadingText.textContent = 'Marker.js failed to load.';
            setStatus('Marker.js not loaded - library missing');
            console.error('Marker.js global not found', window);
            return;
        }

        if (DEBUG_MODE) {
            setStatus("mj keys sample: " + Object.keys(mj).slice(0, 20).join(","));
        }

        markerArea = new mj.MarkerArea(targetImage);
        
        if (DEBUG_MODE) {
            setStatus("markerArea keys sample: " + Object.keys(markerArea).slice(0, 30).join(","));
            setStatus("has availableMarkerTypes: " + ("availableMarkerTypes" in markerArea));
            setStatus("markerArea.availableMarkerTypes type: " + typeof markerArea.availableMarkerTypes);
        }

        // Set display mode - use popup for more reliable initialization
        markerArea.settings.displayMode = 'popup';
        
        if (DEBUG_MODE) {
            // Minimal init in debug mode - no custom UI settings
            setStatus("Using minimal init (DEBUG_MODE=true)");
        } else {
            // Apply custom UI settings only when not in debug mode
            markerArea.uiStyleSettings.toolbarBackgroundColor = '#4CAF50';
            markerArea.uiStyleSettings.toolbarColor = '#ffffff';
        }

        // Restrict to only outline/unfilled marker types using safe direct assignment
        // NEVER use .push() - always use direct assignment
        const tools = [
            mj.FreehandMarker,
            mj.ArrowMarker,
            mj.LineMarker,
            mj.TextMarker,
            mj.EllipseMarker,  // Unfilled circle/ellipse
            mj.FrameMarker      // Unfilled square/rectangle
        ].filter(Boolean);

        if (DEBUG_MODE) setStatus("Tools to register: " + tools.length);

        // Only assign if the property exists; otherwise do not touch it
        // HARD RULE: DO NOT use .push() anywhere
        if ("availableMarkerTypes" in markerArea) {
            markerArea.availableMarkerTypes = tools;
            if (DEBUG_MODE) setStatus("Set markerArea.availableMarkerTypes directly");
        } else if (markerArea.settings && "availableMarkerTypes" in markerArea.settings) {
            markerArea.settings.availableMarkerTypes = tools;
            if (DEBUG_MODE) setStatus("Set markerArea.settings.availableMarkerTypes directly");
        } else {
            // Do not attempt to set availableMarkerTypes if API doesn't exist
            if (DEBUG_MODE) setStatus("No availableMarkerTypes API found; leaving defaults");
        }

        // Track whether save has occurred to prevent double cancel
        let didSave = false;

        // Helper function to send saved image back to Streamlit
        function sendSaved(dataUrl) {
            didSave = true;
            if (DEBUG_MODE) setStatus("Sending saved data to Streamlit");
            Streamlit.setComponentValue({ saved: true, pngDataUrl: dataUrl });
            Streamlit.setFrameHeight();
        }

        // Listen for BOTH render and rendered events (markerjs2 may fire either)
        markerArea.addEventListener('render', (event) => {
            loadingText.classList.remove('active');
            if (DEBUG_MODE) setStatus("render event fired");
            sendSaved(event.dataUrl);
        });

        markerArea.addEventListener('rendered', (event) => {
            loadingText.classList.remove('active');
            if (DEBUG_MODE) setStatus("rendered event fired");
            sendSaved(event.dataUrl);
        });

        markerArea.addEventListener('close', () => {
            loadingText.classList.remove('active');
            // Only send cancelled if save didn't happen
            if (!didSave) {
                if (DEBUG_MODE) setStatus("close event: no save, sending cancelled");
                Streamlit.setComponentValue({
                    cancelled: true,
                    saved: false,
                    pngDataUrl: null
                });
            } else {
                if (DEBUG_MODE) setStatus("close event: save already sent");
            }
            Streamlit.setFrameHeight();
        });

        if (DEBUG_MODE) setStatus("About to call markerArea.show()");
        markerArea.show();
        if (DEBUG_MODE) setStatus("markerArea.show() completed");
        loadingText.classList.remove('active');
    } catch (err) {
        const loadingText = document.getElementById('loadingText');
        loadingText.classList.remove('active');
        loadingText.textContent = 'Editor failed to start. Check console.';
        setStatus(`Editor error: ${err.message}`);
        if (err.stack) {
            setStatus(err.stack);
        }
        console.error(err);
    }
}

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
