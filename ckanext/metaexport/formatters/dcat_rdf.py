# -*- coding: utf-8 -*-

import json

from rdflib import Literal, URIRef, BNode
from rdflib.namespace import RDF, XSD, SKOS

from geomet import wkt, InvalidGeoJSONException

from ckanext.metaexport.formatters._rdf import RdfFormat
from ckanext.metaexport.formatters.triple_helpers import (
    get_date_triple,
    get_triple_from_dict,
    get_triples_from_dict,
    get_list_triples_from_dict,
    resource_uri,
    CleanedURIRef,
    add_mailto,
    DCT,
    DCAT,
    ADMS,
    VCARD,
    FOAF,
    SCHEMA,
    LOCN,
    GSP,
    OWL,
    SPDX,
    GEOJSON_IMT,
)


class DcatRdfFormat(RdfFormat):

    def extract_data(self, id):
        g = self._init_graph(id)

        # Basic fields
        items = [
            ('title', DCT.title, None, Literal),
            ('notes', DCT.description, None, Literal),
            # ('url', DCAT.landingPage, None, URIRef),
            ('identifier', DCT.identifier, ['guid', 'id'], Literal),
            ('version', OWL.versionInfo, ['version'], Literal),
            ('version_notes', ADMS.versionNotes, None, Literal),
            ('frequency', DCT.accrualPeriodicity, None, Literal),
            ('access_rights', DCT.accessRights, None, Literal),
            ('dcat_type', DCT.type, None, Literal),
            ('provenance', DCT.provenance, None, Literal),
        ]
        for triple in get_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items
        ):
            g.add(triple)
        g.add((self._dataset_ref, DCAT.landingPage, URIRef(self._dataset_url)))

        # Tags
        for tag in self._dataset_dict.get('tags', []):
            g.add((self._dataset_ref, DCAT.keyword, Literal(tag['name'])))

        # Dates
        items = [
            ('issued', DCT.issued, ['metadata_created'], Literal),
            ('modified', DCT.modified, ['metadata_modified'], Literal),
        ]
        for triple in get_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items, date_value=True
        ):
            g.add(triple)

        #  Lists
        items = [
            ('language', DCT.language, None, Literal),
            ('theme', DCAT.theme, None, URIRef),
            ('conforms_to', DCT.conformsTo, None, Literal),
            ('alternate_identifier', ADMS.identifier, None, Literal),
            ('documentation', FOAF.page, None, Literal),
            # TODO: why we dont have this field?
            # ('related_resource', DCT.relation, None, Literal),
            ('has_version', DCT.hasVersion, None, Literal),
            ('is_version_of', DCT.isVersionOf, None, Literal),
            ('source', DCT.source, None, Literal),
            ('sample', ADMS.sample, None, Literal),
        ]
        for triple in get_list_triples_from_dict(
            self._dataset_dict, self._dataset_ref, items
        ):
            g.add(triple)

        # Contact details
        if any(
            self._dataset_dict.get(field) for field in [
                'contact_uri',
                'contact_name',
                'contact_email',
                'maintainer',
                'maintainer_email',
                'author',
                'author_email',
            ]
        ):
            contact_uri = self._dataset_dict.get('contact_uri')
            if contact_uri:
                contact_details = CleanedURIRef(contact_uri)
            else:
                contact_details = BNode()

            g.add((contact_details, RDF.type, VCARD.Organization))
            g.add((self._dataset_ref, DCAT.contactPoint, contact_details))

            for triple in get_triple_from_dict(
                self._dataset_dict, contact_details, VCARD.fn, 'contact_name',
                ['maintainer', 'author']
            ):
                g.add(triple)
            # Add mail address as URIRef, and ensure it has a mailto: prefix
            for triple in get_triple_from_dict(
                self._dataset_dict,
                contact_details,
                VCARD.hasEmail,
                'contact_email', ['maintainer_email', 'author_email'],
                _type=URIRef,
                value_modifier=add_mailto
            ):
                g.add(triple)

        # Publisher
        if any(
            self._dataset_dict.get(field) for field in [
                'publisher_uri',
                'publisher_name',
                'organization',
            ]
        ):

            publisher_uri = publisher_uri_from_self._dataset_dict(
                self._dataset_dict
            )
            if publisher_uri:
                publisher_details = CleanedURIRef(publisher_uri)
            else:
                # No organization nor publisher_uri
                publisher_details = BNode()

            g.add((publisher_details, RDF.type, FOAF.Organization))
            g.add((self._dataset_ref, DCT.publisher, publisher_details))

            publisher_name = self._dataset_dict.get('publisher_name')
            if not publisher_name and self._dataset_dict.get('organization'):
                publisher_name = self._dataset_dict['organization']['title']

            g.add((publisher_details, FOAF.name, Literal(publisher_name)))
            # TODO: It would make sense to fallback these to organization
            # fields but they are not in the default schema and the
            # `organization` object in the self._dataset_dict does not include
            # custom fields
            items = [
                ('publisher_email', FOAF.mbox, None, Literal),
                ('publisher_url', FOAF.homepage, None, URIRef),
                ('publisher_type', DCT.type, None, Literal),
            ]

            for triple in get_triples_from_dict(
                self._dataset_dict, publisher_details, items
            ):
                g.add(triple)

        # Temporal
        start = self._dataset_dict.get('temporal_start')
        end = self._dataset_dict.get('temporal_end')
        if start or end:
            temporal_extent = BNode()

            g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
            if start:
                g.add(
                    get_date_triple(temporal_extent, SCHEMA.startDate, start)
                )
            if end:
                g.add(get_date_triple(temporal_extent, SCHEMA.endDate, end))
            g.add((self._dataset_ref, DCT.temporal, temporal_extent))

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

            g.add((self._dataset_ref, DCAT.distribution, distribution))

            g.add((distribution, RDF.type, DCAT.Distribution))

            #  Simple values
            items = [
                ('name', DCT.title, None, Literal),
                ('description', DCT.description, None, Literal),
                ('status', ADMS.status, None, Literal),
                ('rights', DCT.rights, None, Literal),
                # TODO: we are avoiding licenses right now
                # ('license', DCT.license, None, Literal),
                ('access_url', DCAT.accessURL, None, URIRef),
                ('download_url', DCAT.downloadURL, None, URIRef),
            ]

            for triple in get_triples_from_dict(
                resource_dict, distribution, items
            ):
                g.add(triple)

            #  Lists
            items = [
                ('documentation', FOAF.page, None, Literal),
                ('language', DCT.language, None, Literal),
                ('conforms_to', DCT.conformsTo, None, Literal),
            ]
            for triple in get_list_triples_from_dict(
                resource_dict, distribution, items
            ):
                g.add(triple)

            # Format
            if '/' in resource_dict.get('format', ''):
                g.add((
                    distribution, DCAT.mediaType,
                    Literal(resource_dict['format'])
                ))
            else:
                if resource_dict.get('format'):
                    g.add((
                        distribution, DCT['format'],
                        Literal(resource_dict['format'])
                    ))

                if resource_dict.get('mimetype'):
                    g.add((
                        distribution, DCAT.mediaType,
                        Literal(resource_dict['mimetype'])
                    ))

            # URL fallback and old behavior
            url = resource_dict.get('url')
            download_url = resource_dict.get('download_url')
            access_url = resource_dict.get('access_url')
            # Use url as fallback for access_url if access_url is not
            # set and download_url is not equal
            if url and not access_url:
                if (not download_url
                    ) or (download_url and url != download_url):
                    for triple in get_triple_from_dict(
                        resource_dict,
                        distribution,
                        DCAT.accessURL,
                        'url',
                        _type=URIRef
                    ):
                        g.add(triple)

            # Dates
            items = [
                ('issued', DCT.issued, None, Literal),
                ('modified', DCT.modified, None, Literal),
            ]

            for triple in get_triples_from_dict(
                resource_dict, distribution, items, date_value=True
            ):
                g.add(triple)

            # Numbers
            if resource_dict.get('size'):
                try:
                    g.add((
                        distribution, DCAT.byteSize,
                        Literal(
                            float(resource_dict['size']), datatype=XSD.decimal
                        )
                    ))
                except (ValueError, TypeError):
                    g.add((
                        distribution, DCAT.byteSize,
                        Literal(resource_dict['size'])
                    ))
            # Checksum
            if resource_dict.get('hash'):
                checksum = BNode()
                g.add((checksum, RDF.type, SPDX.Checksum))
                g.add((
                    checksum, SPDX.checksumValue,
                    Literal(resource_dict['hash'], datatype=XSD.hexBinary)
                ))

                if resource_dict.get('hash_algorithm'):
                    if resource_dict['hash_algorithm'].startswith('http'):
                        g.add((
                            checksum, SPDX.algorithm,
                            CleanedURIRef(resource_dict['hash_algorithm'])
                        ))
                    else:
                        g.add((
                            checksum, SPDX.algorithm,
                            Literal(resource_dict['hash_algorithm'])
                        ))
                g.add((distribution, SPDX.checksum, checksum))

        # graph.add((dataset. RDF.about , Literal()))
        return {'data': g.serialize(format='pretty-xml')}
