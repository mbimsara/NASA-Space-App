/**
 * MapPicker — click the map to set the farm location (WGS84).
 * Owner: Shehani. Uses Leaflet + OpenStreetMap tiles; numeric inputs remain
 * the accessible alternative for keyboard and screen-reader users.
 */
import { useEffect } from "react";
import { CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface Props {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lng: number) => void;
  label: string;
}

const round = (n: number) => Math.round(n * 1e5) / 1e5;

function ClickHandler({ onChange }: { onChange: Props["onChange"] }) {
  useMapEvents({
    click(e) {
      onChange(round(e.latlng.lat), round(e.latlng.lng));
    },
  });
  return null;
}

function Recenter({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    if (!map.getBounds().contains([lat, lng])) map.setView([lat, lng]);
  }, [lat, lng, map]);
  return null;
}

export function MapPicker({ latitude, longitude, onChange, label }: Props) {
  const valid = Number.isFinite(latitude) && Number.isFinite(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
  const lat = valid ? latitude : 7.9;
  const lng = valid ? longitude : 80.7;

  return (
    <div role="group" aria-label={label}>
      <MapContainer center={[lat, lng]} zoom={8} className="map-picker" scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {valid && <CircleMarker center={[lat, lng]} radius={9} pathOptions={{ color: "#176b4d", weight: 3, fillColor: "#10b981", fillOpacity: 0.75 }} />}
        <ClickHandler onChange={onChange} />
        <Recenter lat={lat} lng={lng} />
      </MapContainer>
    </div>
  );
}
