import React, { useContext, useEffect } from 'react';
import { load } from '@2gis/mapgl';
import MapWrapper from './MapWrapper';
import { MapContext } from './MapContext';

const Map = ({ route }) => {
    const [, setMapInstance] = useContext(MapContext);

    useEffect(() => {
        let map;
        // The component only mounts when route is valid, so we can use it for the initial center.
        const firstPoint = route[0];

        load().then((mapglAPI) => {
            map = new mapglAPI.Map('map-container', {
                center: firstPoint.coord,
                zoom: 14,
                key: 'e50d3992-8076-47d8-bc3c-9add5a142f20', // YOUR_2GIS_API_KEY
            });
            setMapInstance(map);
        });

        return () => {
            if (map) {
                map.destroy();
                setMapInstance(undefined);
            }
        };
    }, [route, setMapInstance]);

    return (
        <div style={{ width: '100%', height: '400px' }}>
            <MapWrapper />
        </div>
    );
};

export default Map;
