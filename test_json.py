import json

# Test JSON parsing
content = '{"type": "read_file", "path": "demo.py"}'
data = json.loads(content)
print(f"Parsed data: {data}")
print(f"Type: {data['type']}")
print(f"Path: {data['path']}") 