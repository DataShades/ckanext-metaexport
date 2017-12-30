# -*- coding: utf-8 -*-

from . import Format


class HTMLFormat(Format):
    _content_type = 'text/html; charset=utf-8'

    def __init__(self):
        super(HTMLFormat, self).__init__()
