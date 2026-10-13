import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Crosshair, Layers, HelpCircle, RotateCcw } from 'lucide-react';

// Fix default Leaflet icon paths in Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface RegionMapProps {
  latitude: number;
  longitude: number;
  onSelectCoordinates: (lat: number, lon: number) => void;
  regionName?: string;
}

export const RegionMap: React.FC<RegionMapProps> = ({
  latitude,
  longitude,
  onSelectCoordinates,
  regionName,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const bboxRectRef = useRef<L.Rectangle | null>(null);
  const [showBbox, setShowBbox] = useState<boolean>(true);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [latitude, longitude],
      zoom: 4,
      zoomControl: true,
      attributionControl: false,
    });

    // Darker / Clean CartoDB Voyager or OSM tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 18,
      subdomains: 'abcd',
    }).addTo(map);

    // Click handler to select new coordinates
    map.on('click', (e: L.LeafletMouseEvent) => {
      const lat = parseFloat(e.latlng.lat.toFixed(4));
      const lon = parseFloat(e.latlng.lng.toFixed(4));
      onSelectCoordinates(lat, lon);
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update marker and bounding box when coordinates change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Pan smoothly
    map.setView([latitude, longitude], map.getZoom() < 3 ? 4 : map.getZoom(), {
      animate: true,
    });

    // Marker
    if (markerRef.current) {
      markerRef.current.setLatLng([latitude, longitude]);
    } else {
      const marker = L.marker([latitude, longitude], {
        title: regionName || 'Selected Location',
      }).addTo(map);
      markerRef.current = marker;
    }

    // Bounding Box (ERA5 ~0.25° representative cell: ±0.15°)
    const bounds: L.LatLngBoundsExpression = [
      [latitude - 0.15, longitude - 0.15],
      [latitude + 0.15, longitude + 0.15],
    ];

    if (bboxRectRef.current) {
      bboxRectRef.current.setBounds(bounds);
    } else {
      const rect = L.rectangle(bounds, {
        color: '#f59e0b',
        weight: 1.5,
        fillColor: '#f59e0b',
        fillOpacity: 0.12,
        dashArray: '4, 4',
      }).addTo(map);
      bboxRectRef.current = rect;
    }

    if (bboxRectRef.current) {
      if (showBbox) {
        bboxRectRef.current.setStyle({ opacity: 1, fillOpacity: 0.12 });
      } else {
        bboxRectRef.current.setStyle({ opacity: 0, fillOpacity: 0 });
      }
    }
  }, [latitude, longitude, showBbox, regionName]);

  const handleResetView = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([latitude, longitude], 5, { animate: true });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden flex flex-col">
      {/* Map Header Toolbar */}
      <div className="px-4 py-2.5 bg-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-semibold text-white">Geographic Target Stage</span>
          <span className="font-mono text-slate-400">
            [{latitude > 0 ? `${latitude}°N` : `${Math.abs(latitude)}°S`},{' '}
            {longitude > 0 ? `${longitude}°E` : `${Math.abs(longitude)}°W`}]
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowBbox(!showBbox)}
            className={`px-2 py-1 rounded text-[11px] font-mono border transition-colors flex items-center gap-1 ${
              showBbox
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                : 'bg-slate-900 border-slate-700 text-slate-400'
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>ERA5 Grid Cell (0.25°)</span>
          </button>

          <button
            type="button"
            onClick={handleResetView}
            title="Center map on selected location"
            className="p-1 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-white transition-colors"
          >
            <Crosshair className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Map Container Stage */}
      <div className="relative w-full h-56 sm:h-64 md:h-72 bg-slate-950">
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Floating guidance overlay */}
        <div className="absolute bottom-2 left-2 z-10 pointer-events-none bg-slate-950/85 backdrop-blur-xs border border-slate-800 px-2.5 py-1.5 rounded text-[10px] font-mono text-slate-300">
          <span>Click anywhere on the map to set analysis coordinates</span>
        </div>
      </div>

      {/* Spatial Coverage Note */}
      <div className="px-4 py-2 bg-slate-950/60 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <span>Point observations extracted from Open-Meteo ERA5 reanalysis grid (~28 km resolution).</span>
        </div>
        <span className="font-mono text-slate-500 hidden sm:inline">Leaflet · OpenStreetMap / CartoDB</span>
      </div>
    </div>
  );
};
