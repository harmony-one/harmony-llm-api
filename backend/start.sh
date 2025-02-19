#!/bin/bash
flask db upgrade
exec python main.py