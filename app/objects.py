class Blob:
    def __init__(self, content: str):
        self.content = content
        self.size = len(content.encode('utf-8'))