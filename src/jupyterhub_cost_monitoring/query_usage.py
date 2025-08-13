"""
Query the Prometheus server to get usage of JupyterHub resources.
"""

from datetime import datetime

import requests
from yarl import URL

from .const_usage import COMPUTE_PER_USER, GRANULARITY

prometheus_url = "http://localhost:9090"  # TODO: replace server URL definition


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
    query = COMPUTE_PER_USER
    response = query_prometheus(query, from_date, to_date)

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
                "date": date,
                "value": usage,
            }
        )

    return result
