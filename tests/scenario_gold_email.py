import httpx
import json
import traceback

def test_gold_email_scenario():
    url = "http://localhost:8000/api/v1/agents/chat"
    payload = {
        "message": "gửi giá vàng hàng ngày vào email tuanm7530@gmail.com",
        "conversation_history": [],
        "debug": True
    }
    
    print(f"Sending request to {url}...")
    try:
        # Increase timeout to 300s for slow LLMs
        with httpx.Client(timeout=300.0) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                print(f"Server Error: {response.status_code}")
                print(response.text)
                return
                
            data = response.json()
            
            print("\n--- Response Summary ---")
            print(f"Reply: {data.get('reply')}")
            
            debug_info = data.get("_debug", {})
            intent = debug_info.get("intent", {})
            print(f"\n--- Intent Detected ---")
            print(json.dumps(intent, indent=2, ensure_ascii=False))
            
            materialize = debug_info.get("materialize", {})
            skill_info = (materialize or {}).get("materialized_skill", {})
            print(f"\n--- Skill Metadata ---")
            if skill_info:
                print(f"Skill ID: {skill_info.get('skill_id')}")
                print(f"Is Static: {skill_info.get('is_static')}")
                print(f"Reused Existing: {skill_info.get('reused_existing')}")
            else:
                print("No skill was materialized.")
            
            if intent.get("is_static"):
                print("\nSUCCESS Part 1: Intent correctly identified as Static.")
            else:
                print("\nFAILED Part 1: Intent NOT identified as Static.")
                
            if skill_info.get("is_static"):
                print("SUCCESS Part 2: Skill correctly marked as Static in registry.")
                
            return data
    except Exception as e:
        print(f"Client Error: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_gold_email_scenario()
