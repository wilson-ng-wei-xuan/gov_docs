# update your project specific environmental
lambda_layers = [
  # layer must be smaller than 70167211 bytes for the PublishLayerVersion
  {
    "layer_name": "cryptography",
    "filename": "cryptography_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "docx-python311",
    "filename": "docx_python3.11.zip",
    "compatible_runtimes": ["python3.11"]
  },
  {
    "layer_name": "jwt-python311",
    "filename": "jwt_python3.11.zip",
    "compatible_runtimes": ["python3.11"]
  },
  {
    "layer_name": "opensearch-py",
    "filename": "opensearch-py_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "pillow-python311",
    "filename": "pillow_python3.11.zip",
    "compatible_runtimes": ["python3.11"]
  },
  {
    "layer_name": "pillow",
    "filename": "pillow_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "pyjwt",
    "filename": "pyjwt_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "pymongo",
    "filename": "pymongo_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "python-docx",
    "filename": "python-docx_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "requests-aws4auth",
    "filename": "requests-aws4auth_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  },
  {
    "layer_name": "unstructured-docx",
    "filename": "unstructured[docx]_python3.12.zip",
    "compatible_runtimes": ["python3.12"]
  }
]