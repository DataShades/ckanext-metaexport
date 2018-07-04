from dateutil.parser import parse
from dateutil.tz import tzlocal
from datetime import datetime
import json

import ckan.logic as logic
import ckan.model as model

def get_helpers():
    return dict(
        filter_list=filter_list,
        coordinate_format=coordinate_format,
        metaexport_iso_date_with_tz=metaexport_iso_date_with_tz,
        dataset_references_dates=dataset_references_dates,
        change_date_time_display=change_date_time_display,
        meta_undump=json.loads,
        metaex_right_year=metaex_right_year,
        metaex_get_top_org=metaex_get_top_org
    )


def filter_list(data):
    sorted_data = filter(lambda x: x, data.strip().split(','))
    return sorted_data


def coordinate_format(coordinate):
    coordinate = "{0:f}".format(coordinate).rstrip('0').rstrip('.')
    return coordinate


def metaexport_iso_date_with_tz(date, with_time=True, to_zero=False):
    try:
        dt, _, us = date.partition(".")
        if with_time:
            return parse(
                dt, dayfirst=True).replace(tzinfo=tzlocal()).isoformat()
        else:
            formated_date = "{:04d}-{:02d}-{:02d}"
            date = parse(dt, dayfirst=True)
            return formated_date.format(date.year, date.month, date.day)
    except Exception, e:
        print e
        return date


def dataset_references_dates(data):
    return [
      (data[date_type + '_date'], date_type if date_type != 'identification' else 'creation')
      for date_type in ('identification', 'publication', 'revision')
      if data.get(date_type + '_date')]


def change_date_time_display(date_time, current_pattern, new_pattern):
    date_time = datetime.strptime(
        date_time,
        current_pattern).strftime(new_pattern)
    return date_time

def metaex_right_year(date):
    time = ''
    wrong_years = [1901, 1900]
    try:     
        time = datetime.strptime(
            date, "%Y-%m-%d")
    except Exception as e:
        print e

    if time:
        year = time.year
        if year not in wrong_years:
            return True
    return False

def metaex_get_top_org(org_id, show_full=False):
    org = model.Group.get(org_id)
    if org is not None:
        parents = org.get_parent_group_hierarchy(type=org.type)
        if parents:
            parent = parents[0]
            if show_full:
                parent = logic.get_action('organization_show')(
                    {}, {'id': parent.id})
            return parent
