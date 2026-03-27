/**
 * lesson.js — Lesson System for unified-memory v1.2
 * Extracts durable high-level lessons from recurring memory recall patterns.
 * MCP tool: memory_lessons (extract/recall/list/stats/delete/touch/candidates)
 */
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const WORKSPACE = process.env.OPENCLAW_WORKSPACE_DIR ?? join(process.env.HOME ?? '/root', '.openclaw', 'workspace');
const SKILL_DIR = join(WORKSPACE, 'memory');
const LESSONS_FILE  = join(SKILL_DIR, 'lessons.json');
const ACCESS_FILE   = join(SKILL_DIR, 'lesson_access_log.json');

const LESSON_CANDIDATE_THRESHOLD = 5;
const MAX_LESSONS = 200;
const MAX_BODY_CHARS = 500;
const MAX_TITLE_CHARS = 120;

let lessonsCache = null, accessLogCache = null;

const load = (f, fallback) => {
  if (!existsSync(f)) return fallback;
  try { return JSON.parse(readFileSync(f, 'utf8')); } catch { return fallback; }
};
const save = (f, data) => { try { writeFileSync(f, JSON.stringify(data, null, 2), 'utf8'); } catch (e) { console.error('[lesson]', f, e.message); } };

function getLessons() { if (lessonsCache !== null) return lessonsCache; lessonsCache = load(LESSONS_FILE, []); return lessonsCache; }
function putLessons(lessons) { lessonsCache = lessons; save(LESSONS_FILE, lessons); }

function getLog() { if (accessLogCache !== null) return accessLogCache; accessLogCache = load(ACCESS_FILE, {}); return accessLogCache; }
function putLog(log) { accessLogCache = log; save(ACCESS_FILE, log); }

/** Record a memory recall for pattern detection */
export function recordRecall(memoryId) {
  const log = getLog();
  const now = Date.now();
  if (!log[memoryId]) log[memoryId] = { recall_count: 0, last_recall: 0, created_at: now };
  log[memoryId].recall_count++;
  log[memoryId].last_recall = now;
  putLog(log);
}

/** Access stats for a memory */
export function getAccessStats(memoryId) {
  const entry = getLog()[memoryId] ?? { recall_count: 0, last_recall: 0 };
  return { ...entry, is_candidate: entry.recall_count >= LESSON_CANDIDATE_THRESHOLD };
}

/** Create or update a lesson */
export function extractLesson(memoryId, title, body, tags = []) {
  const lessons = getLessons();
  const now = Date.now();
  const safeTitle = String(title).slice(0, MAX_TITLE_CHARS).trim();
  const safeBody  = String(body).slice(0, MAX_BODY_CHARS).trim();
  const safeTags  = Array.isArray(tags) ? tags.slice(0, 20) : [];
  if (!safeTitle || !safeBody) throw new Error('title and body are required');

  const idx = lessons.findIndex(l => l.title === safeTitle);
  const isNew = idx === -1;

  if (isNew) {
    if (lessons.length >= MAX_LESSONS) { lessons.sort((a, b) => (a.recall_count ?? 0) - (b.recall_count ?? 0)); lessons.shift(); }
    lessons.push({ id: `lesson_${now}_${Math.random().toString(36).slice(2, 8)}`, memory_id: memoryId ?? null, title: safeTitle, body: safeBody, tags: safeTags, created_at: now, updated_at: now, access_count: 0, recall_count: 0, last_recalled: null });
  } else {
    lessons[idx] = { ...lessons[idx], body: safeBody, tags: safeTags, updated_at: now, memory_id: memoryId ?? lessons[idx].memory_id };
  }
  putLessons(lessons);
  return { success: true, lesson: isNew ? lessons[lessons.length - 1] : lessons[idx], is_new: isNew };
}

export function touchLesson(lessonId) {
  const lessons = getLessons();
  const idx = lessons.findIndex(l => l.id === lessonId);
  if (idx === -1) return;
  lessons[idx].recall_count = (lessons[idx].recall_count ?? 0) + 1;
  lessons[idx].last_recalled = Date.now();
  lessons[idx].access_count  = (lessons[idx].access_count ?? 0) + 1;
  putLessons(lessons);
}

export function deleteLesson(lessonId) {
  const lessons = getLessons();
  const idx = lessons.findIndex(l => l.id === lessonId);
  if (idx === -1) return { success: false };
  lessons.splice(idx, 1);
  putLessons(lessons);
  return { success: true };
}

export function listLessons({ limit = 50, tag } = {}) {
  let lessons = getLessons();
  if (tag) lessons = lessons.filter(l => l.tags?.includes(tag));
  return lessons.sort((a, b) => (b.recall_count ?? 0) - (a.recall_count ?? 0)).slice(0, limit);
}

/** Jaccard-based lesson recall */
export function recallLessons(query, { limit = 5 } = {}) {
  const lessons = getLessons();
  const qWords = new Set(query.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  if (!qWords.size) return lessons.sort((a, b) => (b.recall_count ?? 0) - (a.recall_count ?? 0)).slice(0, limit)
    .map(l => ({ ...l, match_score: 1.0 }));

  const scored = lessons.map(l => {
    const all = new Set([...l.title, ...l.body, ...(l.tags ?? [])].join(' ').toLowerCase().split(/\s+/).filter(w => w.length > 2));
    const inter = [...qWords].filter(w => all.has(w)).length;
    const union = new Set([...qWords, ...all]).size;
    const score = union === 0 ? 0 : inter / union;
    return { ...l, match_score: Math.min(score + Math.log1p(l.recall_count ?? 0) * 0.05, 1.0) };
  });
  return scored.filter(l => l.match_score > 0).sort((a, b) => b.match_score - a.match_score).slice(0, limit);
}

/** Memories recalled >= threshold but no lesson yet */
export function getLessonCandidates() {
  const log = getLog();
  const lessonMids = new Set(getLessons().map(l => l.memory_id).filter(Boolean));
  return Object.entries(log).filter(([id]) => !lessonMids.has(id))
    .map(([memory_id, e]) => ({ memory_id, recall_count: e.recall_count, last_recall: e.last_recall }))
    .filter(c => c.recall_count >= LESSON_CANDIDATE_THRESHOLD)
    .sort((a, b) => b.recall_count - a.recall_count);
}

export function lessonStats() {
  const lessons = getLessons(), log = getLog();
  const totalRecalls = Object.values(log).reduce((s, e) => s + (e.recall_count ?? 0), 0);
  const tagCounts = {}; for (const l of lessons) for (const t of l.tags ?? []) tagCounts[t] = (tagCounts[t] ?? 0) + 1;
  const topTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([tag, count]) => ({ tag, count }));
  const rc = lessons.map(l => l.recall_count ?? 0);
  return {
    total_lessons: lessons.length, total_recalls: totalRecalls, top_tags: topTags,
    lesson_candidates: getLessonCandidates().length,
    by_recall: { total: lessons.length, never_recalled: rc.filter(c => c === 0).length,
      one_to_five: rc.filter(c => c >= 1 && c <= 5).length, six_to_ten: rc.filter(c => c >= 6 && c <= 10).length, above_ten: rc.filter(c => c > 10).length, total_recalls: totalRecalls },
  };
}

export function memoryLessonsTool({ action, memory_id, title, body, tags, query, lesson_id, limit, tag } = {}) {
  try {
    switch (action) {
      case 'extract':    if (!title || !body) throw new Error('title and body required'); return { content: [{ type: 'text', text: JSON.stringify(extractLesson(memory_id, title, body, tags ?? []), null, 2) }] };
      case 'recall':     if (!query) throw new Error('query required'); const r = recallLessons(query, { limit: limit ?? 5 }); r.forEach(l => touchLesson(l.id)); return { content: [{ type: 'text', text: JSON.stringify({ count: r.length, lessons: r }, null, 2) }] };
      case 'list':       return { content: [{ type: 'text', text: JSON.stringify({ count: listLessons({ limit: limit ?? 50, tag }).length, lessons: listLessons({ limit: limit ?? 50, tag }) }, null, 2) }] };
      case 'stats':      return { content: [{ type: 'text', text: JSON.stringify({ ...lessonStats(), top_candidates: getLessonCandidates().slice(0, 5) }, null, 2) }] };
      case 'delete':     if (!lesson_id) throw new Error('lesson_id required'); return { content: [{ type: 'text', text: JSON.stringify(deleteLesson(lesson_id), null, 2) }] };
      case 'touch':      if (!lesson_id) throw new Error('lesson_id required'); touchLesson(lesson_id); return { content: [{ type: 'text', text: JSON.stringify({ success: true }) }] };
      case 'candidates': return { content: [{ type: 'text', text: JSON.stringify({ count: getLessonCandidates().length, candidates: getLessonCandidates() }, null, 2) }] };
      default:           return { content: [{ type: 'text', text: JSON.stringify({ error: `Unknown action: ${action}`, hint: 'extract/recall/list/stats/delete/touch/candidates' }, null, 2) }], isError: true };
    }
  } catch (err) { return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true }; }
}

export default { recordRecall, getAccessStats, extractLesson, touchLesson, deleteLesson, listLessons, recallLessons, getLessonCandidates, lessonStats, memoryLessonsTool };
