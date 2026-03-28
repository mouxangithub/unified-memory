/**
 * version_tools.js — MCP Tools for Memory Versioning
 * Part of Feature #11: Semantic Versioning
 * 
 * Implements MCP tools:
 * - memory_version_list: List versions for a memory
 * - memory_version_diff: Show diff between versions
 * - memory_rollback: Rollback a memory to a specific version
 */
import { getVersions, getVersion, getVersionCount, getVersionStats, createVersion } from '../version_store.js';
import { listVersions, compareAdjacentVersions, getVersionTimeline, createVersionDiff } from '../memory_diff.js';
import { rollback, undoLastChange, getRollbackCandidates, getRollbackPreview, clearVersionHistory } from '../rollback_manager.js';
import { getMemory, getAllMemories } from '../storage.js';

/**
 * Tool: memory_version_list
 * List versions for a memory
 */
export function memoryVersionListTool({ memoryId, limit, offset, changeType } = {}) {
  try {
    if (!memoryId) {
      // List all memories with versions
      const stats = getVersionStats();
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            totalMemories: stats.totalMemories,
            totalVersions: stats.totalVersions,
            memoriesWithVersions: stats.memoryCounts,
          }, null, 2),
        }],
      };
    }
    
    const result = listVersions(memoryId, { limit: limit || 10, offset: offset || 0, changeType });
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_version_diff
 * Show diff between two versions
 */
export function memoryVersionDiffTool({ memoryId, versionId1, versionId2 } = {}) {
  try {
    if (!memoryId) throw new Error('memoryId is required');
    if (!versionId1 && !versionId2) throw new Error('versionId1 or versionId2 is required');
    
    // If only one version, compare with previous
    if (!versionId2) {
      const result = compareAdjacentVersions(memoryId, versionId1);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(result, null, 2),
        }],
      };
    }
    
    // Compare two specific versions
    const result = createVersionDiff(memoryId, versionId1, versionId2);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_rollback
 * Rollback a memory to a specific version
 */
export function memoryRollbackTool({ memoryId, versionId, action, preview } = {}) {
  try {
    if (!memoryId) throw new Error('memoryId is required');
    
    const memory = getMemory(memoryId);
    if (!memory) {
      return { content: [{ type: 'text', text: JSON.stringify({ error: `Memory ${memoryId} not found` }, null, 2) }], isError: true };
    }
    
    // Preview mode
    if (preview) {
      const version = versionId ? getVersion(memoryId, versionId) : null;
      if (!version && versionId) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: `Version ${versionId} not found` }, null, 2) }], isError: true };
      }
      
      // Get latest version if not specified
      const targetVersion = version || getVersions(memoryId).pop();
      const previewData = getRollbackPreview(memoryId, targetVersion?.versionId);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            preview: true,
            ...previewData,
            hint: 'Set preview: false to actually perform rollback',
          }, null, 2),
        }],
      };
    }
    
    // Undo last change
    if (action === 'undo') {
      const result = undoLastChange(memoryId);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(result, null, 2),
        }],
      };
    }
    
    // Clear history
    if (action === 'clear') {
      const result = clearVersionHistory(memoryId);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(result, null, 2),
        }],
      };
    }
    
    // Version ID required for rollback
    if (!versionId) throw new Error('versionId is required for rollback');
    
    const result = rollback(memoryId, versionId);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

/**
 * Tool: memory_version_timeline
 * Get version timeline for a memory
 */
export function memoryVersionTimelineTool({ memoryId } = {}) {
  try {
    if (!memoryId) {
      const candidates = getRollbackCandidates();
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            candidates: candidates.slice(0, 10),
            total: candidates.length,
          }, null, 2),
        }],
      };
    }
    
    const timeline = getVersionTimeline(memoryId);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          memoryId,
          versions: timeline,
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
}

export default {
  memoryVersionListTool,
  memoryVersionDiffTool,
  memoryRollbackTool,
  memoryVersionTimelineTool,
};
