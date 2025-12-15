// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

let markerArea = null;
let imageLoaded = false;
let lastImageData = null;

// Add global error handlers for visibility
window.onerror = function(message, source, lineno, colno, error) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = `Error: ${message} at ${source}:${lineno}`;
        statusText.classList.add('active');
    }
    console.error('Global error:', message, error);
    return false;
};

window.addEventListener('unhandledrejection', function(event) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = `Unhandled promise rejection: ${event.reason}`;
        statusText.classList.add('active');
    }
    console.error('Unhandled rejection:', event.reason);
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
            return;
        }

        const targetImage = document.getElementById('targetImage');
        const loadingText = document.getElementById('loadingText');
        const statusText = document.getElementById('statusText');
        loadingText.classList.add('active');

        const mj = window.markerjs2 || window.markerjs;
        if (!mj) {
            loadingText.classList.remove('active');
            loadingText.textContent = 'Marker.js failed to load.';
            if (statusText) {
                statusText.textContent = 'Marker.js not loaded - library missing';
                statusText.classList.add('active');
            }
            console.error('Marker.js global not found', window);
            return;
        }

        markerArea = new mj.MarkerArea(targetImage);
        
        // Force inline mode to render inside iframe
        markerArea.settings.displayMode = 'inline';
        
        // Set target root for inline UI
        const editorHost = document.getElementById('editorHost');
        if (editorHost) {
            markerArea.settings.targetRoot = editorHost;
        }
        
        markerArea.uiStyleSettings.toolbarBackgroundColor = '#4CAF50';
        markerArea.uiStyleSettings.toolbarColor = '#ffffff';

        // Restrict to only outline/unfilled marker types
        markerArea.availableMarkerTypes = [
            mj.FreehandMarker,
            mj.ArrowMarker,
            mj.LineMarker,
            mj.TextMarker,
            mj.EllipseMarker,  // Unfilled circle/ellipse
            mj.FrameMarker      // Unfilled square/rectangle
        ];

        // Track whether save has occurred to prevent double cancel
        let didSave = false;

        // Helper function to send saved image back to Streamlit
        function sendSaved(dataUrl) {
            didSave = true;
            Streamlit.setComponentValue({ saved: true, pngDataUrl: dataUrl });
            Streamlit.setFrameHeight();
        }

        // Listen for both render and rendered events (markerjs2 may fire either)
        markerArea.addEventListener('render', (event) => {
            loadingText.classList.remove('active');
            sendSaved(event.dataUrl);
        });

        markerArea.addEventListener('rendered', (event) => {
            loadingText.classList.remove('active');
            sendSaved(event.dataUrl);
        });

        markerArea.addEventListener('close', () => {
            loadingText.classList.remove('active');
            // Only send cancelled if save didn't happen
            if (!didSave) {
                Streamlit.setComponentValue({
                    cancelled: true,
                    saved: false,
                    pngDataUrl: null
                });
            }
            Streamlit.setFrameHeight();
        });

        markerArea.show();
        loadingText.classList.remove('active');
    } catch (err) {
        const loadingText = document.getElementById('loadingText');
        const statusText = document.getElementById('statusText');
        loadingText.classList.remove('active');
        loadingText.textContent = 'Editor failed to start. Check console.';
        if (statusText) {
            statusText.textContent = `Editor error: ${err.message}`;
            statusText.classList.add('active');
        }
        console.error(err);
    }
}

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
