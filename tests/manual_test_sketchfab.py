"""
Manual test script for Sketchfab API preview functionality.
Run this script directly to test the API integration.

Usage:
    python tests/manual_test_sketchfab.py
"""

import requests
import base64
import os

# Test API key (should be passed via environment variable in production)
API_KEY = os.environ.get("SKETCHFAB_API_KEY", "0dc102fa15fc42659c2351bcde8c905f")


def test_api_authentication():
    """Test if the API key is valid"""
    print("=" * 50)
    print("Test 1: API Authentication")
    print("=" * 50)
    
    headers = {"Authorization": f"Token {API_KEY}"}
    response = requests.get(
        "https://api.sketchfab.com/v3/me",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Authentication successful!")
        print(f"   Username: {user_data.get('username', 'Unknown')}")
        print(f"   Display name: {user_data.get('displayName', 'Unknown')}")
        return True
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_search_models():
    """Test searching for models"""
    print("\n" + "=" * 50)
    print("Test 2: Search Models")
    print("=" * 50)
    
    headers = {"Authorization": f"Token {API_KEY}"}
    params = {
        "type": "models",
        "q": "chair",
        "count": 3,
        "downloadable": True
    }
    
    response = requests.get(
        "https://api.sketchfab.com/v3/search",
        headers=headers,
        params=params,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"✅ Search successful! Found {len(results)} models")
        
        for i, model in enumerate(results[:3]):
            print(f"\n   Model {i+1}:")
            print(f"   - Name: {model.get('name', 'Unknown')}")
            print(f"   - UID: {model.get('uid', 'Unknown')}")
            print(f"   - Author: {model.get('user', {}).get('username', 'Unknown')}")
            print(f"   - Downloadable: {model.get('isDownloadable', False)}")
        
        return results[0].get("uid") if results else None
    else:
        print(f"❌ Search failed: {response.status_code}")
        return None


def test_get_model_preview(uid):
    """Test getting model preview/thumbnail"""
    print("\n" + "=" * 50)
    print(f"Test 3: Get Model Preview (UID: {uid})")
    print("=" * 50)
    
    headers = {"Authorization": f"Token {API_KEY}"}
    
    # Get model info
    response = requests.get(
        f"https://api.sketchfab.com/v3/models/{uid}",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get model info: {response.status_code}")
        return False
    
    data = response.json()
    thumbnails = data.get("thumbnails", {}).get("images", [])
    
    if not thumbnails:
        print("❌ No thumbnails available")
        return False
    
    print(f"✅ Found {len(thumbnails)} thumbnails:")
    for thumb in thumbnails:
        print(f"   - {thumb.get('width', '?')}x{thumb.get('height', '?')}: {thumb.get('url', 'No URL')[:50]}...")
    
    # Select medium-sized thumbnail (400-800px)
    selected = None
    for thumb in thumbnails:
        width = thumb.get("width", 0)
        if 400 <= width <= 800:
            selected = thumb
            break
    if not selected:
        selected = thumbnails[0]
    
    print(f"\n   Selected thumbnail: {selected.get('width')}x{selected.get('height')}")
    
    # Download thumbnail
    img_response = requests.get(selected.get("url"), timeout=30)
    if img_response.status_code == 200:
        image_data = img_response.content
        base64_data = base64.b64encode(image_data).decode('ascii')
        
        print(f"✅ Thumbnail downloaded successfully!")
        print(f"   - Size: {len(image_data)} bytes")
        print(f"   - Base64 length: {len(base64_data)} chars")
        print(f"   - Content-Type: {img_response.headers.get('Content-Type', 'Unknown')}")
        
        # Save thumbnail for visual verification
        test_output_path = "tests/test_thumbnail.jpg"
        with open(test_output_path, "wb") as f:
            f.write(image_data)
        print(f"   - Saved to: {test_output_path}")
        
        return True
    else:
        print(f"❌ Failed to download thumbnail: {img_response.status_code}")
        return False


def main():
    print("\n" + "=" * 50)
    print("Sketchfab API Preview Feature Test")
    print("=" * 50 + "\n")
    
    # Test 1: Authentication
    if not test_api_authentication():
        print("\n⚠️ Stopping tests due to authentication failure")
        return
    
    # Test 2: Search
    uid = test_search_models()
    if not uid:
        print("\n⚠️ Stopping tests due to search failure")
        return
    
    # Test 3: Preview
    test_get_model_preview(uid)
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()

