import shutil
from pathlib import Path

import file_scanner
import config


class OrganizerError(Exception):
    pass


DEFAULT_CATEGORY_FOLDER_NAMES = {
    "image": "Images",
    "video": "Videos",
    "document": "Documents",
    "text": "Text Files",
    "other": "Other",
}


def organize_by_default_categories(folder_path: str) -> dict:
    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=False)
    except file_scanner.FileScannerError as error:
        raise OrganizerError(f"could not organize folder: {error}")

    rules = []
    for file_type, folder_name in DEFAULT_CATEGORY_FOLDER_NAMES.items():
        extensions = _get_extensions_for_type(file_type)
        if extensions:
            rules.append({
                "extensions": extensions,
                "destination_folder_name": folder_name,
            })

    return organize_by_custom_rules(folder_path, rules)


def _get_extensions_for_type(file_type: str) -> set:
    # maps a broad type name to its extension set from config
    if file_type == "image":
        return config.IMAGE_EXTENSIONS
    elif file_type == "video":
        return config.VIDEO_EXTENSIONS
    elif file_type == "document":
        return config.SUPPORTED_DOCUMENT_EXTENSIONS
    elif file_type == "text":
        return config.SUPPORTED_TEXT_EXTENSIONS
    else:
        return set()


def organize_by_custom_rules(folder_path: str, rules: list[dict]) -> dict:
    source_folder = Path(folder_path)

    if not source_folder.exists() or not source_folder.is_dir():
        raise OrganizerError(f"'{folder_path}' does not exist or is not a folder")

    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=False)
    except file_scanner.FileScannerError as error:
        raise OrganizerError(f"could not scan folder: {error}")

    files_moved = 0
    files_skipped = 0
    moves = []
    skipped_reasons = []

    for file_path in all_files:
        extension = file_path.suffix.lower()

        # first matching rule wins if rules overlap
        matching_rule = None
        for rule in rules:
            if extension in rule["extensions"]:
                matching_rule = rule
                break

        if matching_rule is None:
            continue

        destination_folder = source_folder / matching_rule["destination_folder_name"]

        try:
            destination_folder.mkdir(exist_ok=True)
        except OSError as error:
            raise OrganizerError(
                f"failed to create destination folder '{destination_folder}': {error}"
            )

        destination_path = destination_folder / file_path.name

        if destination_path.exists():
            files_skipped += 1
            skipped_reasons.append((
                file_path.name,
                f"a file named '{file_path.name}' already exists in "
                f"'{matching_rule['destination_folder_name']}'"
            ))
            continue

        try:
            shutil.move(str(file_path), str(destination_path))
            files_moved += 1
            moves.append((file_path.name, matching_rule["destination_folder_name"]))
        except OSError as error:
            files_skipped += 1
            skipped_reasons.append((file_path.name, str(error)))

    return {
        "files_moved": files_moved,
        "files_skipped": files_skipped,
        "moves": moves,
        "skipped_reasons": skipped_reasons,
    }


if __name__ == "__main__":
    import tempfile

    print("organizer.py self-test")
    print("-" * 50)

    temp_dir = Path(tempfile.mkdtemp(prefix="aios_organizer_test_"))

    test_files = [
        "photo1.jpg",
        "photo2.png",
        "clip1.mp4",
        "report.pdf",
        "notes.txt",
        "unknown_file.xyz",
    ]

    for file_name in test_files:
        (temp_dir / file_name).write_text("fake content for testing", encoding="utf-8")

    print(f"created {len(test_files)} test files in {temp_dir}")

    print("-" * 50)
    print("running organize_by_default_categories")
    try:
        result = organize_by_default_categories(str(temp_dir))
        print(f"files moved: {result['files_moved']}")
        print(f"files skipped: {result['files_skipped']}")
        for original_name, destination in result["moves"]:
            print(f"  {original_name} -> {destination}/")
    except OrganizerError as error:
        print(f"failed - {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        exit(1)

    print("-" * 50)
    print("verifying folder structure")
    expected_structure = {
        "Images": ["photo1.jpg", "photo2.png"],
        "Videos": ["clip1.mp4"],
        "Documents": ["report.pdf"],
        "Text Files": ["notes.txt"],
    }

    all_correct = True
    for folder_name, expected_files in expected_structure.items():
        folder = temp_dir / folder_name
        for expected_file in expected_files:
            if (folder / expected_file).exists():
                print(f"  ok - {folder_name}/{expected_file} exists")
            else:
                print(f"  mismatch - {folder_name}/{expected_file} not found")
                all_correct = False

    if (temp_dir / "unknown_file.xyz").exists():
        print("  ok - unknown_file.xyz correctly left in place")
    else:
        print("  mismatch - unknown_file.xyz should not have been moved")
        all_correct = False

    print("-" * 50)
    print("testing custom rules mode")

    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="aios_organizer_custom_test_"))
    (temp_dir / "pic.jpg").write_text("fake", encoding="utf-8")
    (temp_dir / "movie.mp4").write_text("fake", encoding="utf-8")

    custom_rules = [
        {
            "extensions": config.IMAGE_EXTENSIONS | config.VIDEO_EXTENSIONS,
            "destination_folder_name": "Media",
        }
    ]

    custom_result = organize_by_custom_rules(str(temp_dir), custom_rules)
    print(f"files moved: {custom_result['files_moved']}")
    if (temp_dir / "Media" / "pic.jpg").exists() and (temp_dir / "Media" / "movie.mp4").exists():
        print("ok - images and videos correctly grouped into media folder")
    else:
        print("mismatch - custom rule grouping did not work")
        all_correct = False

    print("-" * 50)
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("-" * 50)
    if all_correct:
        print("organizer.py self-test complete, all checks passed")
    else:
        print("organizer.py self-test complete, some checks reported mismatches")