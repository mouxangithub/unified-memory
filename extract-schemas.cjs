const fs = require('fs');
const path = require('path');

const src = fs.readFileSync('/root/.openclaw/workspace/skills/unified-memory/src/index.js', 'utf8');

// Find all tool registrations
const toolRegex = /server\.registerTool\('([^']+)',\s*\{[\s\S]*?inputSchema:\s*z\.object\(\{([\s\S]*?)\)\}/g;
let match;
const tools = {};

while ((match = toolRegex.exec(src)) !== null) {
  const toolName = match[1];
  const fieldsBlock = match[2];
  
  // Extract field names and their types
  const fieldRegex = /(\w+):\s*(?:z\.\w+(?:\([^)]*\))?(?:\.optional\(\))?(?:\.default\([^)]*\))?|\w+\s*\?)/g;
  const fields = [];
  let fmatch;
  while ((fmatch = fieldRegex.exec(fieldsBlock)) !== null) {
    fields.push(fmatch[1]);
  }
  tools[toolName] = fields;
}

console.log(JSON.stringify(tools, null, 2));
