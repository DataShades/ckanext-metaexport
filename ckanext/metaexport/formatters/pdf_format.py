# -*- coding: utf-8 -*-
import StringIO
import pdfkit

from . import Format


class PDFFormat(Format):
    _content_type = 'application/pdf'

    def __init__(self):
        super(PDFFormat, self).__init__()

    def render(self, template, *args, **kwargs):
        html = super(PDFFormat, self).render(template, *args, **kwargs)
        result = StringIO.StringIO()

        result = pdfkit.from_file(StringIO.StringIO(html), False)
        return result
