
class FileLoader:
    def __init__(self):
        """Load files using various file loaders"""
        #self.reader = easyocr.Reader(['en'], gpu=False)

    def extract_text_from_pdf(self, file):
        """PDF extractor
        args:
            pdf_path (str): path to pdf
        returns:
            full_text (str): text in the file
        """
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""

        for page in doc:
            # Extract text from free text
            text += page.get_text("text")

            # Extract text from tables, double column pages, and complex objects (if any)
            blocks = page.get_text("dict", flags=0)["blocks"]
            for block in blocks:
                if block['type'] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text += span["text"]
                elif block['type'] == 2:  # Text from a header or footer
                    text += block["lines"][0]["spans"][0]["text"]

        return text
