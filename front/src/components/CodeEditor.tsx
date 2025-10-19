import { useState } from "react";
import Editor from "@monaco-editor/react";

export default function CodeEditor({ code, setCode, height = "50vh", width = "80%"}) {
  return (
    <Editor
      height={height}
      width={width}
      theme="vs-dark"
      defaultLanguage="python"
      value={code}
      onChange={(value) => setCode(value || "")}
      options={{
          minimap: { enabled: false },
          fontSize: 16,
          automaticLayout: true,
      }}
    />
  );
}
