"""
Query the Prometheus server to get usage of JupyterHub resources.
"""

import os
from collections import defaultdict
from datetime import datetime

import requests
from yarl import URL

from .const_usage import GRANULARITY, USAGE_MAP

prometheus_url = os.environ.get(
    "PROMETHEUS_HOST", "http://localhost:9090"
)  # TODO: replace server URL definition


def query_prometheus(query: str, from_date: str, to_date: str) -> requests.Response:
    """
    Query the Prometheus server with the given query.
    """
    prometheus_api = URL(prometheus_url)
    parameters = {
        "query": query,
        "start": from_date,
        "end": to_date,
        "step": GRANULARITY,
    }
    query_api = URL(prometheus_api.with_path("/api/v1/query_range"))
    response = requests.get(query_api, params=parameters)
    response.raise_for_status()

    result = response.json()

    return result


def query_usage_compute_per_user(
    from_date: str, to_date: str, hub_name: str | None, component_name: str | None
) -> list[dict]:
    """
    Query compute usage per user from the Prometheus server.
    Args:
        from_date: Start date in string ISO format (YYYY-MM-DD).
        to_date: End date in string ISO format (YYYY-MM-DD).
        hub_name: Optional name of the hub to filter results.
    """

    result = []
    if component_name is None:
        raise ValueError("FIX: loop over all component names.")
    else:
        for subcomponent, query in USAGE_MAP[f"{component_name}"].items():
            response = query_prometheus(query, from_date, to_date)
            result.extend(_process_response(response, component_name, subcomponent))

    return result


def _process_response(
    response: requests.Response, component_name: str, subcomponent_name: str
) -> dict:
    """
    Process the response from the Prometheus server to extract compute usage data.
    """
    result = []
    for data in response["data"]["result"]:
        user = data["metric"]["annotation_hub_jupyter_org_username"]
        date = [
            datetime.utcfromtimestamp(value[0]).strftime("%Y-%m-%d")
            for value in data["values"]
        ]
        usage = [float(value[1]) for value in data["values"]]
        hub = data["metric"]["namespace"]
        result.append(
            {
                "user": user,
                "hub": hub,
                "component": component_name,
                "subcomponent": subcomponent_name,
                "date": date,
                "value": usage,
            }
        )
    pivoted_result = _pivot_response_dict(result)
    processed_result = _sum_by_date(pivoted_result)
    return processed_result


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
                    "subcomponent": entry["subcomponent"],
                    "value": value,
                }
            )
    return pivot


def _sum_by_date(result: list[dict]) -> list[dict]:
    """
    Sum the values by date.
    """
    sums = defaultdict(float)
    for entry in result:
        key = (
            entry["date"],
            entry["user"],
            entry["hub"],
            entry["component"],
            entry["subcomponent"],
        )
        sums[key] += entry["value"]
    return [
        {
            "date": date,
            "user": user,
            "hub": hub,
            "component": component,
            "subcomponent": subcomponent,
            "value": total,
        }
        for (date, user, hub, component, subcomponent), total in sums.items()
    ]
