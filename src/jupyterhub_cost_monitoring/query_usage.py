"""
Query the Prometheus server to get usage of JupyterHub resources.
"""

import os
from collections import defaultdict
from datetime import datetime

import requests
from yarl import URL

from .const_usage import TIME_RESOLUTION, USAGE_MAP
from .const_usage import TIME_RESOLUTION, USAGE_MAP

prometheus_url = os.environ.get(
    "PROMETHEUS_HOST", "http://localhost:9090"
)  # TODO: replace server URL definition


def query_prometheus(
    query: str, from_date: str, to_date: str, step: str = TIME_RESOLUTION
) -> requests.Response:
    """
    Query the Prometheus server with the given query.
    """
    prometheus_api = URL(prometheus_url)
    parameters = {
        "query": query,
        "start": from_date,
        "end": to_date,
        "step": TIME_RESOLUTION,
        "step": step,
    }
    query_api = URL(prometheus_api.with_path("/api/v1/query_range"))
    response = requests.get(query_api, params=parameters)
    response.raise_for_status()
    result = response.json()
    return result


def query_usage(
    from_date: str,
    to_date: str,
    hub_name: str | None,
    component_name: str | None,
    user_name: str | None,
) -> list[dict]:
    """
    Query usage from the Prometheus server.
    Args:
        from_date: Start date in string ISO format (YYYY-MM-DD).
        to_date: End date in string ISO format (YYYY-MM-DD).
        hub_name: Optional name of the hub to filter results.
        component_name: Optional name of the component to filter results.
        user_name: Optional name of the user to filter results.
    """
    result = []
    if component_name is None:
        for component, query in USAGE_MAP.items():
            response = query_prometheus(query, from_date, to_date)
            result.extend(_process_response(response, component_name, subcomponent))
    result = _filter_json(result, hub=hub_name, user=user_name)
    return result


def _process_response(
    response: requests.Response,
    component_name: str,
) -> dict:
    """
    Process the response from the Prometheus server to extract compute usage data.
    Args:
        response: The response object from the Prometheus query.
        component_name: Name of the component, e.g "compute", "home directory".
        subcomponent_name: A subset of the component being queried, e.g. "memory", "cpu".
    """
    result = []
    for data in response["data"]["result"]:
        hub = data["metric"]["namespace"]
        user = data["metric"]["annotation_hub_jupyter_org_username"]
        date = [
            datetime.utcfromtimestamp(value[0]).strftime("%Y-%m-%d")
            for value in data["values"]
        ]
        usage = [float(value[1]) for value in data["values"]]
        result.append(
            {
                "hub": hub,
                "component": component_name,
                "user": user,
                "date": date,
                "value": usage,
            }
        )
    pivoted_result = _pivot_response_dict(result)
    summed_result = _sum_by_date(pivoted_result)
    weighted_result = _calculate_user_weights(summed_result)
    return weighted_result


def _filter_json(result: list[dict], **filters):
    """
    Filter the result based on the provided filters.
    """
    return [
        item
        for item in result
        if all(filters[k] is None or item.get(k) == filters[k] for k in filters)
    ]


def _pivot_response_dict(result: list[dict]) -> list[dict]:
    """
    Pivot the response dictionary to have top-level keys as dates.
    """
    pivot = []
    for entry in result:
        for date, value in zip(entry["date"], entry["value"]):
            pivot.append(
                {
                    "date": date,
                    "user": entry["user"],
                    "hub": entry["hub"],
                    "component": entry["component"],
                    "value": value,
                }
            )
    return pivot


def _sum_by_date(result: list[dict]) -> list[dict]:
    """
    Sum over the result values by date, since Prometheus can return multiple entries for a single date.
    """
    sums = defaultdict(float)
    for entry in result:
        key = (
            entry["date"],
            entry["user"],
            entry["hub"],
            entry["component"],
        )
        sums[key] += entry["value"]
    return [
        {
            "date": date,
            "user": user,
            "hub": hub,
            "component": component,
            "value": total,
        }
        for (date, user, hub, component), total in sums.items()
    ]
