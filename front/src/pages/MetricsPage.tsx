import { useLocation } from "react-router-dom";
import CodeEditor from "../components/CodeEditor";

interface Metrics {
  total_functions: number;
  total_classes: number;
  total_lines: number;
  sloc: number;
  average_complexity: number;
  max_complexity: number;
  maintainability: number;
  cohesion: number;
  suggestions?: {
    issue: string;
    severity: string;
    action: string;
    steps: string[];
    estimated_impact: string;
  }[];
}

interface MetricsPageProps {
  code: string;
}

function MetricsPage({ code }: MetricsPageProps) {
  const location = useLocation();
  const result = location.state?.result as Metrics | undefined;

  if (!result) {
    return (
      <div className="bg-neutral-900 text-white min-h-screen flex items-center justify-center">
        <p className="text-gray-400">No metrics data found. Please analyze your code first.</p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 text-white min-h-screen flex flex-col items-center px-8 py-12 space-y-8">
      <div className="text-center">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 animate-rgb mb-4">
          Code Analysis Report
        </h1>
        <p className="text-gray-400">Insights into your project’s modularity, complexity, and maintainability</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full max-w-5xl">
        <MetricCard label="Functions" value={result.total_functions} />
        <MetricCard label="Classes" value={result.total_classes} />
        <MetricCard label="Avg. Complexity" value={result.average_complexity.toFixed(2)} />
        <MetricCard label="Maintainability" value={result.maintainability.toFixed(2)} />
        <MetricCard label="Max Complexity" value={result.max_complexity} />
        <MetricCard label="Lines of Code" value={result.sloc} />
        <MetricCard label="Cohesion" value={result.cohesion.toFixed(2)} />
      </div>

      <div className="w-full max-w-6xl">
        <h2 className="text-2xl font-semibold mb-4 text-center">Your Code</h2>
        <CodeEditor
          code={code}
          setCode={() => {}}
          height="50vh"
          width="100%"
          options={{ readOnly: true }}
        />
      </div>

      {result.suggestions && result.suggestions.length > 0 && (
        <div className="w-full max-w-5xl mt-8">
          <h2 className="text-2xl font-semibold mb-4 text-center">Refactor Suggestions</h2>
          <div className="space-y-4">
            {result.suggestions.map((sug, i) => (
              <div
                key={i}
                className={`p-5 rounded-xl border ${
                  sug.severity === "High"
                    ? "border-red-500/50 bg-red-900/20"
                    : sug.severity === "Medium"
                    ? "border-yellow-500/50 bg-yellow-900/20"
                    : "border-green-500/50 bg-green-900/20"
                }`}
              >
                <h3 className="text-xl font-semibold mb-2">
                  {sug.issue}{" "}
                  <span
                    className={`ml-2 text-sm px-2 py-1 rounded ${
                      sug.severity === "High"
                        ? "bg-red-600"
                        : sug.severity === "Medium"
                        ? "bg-yellow-600"
                        : "bg-green-600"
                    }`}
                  >
                    {sug.severity}
                  </span>
                </h3>
                <p className="text-gray-300 mb-2 italic">{sug.action}</p>
                {sug.steps && (
                  <ul className="list-disc list-inside text-gray-400 text-sm space-y-1">
                    {sug.steps.map((step, j) => (
                      <li key={j}>{step}</li>
                    ))}
                  </ul>
                )}
                {sug.estimated_impact && (
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="font-semibold">Impact:</span> {sug.estimated_impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default MetricsPage;

interface MetricCardProps {
  label: string;
  value: string | number;
}

function MetricCard({ label, value }: MetricCardProps) {
  return (
    <div className="bg-neutral-800 rounded-xl py-6 px-4 text-center shadow-md hover:shadow-lg transition-shadow">
      <p className="text-sm text-gray-400">{label}</p>
      <h3 className="text-2xl font-bold mt-2 text-cyan-400">{value}</h3>
    </div>
  );
}
