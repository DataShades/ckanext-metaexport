import ckan.lib.base as base
import ckan.model as model
import ckan.plugins.toolkit as tk


def _default_data_extractor(pkg_id):
    context = {"user": tk.c.user, "model": model}
    pkg_dict = tk.get_action("package_show")(context, {"id": pkg_id})
    return dict(
        pkg_id=pkg_id,
        pkg_dict=pkg_dict,
        owner_org=tk.get_action("organization_show")(
            {}, {"id": pkg_dict.get("owner_org")},
        ),
        date_stamp=pkg_dict["metadata_modified"],
    )


class Formatter:
    """Potentially static class-collection of all supported formats."""

    _formats = dict()

    @classmethod
    def register(cls, **formats):
        """Add new format(or replace old one)."""
        cls._formats.update(formats)

    @classmethod
    def list_formats(cls):
        """List all registered formats."""
        return list(cls._formats.keys())

    @classmethod
    def get(cls, format):
        """Return registered format or raise `NameError`"""
        if format in cls._formats:
            return cls._formats[format]
        raise NameError(format)


class Format:
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
