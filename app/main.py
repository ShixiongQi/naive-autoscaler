#!/usr/bin/python

import argparse
import yaml
import logging
from pytz import utc
from apscheduler.schedulers.blocking import BlockingScheduler

from .scaling_client.scaling_client import ScalingClient
from .metricstores import MetricStoreFactory
from .autoscaler import Autoscaler

DEFAULT_LOG_LEVEL='info'

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse the configuration files
    parser = argparse.ArgumentParser(description='Autoscale services for Bouncer/Divider in Mizar')
    parser.add_argument('config_file', help='Path of the config file')
    parser.add_argument('--log-level', help='Log level', default = DEFAULT_LOG_LEVEL)
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.getLevelName(args.log_level.upper()))

    # Setup components
    with open(args.config_file) as config_file:
        config = yaml.load(config_file, Loader=yaml.Loader)
        logger.debug("Config %s", config)
        metric_store_factory = MetricStoreFactory() # Setup MetricsStore # TODO: need to be fixed
        scaling_client = ScalingClient() # Setup Scaling Client
        scheduler = BlockingScheduler(timezone=utc)
        autoscaler = Autoscaler(config, scaling_client, metric_store_factory, scheduler)
    autoscaler.start()
