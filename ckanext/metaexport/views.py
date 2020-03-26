# -*- coding: utf-8 -*-

from __future__ import print_function
import ckan.model as model
import ckan.plugins.toolkit as tk
import logging
from flask import Blueprint, make_response

from ckanext.metaexport.formatters import Formatter
from ckanext.metaexport.helpers import metaex_get_top_org


log = logging.getLogger(__name__)

metaexport = Blueprint("metaexport", __name__)


@metaexport.route("/dataset/<id>/metaexport/<format>")
def export(id, format):
    context = {"user": tk.c.user, "model": model}
    try:
        tk.check_access("package_show", context, {"id": id})
    except tk.NotAuthorized:
        return tk.abort(
            403,
            tk._("Not authorized to read dataset %s in %s format")
            % (id, format),
        )
    except tk.ObjectNotFound:
        return tk.abort(404, tk._("%s does not exist") % (id))
    try:
        fmt = Formatter.get(format)
    except NameError:
        return tk.abort(404, tk._("%s format is not supported") % format)
    data = fmt.extract_data(id)

    headers = {"content-type": fmt.get_content_type()}

    try:
        if "owner_org" in data:
            org = data["owner_org"]
            # Try to get parent Organization
            parent_org = metaex_get_top_org(org["id"], True)
            if parent_org:
                org = parent_org
                data["owner_org"] = org
    except Exception as e:
        print(e)
    body = fmt.render("metaexport/{}.html".format(format), extra_vars=data)
    return make_response((body, headers))


def get_blueprints():
    return [metaexport]
