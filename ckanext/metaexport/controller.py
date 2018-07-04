# -*- coding: utf-8 -*-

import ckan.lib.base as base
from ckan.common import response, _
from ckanext.metaexport.helpers import metaex_get_top_org

from .formatters import Formatter


class MetaexportController(base.BaseController):

    def export(self, id, format):
        try:
            fmt = Formatter.get(format)
        except NameError:
            return base.abort(404, _('%s format is not supported') % format)
        data = fmt.extract_data(id)
        response.headers['content-type'] = fmt.get_content_type()

        try:
            if 'owner_org' in data:
                org = data['owner_org']
                # Try to get parent Organization
                parent_org = metaex_get_top_org(org['id'], True)
                if parent_org:
                    org = parent_org
                    data['owner_org'] = org
        except Exception as e:
            print e
        return base.render(
            'metaexport/{}.html'.format(format), extra_vars=data
        )
