from unicodedata import name
import dns.resolver
import requests
import json
import sys
from os import getenv
from kubernetes import client, config


# Check each environment variable
# Nameservers
nameservers = getenv('nameservers', '8.8.8.8')
nameservers = nameservers.split(',')
# DNS Target
target = getenv('target', 'kube.danmanners.com')
# IP Fetch URL
ipUrl = getenv('ipurl', 'https://icanhazip.com')


# Do the DNS work
querier = dns.resolver.Resolver(configure=False)
querier.nameservers = nameservers
answers = [str(item) for item in querier.resolve(target, 'A')]
print(f'Addresses: {answers}')


# Get the Current IP Address
r = requests.get(ipUrl)
data = str(r.text).strip('\n')
print(f'Current IP: {data}')


# Kubernetes PoC Checks
config.load_kube_config()
v1 = client.CoreV1Api()
getExternalNameSvc = v1.list_namespaced_service(
    namespace="kube-system",
    _preload_content=False
)


# Fetch the data from Kubernetes
data = json.loads(getExternalNameSvc.data)
try:
    for item in data["items"]:
        if "external-ip" not in item["metadata"]["name"]:
            continue
        if item['spec']['type'] == "ExternalName":
            del item["metadata"]["managedFields"]
            del item["metadata"]["annotations"]["kubectl.kubernetes.io/last-applied-configuration"]
            print(json.dumps({
                "name": item["metadata"]["name"],
                "metadata": {
                    "annotations": item["metadata"]["annotations"]
                },
                "spec": item["spec"]
            }))
except:
    print("Something went horribly wrong with the Kubernetes response!")
    sys.exit(1)
