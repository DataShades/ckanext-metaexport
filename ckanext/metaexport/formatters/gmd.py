# -*- coding: utf-8 -*-

from . import Format


class GMD(Format):
    _content_type = 'application/xml; charset=utf-8'

    def __init__(self):
        super(GMD, self).__init__()
