/**
 * FAISS Index - Python Implementation [NOT PORTABLE]
 * 
 * ⚠️  FAISS (Facebook AI Similarity Search) is a C++ library.
 * It CANNOT be directly used in Node.js.
 * 
 * Recommended alternatives for Node.js:
 * 1. LanceDB (RECOMMENDED)
 * 2. sqlite-vec (OpenClaw built-in)
 * 3. Qdrant (external service)
 */

export const FAISS_NOTICE = `
⚠️  FAISS NOT PORTABLE TO NODE.JS

FAISS is a C++ library with Python bindings only.

Recommended Node.js alternatives:

1. LanceDB (Recommended)
   - npm install vectordb

2. sqlite-vec (OpenClaw built-in)
   - Automatic via OpenClaw

3. Cloud services (Qdrant, Weaviate, Pinecone)
   - Require external service
`;

export function printFaissNotice() {
  console.log(FAISS_NOTICE);
}

if (require.main === module) {
  printFaissNotice();
}
