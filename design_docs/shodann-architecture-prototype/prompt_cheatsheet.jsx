import React, { useState } from 'react';

const PromptCheatsheet = () => {
  const [activeLayer, setActiveLayer] = useState('context');
  const [showExample, setShowExample] = useState(false);

  const layers = {
    context: {
      name: 'Context Layer',
      icon: '🎯',
      color: 'blue',
      purpose: 'Helps AI calibrate feedback appropriately',
      description: 'Week 3 students shouldn\'t get advanced optimization suggestions.',
      elements: [
        { label: 'Student Identifier', example: 'Student: @${{ github.event.pull_request.user.login }}' },
        { label: 'Course Information', example: 'Course: Introductory Python Programming' },
        { label: 'Week/Module', example: 'Week: 3 (focusing on loops and conditionals)' },
        { label: 'Learning Objectives', example: 'Current topics: for loops, while loops, break/continue' }
      ],
      template: `## Student Context
Student: @\${{ github.event.pull_request.user.login }}
Course: [Course Name]
Week: [Number] (focusing on [current topics])
Previous PRs: [count if available]`
    },
    data: {
      name: 'Data Layer',
      icon: '📊',
      color: 'pink',
      purpose: 'Gives AI concrete facts to base feedback on',
      description: 'Grounds the AI in reality, reducing hallucination.',
      elements: [
        { label: 'Compilation Results', example: 'Compilation: ${{ steps.syntax-check.outputs.result }}' },
        { label: 'Linter Output', example: 'Style Issues: ${{ steps.style-check.outputs.issues }}' },
        { label: 'Test Results', example: 'Tests: 4 passed, 2 failed' },
        { label: 'File Statistics', example: 'Files Changed: ${{ github.event.pull_request.changed_files }}' }
      ],
      template: `## Technical Analysis
Compilation: \${{ steps.syntax-check.outputs.result }}
Style Issues: \${{ steps.style-check.outputs.issues }}
Test Results: \${{ steps.test.outputs.summary }}
Files Changed: \${{ github.event.pull_request.changed_files }}
Lines Added: \${{ github.event.pull_request.additions }}`
    },
    pedagogical: {
      name: 'Pedagogical Layer',
      icon: '🎓',
      color: 'green',
      purpose: 'Ensures AI acts as supportive teaching assistant',
      description: 'The difference between a harsh critic and an encouraging mentor.',
      elements: [
        { label: 'Priority', example: 'Priority: Learning over perfection' },
        { label: 'Tone', example: 'Style: Encouraging, specific examples' },
        { label: 'Focus Limit', example: 'Focus: 1-3 main concepts per review' },
        { label: 'Level', example: 'Level: Beginner (avoid advanced topics)' }
      ],
      template: `## Teaching Instructions
Priority: Learning over perfection
Style: Encouraging, use specific examples from their code
Focus: Address 1-3 main concepts maximum
Level: [Beginner/Intermediate/Advanced]
Avoid: [Topics they haven't learned yet]`
    },
    format: {
      name: 'Format Layer',
      icon: '📝',
      color: 'amber',
      purpose: 'Creates consistent, scannable feedback',
      description: 'Students know what to expect and how to use the feedback.',
      elements: [
        { label: 'Structure Template', example: 'Use sections: Working Well, Learning, Fixes' },
        { label: 'Length Guidance', example: 'Keep total response under 300 words' },
        { label: 'Emoji Usage', example: 'Use emojis for section headers only' },
        { label: 'Code Examples', example: 'Include corrected code snippets when helpful' }
      ],
      template: `## Response Structure
Use this exact format:

🎉 **What's Working Well**: [specific positives]

📚 **Learning Opportunities**: [explanations with examples]

🔧 **Quick Fixes**: [actionable improvements]

Keep response under 300 words. Be specific, not generic.`
    }
  };

  const fullExamplePrompt = `## Student Context
Student: @\${{ github.event.pull_request.user.login }}
Course: Introductory Python Programming  
Week: 3 (focusing on loops and conditionals)
Previous submissions: This appears to be their 2nd PR

## Technical Analysis
Compilation: \${{ steps.syntax-check.outputs.result }}
Style Issues: \${{ steps.style-check.outputs.issues }}
Files Changed: \${{ github.event.pull_request.changed_files }}

## Teaching Instructions
Priority: Learning over perfection
Style: Encouraging, specific examples from their code
Focus: Address 1-3 main concepts maximum
Level: Beginner (avoid list comprehensions, decorators)

If there are syntax errors:
- Explain each error in student-friendly terms
- Show exactly where the problem is
- Provide a working example

If code compiles:
- Praise what's working
- Focus on code style and organization
- Introduce one new concept they could try

## Response Structure
Use this format:

🎉 **What's Working Well**: [specific positives from their code]

📚 **Learning Opportunities**: [1-2 concepts with examples]

🔧 **Quick Fixes**: [actionable improvements they can make now]

Keep total response under 250 words.`;

  const colorClasses = {
    blue: { bg: 'bg-blue-500/20', border: 'border-blue-500', text: 'text-blue-400', ring: 'ring-blue-500' },
    pink: { bg: 'bg-pink-500/20', border: 'border-pink-500', text: 'text-pink-400', ring: 'ring-pink-500' },
    green: { bg: 'bg-green-500/20', border: 'border-green-500', text: 'text-green-400', ring: 'ring-green-500' },
    amber: { bg: 'bg-amber-500/20', border: 'border-amber-500', text: 'text-amber-400', ring: 'ring-amber-500' }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Prompt Engineering Cheatsheet
          </h1>
          <p className="text-slate-400">
            The 4-Layer Structure for Educational AI Prompts
          </p>
        </div>

        {/* Layer Stack Visualization */}
        <div className="mb-8">
          <div className="flex flex-col gap-2 max-w-md mx-auto">
            {Object.entries(layers).map(([key, layer]) => {
              const colors = colorClasses[layer.color];
              const isActive = activeLayer === key;
              return (
                <button
                  key={key}
                  onClick={() => setActiveLayer(key)}
                  className={`
                    p-4 rounded-lg border-2 transition-all text-left
                    ${isActive ? `${colors.bg} ${colors.border} ring-2 ${colors.ring}` : 'bg-slate-800/50 border-slate-700'}
                  `}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{layer.icon}</span>
                    <div>
                      <span className={`font-semibold ${isActive ? colors.text : 'text-white'}`}>
                        {layer.name}
                      </span>
                      <p className="text-slate-400 text-sm">{layer.purpose}</p>
                    </div>
                    <span className={`ml-auto ${isActive ? colors.text : 'text-slate-500'}`}>
                      {isActive ? '▼' : '▶'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Active Layer Detail */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Explanation */}
          <div className={`rounded-2xl p-6 border-2 ${colorClasses[layers[activeLayer].color].bg} ${colorClasses[layers[activeLayer].color].border}`}>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{layers[activeLayer].icon}</span>
              <div>
                <h2 className="text-xl font-bold text-white">{layers[activeLayer].name}</h2>
                <p className={colorClasses[layers[activeLayer].color].text}>{layers[activeLayer].purpose}</p>
              </div>
            </div>
            
            <p className="text-slate-300 mb-6">{layers[activeLayer].description}</p>
            
            <h3 className="text-white font-semibold mb-3">Key Elements:</h3>
            <div className="space-y-3">
              {layers[activeLayer].elements.map((el, i) => (
                <div key={i} className="bg-slate-900/50 rounded-lg p-3">
                  <div className="text-white font-medium text-sm mb-1">{el.label}</div>
                  <code className="text-slate-400 text-xs font-mono">{el.example}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Template */}
          <div className="bg-slate-800/50 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4">Template:</h3>
            <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto">
              <code className="text-slate-300 whitespace-pre-wrap font-mono">
                {layers[activeLayer].template}
              </code>
            </pre>
            
            <div className="mt-4 p-4 bg-slate-700/30 rounded-lg">
              <h4 className="text-amber-400 font-medium text-sm mb-2">💡 Pro Tip</h4>
              <p className="text-slate-400 text-sm">
                {activeLayer === 'context' && "Include week number to automatically filter out concepts they haven't learned yet."}
                {activeLayer === 'data' && "Always run real tools first - AI analysis is more accurate with concrete compiler/linter output."}
                {activeLayer === 'pedagogical' && "The 1-3 concept limit prevents overwhelming students with too much feedback at once."}
                {activeLayer === 'format' && "Consistent structure helps students quickly find the information they need."}
              </p>
            </div>
          </div>
        </div>

        {/* Full Example Toggle */}
        <div className="bg-slate-800/50 rounded-2xl p-6">
          <button
            onClick={() => setShowExample(!showExample)}
            className="flex items-center gap-2 text-white font-semibold mb-4 hover:text-blue-400 transition-colors"
          >
            <span>{showExample ? '▼' : '▶'}</span>
            Complete 4-Layer Prompt Example
          </button>
          
          {showExample && (
            <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto">
              <code className="text-slate-300 whitespace-pre-wrap font-mono">
                {fullExamplePrompt}
              </code>
            </pre>
          )}
        </div>

        {/* Quick Reference Cards */}
        <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 text-center">
            <div className="text-3xl mb-2">🎯</div>
            <div className="text-blue-400 font-semibold">Context</div>
            <div className="text-slate-500 text-xs mt-1">WHO is the student?</div>
          </div>
          <div className="bg-pink-500/10 border border-pink-500/30 rounded-xl p-4 text-center">
            <div className="text-3xl mb-2">📊</div>
            <div className="text-pink-400 font-semibold">Data</div>
            <div className="text-slate-500 text-xs mt-1">WHAT did tools find?</div>
          </div>
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
            <div className="text-3xl mb-2">🎓</div>
            <div className="text-green-400 font-semibold">Pedagogical</div>
            <div className="text-slate-500 text-xs mt-1">HOW should AI teach?</div>
          </div>
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-center">
            <div className="text-3xl mb-2">📝</div>
            <div className="text-amber-400 font-semibold">Format</div>
            <div className="text-slate-500 text-xs mt-1">WHAT structure?</div>
          </div>
        </div>

        {/* Common Mistakes */}
        <div className="mt-8 bg-red-500/10 border border-red-500/30 rounded-2xl p-6">
          <h3 className="text-red-400 font-semibold mb-4">⚠️ Common Mistakes to Avoid</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex gap-2">
              <span className="text-red-400">✗</span>
              <span className="text-slate-300">No context layer → AI gives advanced feedback to beginners</span>
            </div>
            <div className="flex gap-2">
              <span className="text-red-400">✗</span>
              <span className="text-slate-300">No data layer → AI hallucinates errors that don't exist</span>
            </div>
            <div className="flex gap-2">
              <span className="text-red-400">✗</span>
              <span className="text-slate-300">Harsh tone instructions → Students feel discouraged</span>
            </div>
            <div className="flex gap-2">
              <span className="text-red-400">✗</span>
              <span className="text-slate-300">No format template → Inconsistent, hard-to-read feedback</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptCheatsheet;
