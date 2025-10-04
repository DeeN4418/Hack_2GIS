import React, { useContext, useEffect } from 'react';
import { load } from '@2gis/mapgl';
import MapWrapper from './MapWrapper';
import { MapContext } from './MapContext';

const Map = () => {
    const [, setMapInstance] = useContext(MapContext);

    useEffect(() => {
        let map;
        load().then((mapglAPI) => {
            map = new mapglAPI.Map('map-container', {
                center: [37.6175, 55.7504], // Moscow center
                zoom: 11,
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
    }, []);

    return (
        <div style={{ width: '100%', height: '400px' }}>
            <MapWrapper />
        </div>
    );
};

export default Map;
