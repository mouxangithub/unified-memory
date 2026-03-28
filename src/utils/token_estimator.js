/**
 * token_estimator.js - Lightweight token estimation without external dependencies
 * 
 * Estimates token count using character-based approximation.
 * This is a rough approximation - real tokenizers (tiktoken, cl100k) would be
 * more accurate but require additional dependencies.
 * 
 * Formula:
 * - English: tokens ≈ ceil(chars / 4)
 * - Chinese: tokens ≈ chars / 2
 * - Mixed: weighted blend
 */

const LOWER_CHARS = /[a-z]/g;
const UPPER_CHARS = /[A-Z]/g;
const DIGIT_CHARS = /[0-9]/g;
const CHINESE_CHARS = /[\u4e00-\u9fff]/g;
const PUNCT_CHARS = /[.,!?;:'"()\[\]{}—–-]/g;
const WHITESPACE_CHARS = /[\s\n\r\t]/g;

/**
 * Count characters by category in a string
 * @param {string} text
 * @returns {Object} character counts by category
 */
export function countChars(text) {
  if (!text || typeof text !== 'string') {
    return { total: 0, lower: 0, upper: 0, digits: 0, chinese: 0, punctuation: 0, whitespace: 0, other: 0 };
  }

  const chars = text.split('');
  const counts = {
    total: chars.length,
    lower: 0,
    upper: 0,
    digits: 0,
    chinese: 0,
    punctuation: 0,
    whitespace: 0,
    other: 0,
  };

  for (const char of chars) {
    if (/[a-z]/.test(char)) counts.lower++;
    else if (/[A-Z]/.test(char)) counts.upper++;
    else if (/[0-9]/.test(char)) counts.digits++;
    else if (/[\u4e00-\u9fff]/.test(char)) counts.chinese++;
    else if (/[.,!?;:'"()\[\]{}—–-]/.test(char)) counts.punctuation++;
    else if (/[\s\n\r\t]/.test(char)) counts.whitespace++;
    else counts.other++;
  }

  return counts;
}

/**
 * Estimate tokens using simple approximation
 * 
 * This approach assumes:
 * - ASCII/Latin text: ~4 chars per token (English, etc.)
 * - CJK text: ~2 chars per token (Chinese, Japanese, Korean)
 * - Mixed content: weighted blend
 * 
 * @param {string} text
 * @returns {number} estimated token count
 */
export function estimateTokens(text) {
  if (!text || typeof text !== 'string' || text.length === 0) {
    return 0;
  }

  const counts = countChars(text);
  const { total, lower, upper, digits, chinese, punctuation, whitespace } = counts;

  // English chars (a-z, A-Z, digits)
  const englishChars = lower + upper + digits;

  // Non-english printable chars
  const otherPrintable = chinese + punctuation;

  // Whitespace separator overhead - spaces add ~1 token per word
  // Average English word ~5 chars + 1 space = ~6 chars per word
  // But we already count whitespace, so reduce weight

  if (total === 0) return 0;

  // English approximation: ~4 chars per token (including overhead)
  const englishTokens = Math.ceil(englishChars / 4);

  // Chinese approximation: ~2 chars per token
  const chineseTokens = Math.ceil(chinese / 2);

  // Punctuation and whitespace contribute ~0.5 tokens each
  const otherTokens = Math.ceil((punctuation + whitespace) / 2);

  const totalTokens = englishTokens + chineseTokens + otherTokens;

  // Round up to be safe (over-estimate is safer than under-estimate for budgets)
  return Math.max(1, totalTokens);
}

/**
 * Estimate tokens using a simpler, faster formula
 * Good enough for budget calculations where precision isn't critical
 * 
 * @param {string} text
 * @returns {number}
 */
export function estimateTokensSimple(text) {
  if (!text || typeof text !== 'string') return 0;
  const len = text.length;
  if (len === 0) return 0;

  // Count Chinese chars
  const chineseMatches = text.match(CHINESE_CHARS);
  const chineseCount = chineseMatches ? chineseMatches.length : 0;
  const nonChineseCount = len - chineseCount;

  // English: ceil(chars / 4), Chinese: ceil(chars / 2)
  return Math.ceil(nonChineseCount / 4) + Math.ceil(chineseCount / 2);
}

/**
 * Estimate tokens from an array of memories
 * @param {Array} memories - array of memory objects with text field
 * @returns {number} total estimated tokens
 */
export function estimateMemoriesTokens(memories) {
  if (!Array.isArray(memories)) return 0;
  return memories.reduce((sum, m) => {
    const text = m.text || m.content || '';
    return sum + estimateTokensSimple(text);
  }, 0);
}

/**
 * Estimate tokens from a search query
 * Queries are typically short - use simple estimation
 * @param {string} query
 * @returns {number}
 */
export function estimateQueryTokens(query) {
  return estimateTokensSimple(query || '');
}
