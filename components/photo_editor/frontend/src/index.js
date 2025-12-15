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
    try {
        if (!imageLoaded) return;

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

        markerArea.availableMarkerTypes = [
            mj.FreehandMarker,
            mj.ArrowMarker,
            mj.LineMarker,
            mj.TextMarker,
            mj.EllipseMarker,
            mj.FrameMarker
        ];

        markerArea.addEventListener('render', (event) => {
            loadingText.classList.remove('active');
            Streamlit.setComponentValue({
                pngDataUrl: event.dataUrl,
                saved: true
            });
        });

        markerArea.addEventListener('close', () => {
            loadingText.classList.remove('active');
            Streamlit.setComponentValue({
                cancelled: true,
                saved: false,
                pngDataUrl: null
            });
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
