// src/App.js
import React, { useState } from "react";

function App() {
  const [symptoms, setSymptoms] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // FIX: Always use the backend directly.
  // This removes all mixed-content / origin / redirect issues.
  const API_BASE = "http://127.0.0.1:8001";

  const handleDiagnose = async () => {
    setError("");
    setResults([]);

    const tokens = symptoms
      .split(/\s+|,+/) // split by space or comma
      .map((t) => t.trim())
      .filter(Boolean);

    if (tokens.length === 0) {
      setError("Please enter at least one symptom.");
      return;
    }

    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/diagnose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symptoms: tokens }),
      });

      if (!resp.ok) {
        const txt = await resp.text().catch(() => resp.statusText);
        throw new Error(`API error ${resp.status}: ${txt}`);
      }

      const data = await resp.json();

      if (data.results) {
        setResults(data.results);
      } else {
        setError(data.message || "No results returned");
      }
    } catch (err) {
      console.error("Diagnosis request failed:", err);
      setError("Failed to fetch diagnosis. Please check API connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="bg-white shadow-lg rounded-2xl p-8 max-w-lg w-full">
        <h1 className="text-2xl font-bold text-center mb-4 text-indigo-600">
          🧠 Doc Zaddy
        </h1>
        <p className="text-gray-600 text-center mb-6">
          Enter your symptoms below (space or comma separated) to get a diagnosis.
        </p>

        <textarea
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="e.g., fever cough headache"
          className="w-full border border-gray-300 rounded-lg p-3 mb-4 focus:ring-2 focus:ring-indigo-400 outline-none"
          rows={3}
        />

        <button
          onClick={handleDiagnose}
          disabled={loading}
          className="w-full bg-indigo-500 text-white rounded-lg py-2 font-semibold hover:bg-indigo-600 transition"
        >
          {loading ? "Analyzing..." : "Diagnose"}
        </button>

        {error && <p className="text-red-500 mt-3 text-center">{error}</p>}

        {results.length > 0 && (
          <div className="mt-6">
            <h2 className="font-semibold text-lg mb-2 text-gray-700">
              Possible Conditions:
            </h2>
            <ul className="space-y-2">
              {results.map((r, i) => (
                <li
                  key={i}
                  className="p-3 bg-gray-100 rounded-lg border border-gray-200"
                >
                  <p className="font-bold capitalize text-indigo-700">
                    {r.disease.replace(/_/g, " ")}
                  </p>
                  <p className="text-sm text-gray-600">
                    Match: {r.matched}/{r.total} (
                    {Math.round((r.confidence || 0) * 100)}%)
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
