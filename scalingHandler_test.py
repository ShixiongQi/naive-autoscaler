from app.scaling_client.scaling_client import ScalingClient

scalingHandler = ScalingClient()

[iplist, netlist, vpclist] = scalingHandler.get_bouncer_IP_from_network()

print("IPList: {}, NetList: {}, VPCList: {}".format(iplist, netlist, vpclist))

scalingHandler.scale_service(network_name='net1', service_name='bouncer', replica_count=3)
