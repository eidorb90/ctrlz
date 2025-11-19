import sys
import os
import zlib
import hashlib
import datetime 
from colorama import init, Fore, Style
import requests

def main():
    init(autoreset=True)  # Initialize colorama
    
    command = sys.argv[1]
    if command == "init":
        try:
            os.mkdir(".ctrlz")
            os.mkdir(".ctrlz/objects")
            os.mkdir(".ctrlz/refs")
            with open(".ctrlz/HEAD", "w") as f:
                f.write("ref: refs/heads/main\n")
            print(Fore.GREEN + Style.BRIGHT + "Initialized ctrlz directory")
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during init: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "cat-file":
        try:
            hash = sys.argv[3]
            if not os.path.exists(f".ctrlz/objects/{hash[:2]}/{hash[2:]}"):
                print(Fore.RED + Style.BRIGHT + f"Object {hash} not found", file=sys.stderr)
                sys.exit(1)
            with open(f'.ctrlz/objects/{hash[:2]}/{hash[2:]}', 'rb') as f:
                content = f.read()
                decompressed = zlib.decompress(content)
                _, obj_content = decompressed.split(b'\x00', 1)
                print(Fore.CYAN + obj_content.decode('utf-8'), end="")
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during cat-file: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "hash-object":
        try:
            file_path = sys.argv[3]
            if file_path:
                hash = hash_object(file_path)
                print(Fore.MAGENTA + Style.BRIGHT + hash)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during hash-object: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "ls-tree":
        try:
            if sys.argv[2] != '--name-only':
                print(Fore.RED + Style.BRIGHT + "Only --name-only option is supported for ls-tree", file=sys.stderr)
                raise RuntimeError("Only --name-only option is supported for ls-tree")
            ls_tree(sys.argv[3])
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during ls-tree: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "write-tree":
        try:
            write_tree()
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during write-tree: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "commit-tree":
        try:
            len_of_args = len(sys.argv)

            tree_hash = sys.argv[3]
            message = "blank commit message"
            parent = None
            if len_of_args >= 5:
                if sys.argv[4] == '-m':
                    message = sys.argv[5]
            if len_of_args >= 8:
                if sys.argv[6] == '-p':
                    parent = sys.argv[7]

            commit_hash = commit_tree(tree_hash, message, parent if parent else None)
            print(Fore.MAGENTA + Style.BRIGHT + commit_hash)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during commit-tree: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "add":
        try:
            if len(sys.argv) > 3:
                file_name = sys.argv[3]
                add(file_name)
            elif len(sys.argv) == 3 and sys.argv[2] == ".":
                add(".")
            else:
                print(Fore.RED + Style.BRIGHT + "Usage: ctrlz add <file_name> or ctrlz add .", file=sys.stderr)
                raise RuntimeError("Usage: ctrlz add <file_name> or ctrlz add .")
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during add: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "commit":
        try:
            message = sys.argv[3]
            commit(message=message)

        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during commit: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "status":
        try:
            status()
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during status: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "ls-commits":
        try:
            ls_commit()
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during ls-commits: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "checkout":
        try:
            hash = sys.argv[2] 
            checkout(hash)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"Error during checkout: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "push":
        ...

    else:   
        print(Fore.RED + Style.BRIGHT + f"Unknown command #{command}", file=sys.stderr)
        raise RuntimeError(f"Unknown command #{command}")

def getCurrentRef(branch):
    ...

def hash_object(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        content = f.read()

    hash = hashlib.sha1(content).hexdigest()
    object_dir = f".ctrlz/objects/{hash[:2]}"
    if not os.path.exists(object_dir):
        os.makedirs(object_dir)
    object_path = f"{object_dir}/{hash[2:]}"
    if not os.path.exists(object_path):
        with open(object_path, 'wb') as obj_file:
            obj_file.write(zlib.compress(f"blob {len(content)}\x00".encode() + content))
            obj_file.close()
    return hash

def ls_tree(tree_hash: str):
    print(Fore.YELLOW + Style.BRIGHT + "\n=== Tree entries ===")
    with open(f'.ctrlz/objects/{tree_hash[:2]}/{tree_hash[2:]}', 'rb') as f:
        data = zlib.decompress(f.read())
        _, tree_data = data.split(b'\x00', maxsplit=1)
        offset = 0
        while offset < len(tree_data):
            # mode ends at first space
            space_index = tree_data.find(b' ', offset)
            if space_index == -1:
                break
            mode = tree_data[offset:space_index]
            offset = space_index + 1

            # name ends at first null byte
            null_index = tree_data.find(b'\x00', offset)
            if null_index == -1:
                break
            name = tree_data[offset:null_index]
            offset = null_index + 1

            # SHA-1 hash is next 20 bytes
            sha_bytes = tree_data[offset:offset+20]
            offset += 20

            print(Fore.BLUE + "  " + Style.BRIGHT + name.decode('utf-8'))
    print(Fore.YELLOW + "-" * 32)

def write_tree(dir_path=".", print_hash=True):
    entries = []
    for entry in sorted(os.listdir(dir_path)):
        if entry.startswith(".ctrlz"):
            continue  
        entry_path = os.path.join(dir_path, entry)
        if os.path.isdir(entry_path):
            mode = b"40000"
            sha = bytes.fromhex(write_tree(entry_path, print_hash=False))
        else:
            mode = b"100644"
            sha = bytes.fromhex(hash_object(entry_path))
        entries.append(mode + b" " + entry.encode() + b"\x00" + sha)
    tree_data = b"".join(entries)
    header = f"tree {len(tree_data)}\x00".encode()
    store = header + tree_data
    tree_hash = hashlib.sha1(store).hexdigest()
    object_dir = f".ctrlz/objects/{tree_hash[:2]}"
    if not os.path.exists(object_dir):
        os.makedirs(object_dir)
    object_path = f"{object_dir}/{tree_hash[2:]}"
    if not os.path.exists(object_path):
        with open(object_path, "wb") as obj_file:
            obj_file.write(zlib.compress(store))
    if print_hash:
        print(Fore.MAGENTA + Style.BRIGHT + f"\nTree hash: {tree_hash}")
    return tree_hash

def commit_tree(tree_hash: str, message: str, parent: str = None):
    lines = [f"tree {tree_hash}"]
    if parent:
        lines.append(f"parent {parent}")
    lines.append("author eidorb90 <eidorb90@example.com> 0 +0000")
    lines.append("committer eidorb90 <eidorb90@example.com> 0 +0000")
    lines.append(datetime.datetime.now().strftime("%m/%d/%y -- %I:%M %p").lower())
    lines.append("")
    lines.append(message)
    commit_content = "\n".join(lines).encode()
    header = f"commit {len(commit_content)}\x00".encode()
    store = header + commit_content
    commit_hash = hashlib.sha1(store).hexdigest()
    commit_dir = f".ctrlz/objects/{commit_hash[:2]}"
    if not os.path.exists(commit_dir):
        os.makedirs(commit_dir)
    commit_path = f"{commit_dir}/{commit_hash[2:]}"
    if not os.path.exists(commit_path):
        with open(commit_path, "wb") as commit_file:
            commit_file.write(zlib.compress(store))
    return commit_hash

def status():
    index_path = ".ctrlz/index"
    head_path = ".ctrlz/refs/heads/main"

    # Read the latest commit hash
    with open(head_path, "r") as head_file:
        commit_hash = head_file.read().strip()

    # Read the commit object and extract the tree hash
    commit_obj_path = f".ctrlz/objects/{commit_hash[:2]}/{commit_hash[2:]}"
    with open(commit_obj_path, "rb") as commit_file:
        data = zlib.decompress(commit_file.read())
        _, content = data.split(b'\x00', 1)
        lines = content.decode().split('\n')
        tree_hash = None
        for line in lines:
            if line.startswith("tree "):
                tree_hash = line.split()[1]
                break

    # Read the tree object
    tree_obj_path = f".ctrlz/objects/{tree_hash[:2]}/{tree_hash[2:]}"
    with open(tree_obj_path, "rb") as tree_file:
        tree_data = zlib.decompress(tree_file.read())
        _, tree_entries = tree_data.split(b'\x00', 1)

    print(Fore.YELLOW + Style.BRIGHT + "\n=== Committed tree entries ===")
    offset = 0
    while offset < len(tree_entries):
        space_index = tree_entries.find(b' ', offset)
        mode = tree_entries[offset:space_index].decode()
        offset = space_index + 1
        null_index = tree_entries.find(b'\x00', offset)
        name = tree_entries[offset:null_index].decode()
        offset = null_index + 1
        sha_bytes = tree_entries[offset:offset+20]
        sha = sha_bytes.hex()
        offset += 20
        print(Fore.BLUE + f"  {mode} {name} {sha}")

    # Show staged changes
    with open(index_path, "r") as index_file:
        entries = index_file.readlines()

    if not entries:
        print(Fore.GREEN + Style.BRIGHT + "\n✔ Nothing to commit, working tree clean")
    else:
        print(Fore.YELLOW + Style.BRIGHT + "\n=== Changes to be committed ===")
        for entry in entries:
            print(Fore.BLUE + "  " + entry.strip())
        print(Fore.YELLOW + "-" * 32)

def ls_commit():
    try:
        objects_dir = ".ctrlz/objects"
        print(Fore.YELLOW + Style.BRIGHT + "\n=== Commits ===")
        commits = []
        for subdir in os.listdir(objects_dir):
            subdir_path = os.path.join(objects_dir, subdir)
            if not os.path.isdir(subdir_path):
                continue
            for obj_file in os.listdir(subdir_path):
                obj_path = os.path.join(subdir_path, obj_file)
                with open(obj_path, 'rb') as f:
                    data = zlib.decompress(f.read())
                    if data.startswith(b'commit '):
                        commit_hash = subdir + obj_file
                        # Extract timestamp from commit object
                        try:
                            _, content = data.split(b'\x00', 1)
                            lines = content.decode('utf-8', errors='replace').split('\n')
                            # Find committer line
                            timestamp = None
                            for line in lines:
                                if line.startswith("committer "):
                                    parts = line.split()
                                    # Try to get the second last part as timestamp (if present and isdigit)
                                    if len(parts) >= 3 and parts[-2].isdigit():
                                        timestamp = int(parts[-2])
                                    break
                            commits.append((commit_hash, data, timestamp))
                        except Exception:
                            commits.append((commit_hash, data, None))

        # Sort: first by timestamp (ascending), then those without timestamp at the end
        commits.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else 0))
        for commit_hash, data, _ in commits:
            print(Fore.MAGENTA + Style.BRIGHT + f"\nCommit: {commit_hash}")
            print(Fore.CYAN + Style.BRIGHT + "-" * 40)
            for line in data.decode('utf-8').strip().split('\n'):
                print(Fore.CYAN + "  " + line)
            print(Fore.CYAN + Style.BRIGHT + "-" * 40)
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"Error during ls-commits: {e}", file=sys.stderr)
        sys.exit(1)

def add(file_name: str = None):
    if file_name != '.':
        if os.path.exists(file_name):
            if os.path.isdir(file_name):
                mode = "40000"
                sha = write_tree(file_name, print_hash=False)
                entry = f"{mode} {file_name} {sha}"
            else:
                mode = "100644"
                sha = hash_object(file_name)
                entry = f"{mode} {file_name} {sha}"

            index_path = ".ctrlz/index"
            with open(index_path, "a") as index_file:
                index_file.write(entry + "\n")
            print(Fore.GREEN + Style.BRIGHT + f"✔ Added {file_name} to staging area")
    else:

        working_dir = os.getcwd()
        if not os.path.exists(".ctrlz"):
            print(Fore.RED + Style.BRIGHT + "Not a git repository (or any of the parent directories): .ctrlz", file=sys.stderr)
            sys.exit(1)

        # Read current index if exists
        index_path = ".ctrlz/index"
        current_entries = set()
        if os.path.exists(index_path):
            with open(index_path, "r") as index_file:
                for line in index_file:
                    current_entries.add(line.strip())

        try:
            entries = []
            for entry in sorted(os.listdir(working_dir)):
                if entry.startswith(".ctrlz"):
                    continue
                if os.path.isdir(entry):
                    mode = "40000"
                    sha = write_tree(os.path.join(working_dir, entry), print_hash=False)
                    entries.append(f"{mode} {entry} {sha}")
                else:
                    mode = "100644"
                    sha = hash_object(os.path.join(working_dir, entry))
                    entries.append(f"{mode} {entry} {sha}")

            new_entries_set = set(entries)

            if new_entries_set == current_entries:
                print(Fore.GREEN + Style.BRIGHT + "✔ Index is up to date, nothing to add")
                return

            with open(index_path, "w") as index_file:
                index_file.write("\n".join(entries) + "\n")

            print(Fore.GREEN + Style.BRIGHT + "✔ Added changes to staging area")

        except FileNotFoundError:
            print(Fore.RED + Style.BRIGHT + "No such file or directory", file=sys.stderr)
            sys.exit(1)

def commit(message: str = None):
    index_path = ".ctrlz/index"
    if not os.path.exists(index_path):
        print(Fore.RED + Style.BRIGHT + "No changes added to commit", file=sys.stderr)
        sys.exit(1)

    with open(index_path, "r") as index_file:
        entries = index_file.readlines()

    if not entries:
        print(Fore.RED + Style.BRIGHT + "No changes added to commit", file=sys.stderr)
        sys.exit(1)

    tree_hash = write_tree(print_hash=False)
    message = message or "blank commit message"
    parent = None

    commit_hash = commit_tree(tree_hash, message, parent)

    if not os.path.exists(".ctrlz/refs/heads"):
        os.makedirs(".ctrlz/refs/heads")
    if not os.path.exists(".ctrlz/refs/heads/main"):
        with open(".ctrlz/refs/heads/main", "w") as ref_file:
            ref_file.write(commit_hash + "\n")
            ref_file.close()    

    with open(index_path, "w") as index_file:
        index_file.write("") 

    print(Fore.GREEN + Style.BRIGHT + f"\n✔ Committed as {commit_hash}\n" + Fore.YELLOW + "-" * 32)

def checkout(hash: str):
    head_path = ".ctrlz/refs/heads/main"
    commit_obj_path = f".ctrlz/objects/{hash[:2]}/{hash[2:]}"
    if not os.path.exists(commit_obj_path):
        print(Fore.RED + Style.BRIGHT + f"Commit {hash} does not exist", file=sys.stderr)
        sys.exit(1)
    # Update HEAD
    with open(head_path, "w") as head_file:
        head_file.write(hash + "\n")
    # Read commit object and get tree hash
    with open(commit_obj_path, "rb") as f:
        data = zlib.decompress(f.read())
        _, content = data.split(b'\x00', 1)
        lines = content.decode().split('\n')
        tree_hash = None
        for line in lines:
            if line.startswith("tree "):
                tree_hash = line.split()[1]
                break
    if not tree_hash:
        print(Fore.RED + Style.BRIGHT + "No tree found in commit", file=sys.stderr)
        sys.exit(1)

    # Remove all files/dirs except .ctrlz
    for entry in os.listdir("."):
        if entry == ".ctrlz":
            continue
        entry_path = os.path.join(".", entry)
        if os.path.isdir(entry_path):
            # Recursively remove directory
            import shutil
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)

    # Restore files/dirs from tree
    def restore_tree(tree_hash, path="."):
        tree_obj_path = f".ctrlz/objects/{tree_hash[:2]}/{tree_hash[2:]}"
        with open(tree_obj_path, "rb") as f:
            data = zlib.decompress(f.read())
            _, tree_data = data.split(b'\x00', 1)
            offset = 0
            while offset < len(tree_data):
                space_index = tree_data.find(b' ', offset)
                mode = tree_data[offset:space_index].decode()
                offset = space_index + 1
                null_index = tree_data.find(b'\x00', offset)
                name = tree_data[offset:null_index].decode()
                offset = null_index + 1
                sha_bytes = tree_data[offset:offset+20]
                sha = sha_bytes.hex()
                offset += 20
                if mode == "40000":
                    # Directory
                    dir_path = os.path.join(path, name)
                    if not os.path.exists(dir_path):
                        os.mkdir(dir_path)
                    restore_tree(sha, dir_path)
                else:
                    # Blob (file)
                    blob_obj_path = f".ctrlz/objects/{sha[:2]}/{sha[2:]}"
                    with open(blob_obj_path, "rb") as bf:
                        blob_data = zlib.decompress(bf.read())
                        _, file_content = blob_data.split(b'\x00', 1)
                        file_path = os.path.join(path, name)
                        with open(file_path, "wb") as outf:
                            outf.write(file_content)
    restore_tree(tree_hash)
    print(Fore.GREEN + Style.BRIGHT + f"✔ Checked out commit {hash} and updated working directory")

if __name__ == "__main__":
    print(Fore.YELLOW + "Python executable: " + Fore.WHITE + Style.BRIGHT + sys.executable, file=sys.stderr)
    main()
