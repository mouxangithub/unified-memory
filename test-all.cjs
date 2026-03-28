const { execSync } = require('child_process');
const { writeFileSync } = require('fs');

const MCPORTER = 'mcporter';
const SERVICE = 'unified-memory';

// All 78 tools with correct args (built from actual schema error messages)
const TESTS = [
  // Core (need query/text args)
  { tool: 'memory_search', args: 'query="test"' },
  { tool: 'memory_store', args: 'text="batch test memory"' },
  { tool: 'memory_bm25', args: 'query="test"' },
  { tool: 'memory_vector', args: 'action="embed" text="test embed"' },
  { tool: 'memory_mmr', args: 'query="test" documents=["a","b"] diversity=0.5' },
  { tool: 'memory_rerank_llm', args: 'query="test" memoryIds=["a","b"]' },
  { tool: 'memory_extract', args: 'texts=["刘总喜欢简洁直接的沟通"]' },
  { tool: 'memory_intent', args: 'query="帮我记住这个"' },
  { tool: 'memory_adaptive', args: 'query="今天天气怎么样"' },
  { tool: 'memory_concurrent_search', args: 'action="search" queries=["test1","test2"]' },
  { tool: 'memory_qa', args: 'question="什么是 unified memory"' },
  { tool: 'memory_qmd_vsearch', args: 'query="test"' },
  { tool: 'memory_qmd_search', args: 'action="search" query="test"' },
  { tool: 'memory_predict', args: 'action="predict" context="test"' },
  { tool: 'memory_predict_enhanced', args: 'action="predict" context="test"' },
  { tool: 'memory_inference', args: 'action="infer" query="test"' },
  { tool: 'memory_scope', args: 'action="normalize" scope="USER"' },
  { tool: 'memory_reflection', args: 'action="learn" sessionId="batch-001"' },
  { tool: 'memory_noise', args: 'action="should_store" text="hello world"' },
  { tool: 'memory_lessons', args: 'action="list"' },
  { tool: 'memory_feedback', args: 'action="record" memoryId="non-existent" feedback="useful"' },
  { tool: 'memory_dedup', args: 'action="status"' },
  { tool: 'memory_rollback', args: 'memoryId="non-existent"' },
  { tool: 'memory_recommend', args: 'action="recommend" context="test"' },
  { tool: 'memory_summary', args: 'action="summarize" period="7d"' },
  { tool: 'memory_preference_set', args: 'key="batch_key" value="batch_value"' },
  { tool: 'memory_preference_get', args: 'key="batch_key"' },
  { tool: 'memory_preference_explain', args: 'key="batch_key"' },
  { tool: 'memory_preference_slots', args: 'action="get"' },
  { tool: 'memory_preference_infer', args: 'text="我喜欢简洁的回复"' },
  { tool: 'memory_reminder_add', args: 'text="batch test reminder" time="2026-03-29T20:00:00+08:00"' },
  { tool: 'memory_reminder_cancel', args: 'id="non-existent"' },
  { tool: 'memory_templates', args: 'action="list"' },
  { tool: 'memory_tier', args: 'action="list"' },
  { tool: 'memory_wal', args: 'action="list"' },
  { tool: 'memory_decay', args: 'memoryId="non-existent" action="get"' },
  { tool: 'memory_autostore', args: 'action="extract"' },
  { tool: 'memory_decay_strength', args: 'memory_id="non-existent" strength=1.0' },

  // No args needed
  { tool: 'memory_health', args: '' },
  { tool: 'memory_stats', args: '' },
  { tool: 'memory_metrics', args: '' },
  { tool: 'memory_insights', args: '' },
  { tool: 'memory_list', args: '' },
  { tool: 'memory_delete', args: '' }, // will error on non-existent but that's ok
  { tool: 'memory_export', args: '' },
  { tool: 'memory_decay', args: '' },
  { tool: 'memory_reminder_list', args: '' },
  { tool: 'memory_version_list', args: '' },
  { tool: 'memory_version_timeline', args: '' },
  { tool: 'memory_trace', args: '' },
  { tool: 'memory_proactive_start', args: '' },
  { tool: 'memory_proactive_stop', args: '' },
  { tool: 'memory_proactive_status', args: '' },
  { tool: 'memory_proactive_trigger', args: '' },
  { tool: 'memory_proactive_recall', args: '' },
  { tool: 'memory_proactive_care', args: '' },
  { tool: 'memory_graph_stats', args: '' },
  { tool: 'memory_graph_entity', args: '' },
  { tool: 'memory_graph_relation', args: '' },
  { tool: 'memory_graph_query', args: '' },
  { tool: 'memory_graph_add', args: '' },
  { tool: 'memory_graph_delete', args: '' },
  { tool: 'memory_qmd_list', args: '' },
  { tool: 'memory_qmd_get', args: '' },
  { tool: 'memory_cloud_sync', args: '' },
  { tool: 'memory_cloud_push', args: '' },
  { tool: 'memory_cloud_pull', args: '' },
  { tool: 'memory_git_init', args: '' },
  { tool: 'memory_git_history', args: '' },
  { tool: 'memory_git_status', args: '' },

  // Phase 3 external (not registered in index.js - expected to fail)
  { tool: 'phase3_memory_search', args: 'query="test"' },
  { tool: 'phase3_memory_get', args: '' },
  { tool: 'phase3_memory_write', args: '' },
  { tool: 'memory_qmd_query', args: 'query="test"' },
  { tool: 'memory_qmd_status', args: '' },
];

function callTool(tool, args) {
  const start = Date.now();
  try {
    let cmd = `${MCPORTER} call ${SERVICE}.${tool}`;
    if (args) cmd += ` ${args}`;
    const out = execSync(cmd, { timeout: 20000, encoding: 'utf8', shell: '/bin/bash' });
    const elapsed = Date.now() - start;
    const text = typeof out === 'string' ? out.trim() : String(out).trim();
    const isError = text.includes('"isError": true') ||
                    text.includes('"error"') && text.includes('MCP') ||
                    text.includes('Error:') && text.includes('not found') ||
                    text.includes('Tool .* not found');
    return { ok: !isError, time: elapsed, output: text.slice(0, 300) };
  } catch(e) {
    const elapsed = Date.now() - start;
    const stderr = e.stderr ? String(e.stderr) : '';
    const msg = e.message || String(e);
    return { ok: false, time: elapsed, error: (stderr || msg).slice(0, 200) };
  }
}

console.log(`\n🔍 Testing ${TESTS.length} tools...\n`);
const results = [];

for (const t of TESTS) {
  const result = callTool(t.tool, t.args);
  results.push({ tool: t.tool, args: t.args, ...result });
  const icon = result.ok ? '✅' : '❌';
  const tag = result.ok ? '' : ` → ${(result.error || result.output || '').slice(0, 80)}`;
  console.log(`${icon} [${result.time}ms] ${t.tool}${tag}`);
}

const passed = results.filter(r => r.ok).length;
const failed = results.filter(r => !r.ok).length;
console.log(`\n📊 ${passed}/${TESTS.length} passed, ${failed} failed\n`);

if (failed > 0) {
  console.log('--- Failed detail ---');
  results.filter(r => !r.ok).forEach(r => {
    console.log(`\n❌ ${r.tool}: ${r.error || r.output}`);
  });
}

writeFileSync('/tmp/test-report.json', JSON.stringify(results, null, 2));
console.log('📄 Full report: /tmp/test-report.json');
