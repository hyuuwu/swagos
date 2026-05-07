import sys
import shlex
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Callable, Dict, List, Optional

from colorama import Fore, init

init()


@dataclass
class VFSNode:
    name: str
    parent: Optional["DirNode"]


@dataclass
class FileNode(VFSNode):
    content: str = ""


@dataclass
class DirNode(VFSNode):
    children: Dict[str, VFSNode] = field(default_factory=dict)


class VirtualFileSystem:
    def __init__(self) -> None:
        self.root = DirNode(name="", parent=None)
        self._ensure_dir("/home/user")

    def _ensure_dir(self, path: str) -> None:
        node = self.root
        for part in self._split(path):
            existing = node.children.get(part)
            if existing is None:
                new_node = DirNode(name=part, parent=node)
                node.children[part] = new_node
                node = new_node
            elif isinstance(existing, DirNode):
                node = existing
            else:
                raise ValueError(f"Path segment '{part}' is not a directory.")

    def _split(self, path: str) -> List[str]:
        parts = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            parts.append(part)
        return parts

    def _traverse(self, path: str, cwd: DirNode, stop_before_last: bool = False):
        if path is None or path == "":
            if stop_before_last:
                raise ValueError("Path is required.")
            return cwd
        parts = self._split(path)
        if stop_before_last:
            if not parts:
                raise ValueError("Path is required.")
            target_parts = parts[:-1]
        else:
            target_parts = parts
        node: VFSNode = self.root if path.startswith("/") else cwd
        for part in target_parts:
            if part == "..":
                node = node.parent if node.parent else node
                continue
            if not isinstance(node, DirNode):
                raise NotADirectoryError("Not a directory.")
            next_node = node.children.get(part)
            if next_node is None:
                raise FileNotFoundError("No such file or directory.")
            node = next_node
        if stop_before_last:
            return node, parts[-1]
        return node

    def resolve(self, path: str, cwd: DirNode) -> VFSNode:
        return self._traverse(path, cwd)

    def resolve_dir(self, path: str, cwd: DirNode) -> DirNode:
        node = self.resolve(path, cwd)
        if not isinstance(node, DirNode):
            raise NotADirectoryError("Not a directory.")
        return node

    def path_of(self, node: VFSNode) -> str:
        if node is self.root:
            return "/"
        parts = []
        current = node
        while current.parent is not None:
            parts.append(current.name)
            current = current.parent
        return "/" + "/".join(reversed(parts))

    def list_path(
        self,
        path: Optional[str],
        cwd: DirNode,
        include_hidden: bool,
        long_format: bool,
    ) -> List[str]:
        target = path if path is not None else "."
        node = self.resolve(target, cwd)
        if isinstance(node, FileNode):
            return [self._format_entry(node)] if long_format else [node.name]
        entries = list(node.children.values())
        names = sorted(child.name for child in entries)
        if not include_hidden:
            names = [name for name in names if not name.startswith(".")]
        if long_format:
            lines = []
            if include_hidden:
                lines.append(self._format_entry(node, name_override="."))
                parent = node.parent if node.parent else node
                lines.append(self._format_entry(parent, name_override=".."))
            for name in names:
                lines.append(self._format_entry(node.children[name]))
            return lines
        if include_hidden:
            return [".", ".."] + names
        return names

    def _format_entry(self, node: VFSNode, name_override: Optional[str] = None) -> str:
        is_dir = isinstance(node, DirNode)
        size = 0 if is_dir else len(node.content)
        name = name_override if name_override is not None else node.name
        type_char = "d" if is_dir else "-"
        return f"{type_char} {size:>4} {name}"

    def make_dir(self, path: str, cwd: DirNode) -> None:
        parent, name = self._traverse(path, cwd, stop_before_last=True)
        if name in ("", ".", ".."):
            raise ValueError("Invalid directory name.")
        if not isinstance(parent, DirNode):
            raise NotADirectoryError("Not a directory.")
        if name in parent.children:
            raise FileExistsError("File exists.")
        parent.children[name] = DirNode(name=name, parent=parent)

    def make_file(self, path: str, cwd: DirNode) -> None:
        parent, name = self._traverse(path, cwd, stop_before_last=True)
        if name in ("", ".", ".."):
            raise ValueError("Invalid file name.")
        if not isinstance(parent, DirNode):
            raise NotADirectoryError("Not a directory.")
        existing = parent.children.get(name)
        if existing is None:
            parent.children[name] = FileNode(name=name, parent=parent)
        elif isinstance(existing, DirNode):
            raise IsADirectoryError("Is a directory.")

    def write_file(self, path: str, content: str, cwd: DirNode) -> None:
        parent, name = self._traverse(path, cwd, stop_before_last=True)
        if name in ("", ".", ".."):
            raise ValueError("Invalid file name.")
        if not isinstance(parent, DirNode):
            raise NotADirectoryError("Not a directory.")
        existing = parent.children.get(name)
        if existing is None:
            parent.children[name] = FileNode(name=name, parent=parent, content=content)
        elif isinstance(existing, FileNode):
            existing.content = content
        else:
            raise IsADirectoryError("Is a directory.")

    def read_file(self, path: str, cwd: DirNode) -> str:
        node = self.resolve(path, cwd)
        if isinstance(node, DirNode):
            raise IsADirectoryError("Is a directory.")
        return node.content

    def remove_file(self, path: str, cwd: DirNode) -> None:
        node = self.resolve(path, cwd)
        if isinstance(node, DirNode):
            raise IsADirectoryError("Is a directory.")
        if node.parent is None:
            raise ValueError("Cannot remove root.")
        del node.parent.children[node.name]

    def exists(self, path: str, cwd: Optional[DirNode] = None) -> bool:
        try:
            self.resolve(path, cwd or self.root)
            return True
        except (FileNotFoundError, NotADirectoryError, ValueError):
            return False

    def is_dir(self, path: str, cwd: Optional[DirNode] = None) -> bool:
        try:
            node = self.resolve(path, cwd or self.root)
            return isinstance(node, DirNode)
        except (FileNotFoundError, NotADirectoryError, ValueError):
            return False


@dataclass
class Quest:
    description: str
    hint: str
    check: Callable[["VirtualFileSystem", DirNode], bool]


class QuestEngine:
    def __init__(self) -> None:
        self._quests = self._build_quests()
        self._index = 0

    def _build_quests(self) -> List[Quest]:
        return [
            Quest(
                description="Quest 1: Navigate to /home/user and create a file named 'hello.txt'.",
                hint="Hint: use 'cd /home/user' and 'touch hello.txt'.",
                check=lambda vfs, cwd: vfs.exists("/home/user/hello.txt")
                and vfs.path_of(cwd) == "/home/user",
            ),
            Quest(
                description="Quest 2: Create a directory named 'projects' inside /home/user.",
                hint="Hint: use 'mkdir projects' while in /home/user.",
                check=lambda vfs, cwd: vfs.is_dir("/home/user/projects"),
            ),
            Quest(
                description="Quest 3: Write 'Welcome' into /home/user/projects/notes.txt using echo.",
                hint="Hint: use \"echo Welcome > /home/user/projects/notes.txt\".",
                check=lambda vfs, cwd: vfs.exists("/home/user/projects/notes.txt")
                and vfs.read_file("/home/user/projects/notes.txt", cwd) == "Welcome",
            ),
        ]

    def current(self) -> Optional[Quest]:
        if self._index >= len(self._quests):
            return None
        return self._quests[self._index]

    def check_progress(self, vfs: VirtualFileSystem, cwd: DirNode) -> None:
        quest = self.current()
        if quest and quest.check(vfs, cwd):
            print(Fore.CYAN + f"Completed! {quest.description}")
            self._index += 1
            next_quest = self.current()
            if next_quest:
                print(Fore.MAGENTA + f"Next quest: {next_quest.description}")
            else:
                print(Fore.GREEN + "All quests complete! Great job.")


class CommandDispatcher:
    def __init__(self, vfs: VirtualFileSystem, quest_engine: QuestEngine) -> None:
        self.vfs = vfs
        self.quest_engine = quest_engine
        self.cwd = self.vfs.resolve_dir("/home/user", self.vfs.root)
        self.commands = {
            "pwd": self._cmd_pwd,
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "touch": self._cmd_touch,
            "mkdir": self._cmd_mkdir,
            "rm": self._cmd_rm,
            "echo": self._cmd_echo,
            "cat": self._cmd_cat,
            "help": self._cmd_help,
            "quest": self._cmd_quest,
            "clear": self._cmd_clear,
            "exit": self._cmd_exit,
        }

    def execute(self, raw_command: str) -> None:
        try:
            tokens = shlex.split(raw_command)
        except ValueError as exc:
            print(Fore.RED + f"Parse error: {exc}")
            return
        if not tokens:
            return
        command, args = tokens[0], tokens[1:]
        handler = self.commands.get(command)
        if handler is None:
            self._unknown_command(command)
            return
        handler(args)
        self.quest_engine.check_progress(self.vfs, self.cwd)

    def _unknown_command(self, command: str) -> None:
        suggestions = get_close_matches(command, self.commands.keys(), n=1)
        if suggestions:
            hint = f"Hint: try '{suggestions[0]}'."
        else:
            hint = "Hint: use 'help' to see available commands."
        print(Fore.YELLOW + f"Unknown command: {command}. {hint}")

    def _cmd_pwd(self, args: List[str]) -> None:
        print(self.vfs.path_of(self.cwd))

    def _cmd_ls(self, args: List[str]) -> None:
        include_hidden = False
        long_format = False
        paths = []
        for arg in args:
            if arg.startswith("-"):
                invalid = set(arg[1:]) - {"a", "l"}
                if invalid:
                    invalid_char = sorted(invalid)[0]
                    print(Fore.RED + f"ls: invalid option -- '{invalid_char}'")
                    return
                if "a" in arg:
                    include_hidden = True
                if "l" in arg:
                    long_format = True
            else:
                paths.append(arg)
        targets = paths if paths else [None]
        for index, target in enumerate(targets):
            try:
                if len(targets) > 1:
                    header = target if target is not None else "."
                    print(f"{header}:")
                for line in self.vfs.list_path(target, self.cwd, include_hidden, long_format):
                    print(line)
                if len(targets) > 1 and index < len(targets) - 1:
                    print()
            except (FileNotFoundError, NotADirectoryError) as exc:
                print(Fore.RED + f"ls: {exc}")

    def _cmd_cd(self, args: List[str]) -> None:
        target = args[0] if args else "/home/user"
        try:
            self.cwd = self.vfs.resolve_dir(target, self.cwd)
        except (FileNotFoundError, NotADirectoryError) as exc:
            print(Fore.RED + f"cd: {exc}")

    def _cmd_touch(self, args: List[str]) -> None:
        if not args:
            print(Fore.RED + "touch: missing file operand")
            return
        for target in args:
            try:
                self.vfs.make_file(target, self.cwd)
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError, ValueError) as exc:
                print(Fore.RED + f"touch: {exc}")

    def _cmd_mkdir(self, args: List[str]) -> None:
        if not args:
            print(Fore.RED + "mkdir: missing directory operand")
            return
        for target in args:
            try:
                self.vfs.make_dir(target, self.cwd)
            except (FileExistsError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
                print(Fore.RED + f"mkdir: {exc}")

    def _cmd_rm(self, args: List[str]) -> None:
        if not args:
            print(Fore.RED + "rm: missing file operand")
            return
        for target in args:
            try:
                self.vfs.remove_file(target, self.cwd)
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError, ValueError) as exc:
                print(Fore.RED + f"rm: {exc}")

    def _cmd_echo(self, args: List[str]) -> None:
        if not args:
            print()
            return
        if ">" in args:
            index = args.index(">")
            content = " ".join(args[:index])
            if index + 1 >= len(args):
                print(Fore.RED + "echo: missing file for redirection")
                return
            if index + 2 != len(args):
                print(Fore.RED + "echo: too many arguments for redirection")
                return
            target = args[index + 1]
            try:
                self.vfs.write_file(target, content, self.cwd)
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError, ValueError) as exc:
                print(Fore.RED + f"echo: {exc}")
            return
        print(" ".join(args))

    def _cmd_cat(self, args: List[str]) -> None:
        if not args:
            print(Fore.RED + "cat: missing file operand")
            return
        for target in args:
            try:
                print(self.vfs.read_file(target, self.cwd))
            except (FileNotFoundError, NotADirectoryError, IsADirectoryError) as exc:
                print(Fore.RED + f"cat: {exc}")

    def _cmd_help(self, args: List[str]) -> None:
        print(
            """
Available commands (VFS only):
- pwd: Print working directory
- ls [-a] [-l] [path]: List files/directories
- cd [path]: Change directory
- touch <file>: Create an empty file
- mkdir <dir>: Create a directory
- rm <file>: Remove a file
- echo <text> [> file]: Print text or write to a file
- cat <file>: Display file contents
- quest: Show your current learning quest
- clear: Clear the screen
- exit: Exit the shell
            """
        )

    def _cmd_quest(self, args: List[str]) -> None:
        quest = self.quest_engine.current()
        if quest is None:
            print(Fore.GREEN + "All quests complete! Great job.")
        else:
            print(Fore.MAGENTA + quest.description)
            print(Fore.YELLOW + quest.hint)

    def _cmd_clear(self, args: List[str]) -> None:
        print("\033[2J\033[H", end="")

    def _cmd_exit(self, args: List[str]) -> None:
        sys.exit(0)


_vfs = VirtualFileSystem()
_quests = QuestEngine()
_shell = CommandDispatcher(_vfs, _quests)


def execute_command(command: str) -> None:
    _shell.execute(command)


def show_current_quest() -> None:
    quest = _quests.current()
    if quest is not None:
        print(Fore.MAGENTA + quest.description)
        print(Fore.YELLOW + quest.hint)
