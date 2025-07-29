import sys
import os

import zlib


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
            content = zlib.decompress(content).decode('utf-8')
            print(f" {content[8:]}", end="")


    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
