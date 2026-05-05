"""
Final state tests for the Flyte 2.0 distributed map-reduce pipeline task.
Verifies that the agent correctly implemented the map-reduce word counter and
produced the expected output for the sample text.
"""
import json
import os
import subprocess


PROJECT_DIR = "/home/user/flyte_project"
MAPREDUCE_FILE = os.path.join(PROJECT_DIR, "mapreduce.py")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "wordcount.json")


# ---------------------------------------------------------------------------
# Priority 1: File existence
# ---------------------------------------------------------------------------

def test_mapreduce_file_exists():
    """mapreduce.py must exist in the project directory."""
    assert os.path.isfile(MAPREDUCE_FILE), (
        f"Expected '{MAPREDUCE_FILE}' to exist, but it was not found."
    )


# ---------------------------------------------------------------------------
# Priority 1: Execution
# ---------------------------------------------------------------------------

def test_mapreduce_runs_successfully():
    """Running mapreduce.py with python3 must exit with returncode 0."""
    result = subprocess.run(
        ["python3", MAPREDUCE_FILE],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"mapreduce.py exited with code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Priority 1: Output file and content
# ---------------------------------------------------------------------------

def _load_output() -> dict:
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected output file '{OUTPUT_FILE}' to exist after running mapreduce.py."
    )
    with open(OUTPUT_FILE, "r") as f:
        return json.load(f)


def test_output_file_exists():
    """wordcount.json must be created after running the pipeline."""
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected '{OUTPUT_FILE}' to exist, but it was not found."
    )


def test_total_words_is_eleven():
    """total_words must equal 11 for the sample input text."""
    data = _load_output()
    assert "total_words" in data, (
        f"'total_words' key missing from output. Got keys: {list(data.keys())}"
    )
    assert data["total_words"] == 11, (
        f"Expected total_words=11, got: {data['total_words']}.\n"
        "Input: 'the quick brown fox jumps over the lazy dog the fox' has 11 words."
    )


def test_unique_words_is_nine():
    """unique_words must equal 9 for the sample input text."""
    data = _load_output()
    assert "unique_words" in data, (
        f"'unique_words' key missing from output. Got keys: {list(data.keys())}"
    )
    assert data["unique_words"] == 9, (
        f"Expected unique_words=9, got: {data['unique_words']}.\n"
        "Unique words: the, quick, brown, fox, jumps, over, lazy, dog (9 distinct words)."
    )


def test_frequency_the_is_three():
    """frequencies['the'] must equal 3."""
    data = _load_output()
    assert "frequencies" in data, (
        f"'frequencies' key missing from output. Got keys: {list(data.keys())}"
    )
    freq = data["frequencies"]
    assert "the" in freq, (
        f"Expected 'the' in frequencies, got keys: {list(freq.keys())}"
    )
    assert freq["the"] == 3, (
        f"Expected frequencies['the']=3, got: {freq['the']}.\n"
        "'the' appears at positions 1, 7, 10 in the sample text."
    )


def test_frequency_fox_is_two():
    """frequencies['fox'] must equal 2."""
    data = _load_output()
    assert "frequencies" in data, (
        f"'frequencies' key missing from output. Got keys: {list(data.keys())}"
    )
    freq = data["frequencies"]
    assert "fox" in freq, (
        f"Expected 'fox' in frequencies, got keys: {list(freq.keys())}"
    )
    assert freq["fox"] == 2, (
        f"Expected frequencies['fox']=2, got: {freq['fox']}.\n"
        "'fox' appears at positions 4 and 11 in the sample text."
    )


def test_frequency_quick_is_one():
    """frequencies['quick'] must equal 1."""
    data = _load_output()
    assert "frequencies" in data, (
        f"'frequencies' key missing from output. Got keys: {list(data.keys())}"
    )
    freq = data["frequencies"]
    assert "quick" in freq, (
        f"Expected 'quick' in frequencies, got keys: {list(freq.keys())}"
    )
    assert freq["quick"] == 1, (
        f"Expected frequencies['quick']=1, got: {freq['quick']}."
    )
