import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { WasteHubLogo } from "./WasteHubLogo";
import { WorkspaceNav } from "./WorkspaceNav";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  const home =
    user?.role === "resident"
      ? "/resident"
      : user?.role === "collector"
        ? "/collector"
        : "/organization";

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <WasteHubLogo to={home} />
        <WorkspaceNav />
        <div className="sidebar-message">
          <span>♻</span>
          <strong>Cleaner communities</strong>
          <p>Smarter collection, clearer service.</p>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-context">
            <span className="role-chip">{user?.role.replaceAll("_", " ")}</span>
          </div>
          <div className="topbar-user">
            <div className="avatar">{user?.full_name?.slice(0, 1).toUpperCase()}</div>
            <div>
              <strong>{user?.full_name}</strong>
              <span>{user?.email}</span>
            </div>
            <button className="button ghost compact-button" onClick={logout}>Sign out</button>
          </div>
        </header>

        <main className="page-shell">{children}</main>
      </div>
    </div>
  );
}
