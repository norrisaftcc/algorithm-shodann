import React, { useState } from 'react';

const ArchitectureDiagram = () => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [viewMode, setViewMode] = useState('simple');
  
  const nodes = {
    student: {
      id: 'student',
      title: 'Student Action',
      icon: '👩‍💻',
      color: '#3B82F6',
      simple: 'Opens a Pull Request with code changes',
      detailed: `The workflow begins when a student pushes code:
      
• Opens new PR with assignment code
• Updates existing PR with fixes
• Triggers on specific file types (*.py, *.cpp, etc.)

This is the entry point for the entire feedback loop.`,
      position: { x: 80, y: 200 }
    },
    github: {
      id: 'github',
      title: 'GitHub Event',
      icon: '⚡',
      color: '#6366F1',
      simple: 'GitHub detects the change and fires an event',
      detailed: `GitHub's event system captures the action:

• Event types: opened, synchronize, reopened
• Contains metadata: user, files changed, branch
• Triggers configured workflow runners

Events are the bridge between student actions and automation.`,
      position: { x: 230, y: 200 }
    },
    workflow: {
      id: 'workflow',
      title: 'Actions Workflow',
      icon: '⚙️',
      color: '#8B5CF6',
      simple: 'GitHub Actions runner starts the workflow',
      detailed: `The workflow YAML defines what happens:

• Runs on ubuntu-latest (free tier)
• Checks out student's code
• Has access to GitHub context variables
• Orchestrates all subsequent steps

This is your "recipe" for automated feedback.`,
      position: { x: 380, y: 200 }
    },
    preprocess: {
      id: 'preprocess',
      title: 'Pre-Processing',
      icon: '🔧',
      color: '#EC4899',
      simple: 'Run linters, compilers, and analysis tools',
      detailed: `Real tools provide concrete data for AI:

• python -m py_compile → syntax errors
• flake8/pylint → style issues  
• pytest → test results
• Custom scripts → metrics

Hybrid approach (tools + AI) is more reliable than AI-only.`,
      position: { x: 530, y: 200 }
    },
    gemini: {
      id: 'gemini',
      title: 'Gemini API',
      icon: '🤖',
      color: '#10B981',
      simple: 'AI processes code with educational prompt',
      detailed: `The AI receives a carefully crafted prompt:

• Context: Student info, course week, objectives
• Data: Tool outputs, file changes, diff
• Instructions: Teaching focus, tone, level
• Format: Response structure template

The prompt engineering is where pedagogy meets AI.`,
      position: { x: 680, y: 200 }
    },
    response: {
      id: 'response',
      title: 'Educational Response',
      icon: '📝',
      color: '#F59E0B',
      simple: 'Structured feedback focused on learning',
      detailed: `AI generates pedagogically-sound feedback:

🎉 What's Working Well: Specific positives
📚 Learning Opportunities: Explanations + examples
🔧 Quick Fixes: Actionable improvements

Encourages learning, doesn't just find bugs.`,
      position: { x: 830, y: 200 }
    },
    feedback: {
      id: 'feedback',
      title: 'Student Sees Feedback',
      icon: '✅',
      color: '#06B6D4',
      simple: 'Comment appears on their Pull Request',
      detailed: `Feedback delivered where students work:

• Appears as PR comment within seconds
• Formatted with markdown/emojis
• Links to relevant resources
• Invites iteration and questions

Closes the feedback loop, enabling rapid improvement.`,
      position: { x: 980, y: 200 }
    }
  };

  const nodeOrder = ['student', 'github', 'workflow', 'preprocess', 'gemini', 'response', 'feedback'];

  const Arrow = ({ from, to }) => {
    const x1 = from + 50;
    const x2 = to;
    const y = 200;
    return (
      <g>
        <line 
          x1={x1} y1={y} x2={x2 - 10} y2={y} 
          stroke="#94A3B8" 
          strokeWidth="2"
          markerEnd="url(#arrowhead)"
        />
      </g>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Educational AI Workflow Architecture
          </h1>
          <p className="text-slate-400 mb-4">
            GitHub Actions + Gemini CLI = Automated Learning Feedback
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setViewMode('simple')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                viewMode === 'simple' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Simple View
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                viewMode === 'detailed' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Detailed View
            </button>
          </div>
        </div>

        {/* Main Diagram */}
        <div className="bg-slate-800/50 rounded-2xl p-6 mb-6 overflow-x-auto">
          <svg viewBox="0 0 1100 400" className="w-full min-w-[900px]">
            {/* Arrow marker definition */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#94A3B8" />
              </marker>
            </defs>
            
            {/* Connection lines */}
            {nodeOrder.slice(0, -1).map((nodeId, i) => (
              <Arrow 
                key={nodeId}
                from={nodes[nodeId].position.x}
                to={nodes[nodeOrder[i + 1]].position.x}
              />
            ))}

            {/* Nodes */}
            {nodeOrder.map((nodeId) => {
              const node = nodes[nodeId];
              const isSelected = selectedNode === nodeId;
              return (
                <g 
                  key={nodeId}
                  onClick={() => setSelectedNode(isSelected ? null : nodeId)}
                  className="cursor-pointer"
                >
                  {/* Node circle */}
                  <circle
                    cx={node.position.x}
                    cy={node.position.y}
                    r={isSelected ? 48 : 42}
                    fill={node.color}
                    className="transition-all duration-200"
                    opacity={isSelected ? 1 : 0.85}
                  />
                  
                  {/* Glow effect when selected */}
                  {isSelected && (
                    <circle
                      cx={node.position.x}
                      cy={node.position.y}
                      r={55}
                      fill="none"
                      stroke={node.color}
                      strokeWidth="3"
                      opacity="0.4"
                    />
                  )}
                  
                  {/* Icon */}
                  <text
                    x={node.position.x}
                    y={node.position.y + 8}
                    textAnchor="middle"
                    fontSize="28"
                    className="select-none"
                  >
                    {node.icon}
                  </text>
                  
                  {/* Title */}
                  <text
                    x={node.position.x}
                    y={node.position.y + 70}
                    textAnchor="middle"
                    fill="white"
                    fontSize="12"
                    fontWeight="600"
                    className="select-none"
                  >
                    {node.title}
                  </text>
                </g>
              );
            })}

            {/* Step numbers */}
            {nodeOrder.map((nodeId, i) => {
              const node = nodes[nodeId];
              return (
                <g key={`num-${nodeId}`}>
                  <circle
                    cx={node.position.x - 30}
                    cy={node.position.y - 55}
                    r={12}
                    fill="#1E293B"
                    stroke="#475569"
                    strokeWidth="2"
                  />
                  <text
                    x={node.position.x - 30}
                    y={node.position.y - 51}
                    textAnchor="middle"
                    fill="#94A3B8"
                    fontSize="11"
                    fontWeight="bold"
                  >
                    {i + 1}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Detail Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Selected Node Detail */}
          <div className="bg-slate-800/50 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              {selectedNode ? nodes[selectedNode].title : 'Click a node to learn more'}
            </h2>
            {selectedNode ? (
              <div 
                className="text-slate-300 whitespace-pre-line leading-relaxed"
                style={{ borderLeft: `4px solid ${nodes[selectedNode].color}`, paddingLeft: '1rem' }}
              >
                {viewMode === 'simple' ? nodes[selectedNode].simple : nodes[selectedNode].detailed}
              </div>
            ) : (
              <p className="text-slate-500">
                Select any component in the diagram above to see how it works in the educational AI feedback system.
              </p>
            )}
          </div>

          {/* Key Concepts */}
          <div className="bg-slate-800/50 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Key Design Principles</h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🔍</span>
                <div>
                  <h3 className="text-white font-medium">Transparency Over Magic</h3>
                  <p className="text-slate-400 text-sm">Students understand what's happening. Instructors can see and modify every prompt.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">🎓</span>
                <div>
                  <h3 className="text-white font-medium">Education-First AI</h3>
                  <p className="text-slate-400 text-sm">AI teaches concepts, doesn't just find bugs. Builds confidence while maintaining standards.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">🚀</span>
                <div>
                  <h3 className="text-white font-medium">Minimal Infrastructure</h3>
                  <p className="text-slate-400 text-sm">Uses existing tools (GitHub, Google AI). No servers to maintain. Scales from 1 to 1000 students.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Reference */}
        <div className="mt-6 bg-slate-800/50 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">The Formula</h2>
          <div className="flex flex-wrap items-center justify-center gap-4 text-lg">
            <span className="bg-blue-600/20 text-blue-400 px-4 py-2 rounded-lg font-mono">
              GitHub Actions
            </span>
            <span className="text-slate-500 text-2xl">+</span>
            <span className="bg-green-600/20 text-green-400 px-4 py-2 rounded-lg font-mono">
              Gemini CLI
            </span>
            <span className="text-slate-500 text-2xl">+</span>
            <span className="bg-purple-600/20 text-purple-400 px-4 py-2 rounded-lg font-mono">
              Thoughtful Prompts
            </span>
            <span className="text-slate-500 text-2xl">=</span>
            <span className="bg-amber-600/20 text-amber-400 px-4 py-2 rounded-lg font-mono">
              Powerful Educational Automation
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureDiagram;
