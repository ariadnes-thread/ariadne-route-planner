import json

__all__ = ['config']

with open('config.json', 'r') as f:
    config = json.load(f)
