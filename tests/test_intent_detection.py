import asyncio
from unittest.mock import MagicMock
from app.api.v1.endpoints.agents import _detect_intent

def test_intent_detection():
    # Mock LLM Client
    mock_llm = MagicMock()
    
    # Test 1: Simple Question
    mock_llm.generate.return_value = '{"wants_skill": false, "wants_search": false, "wants_report": false}'
    res1 = _detect_intent(mock_llm, "chào bạn")
    assert res1["wants_skill"] is False
    assert res1["wants_search"] is False
    
    # Test 2: Search Request
    mock_llm.generate.return_value = '{"wants_skill": false, "wants_search": true, "wants_report": false}'
    res2 = _detect_intent(mock_llm, "giá xăng dầu hôm nay")
    assert res2["wants_skill"] is False
    assert res2["wants_search"] is True
    
    # Test 3: Skill Request
    mock_llm.generate.return_value = '{"wants_skill": true, "wants_search": false, "wants_report": true}'
    res3 = _detect_intent(mock_llm, "phân tích dữ liệu doanh nghiệp và tạo báo cáo")
    # Test 4: Chart Request
    mock_llm.generate.return_value = '{"wants_skill": true, "wants_search": true, "wants_image": true, "wants_report": false}'
    res4 = _detect_intent(mock_llm, "vẽ biểu đồ doanh thu vinfast năm 2025")
    assert res4["wants_skill"] is True
    assert res4["wants_image"] is True
    
    print("All Intent Detection tests passed!")

if __name__ == "__main__":
    test_intent_detection()
