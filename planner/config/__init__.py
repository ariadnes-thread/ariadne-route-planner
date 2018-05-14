import json
import os

__all__ = ['config']

with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
    config = json.load(f)
