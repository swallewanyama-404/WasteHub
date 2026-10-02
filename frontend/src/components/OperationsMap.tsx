import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
} from "react-leaflet";
import type { CollectorMapStop } from "../types";
import "leaflet/dist/leaflet.css";

interface OperationsMapProps {
  stops?: CollectorMapStop[];
  truck?: { latitude: number; longitude: number; label?: string } | null;
  pickup?: { latitude: number; longitude: number; label?: string } | null;
}

export function OperationsMap({
  stops = [],
  truck = null,
  pickup = null,
}: OperationsMapProps) {
  const stopPoints = stops
    .filter(
      (stop) =>
        stop.pickup_latitude !== null && stop.pickup_longitude !== null,
    )
    .map((stop) => ({
      latitude: stop.pickup_latitude as number,
      longitude: stop.pickup_longitude as number,
      stop,
    }));

  const fallback = {
    latitude: 0.3476,
    longitude: 32.5825,
  };

  const center =
    truck ??
    pickup ??
    (stopPoints.length
      ? {
          latitude: stopPoints[0].latitude,
          longitude: stopPoints[0].longitude,
        }
      : fallback);

  const linePoints: [number, number][] = stopPoints.map((point) => [
    point.latitude,
    point.longitude,
  ]);

  if (truck) {
    linePoints.unshift([truck.latitude, truck.longitude]);
  }

  return (
    <div className="map-frame" aria-label="WasteHub operations map">
      <MapContainer
        center={[center.latitude, center.longitude]}
        zoom={13}
        scrollWheelZoom
        className="leaflet-map"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {linePoints.length > 1 ? <Polyline positions={linePoints} /> : null}

        {stopPoints.map(({ latitude, longitude, stop }) => (
          <CircleMarker
            key={stop.assignment_id}
            center={[latitude, longitude]}
            radius={stop.is_next_stop ? 10 : 7}
            pathOptions={{
              color:
                stop.map_state === "completed"
                  ? "#0f766e"
                  : stop.map_state === "missed"
                    ? "#b45309"
                    : stop.map_state === "rejected" ||
                        stop.map_state === "cancelled"
                      ? "#6b7280"
                      : "#dc2626",
            }}
          >
            <Popup>
              <strong>{stop.pickup_address}</strong>
              <br />
              Assignment #{stop.assignment_id}
              <br />
              {stop.assignment_status}
            </Popup>
          </CircleMarker>
        ))}

        {pickup ? (
          <CircleMarker
            center={[pickup.latitude, pickup.longitude]}
            radius={9}
            pathOptions={{ color: "#7c3aed" }}
          >
            <Popup>{pickup.label ?? "Pickup location"}</Popup>
          </CircleMarker>
        ) : null}

        {truck ? (
          <CircleMarker
            center={[truck.latitude, truck.longitude]}
            radius={11}
            pathOptions={{ color: "#2563eb" }}
          >
            <Popup>{truck.label ?? "Collection vehicle"}</Popup>
          </CircleMarker>
        ) : null}
      </MapContainer>
    </div>
  );
}
