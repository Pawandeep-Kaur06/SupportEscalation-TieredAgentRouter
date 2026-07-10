import os


class _UnavailableModels:
    def __init__(self, reason):
        self.reason = reason

    def generate_content(self, *args, **kwargs):
        raise RuntimeError(self.reason)


class _UnavailableGeminiClient:
    def __init__(self, reason):
        self.models = _UnavailableModels(reason)


class _GenerativeAiModels:
    def __init__(self, generativeai):
        self.generativeai = generativeai

    def generate_content(self, model, contents):
        model_client = self.generativeai.GenerativeModel(model)
        return model_client.generate_content(contents)


class _GenerativeAiClient:
    def __init__(self, generativeai):
        self.models = _GenerativeAiModels(generativeai)


try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    client = _UnavailableGeminiClient("GEMINI_API_KEY is not configured.")
else:
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
    except ImportError:
        try:
            import google.generativeai as generativeai

            generativeai.configure(api_key=api_key)
            client = _GenerativeAiClient(generativeai)
        except ImportError:
            client = _UnavailableGeminiClient(
                "Neither google-genai nor google-generativeai is installed."
            )
