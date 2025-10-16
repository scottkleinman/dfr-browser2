# Topic Customization Guide

DFR Browser 2 provides flexible configuration options for customizing topic display and metadata field mappings.

## Features

### 1. Custom Topic Labels

Override default topic numbering with meaningful labels.

### 2. Hidden Topics

Hide specific topics from all views (Overview, Word Index, etc.).

### 3. Metadata Field Mappings

Map custom metadata field names to the internal field names used by the application.

## Configuration

All customization is done in `config.json`.

### Custom Topic Labels

Define custom labels for specific topics in the `topics.labels` object. Topics are indexed starting from 0.

```json
{
  "topics": {
    "labels": {
      "0": "Education & Schools",
      "1": "Healthcare System",
      "5": "Economic Policy",
      "12": "Environmental Issues"
    }
  }
}
```

**How it works:**

- Topics without custom labels display as "Topic N" (e.g., "Topic 2", "Topic 3")
- Topics with custom labels display the custom text everywhere in the UI
- Custom labels appear in: Overview (all modes), Topic view headers, Word view, and Document view

### Hidden Topics

Hide topics from display by adding their indices (0-based) to the `topics.hidden` array.

```json
{
  "topics": {
    "hidden": [3, 7, 15]
  }
}
```

**How it works:**

- Hidden topics are filtered from all Overview visualizations (Grid, Scaled, List, Stacked)
- Users can toggle visibility via the Settings modal
- The `showHiddenTopics` setting (default: false) controls this behavior
- When enabled, all topics are shown regardless of the hidden list

**Use cases:**

- Remove low-quality or incoherent topics
- Hide topics that are artifacts of the modeling process
- Focus analysis on topics of interest

### Metadata Field Mappings

Map non-standard metadata field names to the internal names expected by the application.

```json
{
  "metadata": {
    "fieldMappings": {
      "title": "article_title",
      "author": "creator",
      "year": "publication_year",
      "journal": "venue"
    }
  }
}
```

**How it works:**

- The application internally uses standard field names: `title`, `author`, `year`, `journal`, etc.
- If your metadata CSV uses different column names, map them here
- The application will automatically use the mapped names when accessing metadata

**Required fields** (must be mapped if using different names):

- `docNum` - Document number (0-based index)
- `docName` - Document identifier
- `title` - Document title
- `year` - Publication year

**Optional fields** (recommended for better display):

- `author` - Author name(s)
- `journal` - Publication venue
- `date` - Full publication date
- `volume`, `issue`, `pages` - Publication details
- `doi`, `url` - External links

**Example scenario:**

Your metadata CSV has these columns:

```csv
doc_index,doc_id,article_title,creator,pub_year,venue
0,doc1,Example Article,Smith J.,2020,Journal of Examples
```

Configure the mapping:

```json
{
  "metadata": {
    "fieldMappings": {
      "docNum": "doc_index",
      "docName": "doc_id",
      "title": "article_title",
      "author": "creator",
      "year": "pub_year",
      "journal": "venue"
    }
  }
}
```

Now the application will correctly access your metadata using the custom field names.

## Complete Configuration Example

```json
{
  "topics": {
    "labels": {
      "0": "Education & Schools",
      "1": "Healthcare System",
      "2": "Technology & Innovation",
      "5": "Economic Policy",
      "8": "Cultural Heritage",
      "12": "Environmental Issues"
    },
    "hidden": [3, 7, 15, 22]
  },
  "metadata": {
    "fieldMappings": {
      "title": "article_title",
      "author": "creator",
      "year": "publication_year",
      "journal": "venue",
      "docName": "document_id"
    }
  }
}
```

## Settings Modal

Users can control topic visibility through the Settings modal:

- **Show Hidden Topics**: Toggle to show/hide topics marked as hidden in the configuration
- Located in the navbar under "Settings"
- Changes take effect immediately (auto-reload)

## Validation

The application validates your topic configuration on load:

- **Duplicate labels**: Warns if multiple topics have the same label
- **Labeled and hidden**: Warns if a topic has both a custom label and is marked hidden
- Validation warnings appear in the browser console

## API Reference

For developers extending the application, the following functions are available in `topic-config.js`:

### `getTopicLabel(topicIndex)`

Returns the display label for a topic (0-based index).

```javascript
import { getTopicLabel } from './topic-config.js';

const label = getTopicLabel(0); // Returns "Education & Schools" or "Topic 1"
```

### `isTopicHidden(topicIndex)`

Checks if a topic should be hidden (respects user settings).

```javascript
import { isTopicHidden } from './topic-config.js';

if (!isTopicHidden(5)) {
  // Display topic 5
}
```

### `filterHiddenTopics(topics)`

Filters an array of topic objects to remove hidden topics.

```javascript
import { filterHiddenTopics } from './topic-config.js';

const visibleTopics = filterHiddenTopics(allTopics);
```

### `getMetadataValue(doc, internalField)`

Gets metadata value using field mapping.

```javascript
import { getMetadataValue } from './topic-config.js';

const title = getMetadataValue(doc, 'title'); // Uses mapped field name
```

## Best Practices

1. **Topic Labels**: Use concise, descriptive labels (3-7 words)
2. **Hidden Topics**: Document why topics are hidden (in comments or separate file)
3. **Field Mappings**: Map all fields used in your metadata, even if names match
4. **Testing**: After configuration changes, test all views (Overview, Topic, Document, Word)
5. **Version Control**: Track config.json changes to maintain configuration history

## Troubleshooting

**Custom labels not appearing:**

- Check that topic indices are 0-based (Topic 1 = index 0)
- Verify JSON syntax is correct (no trailing commas, proper quotes)
- Check browser console for validation warnings

**Hidden topics still showing:**

- Verify user hasn't enabled "Show Hidden Topics" in Settings
- Check Settings modal to confirm current setting
- Clear browser localStorage if needed: `localStorage.clear()`

**Metadata fields not found:**

- Verify CSV column names match your field mappings exactly (case-sensitive)
- Check that required fields (docNum, docName, title, year) are mapped
- Look for data validation warnings in browser console

## Future Enhancements

Potential future additions to topic customization:

- Color scheme customization per topic
- Topic grouping/categories
- Conditional hiding based on metrics
- Bulk topic label import from CSV
- Interactive configuration editor in UI
