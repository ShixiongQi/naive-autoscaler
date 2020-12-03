import yaml
from pytz import utc
from apscheduler.schedulers.blocking import BlockingScheduler
from app.autoscaler import Autoscaler
from app.scaling_client.scaling_client import ScalingClient
from app.metricstores import MetricStoreFactory


print("AutoScaler Test")
with open("example/autoscaler.yml") as data:
    config = yaml.load(data, Loader=yaml.Loader)
    # print("config: {}".format(yaml.dump(config)))
    scalingHandler = ScalingClient()
    metric_store_factory = MetricStoreFactory()
    scheduler = BlockingScheduler(timezone=utc)
    a_scale = Autoscaler(config=config, scaling_client=scalingHandler, metric_store_factory=metric_store_factory, scheduler=scheduler)

a_scale.start()