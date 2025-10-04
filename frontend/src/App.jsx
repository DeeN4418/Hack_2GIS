import React, { useState, useEffect, useRef, useContext } from 'react';
import { load } from '@2gis/mapgl';
import Map from './Map';
import { MapContext, MapProvider } from './MapContext';

// SVG Icons for the button
const MicIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="48px" height="48px">
        <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.49 6-3.31 6-6.72h-1.7z"/>
    </svg>
);

const StopIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="48px" height="48px">
        <path d="M6 6h12v12H6z"/>
    </svg>
);


const AppContent = () => {
    const [status, setStatus] = useState('Нажмите на микрофон для записи');
    const [recordingState, setRecordingState] = useState('idle'); // idle, recording, sending
    const [response, setResponse] = useState(null);
    
    const [mapInstance] = useContext(MapContext);
    const routeObjectsRef = useRef([]);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const API_URL = 'http://localhost:8000/api';

    // Get and send user's location on initial load
    useEffect(() => {
        if ("geolocation" in navigator) {
            setStatus("Запрашиваем геолокацию...");
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    sendLocationToBackend({ lat: latitude, lon: longitude });
                },
                (error) => {
                    console.error("Geolocation error:", error);
                    setStatus("Не удалось определить геолокацию.");
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000, // 5 seconds
                    maximumAge: 0
                }
            );
        } else {
            setStatus("Геолокация не поддерживается вашим браузером.");
        }
    }, []); // Empty array ensures this runs only once on mount

    const sendLocationToBackend = async (location) => {
        try {
            await fetch(`${API_URL}/user-location`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(location),
            });
            setStatus('Геолокация сохранена. Нажмите для записи.');
        } catch (error) {
            console.error('Failed to send location:', error);
            setStatus('Ошибка при отправке геолокации.');
        }
    };

    // Main recording flow logic
    const handleRecordClick = () => {
        if (recordingState === 'idle') {
            startRecording();
        } else if (recordingState === 'recording') {
            stopRecordingAndSend();
        }
    };
    
    const startRecording = async () => {
        setResponse(null);
        setStatus('Запрос доступа к микрофону...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus' : 'audio/webm';
            
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
            audioChunksRef.current = [];

            mediaRecorderRef.current.addEventListener('dataavailable', event => {
                audioChunksRef.current.push(event.data);
            });

            mediaRecorderRef.current.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
                await sendData(audioBlob);
            });

            mediaRecorderRef.current.start();
            setRecordingState('recording');
            setStatus('Идёт запись...');
        } catch (err) {
            setStatus(`Ошибка доступа к микрофону: ${err.message}`);
            setRecordingState('idle');
        }
    };

    const stopRecordingAndSend = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            setRecordingState('sending');
            setStatus('Обработка и отправка...');
        }
    };

    const sendData = async (audioBlob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'speech.webm');
        
        try {
            const res = await fetch(`${API_URL}/stt-route`, { method: 'POST', body: formData });
            if (!res.ok) throw new Error(`Ошибка сети: ${res.status}`);
            
            const data = await res.json();
            setResponse(data);
            setStatus('Маршрут построен!');
        } catch (error) {
            setStatus(`Ошибка: ${error.message}`);
            setResponse({ error: 'Не удалось построить маршрут.' });
        } finally {
            setRecordingState('idle');
        }
    };

    // Effect to draw the route on the map
    useEffect(() => {
        if (routeObjectsRef.current.length > 0) {
            routeObjectsRef.current.forEach(obj => obj.destroy());
            routeObjectsRef.current = [];
        }

        if (mapInstance && response?.route && response.route.length > 1) {
            const routeCoords = response.route.map(point => point.coord);
            load().then(mapglAPI => {
                const newRouteObjects = [];
                const polyline = new mapglAPI.Polyline(mapInstance, {
                    coordinates: routeCoords,
                    width: 10, color: '#28a745', width2: 14, color2: '#ffffff', zIndex: 1,
                });
                newRouteObjects.push(polyline);
                
                const startPoint = routeCoords[0];
                const endPoint = routeCoords[routeCoords.length - 1];
                
                // Markers A & B
                [startPoint, endPoint].forEach((point, index) => {
                    const circle = new mapglAPI.CircleMarker(mapInstance, {
                        coordinates: point, radius: 16, color: '#0088ff', strokeWidth: 2, strokeColor: '#ffffff', zIndex: 3,
                    });
                    newRouteObjects.push(circle);
                    const label = new mapglAPI.Label(mapInstance, {
                        coordinates: point, text: index === 0 ? 'A' : 'B', fontSize: 14, color: '#ffffff', zIndex: 4,
                    });
                    newRouteObjects.push(label);
                });
                
                routeObjectsRef.current = newRouteObjects;
                const bounds = routeCoords.reduce((b, coord) => [
                    [Math.min(b[0][0], coord[0]), Math.min(b[0][1], coord[1])],
                    [Math.max(b[1][0], coord[0]), Math.max(b[1][1], coord[1])],
                ], [[Infinity, Infinity], [-Infinity, -Infinity]]);
                mapInstance.fitBounds(bounds, { padding: [50, 50, 50, 50] });
            });
        }
    }, [mapInstance, response]);

    return (
        <div className="container">
            <div className="main-content">
                <h1>{recordingState === 'recording' ? 'Говорите...' : 'Нажмите для начала'}</h1>
                <button
                    className={`mic-button ${recordingState === 'recording' ? 'recording' : ''}`}
                    onClick={handleRecordClick}
                    disabled={recordingState === 'sending'}
                >
                    {recordingState === 'recording' ? <StopIcon /> : <MicIcon />}
                </button>
                <p id="status">{status}</p>
            </div>

            <div className="result-container">
                {response?.transcript && (
                    <pre id="result">
                        <strong>Распознано:</strong> {response.transcript}
                    </pre>
                )}
                
                {response?.route && <Map />}
            </div>
        </div>
    );
};

const App = () => (
    <MapProvider>
        <AppContent />
    </MapProvider>
);

export default App;
