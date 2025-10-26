"use client";

// A simple loading spinner component
function Spinner() {
  return (
    <div className="border-4 border-white/20 border-t-white rounded-full w-8 h-8 animate-spin" />
  );
}

export default function AiAnalysisBox({ isLoading, error, explanation }) {
  // Helper function to format the explanation (e.g., handling newlines)
  const formatExplanation = (text) => {
    return text.split('\n').map((line, index) => (
      <p key={index} className="mb-2">
        {line}
      </p>
    ));
  };

  return (
    <section className="w-full h-full rounded-2xl p-6 bg-[#0e1a26] text-white">
      <h2 className="text-lg font-semibold">🤖 AI Analysis</h2>

      <div className="mt-4 p-4 min-h-[200px] rounded-md border border-white/10 bg-white/5 flex items-center justify-center">
        {isLoading && (
          <div className="flex flex-col items-center gap-2 opacity-80">
            <Spinner />
            <span>Analyzing transactions...</span>
          </div>
        )}

        {error && (
          <div className="text-red-400">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!isLoading && !error && explanation && (
          <div className="w-full text-sm opacity-90">
            {formatExplanation(explanation)}
          </div>
        )}

        {!isLoading && !error && !explanation && (
          <div className="opacity-70 text-center">
            Click "Analyze Transactions" in the wallet panel to see AI-powered insights here.
          </div>
        )}
      </div>
    </section>
  );
}