import React, { useState } from "react";
import "./MathTutor.css";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const MathTutor = () => {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [currentTest, setCurrentTest] = useState(null);

  const analyzeQuestion = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error("Failed to analyze the question.");
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error("Error analyzing question:", error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateTest = async () => {
    if (!analysis || !analysis.related_concepts?.length) {
      console.error("No concepts available to generate the test.");
      return;
    }

    const concepts = analysis.related_concepts.map((c) => c.concept);

    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/generate_test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ concepts, num_questions: 10 }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate the test.");
      }

      const data = await response.json();
      setCurrentTest(data); // Store the generated test data
    } catch (error) {
      console.error("Error generating test:", error.message);
    } finally {
      setLoading(false);
    }
  };

  const getConceptColor = (probability) => {
    if (probability > 0.75) return "green";
    if (probability > 0.5) return "yellow";
    return "red";
  };

  return (
    <div className="container">
      <div className="header-card">
        <h2>Math Question Analyzer</h2>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter your math question..."
          className="input"
        />
        <button
          onClick={analyzeQuestion}
          disabled={loading || !question}
          className={`button ${
            loading || !question ? "button-disabled" : "button-primary"
          }`}
        >
          {loading ? "Analyzing..." : "Analyze Question"}
        </button>
      </div>

      {analysis && (
        <div>
          <div className="analysis-card">
            <h3>Identified Concepts</h3>
            <ul>
              { (analysis.related_concepts.length != 0) && analysis.related_concepts.map((concept, index) => (
                <li key={index} className="concept-item">
                  <span>{concept.concept.replace("_", " ")}</span>
                  <span
                    className="concept-probability"
                    style={{ color: getConceptColor(concept.probability) }}
                  >
                    Probability: {(concept.probability * 100).toFixed(1)}%
                  </span>
                </li>
              ))}
            </ul>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={analysis.related_concepts}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="concept"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => value.replace(/_/g, " ")}
                />
                <YAxis
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip
                  formatter={(value) => `${(value * 100).toFixed(1)}%`}
                />
                <Bar dataKey="probability" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <button className={`button ${
            loading || !analysis ? "button-disabled" : "button-primary"
          }`}
           onClick={generateTest} disabled={loading || !analysis}>
        {loading ? "Generating Test..." : "Generate Test"}
      </button>

      {currentTest && (
        <div className="test-section">
          <h3>Generated Test</h3>
          {currentTest.tests.map((test, index) => (
            <div key={index} className="test-item">
              <h4>Concept: {test.concept.replace("_", " ")}</h4>
              <ul>
                {test.questions.map((question, qIndex) => (
                  <li key={qIndex} className="test-question">
                    <p>
                      <strong>Q:</strong> {question.question}
                    </p>
                    <p>
                      <strong>Answer:</strong> {question.expected_answer}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MathTutor;
