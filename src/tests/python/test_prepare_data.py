"""
Pytest test suite for prepare_data.py

Run with: pytest test_prepare_dfr_data.py -v
"""

import gzip
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bin"))

from prepare_data import (
    compute_mds,
    get_top_words_and_weights,
    jensen_shannon,
    jsd_matrix,
    normalize_doc_topic_proportions,
    process_mallet_state_file,
    sparse_doc_topic_matrix,
    topic_word_matrix_from_topic_words,
    write_basic_metadata_csv,
    write_doc_topic_counts_csv,
    write_doc_topic_txt,
    write_doc_topics_zip,
    write_topic_coords_csv,
    write_topic_keys_txt,
    write_topic_words_json,
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_topic_words():
    """Sample topic words data structure."""
    return [
        {
            "words": ["computer", "software", "program", "data", "system"],
            "weights": [100, 80, 60, 40, 20],
        },
        {
            "words": ["health", "medical", "patient", "doctor", "hospital"],
            "weights": [90, 70, 50, 30, 10],
        },
        {
            "words": ["economy", "market", "business", "trade", "finance"],
            "weights": [85, 65, 45, 25, 15],
        },
    ]


@pytest.fixture
def sample_doc_topic_counts():
    """Sample document-topic counts."""
    return [
        {0: 10, 1: 5, 2: 2},  # Doc 0
        {0: 3, 1: 15, 2: 1},  # Doc 1
        {0: 1, 1: 2, 2: 20},  # Doc 2
    ]


@pytest.fixture
def sample_state_file(temp_output_dir):
    """Create a minimal MALLET state file for testing."""
    state_file = os.path.join(temp_output_dir, "test-state.gz")

    with gzip.open(state_file, "wt") as f:
        # Header
        f.write("#doc source pos typeindex type topic\n")
        # Alpha line (3 topics)
        f.write("#alpha : 0.5 0.5 0.5\n")
        # Beta line
        f.write("#beta : 0.01\n")

        # Token lines
        # Doc 0: 10 tokens of topic 0, 5 of topic 1
        for i in range(10):
            f.write(f"0 doc1 {i} 0 computer 0\n")
        for i in range(5):
            f.write(f"0 doc1 {10 + i} 1 health 1\n")

        # Doc 1: 3 tokens of topic 0, 15 of topic 1
        for i in range(3):
            f.write(f"1 doc2 {i} 0 computer 0\n")
        for i in range(15):
            f.write(f"1 doc2 {3 + i} 1 health 1\n")

        # Doc 2: 1 token of topic 0, 20 of topic 2
        f.write("2 doc3 0 0 computer 0\n")
        for i in range(20):
            f.write(f"2 doc3 {1 + i} 2 economy 2\n")

    return state_file


# --- Test utility functions ---


def test_get_top_words_and_weights():
    """Test extraction of top words and weights."""
    word_counts = [10, 5, 20, 3, 15]
    vocab = {0: "word0", 1: "word1", 2: "word2", 3: "word3", 4: "word4"}

    result = get_top_words_and_weights(word_counts, vocab, 3)

    assert "words" in result
    assert "weights" in result
    assert len(result["words"]) == 3
    assert len(result["weights"]) == 3
    # Should be sorted by count: word2(20), word4(15), word0(10)
    assert result["words"] == ["word2", "word4", "word0"]
    assert result["weights"] == [20, 15, 10]


def test_sparse_doc_topic_matrix():
    """Test conversion to sparse matrix format."""
    dense_matrix = [
        [10, 0, 5],  # Topic 0
        [0, 15, 0],  # Topic 1
        [2, 1, 20],  # Topic 2
    ]

    sparse = sparse_doc_topic_matrix(dense_matrix)

    assert "i" in sparse  # indices
    assert "p" in sparse  # indptr
    assert "x" in sparse  # data

    # Check that non-zero values are captured
    assert 10 in sparse["x"]
    assert 5 in sparse["x"]
    assert 15 in sparse["x"]
    assert 20 in sparse["x"]

    # Check that indptr has correct length (num_topics + 1)
    assert len(sparse["p"]) == 4


def test_normalize_doc_topic_proportions(sample_doc_topic_counts):
    """Test normalization of document-topic counts to proportions."""
    proportions = normalize_doc_topic_proportions(sample_doc_topic_counts)

    assert len(proportions) == 3  # 3 documents

    # Each document's proportions should sum to 1.0
    for doc_props in proportions:
        assert abs(sum(doc_props) - 1.0) < 1e-6

    # Doc 0: {0: 10, 1: 5, 2: 2} -> total 17
    assert abs(proportions[0][0] - 10 / 17) < 1e-6
    assert abs(proportions[0][1] - 5 / 17) < 1e-6
    assert abs(proportions[0][2] - 2 / 17) < 1e-6


def test_normalize_empty_document():
    """Test normalization with empty document."""
    doc_counts = [{}]  # Empty document
    proportions = normalize_doc_topic_proportions(doc_counts)

    assert len(proportions) == 1
    assert proportions[0] == []


# --- Test coordinate generation functions ---


def test_topic_word_matrix_from_topic_words(sample_topic_words):
    """Test creation of topic-word matrix."""
    vocab = ["computer", "software", "health", "medical", "economy"]

    mat = topic_word_matrix_from_topic_words(sample_topic_words, vocab, top_n=3)

    assert mat.shape == (3, 5)  # 3 topics, 5 vocab words

    # Each row should be normalized (sum to 1)
    for i in range(3):
        assert abs(mat[i].sum() - 1.0) < 1e-6


def test_jensen_shannon():
    """Test Jensen-Shannon divergence calculation."""
    p = np.array([0.5, 0.3, 0.2])
    q = np.array([0.5, 0.3, 0.2])

    # Identical distributions should have JS divergence of 0
    js = jensen_shannon(p, q)
    assert abs(js) < 1e-10

    # Different distributions should have positive divergence
    r = np.array([0.2, 0.3, 0.5])
    js2 = jensen_shannon(p, r)
    assert js2 > 0


def test_jsd_matrix():
    """Test JSD distance matrix computation."""
    mat = np.array(
        [
            [0.5, 0.3, 0.2],
            [0.5, 0.3, 0.2],
            [0.2, 0.3, 0.5],
        ]
    )

    dist = jsd_matrix(mat)

    assert dist.shape == (3, 3)

    # Diagonal should be zero (topic compared with itself)
    for i in range(3):
        assert abs(dist[i, i]) < 1e-10

    # Identical distributions (rows 0 and 1) should have zero distance
    assert abs(dist[0, 1]) < 1e-10


def test_compute_mds():
    """Test MDS coordinate computation."""
    # Create a simple distance matrix
    dist = np.array(
        [
            [0.0, 0.5, 1.0],
            [0.5, 0.0, 0.7],
            [1.0, 0.7, 0.0],
        ]
    )

    coords = compute_mds(dist, n_components=2)

    assert coords.shape == (3, 2)  # 3 topics, 2D coordinates


# --- Test file writing functions ---


def test_write_topic_keys_txt(sample_topic_words, temp_output_dir):
    """Test topic-keys.txt generation."""
    write_topic_keys_txt(sample_topic_words, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "topic-keys.txt")
    assert os.path.exists(filepath)

    with open(filepath) as f:
        lines = f.readlines()

    assert len(lines) == 3  # 3 topics

    # Check format: topic_num \t weight \t words
    parts = lines[0].strip().split("\t")
    assert parts[0] == "0"  # Topic number
    assert parts[1] == "1.0"  # Weight
    assert "computer" in parts[2]  # Words


def test_write_doc_topic_txt(temp_output_dir):
    """Test doc-topic.txt generation."""
    proportions = [
        [0.5, 0.3, 0.2],
        [0.1, 0.7, 0.2],
    ]

    write_doc_topic_txt(proportions, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "doc-topic.txt")
    assert os.path.exists(filepath)

    with open(filepath) as f:
        lines = f.readlines()

    assert len(lines) == 2  # 2 documents

    # Check format
    parts = lines[0].strip().split("\t")
    assert parts[0] == "0"  # Doc number
    assert parts[1] == "doc1"  # Doc name
    assert len(parts) == 5  # docNum, docName, 3 proportions


def test_write_topic_coords_csv(sample_topic_words, temp_output_dir):
    """Test topic_coords.csv generation."""
    write_topic_coords_csv(sample_topic_words, temp_output_dir, top_n=5)

    filepath = os.path.join(temp_output_dir, "topic_coords.csv")
    assert os.path.exists(filepath)

    df = pd.read_csv(filepath)

    assert len(df) == 3  # 3 topics
    assert list(df.columns) == ["topic", "x", "y"]
    assert df["topic"].tolist() == [0, 1, 2]


def test_write_doc_topic_counts_csv(sample_doc_topic_counts, temp_output_dir):
    """Test doc-topic-counts.csv generation."""
    write_doc_topic_counts_csv(sample_doc_topic_counts, 3, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "doc-topic-counts.csv")
    assert os.path.exists(filepath)

    with open(filepath) as f:
        lines = f.readlines()

    # Header + 3 documents
    assert len(lines) == 4

    # Check header
    assert "docNum,topic0,topic1,topic2" in lines[0]


def test_write_basic_metadata_csv(temp_output_dir):
    """Test metadata.csv generation."""
    write_basic_metadata_csv(5, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "metadata.csv")
    assert os.path.exists(filepath)

    with open(filepath) as f:
        lines = f.readlines()

    # Header + 5 documents
    assert len(lines) == 6

    # Check that it doesn't overwrite existing file
    write_basic_metadata_csv(10, temp_output_dir)
    with open(filepath) as f:
        lines = f.readlines()
    assert len(lines) == 6  # Still 6, not overwritten


def test_write_topic_words_json(sample_topic_words, temp_output_dir):
    """Test tw.json generation."""
    alpha = [0.5, 0.5, 0.5]
    write_topic_words_json(alpha, sample_topic_words, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "tw.json")
    assert os.path.exists(filepath)

    with open(filepath) as f:
        data = json.load(f)

    assert "alpha" in data
    assert "tw" in data
    assert data["alpha"] == alpha
    assert len(data["tw"]) == 3


def test_write_doc_topics_zip(temp_output_dir):
    """Test dt.zip generation."""
    sparse_matrix = {"i": [0, 1, 2], "p": [0, 1, 2, 3], "x": [10, 15, 20]}

    write_doc_topics_zip(sparse_matrix, temp_output_dir)

    filepath = os.path.join(temp_output_dir, "dt.zip")
    assert os.path.exists(filepath)

    # Check that it's a valid zip file
    with zipfile.ZipFile(filepath) as zf:
        assert "dt.json" in zf.namelist()
        data = json.loads(zf.read("dt.json"))
        assert data == sparse_matrix


# --- Integration tests ---


def test_process_mallet_state_file_core_only(sample_state_file, temp_output_dir):
    """Test full processing with core files only (default)."""
    process_mallet_state_file(
        sample_state_file, temp_output_dir, n_top_words=10, generate_all=False
    )

    # Check that core files exist
    assert os.path.exists(os.path.join(temp_output_dir, "topic-keys.txt"))
    assert os.path.exists(os.path.join(temp_output_dir, "doc-topic.txt"))
    assert os.path.exists(os.path.join(temp_output_dir, "topic_coords.csv"))
    assert os.path.exists(os.path.join(temp_output_dir, "metadata.csv"))

    # Check that additional files don't exist
    assert not os.path.exists(os.path.join(temp_output_dir, "doc-topic-counts.csv"))
    assert not os.path.exists(os.path.join(temp_output_dir, "tw.json"))
    assert not os.path.exists(os.path.join(temp_output_dir, "dt.zip"))


def test_process_mallet_state_file_all(sample_state_file, temp_output_dir):
    """Test full processing with all files."""
    process_mallet_state_file(
        sample_state_file, temp_output_dir, n_top_words=10, generate_all=True
    )

    # Check that core files exist
    assert os.path.exists(os.path.join(temp_output_dir, "topic-keys.txt"))
    assert os.path.exists(os.path.join(temp_output_dir, "doc-topic.txt"))
    assert os.path.exists(os.path.join(temp_output_dir, "topic_coords.csv"))
    assert os.path.exists(os.path.join(temp_output_dir, "metadata.csv"))

    # Check that additional files exist
    assert os.path.exists(os.path.join(temp_output_dir, "doc-topic-counts.csv"))
    assert os.path.exists(os.path.join(temp_output_dir, "tw.json"))
    assert os.path.exists(os.path.join(temp_output_dir, "dt.zip"))


def test_process_mallet_state_file_content_accuracy(sample_state_file, temp_output_dir):
    """Test that processed content is accurate."""
    process_mallet_state_file(
        sample_state_file, temp_output_dir, n_top_words=10, generate_all=True
    )

    # Verify doc-topic.txt proportions
    with open(os.path.join(temp_output_dir, "doc-topic.txt")) as f:
        lines = f.readlines()

    # Should have 3 documents
    assert len(lines) == 3

    # Doc 0: 10 tokens topic 0, 5 tokens topic 1 -> proportions ~0.67, 0.33, 0.0
    doc0_parts = lines[0].strip().split("\t")
    doc0_props = [float(x) for x in doc0_parts[2:]]
    assert abs(doc0_props[0] - 10 / 15) < 0.01
    assert abs(doc0_props[1] - 5 / 15) < 0.01

    # Verify topic_coords.csv
    df = pd.read_csv(os.path.join(temp_output_dir, "topic_coords.csv"))
    assert len(df) == 3  # 3 topics
    assert all(col in df.columns for col in ["topic", "x", "y"])


def test_process_nonexistent_file(temp_output_dir):
    """Test error handling for nonexistent file."""
    with pytest.raises(FileNotFoundError):
        process_mallet_state_file("nonexistent.gz", temp_output_dir)


# --- Edge case tests ---


def test_empty_topic_word_counts():
    """Test handling of empty topic."""
    word_counts = []
    vocab = {}

    result = get_top_words_and_weights(word_counts, vocab, 5)

    assert result["words"] == []
    assert result["weights"] == []


def test_single_topic_coordinates():
    """Test coordinate generation with single topic."""
    topic_words = [{"words": ["computer", "software"], "weights": [10, 5]}]

    vocab = ["computer", "software"]
    mat = topic_word_matrix_from_topic_words(topic_words, vocab, top_n=2)
    dist = jsd_matrix(mat)
    coords = compute_mds(dist, n_components=2)

    # Should handle single topic gracefully
    assert coords.shape == (1, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
