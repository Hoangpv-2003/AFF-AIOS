{
  "logic": "import os\n\ndef run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:\n    input_data = input_data or {}\n    directory_path = input_data.get('directory_path')\n    \n    if not directory_path:\n        return {\n            \"status\": \"error\",\n            \"summary\": \"Missing directory_path in input data\",\n            \"error_reason\": \"directory_path is required\"\n        }\n    \n    try:\n        file_list = os.listdir(directory_path)\n        return {\n            \"status\": \"success\",\n            \"summary\": f\"Listed {len(file_list)} items in {directory_path}\",\n            \"file_list\": file_list\n        }\n    except OSError as e:\n        return {\n            \"status\": \"error\",\n            \"summary\": f\"Failed to list directory {directory_path}\",\n            \"error_reason\": str(e)\n        }",
  "schema": {
    "name": "read_my_dir",
    "description": "Liệt kê nội dung thư mục bằng Python sandbox",
    "parameters": {
      "type": "object",
      "properties": {
        "directory_path": {
          "type": "string",
          "description": "Đường dẫn đến thư mục cần liệt kê"
        }
      },
      "required": ["directory_path"]
    }
  }
}