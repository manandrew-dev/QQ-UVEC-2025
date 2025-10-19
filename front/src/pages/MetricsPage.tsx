
import { useLocation } from "react-router-dom";
import CodeEditor from "../components/CodeEditor";

interface Suggestion {
  action: string;
  issue: {
    type: string;
    severity: string;
    description?: string;
    functions?: { name: string; complexity: number; line: number }[];
    score?: number;
    metrics?: {
      function_count?: number;
      class_count?: number;
      average_complexity?: number;
      max_complexity?: number;
      maintainability?: number;
      size?: number;
    };
  };
  steps?: { type: string; description: string; [key: string]: any }[];
  estimated_impact?: Record<string, any>;
}

interface Metrics {
  total_functions?: number;
  total_classes?: number;
  total_lines?: number;
  sloc?: number;
  average_complexity?: number;
  max_complexity?: number;
  maintainability?: number;
  cohesion?: number;
  results?: Suggestion[];
  suggestions?: Suggestion[];
}

interface MetricsPageProps {
  code: string;
}

function MetricsPage({ code }: MetricsPageProps) {
  const location = useLocation();
  const result = location.state?.result as Metrics | undefined;

  console.log("Backend result:", result);

  if (!result) {
    return (
      <div className="bg-neutral-900 text-white min-h-screen flex items-center justify-center">
        <p className="text-gray-400">
          No metrics data found. Please analyze your code first.
        </p>
      </div>
    );
  }

  // 🧠 Determine whether suggestions exist
  const suggestions = Array.isArray(result)
    ? result
    : result.results || result.suggestions || [];

  // 🧮 Merge nested metrics into top-level values if available
  if (result && suggestions.length > 0) {
    const summaryMetrics =
      (suggestions.find((s) => s.issue.metrics) as Suggestion | undefined)
        ?.issue.metrics || {};

    result.total_functions =
      result.total_functions ??
      summaryMetrics.function_count ??
      result.total_functions ??
      0;

    result.total_classes =
      result.total_classes ??
      summaryMetrics.class_count ??
      result.total_classes ??
      0;

    result.average_complexity =
      result.average_complexity ??
      summaryMetrics.average_complexity ??
      result.average_complexity ??
      0;

    result.max_complexity =
      result.max_complexity ??
      summaryMetrics.max_complexity ??
      result.max_complexity ??
      0;

    result.maintainability =
      result.maintainability ??
      summaryMetrics.maintainability ??
      result.maintainability ??
      0;

    result.sloc =
      result.sloc ??
      summaryMetrics.size ??
      result.sloc ??
      0;

    result.cohesion = result.cohesion ?? 0.7;
  }

  const hasMetrics =
    result.total_functions !== undefined ||
    result.average_complexity !== undefined ||
    result.maintainability !== undefined;

  return (
    <div className="bg-neutral-900 text-white min-h-screen flex flex-col items-center px-8 py-12 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 animate-rgb mb-4">
          Code Analysis Report
        </h1>
        <p className="text-gray-400">
          Insights into your project’s modularity, complexity, and maintainability
        </p>
      </div>

      {/* 📊 Metrics Grid */}
      {hasMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full max-w-5xl">
          <MetricCard label="Functions" value={result.total_functions ?? "—"} />
          <MetricCard label="Classes" value={result.total_classes ?? "—"} />
          <MetricCard
            label="Avg. Complexity"
            value={
              result.average_complexity != null
                ? result.average_complexity.toFixed(2)
                : "—"
            }
          />
          <MetricCard
            label="Maintainability"
            value={
              result.maintainability != null
                ? result.maintainability.toFixed(2)
                : "—"
            }
          />
          <MetricCard
            label="Max Complexity"
            value={result.max_complexity ?? "—"}
          />
          <MetricCard label="Lines of Code" value={result.sloc ?? "—"} />
          <MetricCard
            label="Cohesion"
            value={
              result.cohesion != null ? result.cohesion.toFixed(2) : "—"
            }
          />
        </div>
      )}

      {/* 💻 Code Editor */}
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

      {/* 🧩 Suggestions */}
      {suggestions.length > 0 && (
        <div className="w-full max-w-5xl mt-8">
          <h2 className="text-2xl font-semibold mb-4 text-center">
            Refactor Suggestions
          </h2>
          <div className="space-y-4">
            {suggestions.map((sug: Suggestion, i: number) => (
              <div
                key={i}
                className={`p-5 rounded-xl border ${
                  sug.issue.severity?.toLowerCase() === "high"
                    ? "border-red-500/50 bg-red-900/20"
                    : sug.issue.severity?.toLowerCase() === "medium"
                    ? "border-yellow-500/50 bg-yellow-900/20"
                    : "border-green-500/50 bg-green-900/20"
                }`}
              >
                <h3 className="text-xl font-semibold mb-2">
                  {sug.issue.type}{" "}
                  <span
                    className={`ml-2 text-sm px-2 py-1 rounded ${
                      sug.issue.severity?.toLowerCase() === "high"
                        ? "bg-red-600"
                        : sug.issue.severity?.toLowerCase() === "medium"
                        ? "bg-yellow-600"
                        : "bg-green-600"
                    }`}
                  >
                    {sug.issue.severity}
                  </span>
                </h3>

                <p className="text-gray-300 mb-2 italic">{sug.action}</p>

                {sug.issue.description && (
                  <p className="text-gray-400 text-sm mb-2">
                    {sug.issue.description}
                  </p>
                )}

                {sug.steps && (
                  <ul className="list-disc list-inside text-gray-400 text-sm space-y-1">
                    {sug.steps.map((step, j) => (
                      <li key={j}>{step.description}</li>
                    ))}
                  </ul>
                )}

                {sug.estimated_impact && (
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="font-semibold">Impact:</span>{" "}
                    {JSON.stringify(sug.estimated_impact)}
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

/* --------------------------
   Metric Card Component
-------------------------- */
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
