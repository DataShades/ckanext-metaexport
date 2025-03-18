import datetime
import json
import logging
import uuid
from typing import Any, Callable, Generator, Iterator
from urllib.parse import quote

from dateutil.parser import parse as parse_date
from rdflib import Literal, URIRef
from rdflib.namespace import XSD, Namespace

import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

PREFIX_MAILTO = "mailto:"

ADMS = Namespace("http://www.w3.org/ns/adms#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GEOJSON_IMT = "https://www.iana.org/assignments/media-types/application/vnd.geo+json"
GSP = Namespace("http://www.opengis.net/ont/geosparql#")
LOCN = Namespace("http://www.w3.org/ns/locn#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SCHEMA = Namespace("http://schema.org/")
SPDX = Namespace("http://spdx.org/rdf/terms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
EML = Namespace("eml://ecoinformatics.org/eml-2.1.1")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")


def get_date_triple(
    subject: URIRef | Any,
    predicate: URIRef | Any,
    value: str,
    _type: type = Literal,
) -> tuple[Any, Any, Any] | None:
    """Creates a triple containing a date value.

    Parses the input date string and creates a triple with the date value. If parsing
    succeeds, the date is added as an XSD.dateTime typed literal. If parsing fails,
    the original string value is used.

    Args:
        subject: Subject node of the triple
        predicate: Predicate node of the triple
        value: Date string to parse
        _type: Type constructor for the object node (default: Literal)

    Returns:
        A (subject, predicate, object) triple if value is not empty, None otherwise
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


def get_list_triple(
    subject: URIRef | Any,
    predicate: URIRef | Any,
    value: str | list[Any],
    _type: type = Literal,
) -> Iterator[tuple[Any, Any, Any]]:
    """Creates triples from a list or comma-separated string value.

    Generates triples by splitting the input value into individual items. If value is a
    list, creates one triple per list item. If value is a string, attempts to parse it
    as JSON or split on commas before creating triples.

    Args:
        subject: Subject node of the triples
        predicate: Predicate node of the triples
        value: List or string value to split into triples
        _type: Type constructor for the object nodes (default: Literal)

    Returns:
        Iterator yielding (subject, predicate, object) triples
    """
    items = []
    # List of values
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
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
    _dict: dict[str, Any],
    subject: Any,
    predicate: Any,
    key: str,
    fallbacks: list[str] | None = None,
    list_value: bool = False,
    date_value: bool = False,
    _type: type = Literal,
    value_modifier: Callable | None = None,
):
    """Adds a new triple to the graph with the provided parameters.

    Args:
        _dict: Dictionary containing the value to extract.
        subject: Subject of the triple (URIRef or BNode).
        predicate: Predicate of the triple (URIRef or BNode).
        key: Key to look up the value in the dictionary.
        fallbacks: List of fallback keys to check if primary key not found.
        list_value: If True, value is treated as a list.
        date_value: If True, value is treated as a date.
        _type: Type of the object node (default: Literal).
        value_modifier: Optional function to modify the extracted value.

    Returns:
        Iterator yielding triples (subject, predicate, object) if value found,
        empty iterator otherwise.
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
            triple for triple in get_list_triple(subject, predicate, value, _type)
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
    _dict: dict[str, Any],
    subject: Any,
    items: list[tuple[str, str, list[str], type]],
    list_value: bool = False,
    date_value: bool = False,
) -> Generator[
    tuple[Any, Any, URIRef | Literal] | tuple[Any, Any, Literal] | None,
    Any,
    Any,
]:
    for item in items:
        key, predicate, fallbacks, _type = item
        yield from get_triple_from_dict(
            _dict,
            subject,
            predicate,
            key,
            fallbacks=fallbacks,
            list_value=list_value,
            date_value=date_value,
            _type=_type,
        )


def get_list_triples_from_dict(
    _dict: dict[str, Any],
    subject: Any,
    items: list[tuple[str, str, list[str], type]],
) -> Generator[
    tuple[Any, Any, URIRef | Literal] | tuple[Any, Any, Literal] | None,
    Any,
    Any,
]:
    yield from get_triples_from_dict(_dict, subject, items, list_value=True)


def publisher_uri_from_dataset_dict(dataset_dict: dict[str, Any]) -> str | None:
    """Returns an URI for a dataset's publisher.

    This will be used to uniquely reference the publisher on the RDF serializations.

    The value will be the first found of:
      1. The value of the `publisher_uri` field
      2. The value of an extra with key `publisher_uri`
      3. `catalog_uri()` + '/organization/' + `organization id` field

    Check the documentation for `catalog_uri()` for the recommended ways of setting it.

    Returns:
        str: The publisher URI string, or None if no URI could be generated.
    """

    uri = dataset_dict.get("publisher_uri")

    if not uri:
        for extra in dataset_dict.get("extras", []):
            if extra["key"] == "publisher_uri":
                uri = extra["value"]
                break
    if not uri and dataset_dict.get("organization"):
        uri = "{}/organization/{}".format(
            catalog_uri().rstrip("/"),
            dataset_dict["organization"]["id"],
        )

    return uri


def catalog_uri():
    """
    Returns a URI for the entire catalog.

    This URI uniquely identifies the CKAN instance in RDF serializations and serves as
    a base for dataset URIs when not specified in metadata.

    Args:
        None

    Returns:
        str: The catalog URI string.

    The URI is determined by checking the following options in order:
        1. ckanext.dcat.base_uri config option (recommended)
        2. ckan.site_url config option
        3. http:// + app_instance_uuid config option (minus brackets)

    A warning is logged if falling back to the third option.
    """

    uri = tk.config.get("ckanext.dcat.base_uri") or tk.config.get("ckan.site_url")

    if uri:
        return uri

    app_uuid = tk.config.get("app_instance_uuid")

    if app_uuid:
        uri = "http://" + app_uuid.replace("{", "").replace("}", "")
        log.critical(
            "Using app id as catalog URI, you should set the "
            "`ckanext.dcat.base_uri` or `ckan.site_url` option",
        )
    else:
        uri = "http://" + str(uuid.uuid4())
        log.critical(
            "Using a random id as catalog URI, you should set "
            "the `ckanext.dcat.base_uri` or `ckan.site_url` "
            "option",
        )

    return uri


def resource_uri(resource_dict: dict[str, Any]) -> str:
    """
    Returns a URI for the resource.

    This function generates a unique URI to identify the resource in RDF serializations.
    The URI is determined by checking the following in order:
        1. The value of the `uri` field if present
        2. A constructed URI combining:
           - `catalog_uri()`
           - '/dataset/'
           - `package_id`
           - '/resource/'
           - `id` field

    See `catalog_uri()` documentation for recommended configuration.

    Returns:
        str: The unique URI string for the resource.
    """

    uri = resource_dict.get("uri")

    if not uri or uri == "None":
        dataset_id = dataset_id_from_resource(resource_dict)

        uri = "{}/dataset/{}/resource/{}".format(
            catalog_uri().rstrip("/"),
            dataset_id,
            resource_dict["id"],
        )

    return uri


def dataset_id_from_resource(resource_dict: dict[str, Any]) -> str | None:
    """Finds the id for a dataset from a resource dictionary.

    Args:
        resource_dict (dict[str, Any]): Dictionary containing resource metadata.

    Returns:
        str: The ID of the dataset that contains this resource.

    Note:
        For CKAN versions < 2.3, falls back to looking up the resource model
        to find its package ID.
    """
    dataset_id = resource_dict.get("package_id")
    if dataset_id:
        return dataset_id

    # CKAN < 2.3
    resource = model.Resource.get(resource_dict["id"])
    if resource:
        return resource.package_id


class CleanedURIRef:
    """A factory class that performs URL encoding before creating URIRef objects.

    This class creates URIRef objects after performing basic URL encoding on the input value.
    It can be used as a type in graph.add() without affecting the resulting node types.

    Example:
        The following calls will result in the same node type:
            g.add(..., URIRef)
            g.add(..., CleanedURIRef)
    """

    @staticmethod
    def _careful_quote(value: str) -> str:
        # only encode this limited subset of characters to avoid more
        # complex URL parsing (e.g. valid ? in query string vs. ? as
        # value).  can be applied multiple times, as encoded %xy is
        # left untouched. Therefore, no unquote is necessary
        # beforehand.
        quotechars = " !\"$'()*,;<>[]{|}"
        for c in quotechars:
            value = value.replace(c, quote(c))
        return value

    def __new__(cls, value: str) -> URIRef:
        if isinstance(value, str):
            value = CleanedURIRef._careful_quote(value.strip())
        return URIRef(value)


def add_mailto(mail_addr: str) -> str:
    """
    Ensures that the mail address has an URIRef-compatible mailto: prefix.
    Can be used as modifier function for `_add_triple_from_dict`.

    Args:
        mail_addr: The mail address to add the mailto: prefix to.

    Returns:
        str: The mail address with the mailto: prefix.
    """
    if mail_addr:
        return PREFIX_MAILTO + without_mailto(mail_addr)
    else:
        return mail_addr


def without_mailto(mail_addr: str) -> str:
    """
    Ensures that the mail address string has no mailto: prefix.

    Args:
        mail_addr: The mail address to remove the mailto: prefix from.

    Returns:
        str: The mail address without the mailto: prefix.
    """
    if mail_addr:
        return mail_addr.replace(PREFIX_MAILTO, "")
    else:
        return mail_addr
