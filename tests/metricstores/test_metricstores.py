from mock import Mock, call, patch
from app.metricstores.metricStore import MetricStore

class TestMetricStore(object):
    def setup(self):
        self.config = {
            "poll_interval_seconds": 10
        }
        self.ipList = ["128.110.154.72"]
        # self.win_size = 300
        self.metric_store = MetricStore(self.config, self.ipList)

    @patch('requests.get')
    def test_get_metric_value_calls_metricstore_query_api_for_given_metric_query(self, requests_get):
        # print(self.metric_store)
        win_size = 300
        print(MetricStore)
        help(self.metric_store)
        # self.metric_store.viewQueue()
        self.metric_store.get_metric_value(stablization_window_size = win_size)

        requests_get.assert_called_once_with('http://{}:19999/api/v1/allmetrics?format=prometheus'.format(self.ipList[0]))