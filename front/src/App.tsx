import { Routes, Route } from "react-router-dom";
import WelcomePage from "./pages/WelcomePage";
import EditPage from "./pages/EditPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="/editor" element={<EditPage />} />
    </Routes>
  );
}
