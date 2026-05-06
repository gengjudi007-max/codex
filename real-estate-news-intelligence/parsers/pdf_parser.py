import pdfplumber


class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_text(self):
        full_text = []

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if text:
                    full_text.append(text)

        return '\n'.join(full_text)


if __name__ == '__main__':
    parser = PDFParser('sample.pdf')
    content = parser.extract_text()
    print(content[:2000])
