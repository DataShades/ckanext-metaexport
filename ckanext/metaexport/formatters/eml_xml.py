# -*- coding: utf-8 -*-

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import c

from . import Format


class EmlXmlFormat(Format):
    _content_type = 'application/xml; charset=utf-8'

    def extract_data(self, id):
        context = {'user': c.user, 'model': model}
        pkg_dict = tk.get_action('package_show')(context, {'id': id})
        # url = h.url_for(
        #     controller='package',
        #     action='read',
        #     id=pkg_dict['id'],
        #     qualified=True
        # )

        return {'data': pkg_dict}
