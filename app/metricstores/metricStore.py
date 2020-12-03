import requests
import np
import math
import json

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
			# prometheus_query_url = "http://{}:19999/api/v1/allmetrics?format=prometheus".format(prometheus_url)
			prometheus_query_url = "http://{}:19999/api/v1/data?chart=transit_xdp.pps&after=-1".format(prometheus_url)
			response = requests.get(prometheus_query_url).json()
			# print(response['data'][0][1])
			metric_value = response['data'][0][1] # the transit_xdp.pps metrics

			'''Write the data to the metric queue'''
			poll_interval_seconds = self.config['poll_interval_seconds']
			# print(math.ceil(stablization_window_size/poll_interval_seconds))
			if len(self.metric_queue) > math.ceil(stablization_window_size/poll_interval_seconds):
				self.deQueue()
				self.enQueue(metric_value)
			else:
				self.enQueue(metric_value)

			metric_matrix = np.array([self.metric_queue])
			# print("metrics Queue: {}".format(self.metric_queue))
			# print("len(metric_matrix): {}".format(len(metric_matrix)))
			# print("metric_matrix: {}".format(metric_matrix))
			''' Calculate the average value (per bouncer) in the Window '''
			''' Append the "per bouncer" metrics to "per network" metrics '''
			metrics_per_network.append(metric_matrix.mean(axis = 1)) # Mean by row
			# print("metrics_per_net: {}".format(metrics_per_network))
		# print("metrics_per_net: {}".format(metrics_per_network[0]))
		return metrics_per_network[0]
		# ''' Calculate the average value (per bouncer) in the Window '''
		# metrics_per_network_matrix = np.array([metrics_per_network])
		# metrics_per_network_matrix.mean(axis = 1)

		# ''' 3rd element is average RX rate across all the bouncers '''
		# return metrics_per_network_matrix[2]

