import pdfkit
from six import StringIO

from . import Format


class PDFFormat(Format):
    _content_type = "application/pdf"

    def __init__(self):
        super().__init__()

    def render(self, template, *args, **kwargs):
        html = super().render(template, *args, **kwargs)

        result = pdfkit.from_file(StringIO(html), False)
        return result
