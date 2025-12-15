// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

let markerArea = null;
let imageLoaded = false;

function onRender(event) {
    const data = event.detail;
    
    if (!data || !data.args || !data.args.image_data) {
        console.error('No image data received');
        return;
    }

    const imageData = data.args.image_data;
    const targetImage = document.getElementById('targetImage');
    
    // Wait for image to load before auto-opening editor
    targetImage.onload = function() {
        imageLoaded = true;
        console.log('Image loaded successfully');
        
        const h = Math.max(600, targetImage.getBoundingClientRect().height + 80);
        Streamlit.setFrameHeight(h);
        
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
    if (!imageLoaded) {
        console.error('Image not loaded yet');
        return;
    }

    const targetImage = document.getElementById('targetImage');
    const loadingText = document.getElementById('loadingText');
    
    loadingText.classList.add('active');
    
    // Create marker.js instance
    markerArea = new markerjs2.MarkerArea(targetImage);
    
    // Configure marker.js
    markerArea.settings.displayMode = 'popup';
    markerArea.uiStyleSettings.toolbarBackgroundColor = '#4CAF50';
    markerArea.uiStyleSettings.toolbarColor = '#ffffff';
    
    // Available tools: FreehandMarker, ArrowMarker, TextMarker, 
    // EllipseMarker, FrameMarker, LineMarker, etc.
    markerArea.availableMarkerTypes = [
        markerjs2.FreehandMarker,
        markerjs2.ArrowMarker,
        markerjs2.LineMarker,
        markerjs2.TextMarker,
        markerjs2.EllipseMarker,
        markerjs2.FrameMarker
    ];
    
    // Handle render (save) callback
    markerArea.addEventListener('render', (event) => {
        loadingText.classList.remove('active');
        
        // Send result back to Python
        Streamlit.setComponentValue({
            pngDataUrl: event.dataUrl,
            saved: true
        });
    });
    
    // Handle close without saving
    markerArea.addEventListener('close', () => {
        loadingText.classList.remove('active');
        Streamlit.setComponentValue({
            cancelled: true,
            saved: false,
            pngDataUrl: null
        });
    });
    
    // Show the marker area
    markerArea.show();
    loadingText.classList.remove('active');
}

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
