import os
import json
import uuid
import time
import shutil
from pathlib import Path # Import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
import re

from ... import config
from ...utils.logger import log
from ...utils.exceptions import MemoryServiceError, MemdirIOError, MemoryQueryError
from ...models.memory_entry import MemoryEntry # Import the data model

# --- Constants ---
# Memdir subdirectories
TMP_DIR = "tmp"
NEW_DIR = "new"
CUR_DIR = "cur"
INDEX_DIR = "index" # Optional index directory within cur

# Filename format: <timestamp_ns>.<unique_id>.<hostname>[:2,<flags>]
# Flags are Maildir-style (e.g., :2,S for Seen). The :2, part is optional if no flags.
# Updated regex to allow more characters in flags (word chars, hyphen, comma)
FILENAME_REGEX = re.compile(r"^(\d+)\.([^.]+)\.([^:]+?)(?::2,([\w,-]*))?$") # Made hostname non-greedy, flags more permissive
# Groups: 1=timestamp_ns, 2=unique_id, 3=hostname, 4=flags(optional)

HOSTNAME = os.uname().nodename # Get hostname once


class MemoryStorage:
    """
    Handles low-level filesystem operations for the Memdir structure.
    Provides atomic writes, reads, moves, flag updates, and basic querying/pruning.
    """

    def __init__(self):
        self.memdir_root = Path(config.MEMDIR_PATH).resolve() # Use Path and resolve
        self.tmp_path = self.memdir_root / TMP_DIR
        self.new_path = self.memdir_root / NEW_DIR
        self.cur_path = self.memdir_root / CUR_DIR
        self.index_path = self.cur_path / INDEX_DIR # Optional

        # Ensure Memdir structure exists using Path methods
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.new_path.mkdir(parents=True, exist_ok=True)
        self.cur_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True) # Create index dir too
        log.info(f"MemoryStorage initialized. Memdir root: {self.memdir_root}")

    def _generate_unique_id(self) -> str:
        """Generates a unique ID component for the filename."""
        # Combine timestamp, process ID, and a random element for high uniqueness guarantee
        # Using UUID is simpler and generally sufficient
        return str(uuid.uuid4())

    def _generate_filename(self, flags: Optional[str] = None, size: Optional[int] = None) -> str:
        """Generates a unique filename based on the Memdir format."""
        timestamp_ns = time.time_ns()
        unique_id = self._generate_unique_id()
        filename_base = f"{timestamp_ns}.{unique_id}.{HOSTNAME}"
        if flags or size is not None:
             flag_str = flags or ""
             size_str = str(size) if size is not None else "" # Maildir spec uses size, but we might not need it strictly
             filename = f"{filename_base}:2,{flag_str}" # Using Maildir v2 format marker ':2,'
             # filename = f"{filename_base}:{size_str},{flag_str}" # If size is needed
        else:
             filename = filename_base # No flags initially in 'new'
        return filename

    def _parse_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Parses a Memdir filename into its components."""
        match = FILENAME_REGEX.match(filename)
        if match:
            # Groups: 1=timestamp_ns, 2=unique_id, 3=hostname, 4=flags(optional)
            ts_ns, unique_id, hostname, flags_str = match.groups()
            return {
                "timestamp_ns": int(ts_ns),
                "unique_id": unique_id,
                "hostname": hostname,
                "size": None, # Explicitly add size as None as it's not captured by regex
                "flags": flags_str if flags_str is not None else "", # Handle case where flags group doesn't match
                "timestamp_dt": datetime.fromtimestamp(int(ts_ns) / 1e9, tz=timezone.utc)
            }
        else: # Correctly indented else block
            log.warning(f"Could not parse filename: {filename}")
            return None

    def save_memory(self, entry: MemoryEntry) -> str:
        """
        Saves a MemoryEntry object to a new file in the 'new' directory.
        Uses atomic write (write to tmp, then move).

        Args:
            entry: The MemoryEntry object to save.

        Returns:
            The filename (without path) of the newly created memory file in 'new'.

        Raises:
            MemdirIOError: If saving fails.
        """
        try:
            entry_json = entry.model_dump_json(indent=2)
            entry_bytes = entry_json.encode('utf-8')
        except Exception as e:
            log.error(f"Failed to serialize MemoryEntry (ID: {entry.entry_id}): {e}", exc_info=True)
            raise MemdirIOError(f"Serialization failed for entry {entry.entry_id}: {e}") from e

        tmp_filename = self._generate_filename() # No flags/size needed for tmp name itself
        tmp_filepath = self.tmp_path / tmp_filename # Use Path object
        new_filename = self._generate_filename() # Final name for the 'new' dir (no flags yet)
        new_filepath = self.new_path / new_filename # Use Path object

        try:
            # Write to temporary file first using Path object
            tmp_filepath.write_bytes(entry_bytes)

            # Atomically move from tmp to new using Path.rename
            tmp_filepath.rename(new_filepath)

            log.debug(f"Saved memory entry {entry.entry_id} to {new_filepath}")
            return new_filename # Return just the filename part

        except OSError as e:
            log.error(f"OS Error saving memory entry {entry.entry_id} (tmp: {tmp_filepath}, new: {new_filepath}): {e}", exc_info=True)
            # Clean up tmp file if it exists using Path.unlink
            if tmp_filepath.exists():
                try:
                    tmp_filepath.unlink()
                except OSError as cleanup_e:
                    log.error(f"Failed to clean up temporary file {tmp_filepath}: {cleanup_e}")
            raise MemdirIOError(f"Failed to save memory entry {entry.entry_id}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error saving memory entry {entry.entry_id}: {e}", exc_info=True)
            raise MemdirIOError(f"Unexpected error saving memory entry {entry.entry_id}: {e}") from e

    def read_memory(self, directory: str, filename: str) -> MemoryEntry:
        """
        Reads and deserializes a MemoryEntry from a file in a specified directory (new or cur).

        Args:
            directory: The directory containing the file ('new' or 'cur').
            filename: The name of the file to read.

        Returns:
            The deserialized MemoryEntry object.

        Raises:
            MemdirIOError: If reading or deserialization fails.
            FileNotFoundError: If the file does not exist.
        """
        if directory not in [NEW_DIR, CUR_DIR]:
             raise ValueError(f"Invalid directory specified for reading: {directory}. Must be '{NEW_DIR}' or '{CUR_DIR}'.")

        base_path = self.new_path if directory == NEW_DIR else self.cur_path
        filepath = base_path / filename # Use Path object
        log.debug(f"Reading memory file: {filepath}")

        try:
            # Use Path object methods for reading
            entry_json = filepath.read_text(encoding='utf-8')
            entry_data = json.loads(entry_json)
            entry = MemoryEntry(**entry_data)
            return entry
        except FileNotFoundError:
            log.error(f"Memory file not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            log.error(f"Failed to decode JSON from memory file {filepath}: {e}", exc_info=True)
            raise MemdirIOError(f"JSON decode error in {filepath}: {e}") from e
        except Exception as e: # Catches Pydantic validation errors too
            log.error(f"Failed to read or parse memory file {filepath}: {e}", exc_info=True)
            raise MemdirIOError(f"Failed to process memory file {filepath}: {e}") from e

    def update_flags(self, filename: str, add_flags: Optional[str] = None, remove_flags: Optional[str] = None) -> str:
        """
        Updates the flags of a memory file located in the 'cur' directory by renaming it.

        Args:
            filename: The current filename in the 'cur' directory.
            add_flags: String containing flags to add (e.g., "ST").
            remove_flags: String containing flags to remove.

        Returns:
            The new filename with updated flags.

        Raises:
            MemdirIOError: If renaming fails or the file is not found in 'cur'.
            FileNotFoundError: If the original file does not exist in 'cur'.
        """
        cur_filepath = self.cur_path / filename # Use Path object
        if not cur_filepath.exists(): # Use Path.exists()
            log.error(f"Cannot update flags for non-existent file in cur: {filename}")
            raise FileNotFoundError(f"File not found in cur directory: {filename}")

        parsed = self._parse_filename(filename)
        if not parsed:
            raise MemdirIOError(f"Cannot update flags: Failed to parse filename {filename}")

        current_flags = set(parsed.get("flags", ""))
        if add_flags:
            current_flags.update(add_flags)
        if remove_flags:
            current_flags.difference_update(remove_flags)

        new_flags_str = "".join(sorted(list(current_flags))) # Keep flags sorted

        # Reconstruct filename base
        filename_base = f"{parsed['timestamp_ns']}.{parsed['unique_id']}.{parsed['hostname']}"
        if new_flags_str:
             new_filename = f"{filename_base}:2,{new_flags_str}"
        else:
             # If no flags remain, the :2, part might be omitted depending on strictness
             # For consistency, let's keep it but empty: filename_base + ":2,"
             # Or remove it entirely:
             new_filename = filename_base # Revert to base if no flags

        if new_filename == filename:
            log.debug(f"Flags for {filename} already up-to-date.")
            return filename # No change needed

        new_filepath = self.cur_path / new_filename # Use Path object

        try:
            cur_filepath.rename(new_filepath) # Use Path.rename()
            log.debug(f"Updated flags for {filename} -> {new_filename}")
            return new_filename
        except OSError as e:
            log.error(f"OS Error updating flags for {filename} -> {new_filename}: {e}", exc_info=True)
            raise MemdirIOError(f"Failed to update flags for {filename}: {e}") from e

    def move_memory(self, source_dir: str, filename: str, dest_dir: str = CUR_DIR, add_flags: Optional[str] = None) -> str:
        """
        Moves a memory file between directories (e.g., new -> cur) and optionally adds flags.

        Args:
            source_dir: The source directory ('new' or 'cur').
            filename: The filename to move.
            dest_dir: The destination directory (usually 'cur').
            add_flags: Optional flags to add during the move (applied to the destination filename).

        Returns:
            The final filename in the destination directory.

        Raises:
            MemdirIOError: If moving fails.
            FileNotFoundError: If the source file doesn't exist.
        """
        if source_dir not in [NEW_DIR, CUR_DIR] or dest_dir not in [CUR_DIR]: # Only allow moving to 'cur' for now
             raise ValueError(f"Invalid source ('{source_dir}') or destination ('{dest_dir}') directory.")

        source_base = self.new_path if source_dir == NEW_DIR else self.cur_path
        source_filepath = source_base / filename # Use Path object

        if not source_filepath.exists(): # Use Path.exists()
            log.error(f"Cannot move non-existent file from {source_dir}: {filename}")
            raise FileNotFoundError(f"File not found in {source_dir} directory: {filename}")

        parsed = self._parse_filename(filename)
        if not parsed:
            raise MemdirIOError(f"Cannot move file: Failed to parse filename {filename}")

        current_flags = set(parsed.get("flags", ""))
        if add_flags:
            current_flags.update(add_flags)
        new_flags_str = "".join(sorted(list(current_flags)))

        # Construct destination filename
        filename_base = f"{parsed['timestamp_ns']}.{parsed['unique_id']}.{parsed['hostname']}"
        if new_flags_str:
             dest_filename = f"{filename_base}:2,{new_flags_str}"
        else:
             dest_filename = filename_base

        dest_filepath = os.path.join(self.cur_path, dest_filename) # Assuming dest_dir is always 'cur'

        try:
            os.rename(source_filepath, dest_filepath)
            log.debug(f"Moved memory file {filename} from {source_dir} to {dest_dir} as {dest_filename}")
            return dest_filename
        except OSError as e:
            log.error(f"OS Error moving file {filename} from {source_dir} to {dest_dir}: {e}", exc_info=True)
            raise MemdirIOError(f"Failed to move file {filename}: {e}") from e

    def list_files(self, directory: str) -> List[str]:
         """Lists all files directly within a specified Memdir subdirectory (new or cur)."""
         if directory not in [NEW_DIR, CUR_DIR, TMP_DIR]:
              raise ValueError(f"Invalid directory specified for listing: {directory}")

         path = self.memdir_root / directory # Use Path object
         try:
              # Use Path.iterdir() and check if it's a file
              return [f.name for f in path.iterdir() if f.is_file()]
         except OSError as e:
              log.error(f"Error listing files in {path}: {e}", exc_info=True)
              raise MemdirIOError(f"Failed to list files in {directory}: {e}") from e


    def query_memories(
        self,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        flags_include: Optional[str] = None,
        flags_exclude: Optional[str] = None,
        max_results: Optional[int] = None,
        content_keywords: Optional[List[str]] = None # Basic keyword search (slow)
        ) -> List[Tuple[str, Dict[str, Any]]]: # Returns list of (filename, parsed_info)
        """
        Queries memory files in the 'cur' directory based on criteria.
        NOTE: This is a basic implementation scanning filenames. Content search is slow.
              Consider implementing proper indexing for performance.

        Args:
            time_start: Minimum timestamp (inclusive).
            time_end: Maximum timestamp (exclusive).
            flags_include: String of flags that MUST be present.
            flags_exclude: String of flags that MUST NOT be present.
            max_results: Maximum number of results to return.
            content_keywords: List of keywords to search for in the file content (SLOW).

        Returns:
            A list of tuples, each containing (filename, parsed_filename_info).
            Sorted by timestamp descending (most recent first).
        """
        log.debug(f"Querying memories in 'cur': start={time_start}, end={time_end}, incl='{flags_include}', excl='{flags_exclude}', keywords='{content_keywords}'")
        results = []
        files_scanned = 0

        try:
            # Iterate through files in 'cur' directory, sorting by name might help slightly
            # but true chronological order requires parsing timestamps.
            # Listing and then sorting might be memory intensive for huge dirs.
            # For now, list all and sort in memory.
            all_filenames = self.list_files(CUR_DIR)
            # Sort filenames primarily by timestamp (first part) descending
            all_filenames.sort(key=lambda f: int(f.split('.', 1)[0]) if '.' in f else 0, reverse=True)

            for filename in all_filenames:
                files_scanned += 1
                parsed_info = self._parse_filename(filename)
                if not parsed_info:
                    continue # Skip unparseable filenames

                # --- Filter by Timestamp ---
                file_dt = parsed_info['timestamp_dt']
                if time_start and file_dt < time_start:
                    continue
                if time_end and file_dt >= time_end:
                    continue

                # --- Filter by Flags ---
                file_flags = set(parsed_info.get("flags", ""))
                if flags_include and not set(flags_include).issubset(file_flags):
                    continue
                if flags_exclude and not set(flags_exclude).isdisjoint(file_flags):
                    continue

                # --- Filter by Content Keywords (SLOW) ---
                if content_keywords:
                    try:
                        # Read the content only if other filters pass
                        entry = self.read_memory(CUR_DIR, filename)
                        content_str = entry.model_dump_json() # Search in the JSON string
                        if not all(keyword.lower() in content_str.lower() for keyword in content_keywords):
                            continue
                    except MemdirIOError as e:
                        log.warning(f"Could not read content of {filename} for keyword search: {e}")
                        continue # Skip file if content cannot be read

                # If all filters pass, add to results
                results.append((filename, parsed_info))

                if max_results is not None and len(results) >= max_results:
                    break # Stop early if max results reached

            log.debug(f"Query finished. Scanned {files_scanned} files, found {len(results)} results.")
            # Results are already sorted by timestamp descending due to initial sort
            return results

        except MemdirIOError as e:
             log.error(f"IO Error during memory query: {e}", exc_info=True)
             raise MemoryQueryError(f"IO Error during query: {e}") from e
        except Exception as e:
             log.error(f"Unexpected error during memory query: {e}", exc_info=True)
             raise MemoryQueryError(f"Unexpected error during query: {e}") from e


    def prune_memories(self, max_age_days: Optional[int] = None, max_count: Optional[int] = None) -> Tuple[int, int]:
        """
        Prunes old memory files from the 'cur' directory based on age or count.

        Args:
            max_age_days: Maximum age in days. Files older than this will be deleted.
            max_count: Maximum number of files to keep. If exceeded, oldest files are deleted.

        Returns:
            A tuple: (number_of_files_deleted_by_age, number_of_files_deleted_by_count)
        """
        deleted_by_age = 0
        deleted_by_count = 0

        if max_age_days is None and max_count is None:
            log.info("Pruning skipped: No max_age_days or max_count specified.")
            return 0, 0

        log.info(f"Starting memory pruning in 'cur'. Max Age: {max_age_days} days, Max Count: {max_count}")
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(days=max_age_days) if max_age_days is not None else None

        try:
            all_files_info = []
            for filename in self.list_files(CUR_DIR):
                parsed = self._parse_filename(filename)
                if parsed:
                    all_files_info.append((filename, parsed['timestamp_dt']))

            # Sort by timestamp ascending (oldest first)
            all_files_info.sort(key=lambda item: item[1])

            files_to_delete = set() # Store filenames to delete

            # --- Pruning by Age ---
            if cutoff_time:
                for filename, timestamp_dt in all_files_info:
                    if timestamp_dt < cutoff_time:
                        files_to_delete.add(filename)
                    else:
                        break # Since sorted, no need to check further
                deleted_by_age = len(files_to_delete)
                log.info(f"Identified {deleted_by_age} files older than {max_age_days} days for deletion.")

            # --- Pruning by Count ---
            if max_count is not None:
                 current_count = len(all_files_info)
                 if current_count > max_count:
                      num_to_delete_by_count = current_count - max_count
                      # Add the oldest files to the deletion set, avoiding duplicates
                      added_for_count = 0
                      for filename, _ in all_files_info:
                           if filename not in files_to_delete:
                                files_to_delete.add(filename)
                                added_for_count += 1
                                if added_for_count >= num_to_delete_by_count:
                                     break
                      # Calculate actual deletions *caused* by count limit
                      deleted_by_count = added_for_count
                      log.info(f"Identified {deleted_by_count} additional oldest files for deletion to meet max count ({max_count}).")


            # --- Perform Deletion ---
            total_deleted = 0
            for filename in files_to_delete:
                filepath = self.cur_path / filename # Use Path object
                try:
                    filepath.unlink() # Use Path.unlink()
                    log.debug(f"Pruned memory file: {filepath}")
                    total_deleted += 1
                except OSError as e:
                    log.error(f"Error pruning file {filepath}: {e}", exc_info=True)

            log.info(f"Memory pruning complete. Total files deleted: {total_deleted} (Age: {deleted_by_age}, Count: {deleted_by_count})")
            return deleted_by_age, deleted_by_count

        except MemdirIOError as e:
             log.error(f"IO Error during memory pruning: {e}", exc_info=True)
             # Don't re-raise, just log the error and return 0,0
             return 0, 0
        except Exception as e:
             log.error(f"Unexpected error during memory pruning: {e}", exc_info=True)
             return 0, 0

# Example Usage (can be removed or moved to tests)
# if __name__ == "__main__":
#     print("Testing MemoryStorage...")
#     storage = MemoryStorage()

#     # Create dummy entries
#     entry1 = MemoryEntry(entry_type="Test", source_service="TestScript", payload={"data": 1})
#     entry2 = MemoryEntry(entry_type="Test", source_service="TestScript", payload={"data": 2, "info": "abc"})

#     try:
#         # Save
#         fname1 = storage.save_memory(entry1)
#         print(f"Saved entry 1 as: {fname1}")
#         time.sleep(0.1) # Ensure different timestamp
#         fname2 = storage.save_memory(entry2)
#         print(f"Saved entry 2 as: {fname2}")

#         # List 'new'
#         new_files = storage.list_files(NEW_DIR)
#         print(f"\nFiles in 'new': {new_files}")

#         # Move to 'cur' with flags
#         cur_fname1 = storage.move_memory(NEW_DIR, fname1, add_flags="S") # Mark as Seen
#         print(f"Moved {fname1} to 'cur' as {cur_fname1}")
#         cur_fname2 = storage.move_memory(NEW_DIR, fname2, add_flags="SI") # Mark as Seen, Important
#         print(f"Moved {fname2} to 'cur' as {cur_fname2}")

#         # List 'cur'
#         cur_files = storage.list_files(CUR_DIR)
#         print(f"\nFiles in 'cur': {cur_files}")

#         # Read back
#         read_entry1 = storage.read_memory(CUR_DIR, cur_fname1)
#         print(f"\nRead entry 1 ({cur_fname1}): {read_entry1.payload}")
#         read_entry2 = storage.read_memory(CUR_DIR, cur_fname2)
#         print(f"Read entry 2 ({cur_fname2}): {read_entry2.payload}")

#         # Update flags
#         updated_fname2 = storage.update_flags(cur_fname2, add_flags="P", remove_flags="I") # Add Processed, remove Important
#         print(f"\nUpdated flags for {cur_fname2} -> {updated_fname2}")
#         cur_files = storage.list_files(CUR_DIR)
#         print(f"Files in 'cur' after flag update: {cur_files}")

#         # Query
#         print("\nQuerying memories (flag 'S'):")
#         query_results_s = storage.query_memories(flags_include="S")
#         for fname, info in query_results_s:
#             print(f"- {fname} (ts: {info['timestamp_dt']})")

#         print("\nQuerying memories (flag 'P'):")
#         query_results_p = storage.query_memories(flags_include="P")
#         for fname, info in query_results_p:
#             print(f"- {fname} (ts: {info['timestamp_dt']})")

#         print("\nQuerying memories (keyword 'abc'):")
#         query_results_kw = storage.query_memories(content_keywords=["abc"])
#         for fname, info in query_results_kw:
#             print(f"- {fname} (ts: {info['timestamp_dt']})")


#         # Pruning (Example - set low limits for testing)
#         print("\nTesting pruning...")
#         # Create a few more files to test pruning
#         for i in range(3):
#              time.sleep(0.05)
#              ef = storage.save_memory(MemoryEntry(entry_type="Filler", source_service="PruneTest", payload={"i":i}))
#              storage.move_memory(NEW_DIR, ef, add_flags="S")

#         print(f"Files in 'cur' before prune: {storage.list_files(CUR_DIR)}")
#         # deleted_age, deleted_count = storage.prune_memories(max_age_days=0.0001) # Prune very old (likely none)
#         deleted_age, deleted_count = storage.prune_memories(max_count=2) # Keep only 2 newest
#         print(f"Pruning result: Deleted by age={deleted_age}, Deleted by count={deleted_count}")
#         print(f"Files in 'cur' after prune: {storage.list_files(CUR_DIR)}")


#     except (MemoryServiceError, MemdirIOError, FileNotFoundError) as e:
#         print(f"\nError during MemoryStorage test: {e}")
#     except Exception as e:
#         print(f"\nUnexpected error during MemoryStorage test: {e}")
