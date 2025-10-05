import React, { createContext, useState } from 'react';

export const MapContext = createContext([{}, () => {}]);

export const MapProvider = (props) => {
    const [mapState, setMapState] = useState({
        mapInstance: undefined,
        mapglAPI: undefined,
    });

    return (
        <MapContext.Provider value={[mapState, setMapState]}>
            {props.children}
        </MapContext.Provider>
    );
};
