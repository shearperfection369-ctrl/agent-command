import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Landing from "@/pages/Landing";
import AgentDemo from "@/pages/AgentDemo";
import BusinessPlan from "@/pages/BusinessPlan";
import LaunchKit from "@/pages/LaunchKit";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import PitchDeck from "@/pages/PitchDeck";
import DemoReel from "@/pages/DemoReel";
import { CaseStudiesIndex, CaseStudyDetail } from "@/pages/CaseStudies";
import Billing from "@/pages/Billing";
import BillingSuccess from "@/pages/BillingSuccess";
import Portal from "@/pages/Portal";
import Lighthouse from "@/pages/Lighthouse";
import Logistics from "@/pages/Logistics";
import PlaybookBuilder from "@/pages/PlaybookBuilder";
import EmbedReel from "@/pages/EmbedReel";
import PressKit from "@/pages/PressKit";
import ClientLogin from "@/pages/ClientLogin";
import ClientDashboard from "@/pages/ClientDashboard";
import { MoodPicker } from "@/components/MoodPicker";
import LlmHealthBanner from "@/components/LlmHealthBanner";
import { initSentry } from "@/lib/sentry";

// Fire-and-forget Sentry init. No-op if REACT_APP_SENTRY_DSN is unset.
initSentry();

function Chrome({ children }) {
  const { pathname } = useLocation();
  const bare = pathname.startsWith("/embed/");
  return (
    <>
      {!bare && <LlmHealthBanner />}
      {!bare && <Nav />}
      {children}
      {!bare && <Footer />}
      {!bare && <MoodPicker />}
    </>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Toaster
          position="top-right"
          theme="dark"
          toastOptions={{
            style: {
              background: "#0a0c18",
              border: "1px solid #ccff00",
              color: "#fff",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "12px",
              letterSpacing: "0.05em",
            },
          }}
        />
        <Chrome>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/demo" element={<AgentDemo />} />
            <Route path="/reel" element={<DemoReel />} />
            <Route path="/deck" element={<PitchDeck />} />
            <Route path="/plan" element={<BusinessPlan />} />
            <Route path="/launch" element={<LaunchKit />} />
            <Route path="/cases" element={<CaseStudiesIndex />} />
            <Route path="/cases/:slug" element={<CaseStudyDetail />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/billing/success" element={<BillingSuccess />} />
            <Route path="/portal" element={<Portal />} />
            <Route path="/lighthouse" element={<Lighthouse />} />
            <Route path="/logistics" element={<Logistics />} />
            <Route path="/playbooks/new" element={<PlaybookBuilder />} />
            <Route path="/embed/reel" element={<EmbedReel />} />
            <Route path="/press" element={<PressKit />} />
            <Route path="/login" element={<Login />} />
            <Route path="/admin" element={<Dashboard />} />
            <Route path="/client/login" element={<ClientLogin />} />
            <Route path="/client/verify" element={<ClientLogin />} />
            <Route path="/client/dashboard" element={<ClientDashboard />} />
          </Routes>
        </Chrome>
      </BrowserRouter>
    </div>
  );
}

export default App;
