# -*- coding: utf-8 -*-

import ckan.plugins as p
from ckanext.metaexport.views import get_blueprints


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()
