# -*- coding: utf-8 -*-

import ckan.plugins.interfaces as interfaces


class IMetaexport(interfaces.Interface):
    '''Define metadata export formats.'''

    def register_metaexport_format(self):
        """Register metadata format.

        Example:
        return dict(gmd=GMD())

        :returns: dictonary with available formats.
        :rtype: dict
        """
        return dict()

    def register_data_extractors(self, formatters):
        """
        Example:
        fmt = formatters.get('gmd')
        fmt.set_data_extractor(custom_data_extractor)
        """
        return formatters
