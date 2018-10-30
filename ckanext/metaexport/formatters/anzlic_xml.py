# -*- coding: utf-8 -*-

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import c

from . import Format


class AnzlicXmlFormat(Format):
    _content_type = 'application/xml; charset=utf-8'

    def extract_data(self, id):
        context = {'user': c.user, 'model': model}
        pkg_dict = tk.get_action('package_show')(context, {'id': id})

        return {'data': pkg_dict}
