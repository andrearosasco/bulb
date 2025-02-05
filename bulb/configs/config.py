from datetime import datetime as dt
from multiprocessing import Process

class ProjectConfig:
    project_dir = ''
    experiment_root = ''

    class Test:
        test = 'test'
        class A(Process):
            ciao = 'ciao'

class ExperimentConfig:
    experiment_name = f'{dt.now().strftime("%Y%m%d_%H%M%S")}'
    experiment_description = ''
    runner = 'qsub'

