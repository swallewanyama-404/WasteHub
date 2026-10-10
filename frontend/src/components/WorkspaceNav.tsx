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
  Operations: "⌂",
  Dispatch: "➜",
  Monitoring: "◉",
  Reviews: "✓",
  "Service desk": "☰",
  Team: "●",
  Fleet: "🚛",
  Overview: "◆",
  Users: "●",
  Organizations: "▦",
  Audit: "☷",
};

type NavItem = [string, string];
type NavGroup = { label?: string; items: NavItem[] };

export function WorkspaceNav() {
  const { user } = useAuth();
  if (!user) return null;

  let groups: NavGroup[];

  if (user.role === "resident") {
    groups = [{
      items: [
        ["/resident", "Dashboard"],
        ["/resident/requests", "Requests"],
        ["/resident/tracking", "Tracking"],
        ["/resident/payments", "Payments"],
        ["/resident/profile", "Profile"],
        ["/resident/support", "Support"],
      ],
    }];
  } else if (user.role === "collector") {
    groups = [{
      items: [
        ["/collector", "Dashboard"],
        ["/collector/queue", "Queue"],
        ["/collector/map", "Route map"],
      ],
    }];
  } else if (user.role === "system_admin") {
    groups = [
      {
        label: "System",
        items: [
          ["/admin", "Overview"],
          ["/admin/users", "Users"],
          ["/admin/organizations", "Organizations"],
          ["/admin/audit", "Audit"],
        ],
      },
      {
        label: "Operations",
        items: [
          ["/organization", "Operations"],
          ["/organization/dispatch", "Dispatch"],
          ["/organization/monitoring", "Monitoring"],
          ["/organization/review", "Reviews"],
          ["/organization/service", "Service desk"],
        ],
      },
    ];
  } else if (user.role === "supervisor") {
    groups = [
      {
        label: "Operations",
        items: [
          ["/organization", "Operations"],
          ["/organization/dispatch", "Dispatch"],
          ["/organization/monitoring", "Monitoring"],
          ["/organization/review", "Reviews"],
          ["/organization/service", "Service desk"],
        ],
      },
      {
        label: "Organization",
        items: [
          ["/organization/team", "Team"],
          ["/organization/fleet", "Fleet"],
        ],
      },
    ];
  } else {
    groups = [{
      items: [
        ["/organization", "Operations"],
        ["/organization/dispatch", "Dispatch"],
        ["/organization/monitoring", "Monitoring"],
        ["/organization/review", "Reviews"],
        ["/organization/service", "Service desk"],
      ],
    }];
  }

  const exactRoutes = new Set(["/resident", "/collector", "/organization", "/admin"]);

  return (
    <nav className="workspace-nav" aria-label="Workspace navigation">
      {groups.map((group, groupIndex) => (
        <div className="workspace-nav-group" key={group.label ?? groupIndex}>
          {group.label ? <span className="workspace-nav-label">{group.label}</span> : null}
          {group.items.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={exactRoutes.has(to)}
              className={({ isActive }) => isActive ? "workspace-link active" : "workspace-link"}
            >
              <span className="workspace-icon" aria-hidden="true">{icons[label]}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}
