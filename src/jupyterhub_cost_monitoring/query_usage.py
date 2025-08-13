"""
Query the Prometheus server to get usage of JupyterHub resources.
"""

import os
from collections import defaultdict
from datetime import datetime

import requests
from yarl import URL

from .const_usage import GRANULARITY, MEMORY_PER_USER

prometheus_url = os.environ.get(
    "PROMETHEUS_HOST", "http://localhost:9090"
)  # TODO: replace server URL definition


def query_prometheus(query: str, from_date: str, to_date: str):
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
    print(f"Querying Prometheus API: {query_api}")
    response = requests.get(query_api, params=parameters)
    response.raise_for_status()

    result = response.json()

    return result


def query_usage_compute_per_user(
    from_date: str, to_date: str, hub_name: str | None, component_name: str | None
):
    """
    Query compute usage per user from the Prometheus server.
    Args:
        from_date: Start date in string ISO format (YYYY-MM-DD).
        to_date: End date in string ISO format (YYYY-MM-DD).
        hub_name: Optional name of the hub to filter results.
    """
    query = MEMORY_PER_USER
    response = query_prometheus(query, from_date, to_date)

    result_compute = []

    for data in response["data"]["result"]:
        user = data["metric"]["annotation_hub_jupyter_org_username"]
        date = [
            datetime.utcfromtimestamp(value[0]).strftime("%Y-%m-%d")
            for value in data["values"]
        ]
        usage = [float(value[1]) for value in data["values"]]
        hub = data["metric"]["namespace"]

        result_compute.append(
            {
                "user": user,
                "hub": hub,
                "date": date,
                "value": usage,
            }
        )

    # Pivot so that top-level keys are dates
    compute = []
    for result in result_compute:
        for date, value in zip(result["date"], result["value"]):
            compute.append(
                {
                    "date": date,
                    "user": result["user"],
                    "hub": result["hub"],
                    "value": value,
                }
            )

    sums = defaultdict(float)

    for entry in compute:
        key = (entry["date"], entry["user"], entry["hub"])
        sums[key] += entry["value"]

    # Convert back to list of dicts
    result = [
        {"date": date, "user": user, "hub": hub, "value": total}
        for (date, user, hub), total in sums.items()
    ]
    return result
