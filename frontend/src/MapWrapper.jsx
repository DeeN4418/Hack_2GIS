import React, { memo } from 'react';

const MapWrapper = memo(() => {
    return <div id="map-container" style={{ width: '100%', height: '100%' }}></div>;
}, () => true);

export default MapWrapper;
