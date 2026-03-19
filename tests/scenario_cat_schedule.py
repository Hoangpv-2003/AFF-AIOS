import httpx
import json
import traceback

def test_cat_image_schedule():
    url = "http://localhost:8000/api/v1/agents/chat"
    payload = {
        "message": "gửi hình ảnh con mèo vào mỗi 8h hằng ngày cho tôi qua email tuanm7530@gmail.com",
        "conversation_history": [],
        "debug": True
    }
    
    print(f"Sending request to {url}...")
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                print(f"Server Error: {response.status_code}")
                print(response.text[:2000])
                return
                
            data = response.json()
            
            print("\n--- Reply ---")
            print(data.get('reply'))
            
            debug_info = data.get("_debug", {})
            intent = debug_info.get("intent", {})
            print(f"\n--- Intent ---")
            print(json.dumps(intent, indent=2, ensure_ascii=False))
            
            materialize = debug_info.get("materialize", {}) or {}
            all_skills = materialize.get("all_materialized_skills", [])
            print(f"\n--- All Materialized Skills ({len(all_skills)}) ---")
            for s in all_skills:
                skill_info = s.get("materialized_skill", {})
                print(f"  Skill: {skill_info.get('skill_id')} | static={skill_info.get('is_static')} | reused={skill_info.get('reused_existing')}")
                
            # Check assertions
            print("\n--- ASSERTIONS ---")
            if intent.get("wants_skill"):
                print("PASS: wants_skill=True")
            else:
                print("FAIL: wants_skill should be True")
            if len(all_skills) >= 2:
                print(f"PASS: {len(all_skills)} skills generated")
            else:
                print(f"FAIL: Expected >= 2 skills, got {len(all_skills)}")
                
            # Check files on disk
            import pathlib
            static_dir = pathlib.Path("skills/static")
            dynamic_dir = pathlib.Path("skills/dynamic")
            if static_dir.exists():
                static_folders = [d.name for d in static_dir.iterdir() if d.is_dir()]
                print(f"Static skills dir has: {static_folders}")
            else:
                print("No skills/static directory yet")
            return data
    except Exception as e:
        print(f"Client Error: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_cat_image_schedule()
