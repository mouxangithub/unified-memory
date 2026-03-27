/**
 * Connection Pool for unified-memory-ts
 * Manages reusable resources (DB connections, HTTP agents, etc.)
 */

export class Pool {
  constructor(factory, config = {}, validator, destroyer) {
    this.factory = factory;
    this.validator = validator;
    this.destroyer = destroyer;
    this.config = {
      min: config.min ?? 2,
      max: config.max ?? 10,
      acquireTimeout: config.acquireTimeout ?? 5000,
      idleTimeout: config.idleTimeout ?? 30000,
    };
    this.pool = [];
    this.waiting = [];
    this.closed = false;
    this.init();
  }
  
  async init() {
    for (let i = 0; i < this.config.min; i++) {
      const resource = await this.factory();
      this.pool.push({
        resource,
        createdAt: Date.now(),
        lastUsed: Date.now(),
        inUse: false,
      });
    }
  }
  
  async acquire() {
    if (this.closed) throw new Error('Pool is closed');
    
    const now = Date.now();
    for (const item of this.pool) {
      if (!item.inUse) {
        if (this.validator) {
          const valid = await this.validator(item.resource);
          if (!valid) {
            const idx = this.pool.indexOf(item);
            this.pool.splice(idx, 1);
            continue;
          }
        }
        item.inUse = true;
        item.lastUsed = now;
        return item.resource;
      }
    }
    
    if (this.pool.length < this.config.max) {
      const resource = await this.factory();
      const item = { resource, createdAt: now, lastUsed: now, inUse: true };
      this.pool.push(item);
      return item.resource;
    }
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        const idx = this.waiting.indexOf(resolve);
        if (idx !== -1) this.waiting.splice(idx, 1);
        reject(new Error('Pool acquire timeout'));
      }, this.config.acquireTimeout);
      
      this.waiting.push((resource) => {
        clearTimeout(timeout);
        resolve(resource);
      });
    });
  }
  
  release(resource) {
    const item = this.pool.find(p => p.resource === resource);
    if (!item) return;
    
    item.inUse = false;
    item.lastUsed = Date.now();
    
    if (this.waiting.length > 0) {
      const waiter = this.waiting.shift();
      item.inUse = true;
      item.lastUsed = Date.now();
      waiter(item.resource);
    }
  }
  
  async destroy(resource) {
    const idx = this.pool.findIndex(p => p.resource === resource);
    if (idx === -1) return;
    
    const item = this.pool[idx];
    this.pool.splice(idx, 1);
    
    if (this.destroyer) await this.destroyer(item.resource);
  }
  
  async clearIdle() {
    const now = Date.now();
    let cleared = 0;
    
    for (let i = this.pool.length - 1; i >= 0; i--) {
      const item = this.pool[i];
      if (!item.inUse && now - item.lastUsed > this.config.idleTimeout) {
        if (this.pool.length > this.config.min) {
          if (this.destroyer) await this.destroyer(item.resource);
          this.pool.splice(i, 1);
          cleared++;
        }
      }
    }
    return cleared;
  }
  
  async close() {
    this.closed = true;
    for (const item of this.pool) {
      if (this.destroyer) await this.destroyer(item.resource);
    }
    this.pool = [];
    this.waiting = [];
  }
  
  getStats() {
    return {
      total: this.pool.length,
      idle: this.pool.filter(p => !p.inUse).length,
      inUse: this.pool.filter(p => p.inUse).length,
      waiting: this.waiting.length,
    };
  }
}

const pools = new Map();

export function getPool(name, factory, config) {
  if (!pools.has(name)) {
    pools.set(name, new Pool(factory, config));
  }
  return pools.get(name);
}

export async function closeAllPools() {
  for (const pool of pools.values()) {
    await pool.close();
  }
  pools.clear();
}
