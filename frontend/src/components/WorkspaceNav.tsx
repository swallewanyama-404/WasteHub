import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const icons: Record<string, string> = {
  Dashboard: "⌂",
  Requests: "⚡",
  Tracking: "⌖",
  Payments: "▣",
  Profile: "●",
  Support: "?",
  Queue: "☷",
  "Route map": "⌖",
  Dispatch: "➜",
  Monitoring: "◉",
  "Service desk": "☰",
};

export function WorkspaceNav() {
  const { user } = useAuth();
  if (!user) return null;

  const links =
    user.role === "resident"
      ? [
          ["/resident", "Dashboard"],
          ["/resident/requests", "Requests"],
          ["/resident/tracking", "Tracking"],
          ["/resident/payments", "Payments"],
          ["/resident/profile", "Profile"],
          ["/resident/support", "Support"],
        ]
      : user.role === "collector"
        ? [["/collector", "Queue"], ["/collector/map", "Route map"]]
        : [
            ["/organization", "Dashboard"],
            ["/organization/dispatch", "Dispatch"],
            ["/organization/monitoring", "Monitoring"],
            ["/organization/service", "Service desk"],
          ];

  return (
    <nav className="workspace-nav" aria-label="Workspace navigation">
      {links.map(([to, label]) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/resident" || to === "/collector" || to === "/organization"}
          className={({ isActive }) => isActive ? "workspace-link active" : "workspace-link"}
        >
          <span className="workspace-icon" aria-hidden="true">{icons[label]}</span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
