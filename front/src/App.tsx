import { Routes, Route } from "react-router-dom";
import WelcomePage from "./pages/WelcomePage";
import EditPage from "./pages/EditPage";
import MetricsPage from "./pages/MetricsPage"
import { useState } from "react";

export default function App() {
  const [code, setCode] = useState("");
  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="/editor" element={<EditPage code={code} setCode={setCode}/>} />
      <Route path="/metrics" element={<MetricsPage code={code} />} />
    </Routes>
  );
}
