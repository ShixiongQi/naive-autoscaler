from app.metricstores.metricStore import MetricStore
import time

config = {
    "poll_interval_seconds": 1
}
# ipList = ["172.18.0.6", "172.18.0.5", "172.18.0.4"]
ipList = ["172.18.0.6"]
# self.win_size = 300
metric_store = MetricStore(config)

win_size = 10
# print(MetricStore)

# self.metric_store.viewQueue()
for i in range(0, 30):
    metric_store.get_metric_value(stablization_window_size = win_size, ipList = ipList)
    # metric_store.viewQueue()
    # print('Cycle: #{}'.format(i))
    time.sleep(config['poll_interval_seconds'])