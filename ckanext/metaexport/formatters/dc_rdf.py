# -*- coding: utf-8 -*-

import json

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import c
from geomet import wkt, InvalidGeoJSONException
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.namespace import Namespace, RDF, XSD, SKOS, DC

from ckanext.metaexport.formatters import Format
from ckanext.metaexport.formatters.triple_helpers import (
    get_triple_from_dict, get_triples_from_dict, get_list_triples_from_dict,
    publisher_uri_from_dataset_dict, resource_uri, CleanedURIRef
)

ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace('http://schema.org/')
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
GEOJSON_IMT = 'https://www.iana.org/assignments/media-types/application/vnd.geo+json'
DCT = Namespace("http://purl.org/dc/terms/")

namespaces = {
    'dct': DCT,
    'dc': DC,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'spdx': SPDX,
}


def _bind_namespaces(g):
    for k, v in namespaces.items():
        g.bind(k, v)


class DcRdfFormat(Format):
    _content_type = 'application/rdf+xml; charset=utf-8'
    # _content_type = 'application/xml; charset=utf-8'

    def extract_data(self, id):
        context = {'user': c.user, 'model': model}
        dataset_dict = tk.get_action('package_show')(context, {'id': id})
        dataset_url = h.url_for(
            controller='package',
            action='read',
            id=dataset_dict['id'],
            qualified=True
        )

        g = Graph()
        _bind_namespaces(g)

        dataset_ref = URIRef(dataset_url)
        g.add((dataset_ref, RDF.type, DC.Description))

        # Basic fields
        items = [
            ('title', DC.title, None, Literal),
            ('notes', DC.description, None, Literal),
        ]
        for triple in get_triples_from_dict(dataset_dict, dataset_ref, items):
            g.add(triple)
        g.add((dataset_ref, DC.landingPage, URIRef(dataset_url)))

        # Tags
        for tag in dataset_dict.get('tags', []):
            g.add((dataset_ref, DC.keyword, Literal(tag['name'])))

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
            dataset_dict, dataset_ref, items
        ):
            g.add(triple)

        # Dates
        items = [
            ('date', DC.date, None, Literal),
        ]
        for triple in get_list_triples_from_dict(
            dataset_dict, dataset_ref, items
        ):
            g.add(triple)

        # Spatial
        spatial_uri = dataset_dict.get('spatial_uri')
        spatial_text = dataset_dict.get('spatial_text')
        spatial_geom = dataset_dict.get('spatial')

        if spatial_uri or spatial_text or spatial_geom:
            if spatial_uri:
                spatial_ref = CleanedURIRef(spatial_uri)
            else:
                spatial_ref = BNode()

            g.add((spatial_ref, RDF.type, DCT.Location))
            g.add((dataset_ref, DCT.spatial, spatial_ref))

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
        for resource_dict in dataset_dict.get('resources', []):

            distribution = CleanedURIRef(resource_uri(resource_dict))

            g.add((dataset_ref, DC.distribution, distribution))

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
