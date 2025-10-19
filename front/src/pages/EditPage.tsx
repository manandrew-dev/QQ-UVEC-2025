import { useNavigate } from "react-router-dom";
import CodeEditor from "../components/CodeEditor";
import FileUpload from "../components/FileUpload";
import { useState } from "react";

interface EditPageProps {
  code: string;
  setCode: (value: string) => void;
}

export default function EditPage({ code, setCode }: EditPageProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (!code.trim()) {
      alert("Please enter or upload some code first!");
      return;
    }

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append("code", code);

      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Backend analysis failed");
      }

      const result = await response.json();
      console.log("Analysis result:", result);

      navigate("/metrics", { state: { result } });
    } catch (error) {
      console.error("Error analyzing code:", error);
      alert("An error occurred while analyzing the code.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="bg-neutral-800 min-h-screen flex flex-col items-center m-0 p-0 overflow-hidden text-white">
      <h1 className="text-3xl font-bold text-gray-300 my-6">Editor</h1>

      <div className="w-[90vw] max-w-6xl">
        <CodeEditor code={code} setCode={setCode} height="70vh" width="100%" />
      </div>

      <div className="flex flex-col items-center mt-6 space-y-4">
        <FileUpload onCodeLoaded={setCode} />

        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className={`px-6 py-2 rounded-xl text-lg font-medium transition-transform duration-200 ${
            isAnalyzing
              ? "bg-gray-600 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 hover:scale-105"
          }`}
        >
          {isAnalyzing ? "Analyzing..." : "Analyze Code"}
        </button>
      </div>
    </div>
  );
}
