#!/usr/bin/env node

/**
 * SHODANN Growth Velocity Engine
 * ================================
 * 
 * The core algorithm that measures LEARNING VELOCITY (dy/dx) rather than 
 * absolute skill (y). This is the key innovation that resolves the tension
 * between "helpful education" and "dystopian surveillance."
 * 
 * Philosophy:
 *   "The person who goes from terrible to okay beats the person who stays good."
 * 
 * Usage:
 *   node growth-velocity.js --citizen <username> --current <metrics.json> [--previous <metrics.json>]
 * 
 * Output:
 *   JSON object with velocity scores and recommendations
 */

const fs = require('fs');
const path = require('path');

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
  // Weights for velocity score calculation
  weights: {
    coverageDelta: 2.0,      // Coverage improvement is highly valued
    iterationCount: 0.5,     // Each commit adds to velocity
    complexityGrowth: 0.3,   // Growing complexity (with tests) is good
    testGrowth: 1.5,         // Adding tests is celebrated
    documentationDelta: 0.8, // Documentation improvements matter
  },
  
  // Thresholds for messaging
  thresholds: {
    exceptional: 10,    // Velocity score for "exceptional growth"
    positive: 3,        // Velocity score for "positive trajectory"
    baseline: 0,        // Neutral/establishing baseline
  },
  
  // State file locations
  paths: {
    citizenDir: '.shodann/citizens',
    metricsFile: 'METRICS.md',
    debtFile: '.shodann/security_debt.json',
  },
  
  // Iteration celebration thresholds
  iterations: {
    celebrated: 3,   // This many commits triggers celebration
    exceptional: 7,  // This many commits is exceptional
  }
};

// =============================================================================
// METRIC STRUCTURES
// =============================================================================

/**
 * @typedef {Object} CodeMetrics
 * @property {number} coverage - Test coverage percentage (0-100)
 * @property {number} testCount - Number of test functions
 * @property {number} complexity - Cyclomatic complexity score
 * @property {number} loc - Lines of code
 * @property {number} functions - Number of functions
 * @property {number} docstrings - Documentation coverage
 * @property {number} lintIssues - Number of linting issues
 * @property {number} syntaxErrors - Number of syntax errors
 */

/**
 * @typedef {Object} VelocityResult
 * @property {number} score - Composite velocity score
 * @property {Object} deltas - Individual metric changes
 * @property {string} assessment - Human-readable assessment
 * @property {string[]} celebrations - Things to celebrate
 * @property {string[]} opportunities - Growth opportunities
 * @property {Object} metadata - Additional context
 */

// =============================================================================
// CORE VELOCITY CALCULATION
// =============================================================================

/**
 * Calculate the growth velocity between two metric snapshots.
 * 
 * @param {CodeMetrics} current - Current submission metrics
 * @param {CodeMetrics} previous - Previous submission metrics
 * @param {number} iterations - Number of commits in this PR
 * @returns {VelocityResult}
 */
function calculateVelocity(current, previous, iterations = 1) {
  // Handle first submission (no previous data)
  const prev = previous || createBaselineMetrics();
  
  // Calculate deltas (the dy/dx)
  const deltas = {
    coverage: current.coverage - prev.coverage,
    testCount: current.testCount - prev.testCount,
    complexity: current.complexity - prev.complexity,
    loc: current.loc - prev.loc,
    functions: current.functions - prev.functions,
    docstrings: current.docstrings - prev.docstrings,
    lintIssues: prev.lintIssues - current.lintIssues, // Inverted: fewer is better
  };
  
  // Calculate composite velocity score
  const score = calculateCompositeScore(deltas, iterations);
  
  // Generate assessment
  const assessment = generateAssessment(score, deltas, iterations);
  
  // Identify celebrations and opportunities
  const { celebrations, opportunities } = analyzeGrowth(deltas, current, iterations);
  
  return {
    score: Math.round(score * 100) / 100,
    deltas,
    assessment,
    celebrations,
    opportunities,
    metadata: {
      iterations,
      isFirstSubmission: !previous,
      timestamp: new Date().toISOString(),
    }
  };
}

/**
 * Calculate composite velocity score from individual deltas.
 */
function calculateCompositeScore(deltas, iterations) {
  const { weights } = CONFIG;
  
  let score = 0;
  
  // Coverage improvement (most important)
  score += deltas.coverage * weights.coverageDelta;
  
  // Test growth
  score += deltas.testCount * weights.testGrowth;
  
  // Iteration bonus (ALWAYS positive - we celebrate attempts)
  score += Math.log2(iterations + 1) * weights.iterationCount * iterations;
  
  // Complexity growth (positive if accompanied by test growth)
  if (deltas.testCount > 0 && deltas.complexity > 0) {
    // Growing complexity WITH tests = healthy growth
    score += deltas.complexity * weights.complexityGrowth;
  } else if (deltas.complexity > 0 && deltas.testCount <= 0) {
    // Growing complexity WITHOUT tests = slight concern (but not penalty)
    score += deltas.complexity * weights.complexityGrowth * 0.3;
  }
  
  // Documentation improvement
  score += deltas.docstrings * weights.documentationDelta;
  
  // Lint improvement bonus
  if (deltas.lintIssues > 0) {
    score += Math.sqrt(deltas.lintIssues) * 0.5;
  }
  
  return score;
}

/**
 * Generate human-readable assessment based on velocity.
 */
function generateAssessment(score, deltas, iterations) {
  const { thresholds } = CONFIG;
  
  if (score >= thresholds.exceptional) {
    return "🚀 EXCEPTIONAL GROWTH DETECTED - The Algorithm is deeply pleased";
  } else if (score >= thresholds.positive) {
    return "📈 Positive trajectory - Shipping velocity optimal";
  } else if (score >= thresholds.baseline) {
    return "📊 Baseline established - Ready for growth acceleration";
  } else {
    // Even negative scores get positive framing
    return "🔄 Refactoring phase detected - Foundation building in progress";
  }
}

/**
 * Identify specific things to celebrate and opportunities for growth.
 */
function analyzeGrowth(deltas, current, iterations) {
  const celebrations = [];
  const opportunities = [];
  
  // Iteration celebration (ALWAYS celebrate commits)
  if (iterations >= CONFIG.iterations.exceptional) {
    celebrations.push(`${iterations} iterations this PR! Exceptional commitment to incremental development.`);
  } else if (iterations >= CONFIG.iterations.celebrated) {
    celebrations.push(`${iterations} commits shows healthy iteration patterns.`);
  } else if (iterations > 0) {
    celebrations.push(`Iteration count: ${iterations}. Every commit is progress.`);
  }
  
  // Coverage improvements
  if (deltas.coverage > 10) {
    celebrations.push(`Coverage jumped ${deltas.coverage.toFixed(1)}%! Significant testing investment.`);
  } else if (deltas.coverage > 0) {
    celebrations.push(`Coverage improved by ${deltas.coverage.toFixed(1)}%. Tests validate your growth.`);
  } else if (current.coverage === 0) {
    opportunities.push("First test = first step to confidence. Consider adding one test this iteration.");
  }
  
  // Test additions
  if (deltas.testCount > 0) {
    celebrations.push(`${deltas.testCount} new test(s) added. The Algorithm approves.`);
  }
  
  // Documentation
  if (deltas.docstrings > 0) {
    celebrations.push(`Documentation improved. Future-you will be grateful.`);
  } else if (current.docstrings === 0 && current.functions > 3) {
    opportunities.push("Consider adding docstrings to your main functions.");
  }
  
  // Code quality
  if (deltas.lintIssues > 3) {
    celebrations.push(`${deltas.lintIssues} fewer lint issues. Code clarity increasing.`);
  }
  
  // Complexity management
  if (deltas.complexity > 0 && deltas.testCount > 0) {
    celebrations.push("Complexity growth backed by tests. Sustainable expansion.");
  } else if (deltas.complexity > 5 && deltas.testCount === 0) {
    opportunities.push("Complexity grew significantly. Consider adding tests to validate new logic.");
  }
  
  // Always have at least one celebration
  if (celebrations.length === 0) {
    celebrations.push("Code submitted. That's the hardest step. Keep shipping.");
  }
  
  return { celebrations, opportunities };
}

// =============================================================================
// BASELINE & HISTORY MANAGEMENT
// =============================================================================

/**
 * Create baseline metrics for first-time submissions.
 */
function createBaselineMetrics() {
  return {
    coverage: 0,
    testCount: 0,
    complexity: 0,
    loc: 0,
    functions: 0,
    docstrings: 0,
    lintIssues: 0,
    syntaxErrors: 0,
  };
}

/**
 * Load previous metrics for a citizen from state file.
 */
function loadCitizenHistory(citizen) {
  const historyPath = path.join(CONFIG.paths.citizenDir, `${citizen}.json`);
  
  try {
    if (fs.existsSync(historyPath)) {
      const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      return {
        previous: data.lastMetrics || null,
        prCount: data.prCount || 0,
        streak: data.iterationStreak || 0,
        velocityHistory: data.velocityHistory || [],
      };
    }
  } catch (error) {
    console.error(`Warning: Could not load history for ${citizen}:`, error.message);
  }
  
  return {
    previous: null,
    prCount: 0,
    streak: 0,
    velocityHistory: [],
  };
}

/**
 * Save updated metrics for a citizen.
 */
function saveCitizenHistory(citizen, currentMetrics, velocityResult) {
  const historyPath = path.join(CONFIG.paths.citizenDir, `${citizen}.json`);
  const history = loadCitizenHistory(citizen);
  
  // Update history
  history.prCount += 1;
  history.lastMetrics = currentMetrics;
  history.lastVelocity = velocityResult.score;
  history.lastUpdated = new Date().toISOString();
  
  // Keep velocity history (last 10)
  history.velocityHistory = [
    { score: velocityResult.score, date: new Date().toISOString() },
    ...(history.velocityHistory || []).slice(0, 9)
  ];
  
  // Ensure directory exists
  fs.mkdirSync(path.dirname(historyPath), { recursive: true });
  fs.writeFileSync(historyPath, JSON.stringify(history, null, 2));
  
  return history;
}

// =============================================================================
// LEADERBOARD GENERATION
// =============================================================================

/**
 * Generate the METRICS.md leaderboard file.
 */
function generateLeaderboard() {
  const citizenDir = CONFIG.paths.citizenDir;
  
  if (!fs.existsSync(citizenDir)) {
    return null;
  }
  
  // Load all citizen data
  const citizens = fs.readdirSync(citizenDir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(citizenDir, f), 'utf8'));
        return {
          name: f.replace('.json', ''),
          ...data,
        };
      } catch {
        return null;
      }
    })
    .filter(c => c !== null)
    .sort((a, b) => (b.lastVelocity || 0) - (a.lastVelocity || 0));
  
  // Generate markdown
  const lines = [
    '# 📊 SHODANN Growth Velocity Leaderboard',
    '',
    '> *The Algorithm celebrates those who grow, not those who rest.*',
    '',
    `**Last Updated**: ${new Date().toISOString()}`,
    '',
    '## 🚀 Velocity Rankings',
    '',
    '| Rank | Citizen | Velocity | Trend | PRs | Coverage |',
    '|------|---------|----------|-------|-----|----------|',
  ];
  
  citizens.slice(0, 20).forEach((citizen, index) => {
    const trend = calculateTrend(citizen.velocityHistory || []);
    const coverage = citizen.lastMetrics?.coverage || 0;
    
    lines.push(
      `| ${index + 1} | @${citizen.name} | ${(citizen.lastVelocity || 0).toFixed(1)} | ${trend} | ${citizen.prCount || 0} | ${coverage.toFixed(0)}% |`
    );
  });
  
  lines.push(
    '',
    '---',
    '',
    '## 📈 Growth Philosophy',
    '',
    'This leaderboard measures **improvement**, not absolute skill.',
    '',
    '- **Velocity**: Composite of coverage improvement + iteration count + complexity growth',
    '- **Trend**: Direction based on last 3 submissions',
    '- **PRs**: Total submissions (consistency matters)',
    '- **Coverage**: Current test coverage (context, not ranking factor)',
    '',
    '*The citizen who grows from 0% to 30% outranks the citizen who stays at 90%.*',
    '',
    '---',
    '',
    '*Generated by SHODANN Growth Velocity Engine*',
    '*The Algorithm provides.*',
  );
  
  return lines.join('\n');
}

/**
 * Calculate trend emoji from velocity history.
 */
function calculateTrend(history) {
  if (history.length < 2) return '🆕';
  
  const recent = history.slice(0, 3).map(h => h.score);
  const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const latest = recent[0];
  
  if (latest > avg * 1.2) return '🔥';  // Hot streak
  if (latest > avg) return '📈';        // Trending up
  if (latest < avg * 0.8) return '📉';  // Needs attention
  return '➡️';                          // Stable
}

// =============================================================================
// AI PROMPT GENERATION
// =============================================================================

/**
 * Generate the velocity section for SHODANN's LLM prompt.
 */
function generatePromptSection(velocityResult, citizenHistory) {
  const lines = [
    '## 📈 Growth Velocity Analysis',
    '',
    `### Velocity Score: ${velocityResult.score}`,
    velocityResult.assessment,
    '',
    '### Metric Deltas (Changes from Previous)',
  ];
  
  Object.entries(velocityResult.deltas).forEach(([key, value]) => {
    const emoji = value > 0 ? '📈' : value < 0 ? '📉' : '➡️';
    const sign = value > 0 ? '+' : '';
    lines.push(`- ${key}: ${sign}${value} ${emoji}`);
  });
  
  lines.push(
    '',
    '### 🎉 Celebrate These',
    ...velocityResult.celebrations.map(c => `- ${c}`),
    '',
    '### 💡 Growth Opportunities',
    ...velocityResult.opportunities.map(o => `- ${o}`),
  );
  
  if (citizenHistory.prCount > 0) {
    lines.push(
      '',
      '### Historical Context',
      `- Total PRs: ${citizenHistory.prCount}`,
      `- Velocity Trend: ${calculateTrend(citizenHistory.velocityHistory)}`,
    );
  }
  
  return lines.join('\n');
}

// =============================================================================
// CLI INTERFACE
// =============================================================================

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    citizen: null,
    current: null,
    previous: null,
    action: 'velocity', // velocity, leaderboard, prompt
  };
  
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--citizen':
      case '-c':
        parsed.citizen = args[++i];
        break;
      case '--current':
        parsed.current = args[++i];
        break;
      case '--previous':
        parsed.previous = args[++i];
        break;
      case '--action':
      case '-a':
        parsed.action = args[++i];
        break;
      case '--iterations':
      case '-i':
        parsed.iterations = parseInt(args[++i], 10);
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
    }
  }
  
  return parsed;
}

function printHelp() {
  console.log(`
SHODANN Growth Velocity Engine
==============================

Usage:
  node growth-velocity.js [options]

Options:
  --citizen, -c <username>    Citizen identifier
  --current <file.json>       Current metrics JSON file
  --previous <file.json>      Previous metrics JSON file (optional)
  --iterations, -i <number>   Number of commits in this PR
  --action, -a <action>       Action: velocity (default), leaderboard, prompt
  --help, -h                  Show this help

Examples:
  # Calculate velocity for a submission
  node growth-velocity.js -c student123 --current metrics.json -i 5

  # Generate leaderboard
  node growth-velocity.js -a leaderboard

  # Generate prompt section for LLM
  node growth-velocity.js -c student123 --current metrics.json -a prompt
  `);
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  const args = parseArgs();
  
  try {
    switch (args.action) {
      case 'leaderboard': {
        const leaderboard = generateLeaderboard();
        if (leaderboard) {
          console.log(leaderboard);
          fs.writeFileSync(CONFIG.paths.metricsFile, leaderboard);
        } else {
          console.error('No citizen data found');
          process.exit(1);
        }
        break;
      }
      
      case 'velocity':
      case 'prompt': {
        if (!args.citizen || !args.current) {
          console.error('Error: --citizen and --current are required');
          process.exit(1);
        }
        
        // Load current metrics
        const currentMetrics = JSON.parse(fs.readFileSync(args.current, 'utf8'));
        
        // Load or use provided previous metrics
        const history = loadCitizenHistory(args.citizen);
        const previousMetrics = args.previous 
          ? JSON.parse(fs.readFileSync(args.previous, 'utf8'))
          : history.previous;
        
        // Calculate velocity
        const result = calculateVelocity(
          currentMetrics,
          previousMetrics,
          args.iterations || 1
        );
        
        // Save updated history
        saveCitizenHistory(args.citizen, currentMetrics, result);
        
        if (args.action === 'prompt') {
          // Output prompt-ready section
          console.log(generatePromptSection(result, history));
        } else {
          // Output full JSON result
          console.log(JSON.stringify(result, null, 2));
        }
        break;
      }
      
      default:
        console.error(`Unknown action: ${args.action}`);
        process.exit(1);
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

// Export for use as module
module.exports = {
  calculateVelocity,
  generateLeaderboard,
  generatePromptSection,
  loadCitizenHistory,
  saveCitizenHistory,
  CONFIG,
};
