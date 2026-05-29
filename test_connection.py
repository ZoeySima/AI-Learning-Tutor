"""Quick test script to verify API key works."""
import os
import sys

def test_connection():
    """Test if API key is configured and Claude API is accessible."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set it first:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        sys.exit(1)

    print(f"✓ API Key found: {api_key[:15]}...")

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        print("\n📡 Testing API connection...")
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello! API works!' in Chinese."}
            ],
        )

        print(f"✓ Response: {response.content[0].text}")
        print(f"✓ Model used: {response.model}")
        print(f"✓ Tokens: input={response.usage.input_tokens}, output={response.usage.output_tokens}")
        print("\n🎉 All good! You can now run 'ai-tutor start' to begin learning.")

    except Exception as e:
        print(f"\n❌ API call failed: {e}")
        print("\nCommon issues:")
        print("  1. Invalid API key - get one from https://console.anthropic.com/")
        print("  2. Insufficient credits - add billing at https://console.anthropic.com/settings/billing")
        print("  3. Network issue - check your internet/proxy")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
