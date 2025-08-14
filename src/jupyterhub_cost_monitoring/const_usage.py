"""
Constants used to query Prometheus for JupyterHub usage data.
"""

GRANULARITY = "1d"

MEMORY_PER_USER = """
    sum(
        container_memory_working_set_bytes{name!=\"\", pod=~\"jupyter-.*\", namespace=~\".*\"}
        * on (namespace, pod) group_left(annotation_hub_jupyter_org_username)
        group(
            kube_pod_annotations{namespace=~\".*\", annotation_hub_jupyter_org_username=~\".*\", pod=~\"jupyter-.*\"}
        ) by (pod, namespace, annotation_hub_jupyter_org_username)
    ) by (annotation_hub_jupyter_org_username, namespace)
"""

CPU_PER_USER = """
    sum(
        irate(container_cpu_usage_seconds_total{name!="", pod=~"jupyter-.*"}[5m])
        * on (namespace, pod) group_left(annotation_hub_jupyter_org_username)
        group(
            kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username=~".*"}
        ) by (pod, namespace, annotation_hub_jupyter_org_username)
    ) by (annotation_hub_jupyter_org_username, namespace)
"""

USAGE_MAP = {
    "compute": {
        "memory": MEMORY_PER_USER,
        "cpu": CPU_PER_USER,
    },
}
