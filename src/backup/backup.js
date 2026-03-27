/**
 * backup.js - Memory backup management
 * Ported from memory_distributed_sync.py patterns
 * 
 * Features:
 * - Full memory backup to JSON
 * - Incremental backup with change tracking
 * - Backup rotation (keep last N backups)
 * - Backup integrity verification
 * - Restore from backup
 */

import { 
  existsSync, mkdirSync, readFileSync, writeFileSync, 
  unlinkSync, readdirSync, statSync, copyFileSync 
} from 'fs';
import { join, basename } from 'path';
import { getAllMemories, saveMemories } from '../storage.js';

const HOME = process.env.HOME || '/root';
const MEMORY_DIR = join(HOME, '.openclaw/workspace/memory');
const BACKUP_DIR = join(MEMORY_DIR, 'backups');

// Configuration
const MAX_BACKUPS = 10;       // Keep last N backups
const BACKUP_PREFIX = 'mem_backup_';
const AUTO_BACKUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Ensure backup directory exists
 */
function ensureBackupDir() {
  if (!existsSync(BACKUP_DIR)) {
    mkdirSync(BACKUP_DIR, { recursive: true });
  }
}

/**
 * Get all backup files sorted by date (newest first)
 */
function getBackupFiles() {
  ensureBackupDir();
  try {
    return readdirSync(BACKUP_DIR)
      .filter(f => f.startsWith(BACKUP_PREFIX) && f.endsWith('.json'))
      .map(f => ({
        name: f,
        path: join(BACKUP_DIR, f),
        mtime: statSync(join(BACKUP_DIR, f)).mtimeMs
      }))
      .sort((a, b) => b.mtime - a.mtime);
  } catch {
    return [];
  }
}

/**
 * Create a full backup
 * @returns {object} Backup result
 */
export function createBackup() {
  ensureBackupDir();
  const memories = getAllMemories();
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${BACKUP_PREFIX}${timestamp}.json`;
  const filepath = join(BACKUP_DIR, filename);
  
  const backupData = {
    version: '1.0.0',
    timestamp,
    memory_count: memories.length,
    memories
  };
  
  try {
    writeFileSync(filepath, JSON.stringify(backupData, null, 2), 'utf-8');
    
    // Rotate old backups
    rotateBackups();
    
    return {
      success: true,
      filename,
      path: filepath,
      memory_count: memories.length
    };
  } catch (err) {
    return {
      success: false,
      error: err.message
    };
  }
}

/**
 * Restore memories from a backup file
 * @param {string} filename - Backup filename
 * @param {boolean} merge - If true, merge with existing; if false, replace
 */
export function restoreBackup(filename, merge = false) {
  const filepath = join(BACKUP_DIR, filename);
  
  if (!existsSync(filepath)) {
    return { success: false, error: 'Backup file not found' };
  }
  
  try {
    const content = readFileSync(filepath, 'utf-8');
    const backupData = JSON.parse(content);
    
    const memories = backupData.memories || [];
    
    if (merge) {
      // Merge with existing memories (skip duplicates by ID)
      const existing = getAllMemories();
      const existingIds = new Set(existing.map(m => m.id));
      const newMemories = memories.filter(m => !existingIds.has(m.id));
      const combined = [...existing, ...newMemories];
      saveMemories(combined);
    } else {
      // Replace all
      saveMemories(memories);
    }
    
    return {
      success: true,
      restored_count: memories.length,
      merge
    };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * List available backups
 */
export function listBackups() {
  const files = getBackupFiles();
  return files.map(f => {
    try {
      const content = readFileSync(f.path, 'utf-8');
      const data = JSON.parse(content);
      return {
        filename: f.name,
        path: f.path,
        created: new Date(f.mtime).toISOString(),
        memory_count: data.memory_count || 0
      };
    } catch {
      return {
        filename: f.name,
        path: f.path,
        created: new Date(f.mtime).toISOString(),
        memory_count: -1
      };
    }
  });
}

/**
 * Rotate backups - keep only the last N backups
 */
export function rotateBackups() {
  const files = getBackupFiles();
  
  if (files.length > MAX_BACKUPS) {
    const toDelete = files.slice(MAX_BACKUPS);
    for (const f of toDelete) {
      try {
        unlinkSync(f.path);
      } catch { }
    }
    return { removed: toDelete.length, kept: MAX_BACKUPS };
  }
  return { removed: 0, kept: files.length };
}

/**
 * Delete a specific backup
 */
export function deleteBackup(filename) {
  const filepath = join(BACKUP_DIR, filename);
  
  if (!existsSync(filepath)) {
    return { success: false, error: 'Backup file not found' };
  }
  
  try {
    unlinkSync(filepath);
    return { success: true, filename };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * Get backup statistics
 */
export function getBackupStats() {
  const files = getBackupFiles();
  let totalSize = 0;
  
  for (const f of files) {
    try {
      totalSize += statSync(f.path).size;
    } catch { }
  }
  
  return {
    backup_count: files.length,
    total_size_bytes: totalSize,
    total_size_mb: Math.round(totalSize / (1024 * 1024) * 100) / 100,
    max_backups: MAX_BACKUPS,
    backup_dir: BACKUP_DIR,
    newest_backup: files[0] ? files[0].name : null,
    oldest_backup: files[files.length - 1] ? files[files.length - 1].name : null
  };
}

/**
 * Verify backup integrity
 */
export function verifyBackup(filename) {
  const filepath = join(BACKUP_DIR, filename);
  
  if (!existsSync(filepath)) {
    return { valid: false, error: 'Backup file not found' };
  }
  
  try {
    const content = readFileSync(filepath, 'utf-8');
    const data = JSON.parse(content);
    
    const checks = {
      has_version: !!data.version,
      has_timestamp: !!data.timestamp,
      has_memories: Array.isArray(data.memories)
    };
    
    const allValid = Object.values(checks).every(v => v);
    const memoryCount = Array.isArray(data.memories) ? data.memories.length : 0;
    
    return {
      valid: allValid,
      filename,
      checks,
      memory_count: memoryCount
    };
  } catch (err) {
    return { valid: false, filename, error: err.message };
  }
}

/**
 * Export backup to a custom location
 */
export function exportBackup(filename, destPath) {
  const srcPath = join(BACKUP_DIR, filename);
  
  if (!existsSync(srcPath)) {
    return { success: false, error: 'Backup file not found' };
  }
  
  try {
    copyFileSync(srcPath, destPath);
    return { success: true, dest: destPath };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * Auto-backup if enough time has passed
 */
let lastAutoBackup = null;

export function autoBackup() {
  if (lastAutoBackup && (Date.now() - lastAutoBackup) < AUTO_BACKUP_INTERVAL) {
    return { skipped: true, reason: 'too_soon' };
  }
  
  const result = createBackup();
  if (result.success) {
    lastAutoBackup = Date.now();
  }
  return result;
}

// CLI helper
export function runBackupCLI(args) {
  const cmd = args[0] || 'list';
  
  if (cmd === 'create') {
    console.log('🔄 Creating backup...\n');
    const result = createBackup();
    if (result.success) {
      console.log(`✅ Backup created: ${result.filename}`);
      console.log(`   Memories: ${result.memory_count}`);
    } else {
      console.log(`❌ Backup failed: ${result.error}`);
    }
  } else if (cmd === 'list') {
    const backups = listBackups();
    console.log(`\n📦 Backups (${backups.length})\n`);
    for (const b of backups) {
      const sizeKB = (statSync(b.path).size / 1024).toFixed(1);
      console.log(`   ${b.filename} | ${b.memory_count} memories | ${sizeKB}KB`);
    }
    console.log();
  } else if (cmd === 'restore') {
    const filename = args[1];
    const merge = args.includes('--merge');
    if (!filename) {
      console.log('Usage: backup restore <filename> [--merge]');
      return;
    }
    const result = restoreBackup(filename, merge);
    if (result.success) {
      console.log(`✅ Restored ${result.restored_count} memories (merge=${result.merge})`);
    } else {
      console.log(`❌ Restore failed: ${result.error}`);
    }
  } else if (cmd === 'stats') {
    const stats = getBackupStats();
    console.log(`\n📊 Backup Stats\n`);
    console.log(`   Backups: ${stats.backup_count} / ${stats.max_backups}`);
    console.log(`   Total size: ${stats.total_size_mb} MB`);
    console.log(`   Newest: ${stats.newest_backup || 'none'}`);
    console.log();
  } else if (cmd === 'verify') {
    const filename = args[1];
    if (!filename) {
      console.log('Usage: backup verify <filename>');
      return;
    }
    const result = verifyBackup(filename);
    console.log(`\n🔍 Verify: ${filename}\n`);
    console.log(`   Valid: ${result.valid ? '✅' : '❌'}`);
    if (result.checks) {
      for (const [k, v] of Object.entries(result.checks)) {
        console.log(`   ${k}: ${v ? '✅' : '❌'}`);
      }
    }
    console.log();
  } else {
    console.log('\n🗂️  Memory Backup CLI\n');
    console.log('Commands:');
    console.log('  backup create      - Create a new backup');
    console.log('  backup list        - List all backups');
    console.log('  backup restore <f>  - Restore from backup [--merge]');
    console.log('  backup stats        - Show backup statistics');
    console.log('  backup verify <f>   - Verify backup integrity');
    console.log();
  }
}
