"""Kubernetes client initialisation -supports both local kubeconfig and in-cluster."""
import os
from kubernetes import client, config
from kubernetes.client import CoreV1Api, AppsV1Api
 
 
def get_k8s_clients() -> tuple[CoreV1Api, AppsV1Api]:
    """
    Load kubeconfig from:
    1. KUBECONFIG env var (if set)
    2. ~/.kube/config (default, for local dev)
    3. In-cluster config (when running inside a pod)
    """
    try:
        if os.getenv('KUBERNETES_SERVICE_HOST'):  # running inside a pod
            config.load_incluster_config()
        else:
            config.load_kube_config()  # uses ~/.kube/config or $KUBECONFIG
    except Exception as e:
        raise RuntimeError(
            f'Cannot connect to Kubernetes cluster.\n'
            f'Make sure kubectl is configured correctly.\n'
            f'Error: {e}'
        )
 
    return client.CoreV1Api(), client.AppsV1Api()
