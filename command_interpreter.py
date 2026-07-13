from pathlib import Path

import llm_engine
import organizer
import duplicate_finder
import renamer
import config


class CommandInterpreterError(Exception):
    pass


SYSTEM_INSTRUCTION = """
you are a command interpreter for a windows file assistant
you convert a plain english instruction into a single json plan
never explain anything, only output the json object

supported actions are organize, find_duplicates, rename

for organize, output this shape
{"action": "organize", "folder_path": "D:\\\\Downloads", "rules": [{"categories": ["images", "videos"], "destination_folder_name": "Media"}]}
valid categories are images, videos, documents, text, other
each rule can list one or more categories that go into the same destination folder

for find_duplicates, output this shape
{"action": "find_duplicates", "folder_path": "D:\\\\Downloads"}

for rename, output this shape
{"action": "rename", "folder_path": "D:\\\\Downloads"}

always include folder_path exactly as given in the instruction
if no folder is mentioned use the downloads folder
"""


CATEGORY_TO_EXTENSIONS = {
    "images": config.IMAGE_EXTENSIONS,
    "videos": config.VIDEO_EXTENSIONS,
    "documents": config.SUPPORTED_DOCUMENT_EXTENSIONS,
    "text": config.SUPPORTED_TEXT_EXTENSIONS,
}


def parse_command(instruction: str) -> dict:
    # turns free text into a structured plan without executing anything
    if not instruction or not instruction.strip():
        raise CommandInterpreterError("instruction cannot be empty")

    try:
        plan = llm_engine.ask_llm_for_json(
            prompt=instruction.strip(),
            system_instruction=SYSTEM_INSTRUCTION,
        )
    except (llm_engine.LLMConnectionError, ValueError) as error:
        raise CommandInterpreterError(f"failed to interpret command: {error}")

    _validate_plan(plan)
    return plan


def _validate_plan(plan: dict) -> None:
    # checks the plan has everything execute_plan will need
    if "action" not in plan:
        raise CommandInterpreterError("plan is missing an action")

    action = plan["action"]

    if action not in ("organize", "find_duplicates", "rename"):
        raise CommandInterpreterError(f"unknown action '{action}'")

    if "folder_path" not in plan or not plan["folder_path"]:
        raise CommandInterpreterError("plan is missing a folder_path")

    folder = Path(plan["folder_path"])
    if not folder.exists() or not folder.is_dir():
        raise CommandInterpreterError(
            f"'{plan['folder_path']}' does not exist or is not a folder"
        )

    if action == "organize":
        if "rules" not in plan or not plan["rules"]:
            raise CommandInterpreterError("organize plan is missing rules")

        for rule in plan["rules"]:
            if "categories" not in rule or "destination_folder_name" not in rule:
                raise CommandInterpreterError("each rule needs categories and a destination folder name")

            for category in rule["categories"]:
                if category not in CATEGORY_TO_EXTENSIONS:
                    raise CommandInterpreterError(f"unknown category '{category}'")


def execute_plan(plan: dict) -> dict:
    # runs the actual file operation described by a validated plan
    _validate_plan(plan)

    action = plan["action"]
    folder_path = plan["folder_path"]

    if action == "organize":
        rules = []
        for rule in plan["rules"]:
            extensions = set()
            for category in rule["categories"]:
                extensions |= CATEGORY_TO_EXTENSIONS[category]
            rules.append({
                "extensions": extensions,
                "destination_folder_name": rule["destination_folder_name"],
            })

        try:
            return organizer.organize_by_custom_rules(folder_path, rules)
        except organizer.OrganizerError as error:
            raise CommandInterpreterError(f"organize failed: {error}")

    elif action == "find_duplicates":
        try:
            groups = duplicate_finder.find_duplicates(folder_path, recursive=False)
            wasted = duplicate_finder.get_total_wasted_space(groups)
            return {"duplicate_groups": groups, "wasted_bytes": wasted}
        except duplicate_finder.DuplicateFinderError as error:
            raise CommandInterpreterError(f"duplicate search failed: {error}")

    elif action == "rename":
        try:
            all_files = organizer.file_scanner.list_files_in_folder(folder_path, recursive=False)
        except organizer.file_scanner.FileScannerError as error:
            raise CommandInterpreterError(f"could not scan folder: {error}")

        renamed = []
        skipped = []

        for file_path in all_files:
            try:
                result = renamer.suggest_and_rename(str(file_path))
                renamed.append(result)
            except renamer.RenamerError as error:
                skipped.append((file_path.name, str(error)))

        return {"renamed": renamed, "skipped": skipped}


if __name__ == "__main__":
    import tempfile
    import shutil

    print("command_interpreter.py self-test")
    print("-" * 50)

    print("checking ollama connection")
    if not llm_engine.is_ollama_available():
        print("failed - ollama is not reachable")
        exit(1)
    print("ok - ollama is reachable")

    print("-" * 50)
    print("creating temp folder with fake images and videos")

    temp_dir = Path(tempfile.mkdtemp(prefix="aios_cmd_test_"))
    (temp_dir / "photo.jpg").write_text("fake", encoding="utf-8")
    (temp_dir / "clip.mp4").write_text("fake", encoding="utf-8")
    (temp_dir / "notes.txt").write_text("fake", encoding="utf-8")

    print(f"created test files in {temp_dir}")

    print("-" * 50)
    instruction = f"go to {temp_dir} and separate images and videos into two folders"
    print(f"instruction: {instruction}")

    try:
        plan = parse_command(instruction)
        print(f"parsed plan: {plan}")
    except CommandInterpreterError as error:
        print(f"failed - {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        exit(1)

    print("-" * 50)
    print("executing plan")
    try:
        result = execute_plan(plan)
        print(f"result: {result}")
    except CommandInterpreterError as error:
        print(f"failed - {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        exit(1)

    print("-" * 50)
    print("verifying folders were created separately")
    contents = [p.name for p in temp_dir.iterdir()]
    print(f"top level contents now: {contents}")

    print("-" * 50)
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("-" * 50)
    print("command_interpreter.py self-test complete")