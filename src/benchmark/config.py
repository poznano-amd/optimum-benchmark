from dataclasses import MISSING, dataclass
from logging import getLogger

from binascii import hexlify
from random import getrandbits

from platform import python_version
import time
from transformers import __version__ as transformers_version
from optimum.version import __version__ as optimum_version

from src.backends.config import BackendConfig

LOGGER = getLogger("benchmark")

@dataclass()
class BenchmarkConfig:

    # MODEL & TASK CONFIGURATION
    # Name of the model used for the benchmark
    model: str = MISSING

    # BENCHMARK CONFIGURATION
    # Number of forward pass to run before recording any performance counters.
    warmup_runs: int = MISSING
    # Duration in seconds the benchmark will collect performance counters
    benchmark_duration: int = MISSING

    # INPUTS CONFIGURATION
    # Number of samples given to the model at each forward
    batch_size: int = MISSING
    # The length of the sequence (in tokens) given to the model
    sequence_length: int = MISSING
    # Attention mask sparsity ratio (0.0 <= sparsity <= 1.0)
    sparsity: float = MISSING

    # BACKEND CONFIGURATION
    # The backend to use for recording timing (pytorch, optimum-onnxruntime)
    backend: BackendConfig = MISSING

    # EXPERIMENT CONFIGURATION
    # Experiment name
    experiment_name: str = 'default'
    # Experiment datetime
    experiment_datetime_id: int = int(time.time_ns())
    
    # ENVIRONMENT CONFIGURATION
    # Python interpreter version
    python_version: str = python_version()
    # Store the transformers version used during the benchmark
    transformers_version: str = transformers_version
    # # # Store the optimum version used during the benchmark
    optimum_version: str = optimum_version