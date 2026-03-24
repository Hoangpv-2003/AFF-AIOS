import asyncio
import os
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.system('chcp 65001 > nul')

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from app.infrastructure.external_apis.ollama_client import OllamaLLMClient
from app.agents.manager import UnifiedPipelineManager

async def test_pipeline():
    print("=" * 60)
    print("AIOS V2.0 10-PHASE PIPELINE BOOTSTRAPPER")
    print("=" * 60)
    
    from app.core.config import get_settings
    settings = get_settings()
    llm = OllamaLLMClient(
        base_url=settings.ollama_base_url,
        primary_model=settings.ollama_chat_model,
        fallback_models=[]
    )
    
    # 2. Instantiate master orchestrator
    manager = UnifiedPipelineManager(llm_client=llm)
    
    # 3. Simulate user request
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = "Ngày mai tại Hà Nội có mưa không?"
        
    print(f"\n[USER]: {user_prompt}\n")
    print("Executing Pipeline... (This may take roughly 10-15s based on 10 nodes)\n")
    
    # 4. Trigger state machine
    try:
        result = await manager.run_pipeline(
            task_id="demo-test",
            user_prompt=user_prompt,
            history=[]
        )
    except Exception as e:
        print(f"PIPELINE CRASHED: {e}")
        return

    print("=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    print(f"FINAL STATE   : {result.get('current_phase')}")
    print(f"JUMPS (HOPS)  : {len(result.get('debug_trace', []))}")
    print("\n--- STATE TRACE ---")
    for tr in result.get('debug_trace', []):
        print(f"  {tr}")
        
    print("\n--- RAW SKILL RUNNER DICT ---")
    print(result.get('skill_outputs', {}))
        
    print("\n--- RAW SYNTHESIS DICT ---")
    print(result.get('synthesis_output', {}))
    
    print("\n--- FINAL AGENT REPLY ---")
    reply = result.get('synthesis_output', {}).get('reply', 'No reply generated.')
    print(reply)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_pipeline())
