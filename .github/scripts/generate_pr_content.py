import os
import json
import requests
import subprocess


def call_api(url, headers, payload):
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )
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
        diff = subprocess.check_output(["git", "diff", "HEAD^", "HEAD"], text=True)
    except subprocess.CalledProcessError:
        diff = "No previous commit to compare."
    return diff


def main():
    diff = get_git_diff()
    prompt = f"Summarize the following code changes in a detailed and formatted manner:\n{diff}"

    api_provider = os.getenv("API_PROVIDER", "openai").lower()
    if api_provider == "openai":
        engine_url = "https://api.openai.com/v1/completions"
        api_key = os.getenv("OPENAI_API_KEY")
    elif api_provider == "gemini":
        engine_url = "https://gemini.api.endpoint/v1/completions"
        api_key = os.getenv("GEMINI_API_KEY")
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")

    summary = generate_summary(api_provider, api_key, engine_url, prompt)["choices"][0][
        "text"
    ]

    formatted_content = f"## {api_provider.capitalize()} Summary\n{summary}\n\n## Further details to be added as required."
    print(f"::set-output name=pr_content::{json.dumps(formatted_content)}")


if __name__ == "__main__":
    main()
