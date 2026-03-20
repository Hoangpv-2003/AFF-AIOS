import sys
import json
import importlib.util
import os
import io
from pathlib import Path

# Force UTF-8 encoding for standard output and error on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Debug for environment (visible only in result.stdout if printed)
# print(f"DEBUG ENV KEYS: {list(os.environ.keys())}", file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "error_reason": "Missing arguments: skill_path input_json"}))
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    input_json = sys.argv[2]

    if not skill_path.exists():
        print(json.dumps({"status": "error", "error_reason": f"Skill not found: {skill_path}"}))
        sys.exit(1)

    try:
        input_data = json.loads(input_json)
    except Exception as e:
        print(json.dumps({"status": "error", "error_reason": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    # Set up environment
    module_name = "aaf_active_skill"
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, skill_path)
        if spec is None or spec.loader is None:
            raise ImportError("Could not load skill spec")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, "run") or not callable(module.run):
            raise AttributeError("Skill does not have a run() function")
            
        # Execute skill
        result = module.run(input_data=input_data, **input_data)
        
        if not isinstance(result, dict):
            # Wrap non-dict output
            result = {"status": "success", "raw_output": str(result)}
        elif "status" not in result:
            result["status"] = "success"
            
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({"status": "error", "error_reason": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
