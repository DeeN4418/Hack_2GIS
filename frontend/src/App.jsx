import React, { useState, useEffect, useRef, useContext } from 'react';
import '@2gis/mapgl-directions';
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
    
    const [mapState] = useContext(MapContext);
    const { mapInstance, mapglAPI } = mapState;
    const directionsRef = useRef(null);
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
            const preferredMimeTypes = [
                'audio/wav',
                'audio/mpeg', // .mp3
                'audio/ogg',
                'audio/flac',
                'audio/mp4', // .m4a
                'audio/aac',
                'audio/webm;codecs=opus', // Fallback
                'audio/webm', // Fallback
            ];

            const mimeType = preferredMimeTypes.find(type => MediaRecorder.isTypeSupported(type));

            if (!mimeType) {
                setStatus('Ни один из аудиоформатов не поддерживается для записи.');
                setRecordingState('idle');
                return;
            }

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
        const mimeType = mediaRecorderRef.current.mimeType;
        let extension = mimeType.split('/')[1].split(';')[0];
        if (extension === 'mpeg') extension = 'mp3';
        if (extension === 'mp4' || extension === 'x-m4a') extension = 'm4a';
        formData.append('audio', audioBlob, `speech.${extension}`);
        
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

    useEffect(() => {
        if (mapInstance && mapglAPI && !directionsRef.current) {
            directionsRef.current = new mapglAPI.Directions(mapInstance, {
                directionsApiKey: import.meta.env.VITE_2GIS_API_KEY,
            });
        }
    }, [mapInstance, mapglAPI]);

    useEffect(() => {
        // Clear previous routes from both systems
        if (directionsRef.current) {
            directionsRef.current.clear();
        }
        if (routeObjectsRef.current.length > 0) {
            routeObjectsRef.current.forEach(obj => obj.destroy());
            routeObjectsRef.current = [];
        }

        if (mapInstance && response?.route && response.route.length > 1) {
            if (response.route_type === 'pedestrian' && directionsRef.current) {
                const routeCoords = response.pivot_route_points.map(point => point.coord);
                directionsRef.current.pedestrianRoute({
                    points: routeCoords,
                    style: {
                        routeLineWidth: 5,
                    }
                });
            } else if (mapglAPI) { // Handle segmented route
                const segments = response.route;
                const newRouteObjects = [];
                segments.forEach((segment, i) => {
                    const zIndex = segments.length - 1 - i;
                    const polyline = new mapglAPI.Polyline(mapInstance, {
                        coordinates: segment.coords,
                        width: 5,
                        color: segment.color,
                        width2: 9,
                        color2: '#ffffff',
                        zIndex,
                    });
                    newRouteObjects.push(polyline);

                    if (segment.label) {
                        const isFirstPoint = i === 0;
                        const lastPointIndex = segment.coords.length - 1;
                        const coords = isFirstPoint ? segment.coords[0] : segment.coords[lastPointIndex];

                        const circle = new mapglAPI.CircleMarker(mapInstance, {
                            coordinates: coords,
                            radius: 16,
                            color: '#0088ff',
                            strokeWidth: 2,
                            strokeColor: '#ffffff',
                            zIndex: isFirstPoint ? 5 : 3,
                        });
                        newRouteObjects.push(circle);

                        const label = new mapglAPI.Label(mapInstance, {
                            coordinates: coords,
                            text: segment.label,
                            fontSize: 14,
                            color: '#ffffff',
                            zIndex: isFirstPoint ? 6 : 4,
                        });
                        newRouteObjects.push(label);
                    }
                });
                routeObjectsRef.current = newRouteObjects;
            }
        }
    }, [mapInstance, mapglAPI, response]);

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
                
                {response?.route && <Map route={response.route} />}
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
