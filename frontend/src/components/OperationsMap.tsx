import { useEffect, useMemo, useState } from "react";
import { divIcon } from "leaflet";
import {
  MapContainer,
  Marker,
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
  legendMode?: "operations" | "resident";
}

type LatLngTuple = [number, number];

function markerIcon(kind: "truck" | "home", state = "upcoming") {
  const label = kind === "truck" ? "🚛" : "⌂";
  return divIcon({
    className: "wastehub-div-icon",
    html: `<div class="map-marker ${kind} ${state}"><span>${label}</span></div>`,
    iconSize: [38, 44],
    iconAnchor: [19, 40],
    popupAnchor: [0, -38],
  });
}

export function OperationsMap({
  stops = [],
  truck = null,
  pickup = null,
  legendMode = "operations",
}: OperationsMapProps) {
  const [roadRoute, setRoadRoute] = useState<LatLngTuple[]>([]);

  const stopPoints = useMemo(
    () =>
      stops
        .filter((stop) => stop.pickup_latitude !== null && stop.pickup_longitude !== null)
        .map((stop) => ({
          latitude: stop.pickup_latitude as number,
          longitude: stop.pickup_longitude as number,
          stop,
        })),
    [stops],
  );

  const fallback = { latitude: 0.3476, longitude: 32.5825 };
  const center =
    truck ??
    pickup ??
    (stopPoints.length
      ? { latitude: stopPoints[0].latitude, longitude: stopPoints[0].longitude }
      : fallback);

  const routeWaypoints = useMemo(() => {
    const points: { latitude: number; longitude: number }[] = [];
    if (truck) points.push(truck);

    if (stopPoints.length) {
      const activeStops = stopPoints.filter(
        ({ stop }) =>
          !["completed", "missed", "rejected", "cancelled"].includes(stop.map_state),
      );
      points.push(
        ...(activeStops.length ? activeStops : stopPoints).map((point) => ({
          latitude: point.latitude,
          longitude: point.longitude,
        })),
      );
    } else if (pickup) {
      points.push(pickup);
    }

    return points;
  }, [truck, pickup, stopPoints]);

  useEffect(() => {
    if (routeWaypoints.length < 2) {
      setRoadRoute([]);
      return;
    }

    const controller = new AbortController();
    const coordinates = routeWaypoints
      .map((point) => `${point.longitude},${point.latitude}`)
      .join(";");

    fetch(
      `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson&steps=false`,
      { signal: controller.signal },
    )
      .then((response) => {
        if (!response.ok) throw new Error("Routing service unavailable");
        return response.json();
      })
      .then((data) => {
        const coordinatesList = data?.routes?.[0]?.geometry?.coordinates;
        if (!Array.isArray(coordinatesList)) throw new Error("No road route");
        setRoadRoute(
          coordinatesList.map(([longitude, latitude]: [number, number]) => [
            latitude,
            longitude,
          ]),
        );
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setRoadRoute(
            routeWaypoints.map((point) => [point.latitude, point.longitude]),
          );
        }
      });

    return () => controller.abort();
  }, [routeWaypoints]);

  function stateForStop(stop: CollectorMapStop) {
    if (stop.map_state === "completed") return "completed";
    if (stop.map_state === "missed") return "missed";
    if (stop.is_next_stop) return "next";
    if (stop.map_state === "rejected" || stop.map_state === "cancelled") return "closed";
    return "upcoming";
  }

  return (
    <div className="map-frame" aria-label="WasteHub operations map">
      <MapContainer
        center={[center.latitude, center.longitude]}
        zoom={14}
        scrollWheelZoom
        className="leaflet-map"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {roadRoute.length > 1 ? (
          <Polyline
            positions={roadRoute}
            pathOptions={{ color: "#12823b", weight: 5, opacity: 0.88 }}
          />
        ) : null}

        {stopPoints.map(({ latitude, longitude, stop }) => {
          const state = stateForStop(stop);
          return (
            <Marker
              key={stop.assignment_id}
              position={[latitude, longitude]}
              icon={markerIcon("home", state)}
            >
              <Popup>
                <strong>{stop.pickup_address}</strong>
                <br />
                Assignment #{stop.assignment_id}
                <br />
                {state === "next" ? "Next collection stop" : stop.assignment_status}
              </Popup>
            </Marker>
          );
        })}

        {pickup ? (
          <Marker
            position={[pickup.latitude, pickup.longitude]}
            icon={markerIcon("home", "resident")}
          >
            <Popup>{pickup.label ?? "Your pickup location"}</Popup>
          </Marker>
        ) : null}

        {truck ? (
          <Marker
            position={[truck.latitude, truck.longitude]}
            icon={markerIcon("truck", "live")}
          >
            <Popup>{truck.label ?? "Collection vehicle"}</Popup>
          </Marker>
        ) : null}
      </MapContainer>

      <div className="map-legend" aria-label="Map legend">
        {legendMode === "resident" ? (
          <>
            <span><i className="legend-truck">🚛</i> Collection truck</span>
            <span><i className="legend-route" /> Truck route</span>
          </>
        ) : (
          <>
            <span><i className="legend-home completed">⌂</i> Completed</span>
            <span><i className="legend-home next">⌂</i> Next stop</span>
            <span><i className="legend-home upcoming">⌂</i> Upcoming</span>
            <span><i className="legend-home missed">⌂</i> Missed</span>
            <span><i className="legend-route" /> Truck route</span>
          </>
        )}
      </div>
    </div>
  );
}
