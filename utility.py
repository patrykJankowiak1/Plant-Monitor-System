#!/usr/bin/python3
# -*- coding: utf-8 -*-

from time import  time
import json

def read_config(path):
    """ Function read json format config and return dict """
    with open(path,'r') as cfg:
        return json.load(cfg)

def get_timestamp():
    return int(time())


def deep_get(_dict, *keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict

