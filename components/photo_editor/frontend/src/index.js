// Import Streamlit component library
import { Streamlit } from "streamlit-component-lib";

// DEBUG_MODE: Set to true for verbose debugging with minimal initialization
const DEBUG_MODE = false;

let markerArea = null;
let imageLoaded = false;
let lastImageData = null;
let targetImage = null;

// Enhanced status logging with stack traces (limited to prevent memory leaks)
const statusLogs = [];
const MAX_STATUS_LOGS = 50;

function setStatus(msg) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusLogs.push(`[${new Date().toISOString().split('T')[1].slice(0, -1)}] ${msg}`);
        // Keep only the last MAX_STATUS_LOGS entries
        if (statusLogs.length > MAX_STATUS_LOGS) {
            statusLogs.shift();
        }
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
    if (imageData === lastImageData && markerArea) {
        Streamlit.setFrameHeight();
        return;
    }
    
    // Image has changed - close existing editor and prepare for new one
    lastImageData = imageData;
    
    // Clean up existing marker area
    if (markerArea) {
        try {
            markerArea.remove();
        } catch (e) {
            console.log('Error removing existing marker area:', e);
        }
        markerArea = null;
    }
    
    targetImage = document.getElementById('targetImage');
    
    // Wait for image to load before auto-opening editor
    targetImage.onload = function() {
        imageLoaded = true;
        console.log('Image loaded successfully');
        
        const h = Math.max(800, targetImage.getBoundingClientRect().height + 300);
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

        const loadingText = document.getElementById('loadingText');
        loadingText.classList.add('active');

        // Ensure image is fully ready before initializing MarkerArea
        if (!targetImage.complete || !targetImage.naturalWidth) {
            setStatus("Image not ready: complete=" + targetImage.complete + ", naturalWidth=" + targetImage.naturalWidth);
            loadingText.classList.remove('active');
            return;
        }

        if (DEBUG_MODE) setStatus("Image ready: " + targetImage.naturalWidth + "x" + targetImage.naturalHeight);

        // Check if markerjs3 is loaded (UMD build exposes window.markerjs3)
        const mj3 = window.markerjs3;
        if (!mj3) {
            loadingText.classList.remove('active');
            loadingText.textContent = 'marker.js 3 failed to load.';
            setStatus('marker.js 3 not loaded - library missing');
            console.error('markerjs3 global not found', window);
            return;
        }

        if (DEBUG_MODE) {
            setStatus("mj3 keys sample: " + Object.keys(mj3).slice(0, 20).join(","));
        }

        // Create MarkerArea instance (markerjs3 is a web component)
        try {
            markerArea = new mj3.MarkerArea();
            markerArea.targetImage = targetImage;
        } catch (constructError) {
            setStatus(`MarkerArea construction failed: ${constructError.message}`);
            if (constructError.stack) setStatus(constructError.stack);
            loadingText.classList.remove('active');
            return;
        }
        
        if (DEBUG_MODE) {
            setStatus("markerArea created successfully");
        }

        // Add markerArea to the DOM
        const editorHost = document.getElementById('editorHost');
        editorHost.innerHTML = ''; // Clear previous content
        editorHost.appendChild(markerArea);

        // Create toolbar for allowed marker types
        createToolbar(editorHost, markerArea);

        loadingText.classList.remove('active');
        
        // Adjust frame height
        const h = Math.max(800, targetImage.getBoundingClientRect().height + 400);
        Streamlit.setFrameHeight(h);
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

function createToolbar(container, markerArea) {
    // Create toolbar div
    const toolbar = document.createElement('div');
    toolbar.id = 'markerToolbar';
    toolbar.style.cssText = `
        background-color: #4CAF50;
        padding: 12px;
        border-radius: 8px;
        margin-top: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        justify-content: center;
    `;

    // Define allowed marker types (unfilled shapes only)
    const allowedMarkers = [
        { name: 'FreehandMarker', label: '✏️ Freehand', title: 'Freehand drawing' },
        { name: 'ArrowMarker', label: '➡️ Arrow', title: 'Arrow' },
        { name: 'LineMarker', label: '━ Line', title: 'Line' },
        { name: 'TextMarker', label: '🔤 Text', title: 'Text annotation' },
        { name: 'EllipseMarker', label: '⭕ Circle', title: 'Unfilled circle/ellipse' },
        { name: 'FrameMarker', label: '▭ Rectangle', title: 'Unfilled rectangle' }
    ];

    // Create buttons for each marker type
    allowedMarkers.forEach(marker => {
        const btn = document.createElement('button');
        btn.textContent = marker.label;
        btn.title = marker.title;
        btn.style.cssText = `
            background-color: white;
            color: #333;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        `;
        btn.onmouseover = () => btn.style.backgroundColor = '#f0f0f0';
        btn.onmouseout = () => btn.style.backgroundColor = 'white';
        btn.onclick = () => {
            try {
                markerArea.createMarker(marker.name);
            } catch (e) {
                console.error(`Failed to create ${marker.name}:`, e);
                setStatus(`Failed to create marker: ${e.message}`);
            }
        };
        toolbar.appendChild(btn);
    });

    // Add separator
    const separator = document.createElement('div');
    separator.style.cssText = 'flex-grow: 1;';
    toolbar.appendChild(separator);

    // Create Save button
    const saveBtn = document.createElement('button');
    saveBtn.textContent = '💾 Save';
    saveBtn.title = 'Save annotations';
    saveBtn.style.cssText = `
        background-color: #2196F3;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        transition: background-color 0.2s;
    `;
    saveBtn.onmouseover = () => saveBtn.style.backgroundColor = '#1976D2';
    saveBtn.onmouseout = () => saveBtn.style.backgroundColor = '#2196F3';
    saveBtn.onclick = async () => {
        try {
            // Get current state
            const state = markerArea.getState();
            
            // Use Renderer to rasterize the annotated image
            const mj3 = window.markerjs3;
            const renderer = new mj3.Renderer();
            renderer.targetImage = targetImage;
            
            // Rasterize to data URL
            const dataUrl = await renderer.rasterize(state);
            
            // Send to Streamlit
            Streamlit.setComponentValue({ saved: true, pngDataUrl: dataUrl });
            Streamlit.setFrameHeight();
        } catch (e) {
            console.error('Failed to save:', e);
            setStatus(`Save failed: ${e.message}`);
        }
    };
    toolbar.appendChild(saveBtn);

    // Create Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '✖ Cancel';
    cancelBtn.title = 'Cancel editing';
    cancelBtn.style.cssText = `
        background-color: #f44336;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.2s;
    `;
    cancelBtn.onmouseover = () => cancelBtn.style.backgroundColor = '#d32f2f';
    cancelBtn.onmouseout = () => cancelBtn.style.backgroundColor = '#f44336';
    cancelBtn.onclick = () => {
        Streamlit.setComponentValue({ cancelled: true, saved: false, pngDataUrl: null });
        Streamlit.setFrameHeight();
    };
    toolbar.appendChild(cancelBtn);

    container.appendChild(toolbar);
}

// Register with Streamlit
Streamlit.setComponentReady();
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
