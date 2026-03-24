import subprocess
from typing import Dict, Any, Optional

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        # Execute the command to count .py files in the current directory
        command = 'find . -name "*.py" | wc -l'
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            return {
                "status": "error",
                "summary": "Không thể đếm file .py",
                "error_reason": "Lỗi khi thực thi lệnh"
            }
        
        count = int(result.stdout.strip())
        return {
            "status": "success",
            "summary": f"Đã đếm được {count} file .py trong thư mục hiện tại.",
            "count": count
        }
    
    except Exception as e:
        return {
            "status": "error",
            "summary": "Lỗi không xác định khi đếm file .py",
            "error_reason": str(e)
        }