# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()
import io
import pdfkit

from . import Format


class PDFFormat(Format):
    _content_type = "application/pdf"

    def __init__(self):
        super(PDFFormat, self).__init__()

    def render(self, template, *args, **kwargs):
        html = super(PDFFormat, self).render(template, *args, **kwargs)
        result = io.StringIO()

        result = pdfkit.from_file(io.StringIO(html), False)
        return result
