# -*- coding: utf-8 -*-

import json

from geomet import wkt, InvalidGeoJSONException
from rdflib import Literal, URIRef, BNode
from rdflib.namespace import RDF, XSD, SKOS, DC

from ckanext.metaexport.formatters._rdf import RdfFormat
from ckanext.metaexport.formatters.triple_helpers import (
    get_triple_from_dict,
    get_triples_from_dict,
    get_list_triples_from_dict,
    resource_uri,
    CleanedURIRef,
    LOCN,
    GSP,
    GEOJSON_IMT,
    DCT,
)


class DcRdfFormat(RdfFormat):
    def extract_data(self, id):
        g = self._init_graph(id)

        # Basic fields
        items = [
            ('title', DC.title, None, Literal),
            ('notes', DC.description, None, Literal),
        ]

        for triple in get_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items
        ):
            g.add(triple)
        g.add((self._dataset_ref, DC.landingPage, URIRef(self._dataset_url)))

        # Tags
        for tag in self._dataset_dict.get('tags', []):
            g.add((self._dataset_ref, DC.keyword, Literal(tag['name'])))

        #  Lists
        items = [
            ('creator', DC.creator, None, Literal),
            ('subject', DC.subject, None, Literal),
            ('publisher', DC.publisher, None, Literal),
            ('contributor', DC.contributer, None, Literal),
            ('publication_type', DC.publication_type, None, Literal),
            ('format', DC['format'], None, Literal),
            ('identifier', DC.identifier, None, Literal),
            ('source', DC.source, None, Literal),
            ('language', DC.languate, None, Literal),
            ('relation', DC.relations, None, Literal),
            ('rights', DC.rights, None, Literal),
        ]
        for triple in get_list_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items
        ):
            g.add(triple)

        # Dates
        items = [
            ('date', DC.date, None, Literal),
        ]
        for triple in get_list_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items
        ):
            g.add(triple)

        # Spatial
        spatial_uri = self._dataset_dict.get('spatial_uri')
        spatial_text = self._dataset_dict.get('spatial_text')
        spatial_geom = self._dataset_dict.get('spatial')

        if spatial_uri or spatial_text or spatial_geom:
            if spatial_uri:
                spatial_ref = CleanedURIRef(spatial_uri)
            else:
                spatial_ref = BNode()

            g.add((spatial_ref, RDF.type, DCT.Location))
            g.add((self._dataset_ref, DCT.spatial, spatial_ref))

            if spatial_text:
                g.add((spatial_ref, SKOS.prefLabel, Literal(spatial_text)))

            if spatial_geom:
                # GeoJSON
                g.add((
                    spatial_ref, LOCN.geometry,
                    Literal(spatial_geom, datatype=GEOJSON_IMT)
                ))
                # WKT, because GeoDCAT-AP says so
                try:
                    g.add((
                        spatial_ref, LOCN.geometry,
                        Literal(
                            wkt.dumps(json.loads(spatial_geom), decimals=4),
                            datatype=GSP.wktLiteral
                        )
                    ))
                except (TypeError, ValueError, InvalidGeoJSONException):
                    pass

        # Resources
        for resource_dict in self._dataset_dict.get('resources', []):

            distribution = CleanedURIRef(resource_uri(resource_dict))

            g.add((self._dataset_ref, DC.distribution, distribution))

            g.add((distribution, RDF.type, DC.Distribution))

            #  Simple values
            items = [
                ('name', DC.title, None, Literal),
                ('description', DC.description, None, Literal),
            ]

            for triple in get_triples_from_dict(
                resource_dict, distribution, items
            ):
                g.add(triple)

            # Format
            if '/' in resource_dict.get('format', ''):
                g.add((
                    distribution, DC.mediaType,
                    Literal(resource_dict['format'])
                ))
            else:
                if resource_dict.get('format'):
                    g.add((
                        distribution, DC['format'],
                        Literal(resource_dict['format'])
                    ))

                if resource_dict.get('mimetype'):
                    g.add((
                        distribution, DC.mediaType,
                        Literal(resource_dict['mimetype'])
                    ))

            # URL fallback and old behavior
            url = resource_dict.get('url')
            if url:
                for triple in get_triple_from_dict(
                    resource_dict,
                    distribution,
                    DC.accessURL,
                    'url',
                    _type=URIRef
                ):
                    g.add(triple)

            # Numbers
            if resource_dict.get('size'):
                try:
                    g.add((
                        distribution, DC.byteSize,
                        Literal(
                            float(resource_dict['size']), datatype=XSD.decimal
                        )
                    ))
                except (ValueError, TypeError):
                    g.add((
                        distribution, DC.byteSize,
                        Literal(resource_dict['size'])
                    ))

        return {'data': g.serialize(format='pretty-xml')}
