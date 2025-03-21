from rdflib import Graph, URIRef
from rdflib.namespace import DC, RDF, SKOS

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.metaexport.formatters import Format
from ckanext.metaexport.formatters.triple_helpers import (
    ADMS,
    DCAT,
    DCT,
    FOAF,
    GSP,
    LOCN,
    OWL,
    SCHEMA,
    SPDX,
    VCARD,
    XS,
)


class RdfFormat(Format):
    _with_ref = True
    _content_type = "application/xml; charset=utf-8"
    NAMESPACES = {
        "adms": ADMS,
        "dc": DC,
        "dcat": DCAT,
        "dct": DCT,
        "foaf": FOAF,
        "gsp": GSP,
        "locn": LOCN,
        "owl": OWL,
        "schema": SCHEMA,
        "skos": SKOS,
        "spdx": SPDX,
        "vcard": VCARD,
        "xs": XS,
    }

    def bind_namespaces(self, g):
        for k, v in list(self.NAMESPACES.items()):
            g.bind(k, v)

    def _init_graph(self, id):
        self._dataset_dict = tk.get_action("package_show")(
            {"user": tk.current_user, "model": model}, {"id": id},
        )

        self._dataset_url = h.url_for(
            "dataset.read",
            id=self._dataset_dict["id"],
            qualified=True,
        )

        g = Graph()
        self.bind_namespaces(g)

        if self._with_ref:
            self._dataset_ref = URIRef(self._dataset_url)
            g.add((self._dataset_ref, RDF.type, DC.description))

        return g
