# DFR-Browser Data Preparation

This directory contains scripts for preparing topic modeling data for use with dfr-browser.

## Quick Start

If you have a MALLET topic-state file, use the unified script:

```bash
# Generate all dfr-browser files from MALLET state file
python3 prepare_dfr_data.py topic-state.gz

# Generate files in a specific directory
python3 prepare_dfr_data.py topic-state.gz -o sample_data

# Generate only core files (faster, smaller)
python3 prepare_dfr_data.py topic-state.gz --core-only
```

## Unified Script: `prepare_dfr_data.py`

**Recommended approach** - Combines functionality from all the individual scripts below.

### What it does

- Processes a MALLET topic-state file in one pass
- Generates all necessary files for dfr-browser
- Much faster than running multiple scripts
- Handles all edge cases and data validation

### Generated Files

**Core files (always created):**

- `topic-keys.txt` - Topic words for dfr-browser navigation
- `doc-topic.txt` - Document-topic proportions for topic analysis
- `doc-lengths.txt` - Real token counts per document (extracted from state file)
- `metadata.csv` - Basic document metadata (if not already present)

**Additional files (with `--all`, default):**

- `doc-topic-counts.csv` - Raw topic counts per document for analysis
- `tw.json` - Topic-words JSON for advanced features
- `dt.zip` - Sparse document-topic matrix for advanced features

### Usage Examples

```bash
# Basic usage - generate all files in current directory
python3 prepare_dfr_data.py topic-state.gz

# Specify output directory
python3 prepare_dfr_data.py topic-state.gz -o my_data/

# Generate only essential files (faster, smaller output)
python3 prepare_dfr_data.py topic-state.gz --core-only

# Include more words per topic (default: 30)
python3 prepare_dfr_data.py topic-state.gz --top-words 50

# Help and full options
python3 prepare_dfr_data.py --help
```

## Individual Scripts (Legacy)

These scripts are kept for compatibility but **prepare_dfr_data.py is recommended** instead.

### `convert_state.py`

Original script that converts MALLET state files to tw.json and dt.zip formats.

```bash
python3 convert_state.py topic-state.gz tw.json dt.zip 30
```

### `extract_doc_topic_counts.py`

Extracts raw document-topic counts (not proportions) to CSV format.

```bash
python3 extract_doc_topic_counts.py topic-state.gz doc-topic-counts.csv
```

### `extract_doc_lengths.py`

Extracts real token counts per document from the topic-state file.

```bash
python3 extract_doc_lengths.py  # Uses topic-state.gz, outputs doc-lengths.txt
```

## Why Use the Unified Script?

1. **Efficiency**: Reads the large topic-state file only once instead of 3 times
2. **Consistency**: All outputs use the same data parsing, avoiding mismatches
3. **Convenience**: One command generates all needed files
4. **Accuracy**: Uses real token counts from MALLET state data, not estimates
5. **Validation**: Built-in data validation and error checking
6. **Flexibility**: Core-only mode for faster processing

## File Format Details

### topic-keys.txt

```csv
0	1.0	word1 word2 word3 word4 word5...
1	1.0	word1 word2 word3 word4 word5...
```

### doc-topic.txt

```csv
0	doc1	0.1234567890	0.0000000000	0.2345678901...
1	doc2	0.0000000000	0.3456789012	0.1234567890...
```

### doc-lengths.txt

```csv
docId,tokenCount
0,27
1,8
2,16
```

### metadata.csv

```csv
docNum,docName,title,author,year
0,doc1,Document 1,Unknown,2024
1,doc2,Document 2,Unknown,2024
```

## Troubleshooting

**File not found errors**: Make sure your topic-state file path is correct and the file exists.

**Memory errors**: For very large datasets, use `--core-only` to reduce memory usage.

**Permission errors**: Make sure you have write access to the output directory.

**Inconsistent results**: Always use the unified script instead of mixing individual scripts, to ensure all files are generated from the same data parsing.
