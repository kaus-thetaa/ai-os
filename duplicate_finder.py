import hashlib
from pathlib import Path
from collections import defaultdict

import file_scanner


class DuplicateFinderError(Exception):
    pass


# read files in chunks to avoid loading huge files into memory
HASH_CHUNK_SIZE = 65536


def compute_file_hash(file_path: str) -> str:
    # returns sha256 hash of a files content
    file = Path(file_path)

    if not file.exists():
        raise DuplicateFinderError(f"'{file_path}' does not exist")

    hasher = hashlib.sha256()

    try:
        with open(file, "rb") as f:
            while True:
                chunk = f.read(HASH_CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
    except OSError as error:
        raise DuplicateFinderError(f"failed to read '{file_path}': {error}")

    return hasher.hexdigest()


def find_duplicates(folder_path: str, recursive: bool = True) -> list[dict]:
    # groups files by content hash and returns groups with more than one file
    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=recursive)
    except file_scanner.FileScannerError as error:
        raise DuplicateFinderError(f"could not scan folder: {error}")

    hash_to_files = defaultdict(list)

    for file_path in all_files:
        try:
            file_hash = compute_file_hash(str(file_path))
        except DuplicateFinderError:
            # skip files we cant read instead of failing the whole scan
            continue

        hash_to_files[file_hash].append(file_path)

    duplicate_groups = []

    for file_hash, files in hash_to_files.items():
        if len(files) < 2:
            continue

        # suggest keeping the oldest file as the likely original
        files_with_mtime = [(f, f.stat().st_mtime) for f in files]
        files_with_mtime.sort(key=lambda pair: pair[1])

        oldest_file = files_with_mtime[0][0]

        duplicate_groups.append({
            "hash": file_hash,
            "files": [str(f) for f, _ in files_with_mtime],
            "suggested_keep": str(oldest_file),
            "duplicate_count": len(files),
        })

    return duplicate_groups


def get_total_wasted_space(duplicate_groups: list[dict]) -> int:
    # sums up bytes taken by extra copies not counting the one to keep
    total_wasted = 0

    for group in duplicate_groups:
        files = group["files"]
        if len(files) < 2:
            continue

        # every file except the one being kept counts as wasted space
        for file_path in files:
            if file_path == group["suggested_keep"]:
                continue
            try:
                total_wasted += Path(file_path).stat().st_size
            except OSError:
                continue

    return total_wasted


if __name__ == "__main__":
    import tempfile
    import shutil

    print("duplicate_finder.py self-test")
    print("-" * 50)

    temp_dir = Path(tempfile.mkdtemp(prefix="aios_dupe_test_"))

    # create two identical files and one different file
    (temp_dir / "original.txt").write_text("same content here", encoding="utf-8")
    (temp_dir / "copy.txt").write_text("same content here", encoding="utf-8")
    (temp_dir / "different.txt").write_text("totally different content", encoding="utf-8")

    print(f"created test files in {temp_dir}")

    print("-" * 50)
    print("testing compute_file_hash")
    hash_a = compute_file_hash(str(temp_dir / "original.txt"))
    hash_b = compute_file_hash(str(temp_dir / "copy.txt"))
    hash_c = compute_file_hash(str(temp_dir / "different.txt"))

    if hash_a == hash_b:
        print("ok - identical files produced the same hash")
    else:
        print("mismatch - identical files produced different hashes")

    if hash_a != hash_c:
        print("ok - different files produced different hashes")
    else:
        print("mismatch - different files produced the same hash")

    print("-" * 50)
    print("testing find_duplicates")
    duplicate_groups = find_duplicates(str(temp_dir), recursive=False)

    print(f"duplicate groups found: {len(duplicate_groups)}")
    for group in duplicate_groups:
        print(f"  duplicate count: {group['duplicate_count']}")
        print(f"  suggested keep: {Path(group['suggested_keep']).name}")
        for file_path in group["files"]:
            print(f"    - {Path(file_path).name}")

    print("-" * 50)
    print("testing get_total_wasted_space")
    wasted = get_total_wasted_space(duplicate_groups)
    print(f"wasted space: {wasted} bytes")

    print("-" * 50)
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("-" * 50)
    print("duplicate_finder.py self-test complete")