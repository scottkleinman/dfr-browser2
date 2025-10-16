# Error Handling & Data Validation

This document describes the comprehensive error handling and data validation system implemented in DFR Browser 2.

## Overview

The error handling system provides:

- **User-friendly error messages** with detailed information
- **Data validation** to ensure file integrity
- **Recovery suggestions** to help users fix issues
- **Graceful degradation** when optional features fail

## Components

### 1. Error Handler (`error-handler.js`)

The ErrorHandler module provides centralized error management with user-friendly modals.

#### Error Types

- **FILE_NOT_FOUND**: Missing data files
- **PARSE_ERROR**: Invalid file format or corrupted data
- **VALIDATION_ERROR**: Data doesn't meet requirements
- **NETWORK_ERROR**: Connection or server issues
- **CACHE_ERROR**: IndexedDB problems
- **CONFIG_ERROR**: Invalid configuration
- **INTEGRITY_ERROR**: Inconsistent data across files

#### Usage

```javascript
import ErrorHandler from './error-handler.js';

// Show file error
ErrorHandler.handleFileError('data.csv', error, 'metadata file');

// Show parse error
ErrorHandler.handleParseError('topic-keys.txt', error, 42);

// Show validation error
ErrorHandler.handleValidationError(
  'Invalid data format',
  'Topic count mismatch',
  ['Check file format', 'Re-export from MALLET']
);

// Show custom error
ErrorHandler.showError(
  'PARSE_ERROR',
  'Could not parse data',
  'Line 42: Invalid format',
  ['Fix the file', 'Contact support']
);
```

### 2. Data Validator (`data-validator.js`)

The DataValidator module validates all data files and checks for integrity issues.

#### Validation Functions

##### validateTopicKeys(topicKeys, filename)

Validates topic keys data structure:

- Checks for empty data
- Validates required fields (id, words)
- Detects duplicate topic IDs
- Warns about topics with no words

##### validateDocTopics(docTopics, filename)

Validates document-topic distributions:

- Checks for empty data
- Validates array structure
- Checks if proportions sum to 1.0
- Warns about documents with no assignments

##### validateMetadata(metadata, filename)

Validates metadata CSV:

- Checks for required fields (id)
- Warns about missing recommended fields (title, author, date)
- Reports empty critical fields
- Calculates metadata completeness

##### validateDataIntegrity(topicKeys, docTopics, metadata)

Validates consistency across files:

- Checks topic count matches across files
- Checks document count consistency
- Validates data completeness
- Ensures files are from same MALLET run

##### validateAll(topicKeys, docTopics, metadata)

Comprehensive validation of all data:

- Runs all individual validations
- Runs integrity check
- Returns detailed validation results

#### Validation Usage

```javascript
import DataValidator from './data-validator.js';

// Validate all data
const results = await DataValidator.validateAll(
  topicKeys,
  docTopics,
  metadata
);

if (results.topicKeys.valid) {
  console.log('Topic keys valid');
} else {
  console.error('Errors:', results.topicKeys.errors);
}

// Get data quality report
const report = DataValidator.getDataQualityReport(
  topicKeys,
  docTopics,
  metadata
);
console.log('Quality:', report);
```

#### Quality Report Structure

```javascript
{
  summary: {
    topics: 100,
    documents: 5000,
    metadataRecords: 5000
  },
  completeness: {
    topicWords: 1.0,          // 100% of topics have words
    documentAssignments: 0.98, // 98% of docs have assignments
    metadataFields: {
      id: '100%',
      title: '98.5%',
      author: '95.2%',
      date: '87.3%'
    }
  },
  issues: {
    emptyTopics: 0,
    emptyDocuments: 100,
    missingTitles: 75,
    missingDates: 635
  }
}
```

## Integration

### In main.js

Error handling is integrated into all data loading operations:

```javascript
// Config loading with error handling
try {
  const response = await fetch('/config.json');
  config = JSON.parse(await response.text());
} catch (error) {
  ErrorHandler.handleConfigError('Invalid config.json', error.message);
}

// Data loading with validation
const results = await Promise.all([
  CachedDataLoader.loadTopicKeys(path, parser).catch(err => {
    ErrorHandler.handleFileError(path, err, 'topic keys');
    throw err;
  }),
  // ... other files
]);

// Validate loaded data
const validation = await DataValidator.validateAll(
  topicKeys,
  docTopics,
  metadata
);

if (!validation.integrity.valid) {
  // Errors already shown to user
  return;
}
```

### In CachedDataLoader

Cache errors are handled gracefully:

```javascript
try {
  const cached = await CacheManager.get(store, key, version);
  if (cached) return cached.data;
} catch (err) {
  console.warn('[Cache] Retrieval failed:', err);
  // Continue with file loading
}
```

## Error Modal

The error modal provides:

- **Color-coded alerts** (danger, warning, info)
- **Detailed error information** in expandable sections
- **Helpful suggestions** with actionable steps
- **Retry button** when appropriate
- **Console logging** for debugging

## Best Practices

### For Developers

1. **Always use ErrorHandler** for user-facing errors
2. **Validate data** after loading, before processing
3. **Provide specific suggestions** tailored to the error
4. **Log to console** for debugging (ErrorHandler does this automatically)
5. **Graceful degradation** - continue with limited functionality when possible

### Error Message Guidelines

1. **Be specific** - "Topic keys file not found" vs "Error"
2. **Explain impact** - "Some features may be unavailable"
3. **Provide solutions** - "Check that file exists at..."
4. **Use technical details** only in expandable sections
5. **Test error paths** to ensure helpful messages

## Common Error Scenarios

### Missing Files

```txt
Error: FILE_NOT_FOUND
Message: Could not load topic keys file: sample_data/topic-keys.txt
Suggestions:
- Check that sample_data/topic-keys.txt exists
- Verify file path in config.json is correct
- Make sure server is running
```

### Invalid Format

```txt
Error: PARSE_ERROR
Message: Error parsing doc-topics.txt at line 42
Details: Unexpected token ','
Suggestions:
- Check file is properly formatted
- Verify file encoding is UTF-8
- Try re-exporting from MALLET
```

### Data Mismatch

```txt
Error: INTEGRITY_ERROR
Message: Data integrity check failed
Details: Topic count mismatch: topic-keys has 100 topics,
         but doc-topics has 50 topics per document
Suggestions:
- Ensure all files are from same MALLET run
- Re-export all data files together
```

## Testing

Test error handling by:

1. **Missing files** - Remove a required file
2. **Invalid JSON** - Corrupt config.json
3. **Malformed data** - Edit data files with errors
4. **Mismatched data** - Use files from different MALLET runs
5. **Network errors** - Disconnect network during load

## Future Enhancements

Potential improvements:

- Automatic error recovery attempts
- Upload corrected files without reload
- Export error reports
- Integration with external error tracking
- More granular validation rules
- Custom validation rules from config
