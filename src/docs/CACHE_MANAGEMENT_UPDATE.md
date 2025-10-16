# Cache Management Update

## Overview

Enhanced the cache management system to allow users to clear individual caches from the Settings modal, instead of having to manually delete IndexedDB databases from the browser console.

## Changes Made

### 1. **cache-manager.js** - Added New Methods

#### `getCacheStats()`
Returns detailed statistics including:
- Total number of cached files
- Total cache size in bytes
- Per-store statistics (count and size)

```javascript
const stats = await CacheManager.getCacheStats();
// Returns: { totalFiles: 10, totalSize: 5242880, stores: {...} }
```

#### `clearStore(storeName)`
Clear a specific object store by name:
```javascript
await CacheManager.clearStore(CacheManager.stores.BIBLIOGRAPHY);
```

#### `clearAllStores()`
Clear all data from all object stores (alias for `clearAll()`):
```javascript
await CacheManager.clearAllStores();
```

#### `deleteDatabase(dbName)`
Completely delete an IndexedDB database:
```javascript
await CacheManager.deleteDatabase('dfr-browser-cache');
```

### 2. **main.js** - Updated Settings Modal

#### Added Individual Cache Clear Buttons

The Settings modal now includes buttons to clear:
- **Bibliography Cache** - Clear just bibliography data
- **Metadata Cache** - Clear just metadata
- **Topics Cache** - Clear topic keys and doc-topics data
- **Vocabulary Cache** - Clear vocabulary data
- **State Cache** - Clear MALLET state file data

Each button:
- Shows a confirmation dialog
- Clears only the specified cache
- Shows a success notification
- Updates cache statistics

#### Enhanced Cache Statistics Display

The cache stats now show:
- Total number of files cached
- Total cache size (formatted in KB/MB/GB)
- Per-store breakdown with count and size

#### New Functions

**Individual cache clear functions:**
```javascript
window.clearBibliographyCache()
window.clearMetadataCache()
window.clearTopicsCache()
window.clearVocabularyCache()
window.clearStateCache()
```

**Helper functions:**
```javascript
formatBytes(bytes) // Formats bytes to human-readable size
showSuccessAlert(message) // Shows dismissible success toast
```

**Updated:**
```javascript
window.refreshCacheStats() // Now shows detailed size information
```

## Usage

### For Users

1. **Open Settings** (click Settings in navigation)
2. **Scroll to Cache Management section**
3. **View cache statistics** - See what's cached and how much space it uses
4. **Clear individual caches** - Click the specific cache button you want to clear
5. **Clear all caches** - Use the "Clear All" button to remove everything

### For Developers

**Clear a specific cache programmatically:**
```javascript
import CacheManager from './cache-manager.js';

// Clear bibliography cache
await CacheManager.clearStore(CacheManager.stores.BIBLIOGRAPHY);

// Get detailed stats
const stats = await CacheManager.getCacheStats();
console.log(`Total size: ${stats.totalSize} bytes`);
```

**From console:**
```javascript
// Clear just bibliography
await clearBibliographyCache();

// Get stats
await refreshCacheStats();

// Delete entire database
const CacheManager = (await import('./js/cache-manager.js')).default;
await CacheManager.deleteDatabase();
```

## Benefits

1. ✅ **User-friendly** - No need to use browser DevTools
2. ✅ **Selective clearing** - Clear only what needs updating
3. ✅ **Visual feedback** - See what's cached and when it's cleared
4. ✅ **Size awareness** - Know how much space caches are using
5. ✅ **Confirmation dialogs** - Prevent accidental clearing
6. ✅ **Success notifications** - Know when operation completes

## Testing

1. Load some data (bibliography, topics, etc.)
2. Open Settings → Cache Management
3. Verify cache statistics show non-zero values
4. Click individual cache clear buttons
5. Verify stats update after clearing
6. Reload page and verify data reloads from server

## Files Modified

- `/dist/js/cache-manager.js` - Added new cache management methods
- `/dist/js/main.js` - Updated Settings modal and added clear functions

## Migration Notes

To transfer to dfr-browser folder:
1. Copy updated `cache-manager.js`
2. Copy updated `main.js`
3. Test in dfr-browser environment
4. Update documentation if needed
