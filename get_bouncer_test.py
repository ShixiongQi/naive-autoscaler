import json
import yaml
from kubernetes import client, config, watch
import os
import time
import pprint
from kubernetes.client.rest import ApiException

class DecisionApi(object):
    def __init__(self):
        global config
        if 'KUBERNETES_PORT' in os.environ:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        configuration = client.Configuration()
        configuration.assert_hostname = False
        self.api_client = client.api_client.ApiClient(configuration=configuration)

    def create_decision(self, body, namespace='default'):
        resource_path = '/apis/mizar.com/v1/namespaces/' + namespace + '/decisions'# + '/decision-1'
        header_params = {}
        header_params['Accept'] = self.api_client.select_header_accept(['application/json'])
        header_params['Content-Type'] = self.api_client.select_header_content_type(['*/*'])

        (resp, code, header) = self.api_client.call_api(
                resource_path, 'POST', {'namespace': namespace}, {}, header_params, body, [], _preload_content=False)

        return json.loads(resp.data.decode('utf-8'))
    
    def update_decision(self, body, namespace='default'):
        crds = client.CustomObjectsApi(self.api_client)
        group = 'mizar.com' # str | the custom resource's group
        version = 'v1' # str | the custom resource's version
        # namespace = 'default'
        plural = 'decisions' # str | the custom object's plural name. For TPRs this would be lowercase plural kind.
        name = body['metadata']['name'] # str | the custom object's name
        # body = obj # object | The JSON schema of the Resource to patch.
        try:
            api_response = crds.patch_namespaced_custom_object(group, version, namespace, plural, name, body)
            # pp.pprint(api_response)
        except ApiException as e:
            print("Exception when calling CustomObjectsApi->patch_cluster_custom_object: %s\n" % e)

    def find_decision(self, name, namespace='default'):
        # get the resource and print out data
        resource = ''
        api = client.CustomObjectsApi(self.api_client)
        try:
            resource = api.get_namespaced_custom_object(
                group="mizar.com",
                version="v1",
                name=name,
                namespace=namespace,
                plural="decisions",
            )
        except ApiException as e:
            pass
        if resource == '':
            ifFind = 0 # Find the existing decision
        else:
            ifFind = 1 # No decision
        print(ifFind)
        return ifFind

    def delete_decision(self, name, namespace='default'):
        # delete it
        api = client.CustomObjectsApi(self.api_client)
        try:
            api.delete_namespaced_custom_object(
                group="mizar.com",
                version="v1",
                name=name,
                namespace=namespace,
                plural="decisions",
                body=client.V1DeleteOptions(),
            )
        except ApiException as e:
            print("Exception when calling CustomObjectsApi->delete_namespaced_custom_object: %s\n" % e)
        print("Resource deleted")


DOMAIN = "mizar.com"
pp = pprint.PrettyPrinter(indent=4)

if __name__ == "__main__":
    network_name = "net1"
    service_name = "bouncer"
    replica_count = 10

    scaling_decision_data = {
        "network_name" : network_name,
        "service_name" : service_name,
        "replica_count" : replica_count
    }
    
    decisionapi = DecisionApi()
    for i in range(1, 4):
        obj = {'apiVersion': 'mizar.com/v1',
            'metadata': {'name': 'decision-'+str(i)},
            'kind': 'Decision',
            # Arbitrary contents
            'spec' : scaling_decision_data
            }
        resp = decisionapi.create_decision(body=obj, namespace='default')
        print(str(resp))
    '''
    scaling_decision_data = {
        "network_name" : "net2",
        "service_name" : "test",
        "replica_count" : 2
    }

    obj = {'apiVersion': 'mizar.com/v1',
        'metadata': {'name': 'decision-1'},
        'kind': 'Decision',
        # Arbitrary contents
        'spec' : scaling_decision_data
        }

    decisionapi.update_decision(body=obj, namespace='default')

    decisionapi.find_decision('decision-1', namespace='default')

    decisionapi.delete_decision('decision-2', namespace='default')
    '''