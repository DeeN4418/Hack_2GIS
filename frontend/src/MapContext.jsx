import React, { createContext, useState } from 'react';

export const MapContext = createContext([undefined, () => {}]);

export const MapProvider = (props) => {
    const [mapInstance, setMapInstance] = useState();

    return (
        <MapContext.Provider value={[mapInstance, setMapInstance]}>
            {props.children}
        </MapContext.Provider>
    );
};
