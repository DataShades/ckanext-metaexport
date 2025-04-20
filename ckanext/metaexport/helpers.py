from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any
from bleach import clean as bleach_clean
from dateutil.parser import parse
from dateutil.tz import tzlocal

import ckan.logic as logic
import ckan.model as model

log = logging.getLogger(__name__)


def get_helpers():
    return {
        "filter_list": filter_list,
        "coordinate_format": coordinate_format,
        "metaexport_iso_date_with_tz": metaexport_iso_date_with_tz,
        "dataset_references_dates": dataset_references_dates,
        "change_date_time_display": change_date_time_display,
        "meta_undump": json.loads,
        "metaex_right_year": metaex_right_year,
        "metaex_get_top_org": metaex_get_top_org,
        "metaex_clean_html": metaex_clean_html,
    }


def filter_list(data: str) -> list[str]:
    """
    Filter a list of strings.

    Args:
        data: The data to filter.
    """
    return [x for x in data.strip().split(",") if x]


def coordinate_format(coordinate: float) -> str:
    """
    Format a coordinate value to a string with no decimal places.

    Args:
        coordinate: The coordinate value to format.

    Returns:
        The formatted coordinate value.
    """
    return f"{coordinate:f}".rstrip("0").rstrip(".")


def metaexport_iso_date_with_tz(
    date: str, with_time: bool = True, to_zero: bool = False,
) -> str:
    """
    Get the ISO date with the timezone.

    Args:
        date: The date to get the ISO date with the timezone from.
        with_time: Whether to include the time in the date.
        to_zero: Whether to convert the date to zero time.

    Returns:
        The ISO date with the timezone.
    """
    try:
        dt, _, us = date.partition(".")
        if with_time:
            return parse(dt, dayfirst=True).replace(tzinfo=tzlocal()).isoformat()
        else:
            date_obj = parse(dt, dayfirst=True)
            return f"{date_obj.year:04d}-{date_obj.month:02d}-{date_obj.day:02d}"
    except Exception as e:
        log.error("ISO date parse error: %s", e)
        return date


def dataset_references_dates(data: dict[str, Any]) -> list[tuple[str, str]]:
    """
    Get the dataset references dates.

    Args:
        data: The data to get the dataset references dates from.

    Returns:
        The dataset references dates.
    """
    return [
        (
            data[date_type + "_date"],
            date_type if date_type != "identification" else "creation",
        )
        for date_type in ("identification", "publication", "revision")
        if data.get(date_type + "_date")
    ]


def change_date_time_display(
    date_time: str, current_pattern: str, new_pattern: str,
) -> str:
    """
    Change the date time display to the new pattern.

    Args:
        date_time: The date time to change.
        current_pattern: The current pattern of the date time.
        new_pattern: The new pattern of the date time.

    Returns:
        The date time in the new pattern.
    """
    try:
        return datetime.strptime(date_time, current_pattern).strftime(new_pattern)
    except ValueError:
        return date_time


def metaex_right_year(date: str) -> bool:
    """
    Check if the year is correct.

    Args:
        date: The date to check.

    Returns:
        True if the year is correct, False otherwise.
    """
    time = ""
    wrong_years = [1901, 1900]

    try:
        time = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        print(e)

    if time:
        year = time.year
        if year not in wrong_years:
            return True

    return False


def metaex_get_top_org(org_id: str) -> model.Group | dict[str, Any] | None:
    """
    Get the top organization.

    Args:
        org_id: The organization id to get the top organization from.
        show_full: Whether to show the full organization.

    Returns:
        The top organization.
    """
    org = model.Group.get(org_id)

    if not org:
        return None

    if parents := org.get_parent_group_hierarchy(type=org.type):
        return logic.get_action("organization_show")({}, {"id": parents[0].id})

    return


def metaex_clean_html(text: str) -> str:
    """
    Clean the html of malicious content.

    Args:
        text: The html string to clean.

    Returns:
        The cleaned html string.
    """
    return bleach_clean(text, tags=[], strip=True)
