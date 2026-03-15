/**
 * Display AI-generated nudges to the user in real time.
 * Currently shows a static placeholder.
 */

export default function NudgeWidget() {
  // TODO (Step 2): Implement this component — see INSTRUCTIONS.md Step 2
  return (
    <div className="fixed bottom-4 right-4 max-w-sm w-full bg-white border border-gray-200 rounded-xl shadow-lg p-4 opacity-60">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-blue-600 text-sm">AI</span>
        </div>
        <div>
          <h4 className="font-medium text-gray-900 text-sm">AI Nudge</h4>
          <p className="text-sm text-gray-500 mt-1">
            Implement this component to show real AI-generated nudges here.
            See INSTRUCTIONS.md for details.
          </p>
        </div>
      </div>
    </div>
  );
}
