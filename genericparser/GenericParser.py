


if __name__ == "__main__":
    parser = GenericParser()
    current_dir = os.path.dirname(__file__)
    filename = "examples/example.fc"
    filepath = os.path.join(current_dir, filename)
    a = parser.parse(filepath)
    print(a)
