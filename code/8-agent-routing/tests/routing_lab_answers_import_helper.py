"""Imports `routing_lab.answers.py` under a legal module name.

The answers filename has a dot in it, so `import routing_lab.answers` would be
read as a package import — every test module goes through this helper instead.
"""
import importlib.util, pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "routing_lab.answers.py"
spec = importlib.util.spec_from_file_location("routing_lab_answers", p)
answers = importlib.util.module_from_spec(spec); spec.loader.exec_module(answers)
