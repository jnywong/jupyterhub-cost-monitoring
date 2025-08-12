"""
Query the Prometheus server to get the usage of JupyterHub resources.
"""

import argparse

import requests
from yarl import URL


def query_prometheus(prometheus_url: str, query: str):
    """
    Query the Prometheus server with the given query.
    """
    prometheus_api = URL(prometheus_url)
    query_api = prometheus_api.with_path("/api/v1/query").with_query({"query": query})
    response = requests.get(str(query_api))
    response.raise_for_status()

    result = response.json()["data"]["result"]

    return result


def main():
    argparser = argparse.ArgumentParser(
        description="Query JupyterHub usage from Prometheus."
    )
    argparser.add_argument(
        "--prometheus_url",
        default="http://localhost:9090",
        type=str,
        help="URL of the Prometheus server.",
    )
    argparser.add_argument(
        "--query",
        required=True,
        type=str,
        help="Prometheus query to execute.",
    )

    args = argparser.parse_args()

    result = query_prometheus(args.prometheus_url, args.query)

    print(f"Query Result:{result}")


if __name__ == "__main__":
    main()
