import os
import modal

app = modal.App("diagnostic")

@app.function(
    image=modal.Image.debian_slim().pip_install("google-generativeai"),
    secrets=[modal.Secret.from_name("footin-secrets")]
)
def list_gemini_models():
    import google.generativeai as genai
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY') or os.environ.get('MODEL_API_KEY')
    print(f"Using API Key (first 4): {api_key[:4] if api_key else 'None'}")
    if not api_key:
        return "No API key found"
    
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models()]
        return models
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    with app.run():
        print(list_gemini_models.remote())
