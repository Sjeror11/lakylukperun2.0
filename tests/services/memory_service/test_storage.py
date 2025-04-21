import pytest
import os
import sys
import time
import shutil
from datetime import datetime, timezone, timedelta
import re
from typing import Tuple # Ensure Tuple is imported if used elsewhere

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
# Import HOSTNAME constant directly
from src.services.memory_service.storage import MemoryStorage, TMP_DIR, NEW_DIR, CUR_DIR, FILENAME_REGEX, HOSTNAME
from src.models.memory_entry import MemoryEntry, MemoryEntryType
from src.utils.exceptions import MemdirIOError
from src import config

# --- Test Fixture ---

@pytest.fixture
def memory_storage(tmp_path):
    """Provides a MemoryStorage instance using a temporary directory."""
    # Override the config path for the duration of the test
    original_memdir_path = config.MEMDIR_PATH
    test_memdir = tmp_path / "test_memdir"
    config.MEMDIR_PATH = str(test_memdir)

    storage = MemoryStorage() # Initializes with the overridden path

    yield storage # Provide the instance to the test

    # Teardown: Restore original config path (though not strictly necessary with tmp_path)
    config.MEMDIR_PATH = original_memdir_path
    # tmp_path fixture handles directory cleanup automatically

# --- Filename Parsing Tests ---

def test_parse_filename_valid_no_flags(memory_storage):
    """Tests parsing a valid filename without flags."""
    ts_ns = time.time_ns()
    unique_id = "test-uuid"
    hostname = "test-host"
    filename = f"{ts_ns}.{unique_id}.{hostname}"
    parsed = memory_storage._parse_filename(filename)
    assert parsed is not None
    assert parsed["timestamp_ns"] == ts_ns
    assert parsed["unique_id"] == unique_id
    assert parsed["hostname"] == hostname
    assert parsed["size"] is None
    assert parsed["flags"] == ""
    assert isinstance(parsed["timestamp_dt"], datetime)

def test_parse_filename_valid_with_flags(memory_storage):
    """Tests parsing a valid filename with flags."""
    ts_ns = time.time_ns()
    unique_id = "test-uuid-2"
    hostname = "test-host"
    flags = "ST"
    filename = f"{ts_ns}.{unique_id}.{hostname}:2,{flags}" # Maildir v2 format
    parsed = memory_storage._parse_filename(filename)
    assert parsed is not None
    assert parsed["timestamp_ns"] == ts_ns
    assert parsed["unique_id"] == unique_id
    assert parsed["hostname"] == hostname
    # assert parsed["size"] is None # Assuming size isn't used in :2, format
    assert parsed["flags"] == flags
    assert isinstance(parsed["timestamp_dt"], datetime)

def test_parse_filename_invalid(memory_storage):
    """Tests parsing an invalid filename."""
    assert memory_storage._parse_filename("invalid-filename.txt") is None
    assert memory_storage._parse_filename("123.uuid") is None
    assert memory_storage._parse_filename(f"{time.time_ns()}.uuid.host:invalid") is None

# --- Save and Read Tests ---

def test_save_and_read_memory(memory_storage):
    """Tests saving a memory entry and reading it back."""
    entry_data = {"message": "test data", "value": 123}
    entry = MemoryEntry(
        entry_type=MemoryEntryType.SYSTEM_EVENT,
        source_service="pytest",
        payload=entry_data
    )

    # Save
    try:
        new_filename = memory_storage.save_memory(entry)
        assert isinstance(new_filename, str)
        new_filepath = os.path.join(memory_storage.new_path, new_filename)
        assert os.path.exists(new_filepath)
        # Check tmp dir is empty after successful save
        assert not os.listdir(memory_storage.tmp_path)
    except MemdirIOError as e:
        pytest.fail(f"save_memory failed: {e}")

    # Read back from 'new'
    try:
        read_entry = memory_storage.read_memory(NEW_DIR, new_filename)
        assert isinstance(read_entry, MemoryEntry)
        assert read_entry.entry_id == entry.entry_id
        assert read_entry.entry_type == entry.entry_type
        assert read_entry.source_service == entry.source_service
        assert read_entry.payload == entry_data
        assert read_entry.metadata is None # No metadata added yet
    except (MemdirIOError, FileNotFoundError) as e:
        pytest.fail(f"read_memory failed: {e}")

def test_read_non_existent(memory_storage):
    """Tests reading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        memory_storage.read_memory(NEW_DIR, "non_existent_file.json")
    with pytest.raises(FileNotFoundError):
        memory_storage.read_memory(CUR_DIR, "non_existent_file.json")

def test_read_invalid_json(memory_storage, tmp_path):
    """Tests reading a file with invalid JSON content."""
    invalid_file = tmp_path / "test_memdir" / NEW_DIR / "invalid.json"
    invalid_file.write_text("this is not json")
    with pytest.raises(MemdirIOError, match="JSON decode error"):
        memory_storage.read_memory(NEW_DIR, "invalid.json")

# --- Move and Flag Tests ---

def test_move_memory_new_to_cur(memory_storage):
    """Tests moving a file from 'new' to 'cur'."""
    entry = MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={}) # Use valid type
    new_filename = memory_storage.save_memory(entry)
    new_filepath = os.path.join(memory_storage.new_path, new_filename)
    assert os.path.exists(new_filepath)

    try:
        cur_filename = memory_storage.move_memory(NEW_DIR, new_filename, add_flags="S") # Add Seen flag
        cur_filepath = os.path.join(memory_storage.cur_path, cur_filename)

        assert not os.path.exists(new_filepath) # Original should be gone
        assert os.path.exists(cur_filepath)     # New file in 'cur' should exist

        # Check filename includes flags
        parsed_cur = memory_storage._parse_filename(cur_filename)
        assert parsed_cur is not None
        assert "S" in parsed_cur["flags"]

        # Read back from 'cur' to be sure
        read_entry = memory_storage.read_memory(CUR_DIR, cur_filename)
        assert read_entry.entry_id == entry.entry_id

    except (MemdirIOError, FileNotFoundError) as e:
        pytest.fail(f"move_memory failed: {e}")

def test_update_flags(memory_storage):
    """Tests adding and removing flags from a file in 'cur'."""
    entry = MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={}) # Use valid type
    new_filename = memory_storage.save_memory(entry)
    cur_filename_initial = memory_storage.move_memory(NEW_DIR, new_filename, add_flags="S") # Start with 'S'
    cur_filepath_initial = os.path.join(memory_storage.cur_path, cur_filename_initial)
    assert os.path.exists(cur_filepath_initial)

    try:
        # Add 'I' (Important) flag
        cur_filename_si = memory_storage.update_flags(cur_filename_initial, add_flags="I")
        cur_filepath_si = os.path.join(memory_storage.cur_path, cur_filename_si)
        assert not os.path.exists(cur_filepath_initial)
        assert os.path.exists(cur_filepath_si)
        parsed_si = memory_storage._parse_filename(cur_filename_si)
        assert parsed_si is not None
        assert set(parsed_si["flags"]) == {"S", "I"}

        # Remove 'S' flag, add 'P' (Processed)
        cur_filename_ip = memory_storage.update_flags(cur_filename_si, add_flags="P", remove_flags="S")
        cur_filepath_ip = os.path.join(memory_storage.cur_path, cur_filename_ip)
        assert not os.path.exists(cur_filepath_si)
        assert os.path.exists(cur_filepath_ip)
        parsed_ip = memory_storage._parse_filename(cur_filename_ip)
        assert parsed_ip is not None
        assert set(parsed_ip["flags"]) == {"I", "P"}

        # Remove all flags
        cur_filename_none = memory_storage.update_flags(cur_filename_ip, remove_flags="IP")
        cur_filepath_none = os.path.join(memory_storage.cur_path, cur_filename_none)
        assert not os.path.exists(cur_filepath_ip)
        assert os.path.exists(cur_filepath_none)
        parsed_none = memory_storage._parse_filename(cur_filename_none)
        assert parsed_none is not None
        assert parsed_none["flags"] == "" # No flags remain

    except (MemdirIOError, FileNotFoundError) as e:
        pytest.fail(f"update_flags failed: {e}")

def test_update_flags_non_existent(memory_storage):
    """Tests updating flags for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        memory_storage.update_flags("non_existent_file", add_flags="S")

# --- List and Query Tests ---

def test_list_files(memory_storage):
    """Tests listing files in 'new' and 'cur'."""
    fnames_new = [memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": i})) for i in range(3)] # Use valid type
    time.sleep(0.01) # Ensure timestamps differ slightly if needed
    fnames_cur = [memory_storage.move_memory(NEW_DIR, fname, add_flags="S") for fname in fnames_new[1:]] # Move 2 to cur

    assert set(memory_storage.list_files(NEW_DIR)) == {fnames_new[0]}
    assert set(memory_storage.list_files(CUR_DIR)) == set(fnames_cur)
    assert memory_storage.list_files(TMP_DIR) == [] # tmp should be empty

def test_query_memories_basic(memory_storage):
    """Tests basic querying without complex filters."""
    num_files = 5
    fnames_new = [memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": i})) for i in range(num_files)] # Use valid type
    time.sleep(0.01)
    fnames_cur = [memory_storage.move_memory(NEW_DIR, fname, add_flags="S") for fname in fnames_new]

    results = memory_storage.query_memories()
    assert len(results) == num_files
    # Results should be sorted descending by timestamp (most recent first)
    timestamps = [info['timestamp_ns'] for fname, info in results]
    assert timestamps == sorted(timestamps, reverse=True)

def test_query_memories_by_flags(memory_storage):
    """Tests querying by included and excluded flags."""
    f1 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 1})) # Use valid type
    f2 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 2})) # Use valid type
    f3 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 3})) # Use valid type

    cf1 = memory_storage.move_memory(NEW_DIR, f1, add_flags="SA") # Seen, Alert
    cf2 = memory_storage.move_memory(NEW_DIR, f2, add_flags="SP") # Seen, Processed
    cf3 = memory_storage.move_memory(NEW_DIR, f3, add_flags="S")  # Seen

    # Include S -> should get all 3
    res_s = memory_storage.query_memories(flags_include="S")
    assert len(res_s) == 3

    # Include A -> should get cf1
    res_a = memory_storage.query_memories(flags_include="A")
    assert len(res_a) == 1
    assert res_a[0][0] == cf1

    # Include P -> should get cf2
    res_p = memory_storage.query_memories(flags_include="P")
    assert len(res_p) == 1
    assert res_p[0][0] == cf2

    # Include SP -> should get cf2
    res_sp = memory_storage.query_memories(flags_include="SP")
    assert len(res_sp) == 1
    assert res_sp[0][0] == cf2

    # Exclude A -> should get cf2, cf3
    res_not_a = memory_storage.query_memories(flags_exclude="A")
    assert len(res_not_a) == 2
    assert set(r[0] for r in res_not_a) == {cf2, cf3}

    # Include S, Exclude P -> should get cf1, cf3
    res_s_not_p = memory_storage.query_memories(flags_include="S", flags_exclude="P")
    assert len(res_s_not_p) == 2
    assert set(r[0] for r in res_s_not_p) == {cf1, cf3}

def test_query_memories_by_time(memory_storage):
    """Tests querying by time range."""
    t1 = datetime.now(timezone.utc)
    f1 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 1})) # Use valid type
    time.sleep(0.05)
    t2 = datetime.now(timezone.utc)
    f2 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 2})) # Use valid type
    time.sleep(0.05)
    t3 = datetime.now(timezone.utc)
    f3 = memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": 3})) # Use valid type
    t4 = datetime.now(timezone.utc)

    cf1 = memory_storage.move_memory(NEW_DIR, f1, add_flags="S")
    cf2 = memory_storage.move_memory(NEW_DIR, f2, add_flags="S")
    cf3 = memory_storage.move_memory(NEW_DIR, f3, add_flags="S")

    # Query between t1 and t3 (exclusive of t3) -> should get cf1, cf2
    res_t1_t3 = memory_storage.query_memories(time_start=t1, time_end=t3)
    assert len(res_t1_t3) == 2
    assert set(r[0] for r in res_t1_t3) == {cf1, cf2}

    # Query after t2 -> should get cf2, cf3
    res_after_t2 = memory_storage.query_memories(time_start=t2)
    assert len(res_after_t2) == 2 # Should include the one created at t2 and the one after
    assert set(r[0] for r in res_after_t2) == {cf2, cf3}

    # Query before t2 -> should get cf1
    res_before_t2 = memory_storage.query_memories(time_end=t2)
    assert len(res_before_t2) == 1
    assert res_before_t2[0][0] == cf1

# --- Pruning Tests ---

def test_prune_memories_by_age(memory_storage):
    """Tests pruning files older than a certain age."""
    # Create files with varying timestamps (need to manipulate filename for test)
    now_ns = time.time_ns()
    hostname = HOSTNAME # Use imported constant
    uid = "prune-test"
    # File 1: 2 days old
    ts1 = now_ns - int(2 * 24 * 60 * 60 * 1e9)
    fname1 = f"{ts1}.{uid}1.{hostname}:2,S"
    (memory_storage.cur_path / fname1).touch()
    # File 2: 0.5 days old
    ts2 = now_ns - int(0.5 * 24 * 60 * 60 * 1e9)
    fname2 = f"{ts2}.{uid}2.{hostname}:2,S"
    (memory_storage.cur_path / fname2).touch()

    assert len(memory_storage.list_files(CUR_DIR)) == 2

    # Prune files older than 1 day
    deleted_age, deleted_count = memory_storage.prune_memories(max_age_days=1)
    assert deleted_age == 1
    assert deleted_count == 0
    remaining_files = memory_storage.list_files(CUR_DIR)
    assert len(remaining_files) == 1
    assert remaining_files[0] == fname2 # Only the newer file should remain

def test_prune_memories_by_count(memory_storage):
    """Tests pruning files to meet a maximum count."""
    num_files = 5
    fnames_new = [memory_storage.save_memory(MemoryEntry(entry_type=MemoryEntryType.SYSTEM_EVENT, source_service="pytest", payload={"i": i})) for i in range(num_files)] # Use valid type
    time.sleep(0.01)
    fnames_cur = [memory_storage.move_memory(NEW_DIR, fname, add_flags="S") for fname in fnames_new]

    assert len(memory_storage.list_files(CUR_DIR)) == num_files

    # Prune to keep only 2 files (should delete the 3 oldest)
    max_count = 2
    deleted_age, deleted_count = memory_storage.prune_memories(max_count=max_count)
    assert deleted_age == 0
    assert deleted_count == num_files - max_count # 3 deleted by count
    remaining_files = memory_storage.list_files(CUR_DIR)
    assert len(remaining_files) == max_count

    # Check that the remaining files are the newest ones
    remaining_parsed = sorted([memory_storage._parse_filename(f) for f in remaining_files], key=lambda p: p['timestamp_ns'])
    original_parsed = sorted([memory_storage._parse_filename(f) for f in fnames_cur], key=lambda p: p['timestamp_ns'])
    assert remaining_parsed[0]['timestamp_ns'] == original_parsed[num_files - max_count]['timestamp_ns']
    assert remaining_parsed[-1]['timestamp_ns'] == original_parsed[-1]['timestamp_ns']

def test_prune_memories_combined(memory_storage):
    """Tests pruning by both age and count."""
    now_ns = time.time_ns()
    hostname = HOSTNAME # Use imported constant
    uid = "prune-test"
    # File 1: 3 days old
    ts1 = now_ns - int(3 * 24 * 60 * 60 * 1e9)
    fname1 = f"{ts1}.{uid}1.{hostname}:2,S"
    (memory_storage.cur_path / fname1).touch()
    # File 2: 2 days old
    ts2 = now_ns - int(2 * 24 * 60 * 60 * 1e9)
    fname2 = f"{ts2}.{uid}2.{hostname}:2,S"
    (memory_storage.cur_path / fname2).touch()
    # File 3: 1 day old
    ts3 = now_ns - int(1 * 24 * 60 * 60 * 1e9)
    fname3 = f"{ts3}.{uid}3.{hostname}:2,S"
    (memory_storage.cur_path / fname3).touch()
    # File 4: 0.5 days old
    ts4 = now_ns - int(0.5 * 24 * 60 * 60 * 1e9)
    fname4 = f"{ts4}.{uid}4.{hostname}:2,S"
    (memory_storage.cur_path / fname4).touch()

    assert len(memory_storage.list_files(CUR_DIR)) == 4

    # Prune older than 1.5 days AND keep max 2
    deleted_age, deleted_count = memory_storage.prune_memories(max_age_days=1.5, max_count=2)
    # fname1, fname2 should be deleted by age (2 files)
    # Then, the count pruning logic adds the next 2 oldest files (fname3, fname4) to meet the count limit.
    assert deleted_age == 2
    assert deleted_count == 2 # Two additional files deleted by count limit logic
    remaining_files = memory_storage.list_files(CUR_DIR)
    assert len(remaining_files) == 0 # All files should be deleted in this specific scenario
