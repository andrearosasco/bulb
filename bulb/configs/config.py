from datetime import datetime as dt
from clearconf import BaseConfig as bc
from clearconf import Prompt
from multiprocessing import Process

class ProjectConfig(bc):
    project_dir = ''
    experiment_root: Prompt | bool = ''

    class Test:
        test = 'test'
        class A(Process):
            ciao: Prompt = 'ciao'

class ExperimentConfig(bc):
    experiment_name = f'{dt.now().strftime("%Y%m%d_%H%M%S")}'
    experiment_description = ''
    runner = 'qsub'

