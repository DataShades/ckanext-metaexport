from weasyprint import HTML

from . import Format


class PDFFormat(Format):
    _content_type = "application/pdf"

    def __init__(self):
        super().__init__()

    def render(self, template, *args, **kwargs) -> bytes:
        html = super().render(template, *args, **kwargs)

        return  HTML(string=html).write_pdf() or b""
