# -*- coding: utf-8 -*-

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from routes.mapper import SubMapper

from ckanext.metaexport.formatters import Formatter
from ckanext.metaexport.formatters.gmd import GMD
from ckanext.metaexport.formatters.html_format import HTMLFormat
from ckanext.metaexport.formatters.pdf_format import PDFFormat
from ckanext.metaexport.formatters.dcat_rdf import DcatRdfFormat
from ckanext.metaexport.formatters.eml_rdf import EmlRdfFormat
from ckanext.metaexport.formatters.dc_rdf import DcRdfFormat
from ckanext.metaexport.formatters.eml_xml import EmlXmlFormat
from ckanext.metaexport.formatters.anzlic_xml import AnzlicXmlFormat
from ckanext.metaexport.interfaces import IMetaexport
from ckanext.metaexport.helpers import get_helpers


class MetaexportPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(IMetaexport, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

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
        return {
            'gmd': GMD(),
            'html': HTMLFormat(),
            'pdf': PDFFormat(),
            'dcat-rdf': DcatRdfFormat(),
            'dc-rdf': DcRdfFormat(),
            'eml-rdf': EmlRdfFormat(),
            'eml-xml': EmlXmlFormat(),
            'anzlic-xml': AnzlicXmlFormat(),
        }

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()
