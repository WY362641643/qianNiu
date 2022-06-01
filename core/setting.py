#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
BASE_PATH = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
app_data_path = os.path.join(*os.path.split(BASE_PATH)[:-1], "qianNiu", "appData")
