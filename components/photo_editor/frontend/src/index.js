// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

let markerArea = null;
let imageLoaded = false;
let lastImageData = null;

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
        
        // Automatically open the marker.js editor after a brief delay
        // to ensure all resources are ready
        setTimeout(() => {
            showMarkerArea();
        }, 150);
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
        if (!imageLoaded) {
            return;
        }

        const targetImage = document.getElementById('targetImage');
        const loadingText = document.getElementById('loadingText');
        loadingText.classList.add('active');

        const mj = window.markerjs2 || window.markerjs;
        if (!mj) {
            loadingText.classList.remove('active');
            loadingText.textContent = 'Marker.js failed to load.';
            console.error('Marker.js global not found', window);
            return;
        }

        markerArea = new mj.MarkerArea(targetImage);
        markerArea.settings.displayMode = 'popup';
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
        loadingText.classList.remove('active');
        loadingText.textContent = 'Editor failed to start. Check console.';
        console.error(err);
    }
}

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
