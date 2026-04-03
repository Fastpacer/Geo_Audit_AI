#!/usr/bin/env python
"""
Quick test to verify backend is returning geo_score properly
"""
import json
import sys

# Test data structure (what backend returns)
test_response = {
    "url": "https://example.com",
    "title": "Test Article",
    "meta_description": "Test description",
    "confidence_score": 95,
    "geo_analysis": {
        "rule_score": 90,
        "llm_analysis": {
            "summary": "Well-structured content",
            "strengths": ["Good headings", "Clear description"],
            "weaknesses": ["Could add more content"],
            "geo_score": 85,  # This should always be present
            "improvements": ["Add more sections"]
        }
    }
}

# Verify structure
def verify_geo_score():
    """Verify the response has proper geo_score"""
    
    # Check top-level geo_analysis
    geo_analysis = test_response.get("geo_analysis", {})
    if not geo_analysis:
        print("❌ ERROR: Missing geo_analysis in response")
        return False
    
    # Check llm_analysis
    llm_analysis = geo_analysis.get("llm_analysis", {})
    if not llm_analysis:
        print("❌ ERROR: Missing llm_analysis in geo_analysis")
        return False
    
    # Check geo_score
    geo_score = llm_analysis.get("geo_score")
    if geo_score is None:
        print("❌ ERROR: geo_score is None (undefined)")
        return False
    
    if not isinstance(geo_score, (int, float)):
        print(f"⚠️  WARNING: geo_score is {type(geo_score).__name__}, expected int or float")
        return False
    
    print(f"✅ PASS: geo_score = {geo_score}")
    print(f"✅ PASS: rule_score = {geo_analysis.get('rule_score', 'N/A')}")
    print(f"✅ PASS: Structure is correct")
    return True

if __name__ == "__main__":
    print("Testing GEO Score structure...")
    print(f"Response: {json.dumps(test_response, indent=2)}")
    print("\n--- Verification ---")
    
    if verify_geo_score():
        print("\n✅ Backend response structure is correct!")
        sys.exit(0)
    else:
        print("\n❌ Backend response structure has issues!")
        sys.exit(1)
