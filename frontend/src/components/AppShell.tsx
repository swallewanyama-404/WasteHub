import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
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
      <header className="topbar">
        <div>
          <NavLink to={home} className="brand" aria-label="WasteHub home">
            WasteHub
          </NavLink>
          <span className="role-chip">{user?.role.replaceAll("_", " ")}</span>
        </div>
        <div className="topbar-user">
          <span>{user?.full_name}</span>
          <button className="button secondary" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <WorkspaceNav />
      <main className="page-shell">{children}</main>
    </div>
  );
}
