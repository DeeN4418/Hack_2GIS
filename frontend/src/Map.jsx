import React, { useContext, useEffect } from 'react';
import { load } from '@2gis/mapgl';
import MapWrapper from './MapWrapper';
import { MapContext } from './MapContext';

const Map = ({ route }) => {
    const [, setMapState] = useContext(MapContext);

    useEffect(() => {
        let map;
        // The component only mounts when route is valid, so we can use it for the initial center.
        const firstPoint = route[0];

        load().then((mapglAPI) => {
            map = new mapglAPI.Map('map-container', {
                center: firstPoint.coord,
                zoom: 14,
                key: import.meta.env.VITE_2GIS_API_KEY,
            });
            setMapState({ mapInstance: map, mapglAPI: mapglAPI });
        });

        return () => {
            if (map) {
                map.destroy();
                setMapState({ mapInstance: undefined, mapglAPI: undefined });
            }
        };
    }, [route, setMapState]);

    return (
        <div style={{ width: '100%', height: '400px' }}>
            <MapWrapper />
        </div>
    );
};

export default Map;
