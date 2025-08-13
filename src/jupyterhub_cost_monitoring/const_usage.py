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
