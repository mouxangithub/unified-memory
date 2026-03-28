/**
 * preference_tools.js — MCP Tools for Preference Slots
 * Part of Feature #10: Structured Preference Slots
 * 
 * Implements MCP tools:
 * - memory_preference_get: Get one or all preferences
 * - memory_preference_set: Set a preference value
 * - memory_preference_infer: Infer preferences from recent conversation
 * - memory_preference_explain: Explain a preference's source and confidence
 */
import { loadPreferences, getSlotValue, getSlotEntry, updateSlotValue, persistPreferences, getSlotDefinition, getSlotNames } from '../preference_slots_schema.js';
import { extractPreferencesFromHistory, mergeExtractedPreferences } from '../preference_extractor.js';
import { getAllMemories } from '../storage.js';

/**
 * Tool: memory_preference_get
 * Get one preference slot or all preferences
 */
export function memoryPreferenceGetTool({ key } = {}) {
  try {
    const preferences = loadPreferences();
    
    if (key) {
      const entry = preferences[key];
      if (!entry) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: `Unknown slot: ${key}` }, null, 2) }], isError: true };
      }
      const def = getSlotDefinition(key);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            slot: key,
            value: entry.value,
            confidence: entry.confidence,
            source: entry.source,
            lastUpdated: new Date(entry.lastUpdated).toISOString(),
            definition: def,
          }, null, 2),
        }],
      };
    }
    
    // Return all
    const all = {};
    for (const [slotName, entry] of Object.entries(preferences)) {
      all[slotName] = {
        value: entry.value,
        confidence: entry.confidence,
        source: entry.source,
        lastUpdated: new Date(entry.lastUpdated).toISOString(),
      };
    }
    return { content: [{ type: 'text', text: JSON.stringify({ success: true, count: Object.keys(all).length, preferences: all }, null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_preference_set
 * Set a preference slot value
 */
export function memoryPreferenceSetTool({ key, value, confidence, source }) {
  try {
    if (!key) throw new Error('key is required');
    if (value === undefined || value === null) throw new Error('value is required');
    
    const preferences = loadPreferences();
    const def = getSlotDefinition(key);
    
    // Validate options if defined
    if (def?.options && !def.options.includes(value)) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ error: `Invalid value '${value}'. Options: ${def.options.join(', ')}` }, null, 2) }],
        isError: true,
      };
    }
    
    // Validate array type
    if (def?.type === 'array') {
      if (!Array.isArray(value)) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: `Value for '${key}' must be an array` }, null, 2) }], isError: true };
      }
    }
    
    const conf = confidence !== undefined ? parseFloat(confidence) : 0.9;
    const src = source || 'explicit';
    
    preferences[key] = {
      value,
      confidence: Math.min(1, Math.max(0, conf)),
      source: src,
      lastUpdated: Date.now(),
    };
    
    persistPreferences(preferences);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          slot: key,
          value,
          confidence: conf,
          source: src,
          lastUpdated: new Date().toISOString(),
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_preference_infer
 * Analyze recent memories to infer preferences
 */
export function memoryPreferenceInferTool({ messageCount = 20 } = {}) {
  try {
    // Get recent conversation memories
    const allMemories = getAllMemories();
    const recentMemories = allMemories
      .filter(m => m.category === 'conversation' || m.text)
      .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
      .slice(0, messageCount);
    
    if (recentMemories.length === 0) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ message: 'No conversation history found to analyze', inferred: {} }, null, 2) }],
      };
    }
    
    const extracted = extractPreferencesFromHistory(recentMemories);
    const currentPrefs = loadPreferences();
    const merged = mergeExtractedPreferences(currentPrefs, extracted);
    
    // Format results
    const inferred = {};
    for (const [slotName, entry] of Object.entries(extracted)) {
      inferred[slotName] = {
        value: entry.value,
        confidence: Math.round(entry.confidence * 100) / 100,
        source: entry.source,
        isNew: entry.confidence > (currentPrefs[slotName]?.confidence || 0),
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          messagesAnalyzed: recentMemories.length,
          inferred,
          merged: Object.keys(extracted).length,
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_preference_explain
 * Explain a preference's source and confidence reasoning
 */
export function memoryPreferenceExplainTool({ key } = {}) {
  try {
    if (!key) throw new Error('key is required');
    
    const preferences = loadPreferences();
    const entry = preferences[key];
    if (!entry) {
      return { content: [{ type: 'text', text: JSON.stringify({ error: `Unknown slot: ${key}` }, null, 2) }], isError: true };
    }
    
    const def = getSlotDefinition(key);
    
    // Build explanation
    const explanations = [];
    
    explanations.push(`**Slot**: ${key}`);
    explanations.push(`**Current Value**: ${JSON.stringify(entry.value)}`);
    explanations.push(`**Confidence**: ${Math.round(entry.confidence * 100)}%`);
    explanations.push(`**Source**: ${entry.source}`);
    explanations.push(`**Last Updated**: ${new Date(entry.lastUpdated).toLocaleString()}`);
    
    if (def) {
      explanations.push(`**Description**: ${def.description || 'No description'}`);
      if (def.options) {
        explanations.push(`**Valid Options**: ${def.options.join(', ')}`);
      }
    }
    
    // Confidence interpretation
    if (entry.confidence >= 0.8) {
      explanations.push(`**Interpretation**: High confidence — this preference is well-established.`);
    } else if (entry.confidence >= 0.6) {
      explanations.push(`**Interpretation**: Moderate confidence — derived from multiple observations.`);
    } else {
      explanations.push(`**Interpretation**: Low confidence — consider confirming with the user.`);
    }
    
    // Source interpretation
    if (entry.source === 'explicit') {
      explanations.push(`**Source Note**: User directly stated this preference.`);
    } else if (entry.source === 'inferred') {
      explanations.push(`**Source Note**: Automatically inferred from conversation patterns.`);
    } else {
      explanations.push(`**Source Note**: Set from historical defaults.`);
    }
    
    return {
      content: [{
        type: 'text',
        text: explanations.join('\n'),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

export default {
  memoryPreferenceGetTool,
  memoryPreferenceSetTool,
  memoryPreferenceInferTool,
  memoryPreferenceExplainTool,
};
