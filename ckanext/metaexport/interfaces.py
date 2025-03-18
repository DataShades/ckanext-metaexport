from typing import Any

import ckan.plugins.interfaces as interfaces


class IMetaexport(interfaces.Interface):
    """Define metadata export formats."""

    def register_metaexport_format(self) -> dict[str, Any]:
        """Register metadata format.

        Register a new metadata format for export.

        Returns:
            dict: Dictionary mapping format names to formatter instances.

        Example:
            return {'gmd': GMD()}
        """
        return {}

    def register_data_extractors(self, formatters):
        """Register data extractors for formatters.

        Args:
            formatters: The formatters to register data extractors for.

        Returns:
            The formatters with registered data extractors.

        Example:
            fmt = formatters.get('gmd')
            fmt.set_data_extractor(custom_data_extractor)
        """
        return formatters
