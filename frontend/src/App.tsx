import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import AnalysisResultsPage from "@/pages/AnalysisResultsPage";
import DashboardPage from "@/pages/DashboardPage";
import HistoryPage from "@/pages/HistoryPage";
import LandingPage from "@/pages/LandingPage";
import { LoginPage, RegisterPage } from "@/pages/AuthPages";
import NewAnalysisPage from "@/pages/NewAnalysisPage";
import NlpLabPage from "@/pages/NlpLabPage";
import NotFoundPage from "@/pages/NotFoundPage";
import RoadmapPage from "@/pages/RoadmapPage";
import SettingsPage from "@/pages/SettingsPage";
import SkillExplorerPage from "@/pages/SkillExplorerPage";
import { useAuth } from "@/store/auth";

export default function App() {
  const restore = useAuth((s) => s.restore);
  useEffect(() => {
    void restore();
  }, [restore]);

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analyses/new" element={<NewAnalysisPage />} />
          <Route path="/analyses/:id" element={<AnalysisResultsPage />} />
          <Route path="/analyses/:id/skills" element={<SkillExplorerPage />} />
          <Route path="/analyses/:id/roadmap" element={<RoadmapPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/lab" element={<NlpLabPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/roadmap" element={<Navigate to="/history" replace />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
