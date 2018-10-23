# -*- coding: utf-8 -*-

import json
import re

from geomet import wkt, InvalidGeoJSONException
from rdflib import Literal, URIRef, BNode
from rdflib.namespace import RDF, XSD, SKOS, DC

from ckanext.metaexport.formatters._rdf import RdfFormat
from ckanext.metaexport.formatters.triple_helpers import (
    get_triple_from_dict, get_triples_from_dict, get_list_triples_from_dict,
    resource_uri, CleanedURIRef, LOCN, GSP, GEOJSON_IMT, DCT, XS, ADMS, DCAT
)


class EmlRdfFormat(RdfFormat):
    _with_ref = False

    def _address(self, data):
        result = BNode()
        props = (
            ('delivery', 'point'),
            ('city', ),
            ('administrative', 'area'),
            (
                'postal',
                'code',
            ),
            ('country', ),
        )

        for prop in props:
            value = data.get('_'.join(prop))
            if not value:
                continue
            key = ''.join([prop[0]] + [p.title() for p in prop[1:]])
            self.g.add((result, XS[key], Literal(value)))

        return result

    def _agent(self, data):
        result = BNode()
        individual_name = data.get('individual_name')
        if individual_name:
            n = BNode()
            sn = individual_name.get('sur_name')
            self.g.add((n, XS.surName, Literal(sn)))

            gn = individual_name.get('given_name')
            if gn:
                self.g.add((n, XS.givenName, Literal(gn)))
            self.g.add((result, XS.individualName, n))

        props = (
            ('organization', 'name'),
            ('position', 'name'),
            ('phone', 'name'),
            ('electronic', 'mail', 'address'),
            ('online', 'url'),
            ('role', ),
        )
        for prop in props:
            value = data.get('_'.join(prop))
            if not value:
                continue
            key = ''.join([prop[0]] + [p.title() for p in prop[1:]])
            self.g.add((result, XS[key], Literal(value)))
        for value in data.get('user_id'):
            self.g.add((result, XS.userId, Literal(value)))
        address = data.get('address')
        if address:
            self.g.add((result, XS.address, self._address(address)))
        return result

    def _keyword_set(self, data):
        result = BNode()
        for value in data.get('keyword'):
            self.g.add((result, DC.keyword, Literal(value)))
        self.g.add(
            (result, XS.keywordThesaurus, Literal(data['keyword_thesaurus']))
        )

        return result

    def _distribution(self, data):
        result = BNode()
        value = data.get('scope')
        if value:
            self.g.add((result, XS.scope, Literal(value)))
        self.g.add((result, XS.online, Literal(data['url'])))

        return result

    def _coverage(self, data):
        result = BNode()
        value = data.get('scope')
        for type_ in ['geographic', 'temporal', 'taxonomic']:
            value = data.get(type_ + '_coverage')
            if not value:
                continue
            self.g.add((
                result, XS[type_ + '_coverage'], getattr(self,
                                                         '_' + type_)(value)
            ))

        return result

    def _geographic(self, data):
        result = BNode()
        coords = data['bounding_coordinates']
        self.g.add((
            result, XS.geographicDescription,
            Literal(data['geographic_description'])
        ))
        c = BNode()
        self.g.add((result, XS.boundingCoordinates, c))
        for side in ['west', 'east', 'north', 'south']:
            self.g.add((
                c, XS[side + 'BoundingCoordinate'],
                Literal(coords[side + '_bounding_coordinate'])
            ))
        return result

    def _temporal(self, data):
        result = BNode()
        sd = data.get('single_date_time')
        if sd:
            self.g.add((result, XS.singleDateTime, Literal(sd)))
        rd = data.get('range_of_dates')
        if rd:
            r = BNode()
            self.g.add((result, XS.rangeOfDates, r))
            self.g.add((r, XS.beginDate, Literal(rd['begin_date'])))
            self.g.add((r, XS.endDate, Literal(rd['end_date'])))
        return result

    def _taxonomic(self, data):
        result = BNode()
        gtc = data.get('general_taxonomic_coverage')
        if gtc:
            self.g.add((result, XS.generalTaxonomicCoverage, Literal(gtc)))
        tc = data.get('taxonomic_classification')
        if tc:
            for item in tc:
                r = BNode()
                self.g.add((result, XS.taxonomicClassification, r))
                self.g.add(
                    (r, XS.taxonRancValue, Literal(item['taxon_rank_value']))
                )
                tn = item.get('taxon_rank_name')
                if tn:
                    self.g.add((r, XS.taxonRancName, Literal(tn)))
                cn = item.get('common_name')
                if cn:
                    self.g.add((r, XS.taxonRancName, Literal(cn)))

        return result

    def _maintenance(self, data):
        result = BNode()
        value = data.get('description')
        if value:
            self.g.add((result, XS.description, Literal(value)))
        self.g.add((
            result, XS.maintenanceUpdateFrequency,
            Literal(data['maintenance_update_frequency'])
        ))

        return result

    def _methods(self, data):
        result = BNode()
        self.g.add((result, XS.methodStep, Literal(data['method_step'])))

        qc = data.get('quality_control')
        if qc:
            self.g.add((result, XS.qualityControl, Literal(qc)))
        s = data.get('sampling')
        if s:
            r = BNode()
            self.g.add((result, XS.sampling, r))
            self.g.add((r, XS.studyExtent, Literal(s['study_extent'])))
            self.g.add((
                r, XS.samplingDescription, Literal(s['sampling_description'])
            ))
        return result

    def _project(self, data):
        result = BNode()
        self.g.add((result, XS.title, Literal(data['title'])))

        p = data.get('personnel')
        if p:
            for person in p['person']:
                self.g.add((result, XS.personnel, self._agent(person)))
        ab = data.get('abstract')
        if ab:
            self.g.add((result, XS.abstract, Literal(ab)))
        funding = data.get('funding')
        if funding:
            self.g.add((result, XS.funding, Literal(funding)))

        s = data.get('study_area_description')
        if s:
            r = BNode()
            self.g.add((result, XS.studyAreaDescription, r))
            self.g.add((r, XS.descriptorValue, Literal(s['descriptor_value'])))
            self.g.add((
                r, XS.citableClassificationSystem,
                Literal(s['citable_classification_system'])
            ))
            name = s.get('name')
            if name:
                self.g.add((r, XS.name, Literal(name)))

        dd = data.get('design_description')
        if dd:
            self.g.add((result, XS.designDescription, Literal(dd)))

        return result

    def extract_data(self, id):
        self.g = g = self._init_graph(id)

        dataset = BNode()
        g.add((DC.description, XS.dataset, dataset))

        # Base fields
        items = (
            ('title', XS.title, Literal),
            ('pub_date', XS.pubDate, Literal),
            ('abstract', XS.abstract, Literal),
            ('additional_info', XS.additionalInfo, Literal),
            ('intellectual_rights', XS.intellectualRights, Literal),
            ('purpose', XS.purpose, Literal),
        )
        for key, type_, el in items:
            value = self._dataset_dict.get(key)
            if not value:
                continue
            g.add((dataset, type_, el(value)))

        # List fields
        items = (
            ('alternate_identifier', ADMS.identifier, Literal),
            ('creator', DC.creator, self._agent),
            ('metadata_provider', XS.metadataProvider, self._agent),
            ('associated_party', XS.associatedParty, self._agent),
            ('language', DCT.language, Literal),
            ('keyword_set', XS.keywordSet, self._keyword_set),
            ('resources', DCAT.distribution, self._distribution),
            ('coverage', XS.coverage, self._coverage),
            ('maintenance', XS.maintenance, self._maintenance),
            ('contact', XS.contact, self._agent),
            ('methods', XS.methods, self._methods),
            ('project', XS.project, self._project),
        )
        for key, predicate, type_ in items:
            for value in self._dataset_dict[key]:
                g.add((dataset, predicate, type_(value)))

        return {'data': g.serialize(format='pretty-xml')}
