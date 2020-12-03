import json
import yaml
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import os
import pprint

# ScalingHandler
class ScalingClient(object):
    def __init__(self):
        self.DOMAIN = "mizar.com"
        global config
        if 'KUBERNETES_PORT' in os.environ:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        configuration = client.Configuration()
        configuration.assert_hostname = False
        self.api_client = client.api_client.ApiClient(configuration=configuration)
        self.create_scaling_decision_crd() # create CRD of scaling decision

    def create_scaling_decision_crd(self):
        definition = '../../example/scaling_decision_crd.yml'
        v1 = client.ApiextensionsV1beta1Api()
        current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
        # print(current_crds)
        if 'decision' not in current_crds:
            print("Creating Decision definition")
            with open(definition) as data:
                body = yaml.load(data, Loader=yaml.Loader)
                # print(yaml.dump(body))
            try:
                v1.create_custom_resource_definition(body)
            except ValueError as exception: # Check: https://github.com/kubernetes-client/python/issues/1098
                if str(exception) == 'Invalid value for `conditions`, must not be `None`':
                    print("Skipping invalid \'conditions\' value...")
                else:
                    raise exception

    def get_bouncer_IP_from_network(self):
        ipList = []
        networkList = []
        VPCList = []
        if 'KUBERNETES_PORT' in os.environ:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        configuration = client.Configuration()
        configuration.assert_hostname = False
        api_client = client.api_client.ApiClient(configuration=configuration)
        crds = client.CustomObjectsApi(api_client)

        print("Waiting for Bouncers to come up...")
        resource_version = ''
        crd_list = crds.list_cluster_custom_object(self.DOMAIN, "v1", "bouncers", resource_version=resource_version)
        for crd in crd_list["items"]:
            # pp.pprint(crd)
            spec = crd.get("spec")
            ip = spec.get("ip")
            net = spec.get("net")
            vpc = spec.get("vpc")
            ipList.append(ip)
            networkList.append(net)
            VPCList.append(vpc)
            '''
            metadata = crd.get("metadata")
            resource_version = metadata['resourceVersion']
            name = metadata['name']
            print("IP address %s on Bouncer %s @ Network %s @ VPC %s" % (ip, name, net, vpc))
            '''
        return ipList, networkList, VPCList

    '''
    def get_bouncer_replica_count(self, network_name, service_name):
        ipList = self.get_bouncer_IP_from_network(service_name, network_name)
        service_replica_count = len(ipList)
        return service_replica_count
    '''

    '''
    def watch_crd(self):
        crds = client.CustomObjectsApi()
        DOMAIN = "mizar.com"
        resource_version = ''
        while True:
            stream = watch.Watch().stream(crds.list_cluster_custom_object, DOMAIN, "v1", "scaling", resource_version=resource_version)
            for event in stream:
                obj = event["object"]
                operation = event['type']
                spec = obj.get("spec")
                if not spec:
                    continue
                metadata = obj.get("metadata")
                resource_version = metadata['resourceVersion']
                name = metadata['name']
                print("Handling %s on %s" % (operation, name))
                done = spec.get("review", False)
                if done:
                    continue
                review_scaling_decision(crds, obj)
    '''

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
            ifFind = 0 # No decision
        else:
            ifFind = 1 # Find the existing decision
        # print(ifFind)
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
        # print("Resource deleted")

    def SentDecisionToAdaptor(self, network_name, service_name, replica_count):
        scaling_decision_data = {
            "network_name" : network_name,
            "service_name" : service_name,
            "replica_count" : replica_count
        }

        obj = {'apiVersion': 'mizar.com/v1',
            'metadata': {'name': service_name + '-' + network_name},
            'kind': 'Decision',
            'spec' : scaling_decision_data
            }

        # Generate CRD and send
        res = self.find_decision(obj['metadata']['name'], namespace='default')
        print("res: {}".format(res))
        if res == 0:
            # No decision, create new
            self.create_decision(body=obj, namespace='default')

        else:
            # Existing Decision, update
            self.update_decision(body=obj, namespace='default')



    def scale_service(self, network_name, service_name, replica_count):
        # Send Scaling Decision To Adaptor. Adaptor will handle the scaling 
        # of the Bouncer/Divider
        self.SentDecisionToAdaptor(network_name=network_name, service_name=service_name, replica_count=replica_count)
