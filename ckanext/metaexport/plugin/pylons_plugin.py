# -*- coding: utf-8 -*-

import ckan.plugins as p
from routes.mapper import SubMapper


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)

    # IRoutes

    def before_map(self, map):
        ctrl = "ckanext.metaexport.controller:MetaexportController"
        with SubMapper(map, controller=ctrl, path_prefix="/dataset/{id}") as m:
            m.connect(
                "dataset_metaexport", "/metaexport/{format}", action="export"
            )
        return map
