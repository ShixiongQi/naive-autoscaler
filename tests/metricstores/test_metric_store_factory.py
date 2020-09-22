from mock import Mock, call, patch
import pytest
from app.metricstores import MetricStoreFactory
from app.metricstores.metricStore import MetricStore


class TestMetricStoreFactory(object):
    def setup(self):
        self.metric_store_factory = MetricStoreFactory()

    def test_get_metric_store_creates_prometheus_metric_store_when_type_is_prometheus(self):
        metric_store_config = {
            "poll_interval_seconds": 10,
            "autoscale_rules": [
                {
                    "service_name": "bouncer",
                    "network_name": "network_1",
                    "scale_min": 1,
                    "scale_max": 3,
                    "scale_up_threshold": 300,
                    "scale_down_threshold": 250,
                    "scale_step": 1,
                    "stablization_window": 300
                }
            ]
        }

        ipLists = ["128.110.154.72"]

        metric_store = self.metric_store_factory.get_metric_store(metric_store_config, ipLists)

        assert type(metric_store) == MetricStore