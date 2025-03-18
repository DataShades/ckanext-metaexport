import ckan.model as model
import ckan.plugins.toolkit as tk

from . import Format


class AnzlicXmlFormat(Format):
    _content_type = "application/xml; charset=utf-8"

    def extract_data(self, id):
        pkg_dict = tk.get_action("package_show")(
            {"user": tk.current_user, "model": model}, {"id": id},
        )

        return {"data": pkg_dict}
