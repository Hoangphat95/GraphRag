import os

IGNORE = {"__pycache__", ".git", "venv", ".idea", ".vscode"}

def print_tree(start_path, prefix=""):
    try:
        items = [i for i in sorted(os.listdir(start_path)) if i not in IGNORE]
    except PermissionError:
        print(prefix + "└── [Permission Denied]")
        return

    for index, item in enumerate(items):
        path = os.path.join(start_path, item)
        connector = "└── " if index == len(items) - 1 else "├── "
        print(prefix + connector + item)

        if os.path.isdir(path):
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    folder_path = r"E:\KG\graph_rag_enterprise"
    print(folder_path)
    print_tree(folder_path)