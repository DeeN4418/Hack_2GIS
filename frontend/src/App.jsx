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
    const [isTouristMode, setIsTouristMode] = useState(false);
    
    const [mapState] = useContext(MapContext);
    const { mapInstance, mapglAPI } = mapState;
    const directionsRef = useRef(null);

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
        
        const endpoint = isTouristMode ? '/stt-route-tourist' : '/stt-route';

        try {
            const res = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData });
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
        if (directionsRef.current) {
            directionsRef.current.clear();
        }

        if (mapInstance && response?.pivot_route_points && response.pivot_route_points.length > 1 && directionsRef.current) {
            const routeCoords = response.pivot_route_points.map(point => point.coord);
            const style = { routeLineWidth: 5 };

            if (response.route_type === 'pedestrian') {
                directionsRef.current.pedestrianRoute({
                    points: routeCoords,
                    style: style,
                });
            } else { // Handle other route types as car route
                directionsRef.current.carRoute({
                    points: routeCoords,
                    style: style,
                });
            }
        }
    }, [mapInstance, response]);

    return (
        <div className="container">
            <div className="tourist-mode-toggle">
                <label>
                    <input 
                        type="checkbox" 
                        checked={isTouristMode} 
                        onChange={() => setIsTouristMode(!isTouristMode)} 
                    />
                    Tourist Mode
                </label>
            </div>
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
