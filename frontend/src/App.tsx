import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { HomePage } from './pages/HomePage';
import { PanelSetupPage } from './pages/PanelSetupPage';
import { StudioPage } from './pages/StudioPage';
import { ReportPage } from './pages/ReportPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastContainer } from './components/ui/Toast';

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="create/:discussionId/panel" element={<PanelSetupPage />} />
            <Route path="studio/:discussionId" element={<StudioPage />} />
            <Route path="report/:discussionId" element={<ReportPage />} />
          </Route>
        </Routes>
        <ToastContainer />
      </ErrorBoundary>
    </BrowserRouter>
  );
}
