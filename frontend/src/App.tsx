import { Link, Route, Routes } from "react-router-dom";
import RankingsPage from "./pages/RankingsPage";
import CompanyDetailPage from "./pages/CompanyDetailPage";
import IcpBuilderPage from "./pages/IcpBuilderPage";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">
          AccountPulse
        </Link>
        <nav>
          <Link to="/">Rankings</Link>
          <Link to="/icp/new">ICP Builder</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<RankingsPage />} />
          <Route path="/companies/:id" element={<CompanyDetailPage />} />
          <Route path="/icp/new" element={<IcpBuilderPage />} />
        </Routes>
      </main>
    </div>
  );
}
