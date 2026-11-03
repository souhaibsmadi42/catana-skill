# Lets both `python -m unittest discover tests` and `python -m unittest tests.test_scenarios` import `helpers`.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
