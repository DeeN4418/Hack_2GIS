import React, { useState, useEffect, useRef, useContext } from 'react';
import { load } from '@2gis/mapgl';
import Map from './Map';
import { MapContext, MapProvider } from './MapContext';

const AppContent = () => {
    // App state
    const [status, setStatus] = useState('Ready to record');
    const [audioBlob, setAudioBlob] = useState(null);
    const [response, setResponse] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [isSending, setIsSending] = useState(false);
    
    // Map and route state
    const [mapInstance] = useContext(MapContext);
    const routeObjectsRef = useRef([]); // Changed from routeRef to handle multiple objects

    // Audio recording refs
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const API_URL = 'http://localhost:8000/api/stt-route';

    // Effect to draw the route on the map when response data changes
    useEffect(() => {
        // 1. Clean up previous route objects
        if (routeObjectsRef.current.length > 0) {
            routeObjectsRef.current.forEach(obj => obj.destroy());
            routeObjectsRef.current = [];
        }

        if (mapInstance && response?.route && response.route.length > 1) {
            // Unpack the coordinates from the new response structure
            const routeCoords = response.route.map(point => point.coord);

            // 2. Draw the entire route as a single green line with A/B markers
            load().then(mapglAPI => {
                const newRouteObjects = [];
                
                // Polyline for the whole route
                const polyline = new mapglAPI.Polyline(mapInstance, {
                    coordinates: routeCoords,
                    width: 10,
                    color: '#28a745', // Single green color for the route
                    width2: 14,
                    color2: '#ffffff',
                    zIndex: 1,
                });
                newRouteObjects.push(polyline);

                // Markers for start (A) and end (B)
                const startPoint = routeCoords[0];
                const endPoint = routeCoords[routeCoords.length - 1];

                // Marker A
                const startCircle = new mapglAPI.CircleMarker(mapInstance, {
                    coordinates: startPoint,
                    radius: 16,
                    color: '#0088ff',
                    strokeWidth: 2,
                    strokeColor: '#ffffff',
                    zIndex: 3,
                });
                newRouteObjects.push(startCircle);
                const startLabel = new mapglAPI.Label(mapInstance, {
                    coordinates: startPoint,
                    text: 'A',
                    fontSize: 14,
                    color: '#ffffff',
                    zIndex: 4,
                });
                newRouteObjects.push(startLabel);

                // Marker B
                const endCircle = new mapglAPI.CircleMarker(mapInstance, {
                    coordinates: endPoint,
                    radius: 16,
                    color: '#0088ff',
                    strokeWidth: 2,
                    strokeColor: '#ffffff',
                    zIndex: 3,
                });
                newRouteObjects.push(endCircle);
                const endLabel = new mapglAPI.Label(mapInstance, {
                    coordinates: endPoint,
                    text: 'B',
                    fontSize: 14,
                    color: '#ffffff',
                    zIndex: 4,
                });
                newRouteObjects.push(endLabel);

                routeObjectsRef.current = newRouteObjects;

                // 3. Zoom map to fit the whole route
                const bounds = routeCoords.reduce((bounds, coord) => {
                    return [
                        [Math.min(bounds[0][0], coord[0]), Math.min(bounds[0][1], coord[1])],
                        [Math.max(bounds[1][0], coord[0]), Math.max(bounds[1][1], coord[1])],
                    ];
                }, [[Infinity, Infinity], [-Infinity, -Infinity]]);

                mapInstance.fitBounds(bounds, { padding: [50, 50, 50, 50] });
            });
        }
    }, [mapInstance, response]);


    // --- Audio Recording and Sending Logic ---

    const startRecording = async () => {
        setStatus('Requesting mic access...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
            audioChunksRef.current = [];

            mediaRecorderRef.current.addEventListener('dataavailable', event => {
                audioChunksRef.current.push(event.data);
            });

            mediaRecorderRef.current.addEventListener('stop', () => {
                const blob = new Blob(audioChunksRef.current, { type: mimeType });
                setAudioBlob(blob);
                setStatus(`Recording finished. Ready to send.`);
            });

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setResponse(null);
            setAudioBlob(null);
            setStatus(`Recording...`);
        } catch (err) {
            setStatus(`Error accessing microphone: ${err.message}`);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const sendData = async () => {
        if (!audioBlob) return;

        const formData = new FormData();
        formData.append('audio', audioBlob, 'speech.webm');

        setStatus('Sending to backend...');
        setIsSending(true);
        setResponse(null);

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);

            const data = await res.json();
            setResponse(data);
            setStatus('Success! Received response.');
        } catch (error) {
            setStatus(`Error: ${error.message}`);
            setResponse({ error: 'Could not connect to backend. Is it running?' });
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="container">
            <h1>Voice → Route (React + 2GIS MapGL)</h1>
            <p id="status">{status}</p>
            <div className="buttons">
                <button onClick={startRecording} disabled={isRecording}>Record</button>
                <button onClick={stopRecording} disabled={!isRecording}>Stop</button>
                <button onClick={sendData} disabled={!audioBlob || isSending || isRecording}>
                    {isSending ? 'Sending...' : 'Send to Backend'}
                </button>
            </div>

            <Map />

            {response && (
                <pre id="result">
                    {JSON.stringify(response, null, 2)}
                </pre>
            )}
        </div>
    );
};

// The main App component now just wraps the content with the provider
const App = () => {
    return (
        <MapProvider>
            <AppContent />
        </MapProvider>
    )
}

export default App;
