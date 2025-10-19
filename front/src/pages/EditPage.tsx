import CodeEditor from "../components/CodeEditor";
import FileUpload from "../components/FileUpload";
import { useState } from "react";

function App() {
  const [code, setCode] = useState("");

  return (
    <div
      className="bg-neutral-800 min-h-screen m-0 p-0 overflow-hidden"
    >
      <CodeEditor
        code={code}
        setCode={setCode}
        height="80vh"
        width="90vw"
      />
      <FileUpload onCodeLoaded={setCode} />

    </div>
  )
}

export default App
