import { Route, Routes } from "react-router-dom";
import AppLayout from "@/components/layout/AppLayout";
import ActivityPage from "@/pages/ActivityPage";
import ChatPage from "@/pages/ChatPage";
import DashboardPage from "@/pages/DashboardPage";
import HelpPage from "@/pages/HelpPage";
import LogsPage from "@/pages/LogsPage";
import ProviderPage from "@/pages/ProviderPage";
import ProvidersPage from "@/pages/ProvidersPage";
import SearchPage from "@/pages/SearchPage";
import SettingsPage from "@/pages/SettingsPage";
import SkillsPage from "@/pages/SkillsPage";
import ToolsPage from "@/pages/ToolsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="providers" element={<ProvidersPage />} />
        <Route path="brave" element={<ProviderPage name="brave" />} />
        <Route path="exa" element={<ProviderPage name="exa" />} />
        <Route path="tavily" element={<ProviderPage name="tavily" />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="tools" element={<ToolsPage />} />
        <Route path="skills" element={<SkillsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="*" element={<DashboardPage />} />
      </Route>
    </Routes>
  );
}
