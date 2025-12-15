// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

let markerArea = null;
let imageLoaded = false;

// Debug logging helper
function logDebug(msg) {
    const el = document.getElementById("debug");
    if (el) {
        el.textContent += msg + "\n";
    }
    console.log(msg);
}

// Global error handlers
window.addEventListener("error", (e) => logDebug("WINDOW ERROR: " + e.message));
window.addEventListener("unhandledrejection", (e) => logDebug("PROMISE REJECT: " + e.reason));

function onRender(event) {
    logDebug("Render event fired");
    const data = event.detail;
    
    if (!data || !data.args || !data.args.image_data) {
        logDebug('ERROR: No image data received');
        console.error('No image data received');
        return;
    }

    const imageData = data.args.image_data;
    logDebug("image_data length: " + (imageData ? imageData.length : 0));
    const targetImage = document.getElementById('targetImage');
    
    // Wait for image to load before auto-opening editor
    targetImage.onload = function() {
        imageLoaded = true;
        logDebug('Image loaded successfully');
        logDebug('Image dimensions: ' + targetImage.width + 'x' + targetImage.height);
        console.log('Image loaded successfully');
        
        const h = Math.max(600, targetImage.getBoundingClientRect().height + 80);
        Streamlit.setFrameHeight(h);
        
        // Detect Marker.js availability
        logDebug("markerjs present: " + !!window.markerjs);
        logDebug("markerjs2 present: " + !!window.markerjs2);
        
        // Automatically open the marker.js editor after a brief delay
        // to ensure all resources are ready
        setTimeout(() => {
            showMarkerArea();
        }, 300);
    };
    
    targetImage.onerror = function() {
        console.error('Failed to load image');
        imageLoaded = false;
    };
    
    // Set image source (should be base64 data URL)
    targetImage.src = imageData;
}

function showMarkerArea() {
    try {
        logDebug("showMarkerArea called");
        if (!imageLoaded) {
            logDebug("Image not loaded yet, cannot show editor");
            return;
        }

        const targetImage = document.getElementById('targetImage');
        const loadingText = document.getElementById('loadingText');
        loadingText.classList.add('active');

        const mj = window.markerjs2 || window.markerjs;
        if (!mj) {
            const errorMsg = 'Marker.js not available - CDN blocked or wrong script.';
            logDebug(errorMsg);
            loadingText.classList.remove('active');
            loadingText.textContent = 'Marker.js failed to load.';
            console.error('Marker.js global not found', window);
            return;
        }

        logDebug("Marker.js found, creating MarkerArea");
        markerArea = new mj.MarkerArea(targetImage);
        
        markerArea.uiStyleSettings.toolbarBackgroundColor = '#4CAF50';
        markerArea.uiStyleSettings.toolbarColor = '#ffffff';

        markerArea.availableMarkerTypes = [
            mj.FreehandMarker,
            mj.ArrowMarker,
            mj.LineMarker,
            mj.TextMarker,
            mj.EllipseMarker,
            mj.FrameMarker
        ];

        markerArea.addEventListener('render', (event) => {
            logDebug("Editor saved, data URL length: " + (event.dataUrl ? event.dataUrl.length : 0));
            loadingText.classList.remove('active');
            Streamlit.setComponentValue({
                pngDataUrl: event.dataUrl,
                saved: true
            });
        });

        markerArea.addEventListener('close', () => {
            logDebug("Editor closed without saving");
            loadingText.classList.remove('active');
            Streamlit.setComponentValue({
                cancelled: true,
                saved: false,
                pngDataUrl: null
            });
        });

        // Try popup mode first, fallback to inline if it fails
        try {
            logDebug("Attempting to show editor in popup mode");
            markerArea.settings.displayMode = 'popup';
            markerArea.show();
            logDebug("Editor shown successfully in popup mode");
            loadingText.classList.remove('active');
        } catch (e) {
            logDebug("Popup failed, switching to inline: " + e);
            markerArea.settings.displayMode = 'inline';
            markerArea.show();
            logDebug("Editor shown in inline mode");
            loadingText.classList.remove('active');
        }
    } catch (err) {
        const loadingText = document.getElementById('loadingText');
        loadingText.classList.remove('active');
        loadingText.textContent = 'Editor failed to start. Check console.';
        logDebug("ERROR in showMarkerArea: " + err.message);
        console.error(err);
    }
}

// Add button click handler
document.addEventListener('DOMContentLoaded', () => {
    const openBtn = document.getElementById("openBtn");
    if (openBtn) {
        openBtn.onclick = () => {
            logDebug("Open button clicked");
            showMarkerArea();
        };
    }
    logDebug("Component initialized, waiting for render event");
});

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
