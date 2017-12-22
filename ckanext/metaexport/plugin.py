# -*- coding: utf-8 -*-

from routes.mapper import SubMapper

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from .interfaces import IMetaexport
from .formatters import Formatter
from .controller import MetaexportController

from .formatters.gmd import GMD


class MetaexportPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(IMetaexport, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'metaexport')

        for plugin in plugins.PluginImplementations(IMetaexport):
            Formatter.register(**plugin.register_metaexport_format())

        for plugin in plugins.PluginImplementations(IMetaexport):
            plugin.register_data_extractors(Formatter)

    # IRoutes

    def before_map(self, map):
        ctrl = 'ckanext.metaexport.controller:MetaexportController'
        with SubMapper(map, controller=ctrl, path_prefix='/dataset/{id}') as m:
            m.connect(
                'dataset_metaexport', '/metaexport/{format}', action='export'
            )
        return map

    # IMetaexport

    def register_metaexport_format(self):
        return dict(
            gmd=GMD()
        )
