with open(".env", "r") as f:
    data = f.read()
    print(repr(data))
    print("\nLines:")
    lines = data.splitlines()
    for i, line in enumerate(lines):
        print(f"{i}: {repr(line)}")
