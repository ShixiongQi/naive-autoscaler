from .metricStore import MetricStore

class MetricStoreFactory(object):
    def get_metric_store(self, config):
    	return MetricStore(config)
