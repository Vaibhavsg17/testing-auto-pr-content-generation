import os
import json
import requests
import subprocess

def call_api(url, headers, payload):
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    return response.json()

def generate_summary(api_provider, api_key, engine_url, prompt):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if api_provider == "openai":
        payload = {
            "model": "code-davinci-002",
            "prompt": prompt,
            "max_tokens": 150,
            "temperature": 0.7,
        }
    elif api_provider == "gemini":
        payload = {
            "model": "gemini-1.5-pro-latest",
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.7,
        }
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")

    return call_api(engine_url, headers, payload)

def get_git_diff():
    try:
        # Fetch the diff between the latest commit and its parent
        diff = subprocess.check_output(["git", "diff", "HEAD^", "HEAD"], text=True)
    except subprocess.CalledProcessError:
        # Handle case where there is no previous commit
        diff = subprocess.check_output(["git", "diff", "HEAD"], text=True)  # Compare against the current commit
    return diff

def main():
    diff = get_git_diff()
    prompt = f"Summarize the following code changes in a detailed and formatted manner:\n{diff}"

    api_provider = os.getenv("API_PROVIDER", "openai").lower()
    if api_provider == "openai":
        engine_url = "https://api.openai.com/v1/completions"
        api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set as a GitHub secret
        if not api_key:
            raise ValueError("OpenAI API key is missing!")
    elif api_provider == "gemini":
        # Directly use the Gemini Code Review Action, no need for API call
        engine_url = None  # Gemini API key will be passed through GitHub Action
        api_key = os.getenv("GEMINI_API_KEY")  # Securely get Gemini API key
        if not api_key:
            raise ValueError("Gemini API key is missing!")
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")

    if api_provider == "openai":
        summary = generate_summary(api_provider, api_key, engine_url, prompt)["choices"][0]["text"]
    elif api_provider == "gemini":
        summary = "Generated using Gemini AI: (Action handles the generation directly)"
        # Here, you would trigger the GitHub Action for Gemini using its pre-configured steps

    formatted_content = f"## {api_provider.capitalize()} Summary\n{summary}\n\n## Further details to be added as required."
    print(f"::set-output name=pr_content::{json.dumps(formatted_content)}")

if __name__ == "__main__":
    main()
