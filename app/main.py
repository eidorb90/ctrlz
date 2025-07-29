import sys
import os

import zlib
import hashlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file":
        hash = sys.argv[3]
        if not os.path.exists(f".git/objects/{hash[:2]}/{hash[2:]}"):
            print(f"Object {hash} not found", file=sys.stderr)
            sys.exit(1)
        with open(f'.git/objects/{hash[:2]}/{hash[2:]}', 'rb') as f:
            content = f.read()
            decompressed = zlib.decompress(content)
            _, obj_content = decompressed.split(b'\x00', 1)
            print(obj_content.decode('utf-8'), end="")

    elif command == "hash-object":
        file_path = sys.argv[3]
        if file_path:
            hash = hash_object(file_path)
            print(hash)

    else:
        raise RuntimeError(f"Unknown command #{command}")

def hash_object(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        content = f.read()

    hash = hashlib.sha1(content).hexdigest()
    object_dir = f".git/objects/{hash[:2]}"
    if not os.path.exists(object_dir):
        os.makedirs(object_dir)
    object_path = f"{object_dir}/{hash[2:]}"
    if not os.path.exists(object_path):
        with open(object_path, 'wb') as obj_file:
            obj_file.write(zlib.compress(f"blob {len(content)}\x00".encode() + content))
            obj_file.close()
    print(f"Created object {hash} for file {file_path}")
    return hash


if __name__ == "__main__":
    main()
