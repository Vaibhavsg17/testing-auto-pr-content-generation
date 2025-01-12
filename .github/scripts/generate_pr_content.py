import os
import json
import requests
import subprocess

def call_api(url, headers, payload):
    """Helper function to make the API request."""
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )
    return response.json()

def generate_summary(api_provider, api_key, engine_url, prompt):
    """Generates a PR summary using OpenAI or Gemini API."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if api_provider == "openai":
        payload = {
            "model": "gpt-3.5-turbo",  # Change to a valid model
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
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
    """Fetches the git diff between the current and previous commit."""
    try:
        # Fetch the diff between the latest commit and its parent
        diff = subprocess.check_output(["git", "diff", "HEAD^", "HEAD"], text=True)
    except subprocess.CalledProcessError:
        # Handle case where there is no previous commit
        diff = subprocess.check_output(
            ["git", "diff", "HEAD"], text=True
        )  # Compare against the current commit
    return diff

def main():
    # Get the git diff of the changes
    diff = get_git_diff()
    prompt = f"Summarize the following code changes in a detailed and formatted manner:\n{diff}"

    # Read the api_provider from environment variable (set in GitHub Actions)
    api_provider = os.getenv("API_PROVIDER", "openai").lower()

    # Handle OpenAI case
    if api_provider == "openai":
        engine_url = "https://api.openai.com/v1/completions"
        api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set as a GitHub secret
        if not api_key:
            raise ValueError("OpenAI API key is missing!")

        summary = generate_summary(api_provider, api_key, engine_url, prompt)["choices"][0]["text"]
    
    # Handle Gemini case
    elif api_provider == "gemini":
        # Directly use the Gemini Code Review Action, no need for API call
        summary = "Generated using Gemini AI: (Action handles the generation directly)"
    
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")

    # Format the generated content for the PR
    formatted_content = f"## {api_provider.capitalize()} Summary\n{summary}\n\n## Further details to be added as required."

    # Output the generated PR content to GitHub Actions output
    print(f"pr_content={formatted_content}")

if __name__ == "__main__":
    main()
