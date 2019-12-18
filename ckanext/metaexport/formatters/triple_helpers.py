from future import standard_library
standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from builtins import object
import logging
import uuid
import json
import datetime
from dateutil.parser import parse as parse_date
from urllib.parse import quote

from rdflib.namespace import XSD, Namespace
from rdflib import Literal, URIRef
from ckantoolkit import config
import ckan.model as model

log = logging.getLogger(__name__)

PREFIX_MAILTO = u"mailto:"

ADMS = Namespace("http://www.w3.org/ns/adms#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GEOJSON_IMT = (
    "https://www.iana.org/assignments/media-types/application/vnd.geo+json"
)
GSP = Namespace("http://www.opengis.net/ont/geosparql#")
LOCN = Namespace("http://www.w3.org/ns/locn#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SCHEMA = Namespace("http://schema.org/")
SPDX = Namespace("http://spdx.org/rdf/terms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
EML = Namespace("eml://ecoinformatics.org/eml-2.1.1")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")


def get_date_triple(subject, predicate, value, _type=Literal):
    """
    Adds a new triple with a date object
    Dates are parsed using dateutil, and if the date obtained is correct,
    added to the graph as an XSD.dateTime value.
    If there are parsing errors, the literal string value is added.
    """
    if not value:
        return
    try:
        default_datetime = datetime.datetime(1, 1, 1, 0, 0, 0)
        _date = parse_date(value, default=default_datetime)

        return (
            subject,
            predicate,
            _type(_date.isoformat(), datatype=XSD.dateTime),
        )
    except ValueError:
        return (subject, predicate, _type(value))


def get_list_triple(subject, predicate, value, _type=Literal):
    """
    Adds as many triples to the graph as values
    Values are literal strings, if `value` is a list, one for each
    item. If `value` is a string there is an attempt to split it using
    commas, to support legacy fields.
    """
    items = []
    # List of values
    if isinstance(value, list):
        items = value
    elif isinstance(value, basestring):
        try:
            # JSON list
            items = json.loads(value)
            if isinstance(items, ((int, int, float, complex))):
                items = [items]
        except ValueError:
            if "," in value:
                # Comma-separated list
                items = value.split(",")
            else:
                # Normal text value
                items = [value]

    return iter(
        (
            subject,
            predicate,
            (CleanedURIRef if _type == URIRef else _type)(item),
        )
        for item in items
    )


def get_triple_from_dict(
    _dict,
    subject,
    predicate,
    key,
    fallbacks=None,
    list_value=False,
    date_value=False,
    _type=Literal,
    value_modifier=None,
):
    """Adds a new triple to the graph with the provided parameters
    The subject and predicate of the triple are passed as the
    relevant RDFLib objects (URIRef or BNode). As default, the
    object is a literal value, which is extracted from the dict
    using the provided key . If the value for the key is not
    found, then additional fallback keys are checked.  Using
    `value_modifier`, a function taking the extracted value and
    returning a modified value can be passed.  If a value was
    found, the modifier is applied before adding the value.  If
    `list_value` or `date_value` are True, then the value is
    treated as a list or a date respectively.

    """
    value = _dict.get(key)
    if not value and fallbacks:
        for fallback in fallbacks:
            value = _dict.get(fallback)
            if value:
                break

    # if a modifying function was given, apply it to the value
    if value and callable(value_modifier):
        value = value_modifier(value)

    if value and list_value:
        return iter(
            triple
            for triple in get_list_triple(subject, predicate, value, _type)
        )

    elif value and date_value:
        return iter([get_date_triple(subject, predicate, value, _type)])
    elif value:
        # Normal text value
        # ensure URIRef items are preprocessed (space removal/url encoding)
        if _type == URIRef:
            _type = CleanedURIRef
        return iter([(subject, predicate, _type(value))])
    return iter([])


def get_triples_from_dict(
    _dict, subject, items, list_value=False, date_value=False
):
    for item in items:
        key, predicate, fallbacks, _type = item
        for triple in get_triple_from_dict(
            _dict,
            subject,
            predicate,
            key,
            fallbacks=fallbacks,
            list_value=list_value,
            date_value=date_value,
            _type=_type,
        ):
            yield triple


def get_list_triples_from_dict(_dict, subject, items):
    for triple in get_triples_from_dict(
        _dict, subject, items, list_value=True
    ):
        yield triple


def publisher_uri_from_dataset_dict(dataset_dict):
    """
    Returns an URI for a dataset's publisher
    This will be used to uniquely reference the publisher on the RDF
    serializations.
    The value will be the first found of:
        1. The value of the `publisher_uri` field
        2. The value of an extra with key `publisher_uri`
        3. `catalog_uri()` + '/organization/' + `organization id` field
    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.
    Returns a string with the publisher URI, or None if no URI could be
    generated.
    """

    uri = dataset_dict.get("publisher_uri")
    if not uri:
        for extra in dataset_dict.get("extras", []):
            if extra["key"] == "publisher_uri":
                uri = extra["value"]
                break
    if not uri and dataset_dict.get("organization"):
        uri = "{0}/organization/{1}".format(
            catalog_uri().rstrip("/"), dataset_dict["organization"]["id"]
        )

    return uri


def catalog_uri():
    """
    Returns an URI for the whole catalog
    This will be used to uniquely reference the CKAN instance on the RDF
    serializations and as a basis for eg datasets URIs (if not present on
    the metadata).
    The value will be the first found of:
        1. The `ckanext.dcat.base_uri` config option (recommended)
        2. The `ckan.site_url` config option
        3. `http://` + the `app_instance_uuid` config option (minus brackets)
    A warning is emited if the third option is used.
    Returns a string with the catalog URI.
    """

    uri = config.get("ckanext.dcat.base_uri")
    if not uri:
        uri = config.get("ckan.site_url")
    if not uri:
        app_uuid = config.get("app_instance_uuid")
        if app_uuid:
            uri = "http://" + app_uuid.replace("{", "").replace("}", "")
            log.critical(
                "Using app id as catalog URI, you should set the "
                + "`ckanext.dcat.base_uri` or `ckan.site_url` option"
            )
        else:
            uri = "http://" + str(uuid.uuid4())
            log.critical(
                "Using a random id as catalog URI, you should set "
                + "the `ckanext.dcat.base_uri` or `ckan.site_url` "
                + "option"
            )

    return uri


def resource_uri(resource_dict):
    """
    Returns an URI for the resource
    This will be used to uniquely reference the resource on the RDF
    serializations.
    The value will be the first found of:
        1. The value of the `uri` field
        2. `catalog_uri()` + '/dataset/' + `package_id` + '/resource/'
            + `id` field
    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.
    Returns a string with the resource URI.
    """

    uri = resource_dict.get("uri")
    if not uri or uri == "None":
        dataset_id = dataset_id_from_resource(resource_dict)

        uri = "{0}/dataset/{1}/resource/{2}".format(
            catalog_uri().rstrip("/"), dataset_id, resource_dict["id"]
        )

    return uri


def dataset_id_from_resource(resource_dict):
    """
    Finds the id for a dataset if not present on the resource dict
    """
    dataset_id = resource_dict.get("package_id")
    if dataset_id:
        return dataset_id

    # CKAN < 2.3
    resource = model.Resource.get(resource_dict["id"])
    if resource:
        return resource.get_package_id()


class CleanedURIRef(object):
    """Performs either some basic URL encoding on value before creating an
    URIRef object.  This is a factory for URIRef objects, which allows
    usage as type in graph.add() without affecting the resulting node
    types. That is, g.add(..., URIRef) and g.add(..., CleanedURIRef)
    will result in the exact same node type.

    """

    @staticmethod
    def _careful_quote(value):
        # only encode this limited subset of characters to avoid more
        # complex URL parsing (e.g. valid ? in query string vs. ? as
        # value).  can be applied multiple times, as encoded %xy is
        # left untouched. Therefore, no unquote is necessary
        # beforehand.
        quotechars = " !\"$'()*,;<>[]{|}"
        for c in quotechars:
            value = value.replace(c, quote(c))
        return value

    def __new__(cls, value):
        if isinstance(value, basestring):
            value = CleanedURIRef._careful_quote(value.strip())
        return URIRef(value)


def add_mailto(mail_addr):
    """
    Ensures that the mail address has an URIRef-compatible mailto: prefix.
    Can be used as modifier function for `_add_triple_from_dict`.
    """
    if mail_addr:
        return PREFIX_MAILTO + without_mailto(mail_addr)
    else:
        return mail_addr


def without_mailto(mail_addr):
    """
    Ensures that the mail address string has no mailto: prefix.
    """
    if mail_addr:
        return str(mail_addr).replace(PREFIX_MAILTO, u"")
    else:
        return mail_addr
