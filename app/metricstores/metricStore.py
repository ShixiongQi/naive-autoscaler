import requests
import np

class MetricStore(object):

    def __init__(self, config):
        self.config = config
        self.metric_queue = []

	def enQueue(self, metrics):
		self.metric_queue.append(metrics)

	def deQueue(self):
		if len(self.metric_queue) == 0:
			print("Cannot pop from an empty queue")
		else:
			self.metric_queue.pop(0)

	def viewQueue(self):
		print(self.metric_queue)

	def get_metric_value(self, stablization_window_size, ipList):
		metrics_per_network = []
		for ip in range(0, len(ipList)):
			prometheus_url = ipList[ip]
			prometheus_query_url = "http://{}:19999/api/v1/allmetrics?format=prometheus".format(prometheus_url)
			resposnse = requests.get(prometheus_query_url)
			resposnse_list_by_line = list(filter(None,resposnse.text.split("\n")))

			metrics = [] # all collected metrics at that time

			for x in range(1,len(resposnse_list_by_line)):
				r_list = list(filter(None,resposnse_list_by_line[x].split(" ")))
				metric_value = float(r_list[1]) # Metric Value 
				# tmp = r_list[0].split("dimension=")[1].split("\"")
				# metric_name = tmp[1] # Metric Name
				metrics.append(metric_value)

			'''Write the data to the metric queue'''
			poll_interval_seconds = self.config['poll_interval_seconds']
			if len(self.metric_queue) > ceil(stablization_window_size/poll_interval_seconds):
				self.deQueue()
				self.enQueue(metric_value)
			else:
				self.enQueue(metric_value)

			metric_matrix = np.array(self.metric_queue)

			''' Calculate the average value (per bouncer) in the Window '''
			metric_matrix.mean(axis = 1) # Mean by row
			''' Append the "per bouncer" metrics to "per network" metrics '''
			metrics_per_network.append(metric_matrix)

		''' Calculate the average value (per bouncer) in the Window '''
		metrics_per_network_matrix = np.array(metrics_per_network)
		metrics_per_network_matrix.mean(axis = 1)

		''' 3rd element is average RX rate across all the bouncers '''
		return metrics_per_network_matrix[2]

