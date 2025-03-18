
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.metaexport.formatters import Formatter
from ckanext.metaexport.formatters.anzlic_xml import AnzlicXmlFormat
from ckanext.metaexport.formatters.dc_rdf import DcRdfFormat
from ckanext.metaexport.formatters.dcat_rdf import DcatRdfFormat
from ckanext.metaexport.formatters.eml_rdf import EmlRdfFormat
from ckanext.metaexport.formatters.eml_xml import EmlXmlFormat
from ckanext.metaexport.formatters.gmd import GMD
from ckanext.metaexport.formatters.html_format import HTMLFormat
from ckanext.metaexport.formatters.pdf_format import PDFFormat
from ckanext.metaexport.helpers import get_helpers
from ckanext.metaexport.interfaces import IMetaexport
from ckanext.metaexport.views import get_blueprints


class MetaexportPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(IMetaexport, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")

        for plugin in plugins.PluginImplementations(IMetaexport):
            Formatter.register(**plugin.register_metaexport_format())

        for plugin in plugins.PluginImplementations(IMetaexport):
            plugin.register_data_extractors(Formatter)

    # IMetaexport

    def register_metaexport_format(self):
        return {
            "gmd": GMD(),
            "html": HTMLFormat(),
            "pdf": PDFFormat(),
            "dcat-rdf": DcatRdfFormat(),
            "dc-rdf": DcRdfFormat(),
            "eml-rdf": EmlRdfFormat(),
            "eml-xml": EmlXmlFormat(),
            "anzlic-xml": AnzlicXmlFormat(),
        }

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()
