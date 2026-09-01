import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Holdings from "./pages/Holdings";
import Analyze from "./pages/Analyze";

export default function App() {
  return (
    <div className="app-shell">
      <nav className="nav">
        <span className="nav-brand">📈 PortfolioPilot</span>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/holdings" className={({ isActive }) => (isActive ? "active" : "")}>
          Holdings
        </NavLink>
        <NavLink to="/analyze" className={({ isActive }) => (isActive ? "active" : "")}>
          Analyze
        </NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/holdings" element={<Holdings />} />
        <Route path="/analyze" element={<Analyze />} />
      </Routes>
    </div>
  );
}
