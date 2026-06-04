import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Nav />
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
          <Route path="/login" element={<Login />} />
          <Route path="/admin" element={<Dashboard />} />
        </Routes>
        <Footer />
      </BrowserRouter>
    </div>
  );
}

export default App;
