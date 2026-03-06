#!/usr/bin/env python3
import requests
import json

try:
    response = requests.get('http://localhost:5000/api/market-emotion', timeout=30)
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"错误：{e}")
