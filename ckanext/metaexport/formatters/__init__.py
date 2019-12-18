# -*- coding: utf-8 -*-
from builtins import object
import ckan.lib.base as base


def _default_data_extractor(pkg_id):
    return dict(pkg_id=pkg_id)


class Formatter(object):
    """Potentially static class-collection of all supported formats.
    """

    _formats = dict()

    @classmethod
    def register(cls, **formats):
        """Add new format(or replace old one).
        """
        cls._formats.update(formats)

    @classmethod
    def list_formats(cls):
        """List all registered formats.
        """
        return list(cls._formats.keys())

    @classmethod
    def get(cls, format):
        """Return registered format or raise `NameError`
        """
        if format in cls._formats:
            return cls._formats[format]
        raise NameError(format)


class Format(object):
    """Base formatter type.

    :prop _content_type: value of `Content-Type` header
    """

    _content_type = "text/html; charset=utf-8"

    def __init__(self):
        self._mandatory = set()
        self._optional = set()
        self.set_data_extractor(_default_data_extractor)

    def extract_data(self, pkg_id):
        return self._data_extractor(pkg_id)

    def get_content_type(self):
        return self._content_type

    def set_data_extractor(self, func):
        self._data_extractor = func

    def render(self, template, *args, **kwargs):
        return base.render(template, *args, **kwargs)
