"""
Framework for implementing result-patterned state-machines.
"""

from . import config
from . import decorator
from .abstract_machine import AbstractMachine
from .abstract_repository import AbstractRepository
from .base_dependency import BaseDependency
from .logger import Logger
from .logger_model import LoggerModel
from .result import Failure, Result, Success
from .base_state import BaseState
from .transition import Exit, Transition
