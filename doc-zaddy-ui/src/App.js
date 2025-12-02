// src/App.js
import React, { useState } from "react";

function App() {
  const [symptoms, setSymptoms] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Use environment variable for flexibility, fallback to deployed URL
  const API_BASE = process.env.REACT_APP_API_URL || "https://doc-zaddy.onrender.com";

  const handleDiagnose = async () => {
    setError("");
    setResults([]);

    const tokens = symptoms
      .split(/\s+|,+/)
      .map((t) => t.trim())
      .filter(Boolean);

    if (tokens.length === 0) {
      setError("Please enter at least one symptom.");s
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

  // ... rest of your component
}

export default App;