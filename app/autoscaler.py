from datetime import datetime
import logging
import yaml
logger = logging.getLogger(__name__)

class Autoscaler(object):
    def __init__(self, config, scaling_client, metric_store_factory, scheduler, datetime_module=None):
        self.config = config
        self.scaling_client = scaling_client
        self.metric_store_factory = metric_store_factory
        self.scheduler = scheduler
        self.metric_stores_map = {}
        self.datetime_module = datetime_module or datetime
        autoscale_rules = self.config['autoscale_rules']
        # print(yaml.dump(autoscale_rules))
        for autoscale_rule in autoscale_rules:
            # print(yaml.dump(autoscale_rule))
            network_name = autoscale_rule['network_name']
            metric_store = self.metric_store_factory.get_metric_store(self.config) # Each network has its own metric store
            self.metric_stores_map[network_name] = metric_store


    def start(self):
        job = self.scheduler.add_job(self.run, 'interval', seconds=self.config['poll_interval_seconds'])
        job.modify(next_run_time=self.datetime_module.now(self.scheduler.timezone))
        self.scheduler.start()

    def run(self):
        ''' 
            To get the IP of the all bouncers in the cluster
        '''
        [ipList, networkList, VPCList] = self.scaling_client.get_bouncer_IP_from_network()
        # print("ipList: {}, netList: {}, VPCList: {}".format(ipList, networkList, VPCList))
        current_replica_count = 0

        autoscale_rules = self.config['autoscale_rules']
        for autoscale_rule in autoscale_rules:
            service_name = autoscale_rule['service_name']
            network_name = autoscale_rule['network_name']
            scale_min = autoscale_rule['scale_min']
            scale_max = autoscale_rule['scale_max']
            scale_step = autoscale_rule['scale_step']
            scale_up_threshold = autoscale_rule['scale_up_threshold']
            scale_down_threshold = autoscale_rule['scale_down_threshold']
            stablization_window_size = autoscale_rule['stablization_window']
            # Get the metric store by the metric store name
            metric_store = self.metric_stores_map[network_name]
            # print("service_name: {}, network_name: {}, scale_min: {}".format(service_name,network_name,scale_min))

            # Get Bouncer replicas count in Current network
            current_replica_count = len(ipList)
            logger.debug("Replica count for {} @ {}: {}".format(service_name, network_name, current_replica_count)) # "Replica count for bouncer in Network X in VPC X"
            # print("Replica count for {} @ {}: {}".format(service_name, network_name, current_replica_count))
            '''
            Auto scaling algorithm with window --- simple threshold method

            (1) Calcualte average metric value within window size

            (2) Make scaling decision based on threshold
                IF metric value > scale up threshold && (current_replica_count + scale_step) <= scale_max
                    SCALE UP

                IF metric value < scale down threshold && (current_replica_count - scale_step) >= scale_min
                    SCALE DOWN

            HPA: desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]
            '''
            # Get average metrics from the metrics store (per network) WITHIN a window size
            metric_value = metric_store.get_metric_value(stablization_window_size, ipList)
            logger.debug("Metric value for {} @ Network {}: {}".format(service_name, network_name, metric_value))
            print("Metric value for {} @ Network {}: {}".format(service_name, network_name, metric_value))
            if metric_value > scale_up_threshold and (current_replica_count + scale_step) <= scale_max:
                # logger.info("Scaling up {} from {} to {} as metric value is {}".format(service_name, current_replica_count, current_replica_count + scale_step, metric_value))
                print("Scaling up {} from {} to {} as metric value is {}".format(service_name, current_replica_count, current_replica_count + scale_step, metric_value))
                self.scaling_client.scale_service(network_name=network_name, service_name=service_name, replica_count=current_replica_count + scale_step)
            if metric_value < scale_down_threshold and (current_replica_count - scale_step) >= scale_min:
                # logger.info("Scaling down {} from {} to {} as metric value is {}".format(service_name, current_replica_count, current_replica_count - scale_step, metric_value))
                print("Scaling down {} from {} to {} as metric value is {}".format(service_name, current_replica_count, current_replica_count - scale_step, metric_value))
                self.scaling_client.scale_service(network_name=network_name, service_name=service_name, replica_count=current_replica_count - scale_step)
