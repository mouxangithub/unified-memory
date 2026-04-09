# Test Directory

This directory contains the test scripts for unified-memory.

## Core Test Files

| File | Description |
|------|-------------|
| `test_enhanced_system.js` | Complete test for Enhanced Memory System |
| `test_openviking_system.js` | Complete test for OpenViking integration |
| `test_integration_v270.js` | Integration test for v2.7.0 |
| `verify_system.js` | System verification script |

## Running Tests

```bash
# Run enhanced system tests
node test/test_enhanced_system.js

# Run OpenViking system tests
node test/test_openviking_system.js

# Verify system
node test/verify_system.js
```

## Notes

- All test files use anonymized example data (no real user information)
- Tests are designed to run independently without external dependencies
- The `test_report.json` contains the latest test results
