import json
import os
import base64

import google.generativeai as genai
import requests
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

app = Flask(__name__)

# Log the remote IP address for every request
@app.before_request
def log_remote_addr():
    # Prefer X-Forwarded-For for public deployments behind proxy, else remote_addr
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    app.logger.info(f"[REQUEST] {request.method} {request.path} from IP: {ip}")


# --- Gemini configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
else:
    gemini_model = None


# --- OpenAI configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
OPENAI_MODELS = {
    "openai-mini": "gpt-4o-mini",
    "openai": "gpt-4o",
    "openai-5-nano": "gpt-5-nano"  # User confirmed this works
}
# Available OpenAI models:
# - gpt-4o-mini (cost-effective, fast, uses max_tokens)
# - gpt-4o (most capable, higher limits, uses max_completion_tokens)
# - gpt-5-nano (user-tested, available, uses max_completion_tokens)


# --- OpenRouter configuration ---
# Uses OpenRouter API for accessing DeepSeek
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
# Model mappings for OpenRouter models
OPENROUTER_MODELS = {
    "deepseek": os.getenv("OPENROUTER_DEEPSEEK_MODEL", "nex-agi/deepseek-v3.1-nex-n1:free"),
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/version")
def version():
    """
    Simple health/status endpoint.
    Adjust the payload as needed for your service.
    """
    return jsonify(
        {
            "service": "servertest1",
            "status": "ok",
            "version": "1.2.0",
        }
    )


def _reply_from_gemini(message: str) -> str:
    if not gemini_model:
        raise RuntimeError(
            "Gemini API key is not configured. Set GEMINI_API_KEY in your environment."
        )
    response = gemini_model.generate_content(message)
    reply_text = getattr(response, "text", "").strip()
    return reply_text or "I couldn't generate a response."


def _reply_from_openai(message: str, model_key: str = "openai-mini", image_base64: str = None) -> str:
    if not openai_client:
        raise RuntimeError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in your environment."
        )

    if model_key not in OPENAI_MODELS:
        raise RuntimeError(
            f"Unknown OpenAI model key: {model_key}. Supported keys: {list(OPENAI_MODELS.keys())}"
        )

    try:
        # System prompt for consistent formatting across all OpenAI models
        system_prompt = """You are a helpful AI assistant with expertise in mathematics and science.

Formatting Rules:
- Use Markdown for lists, tables, and styling.
- Use ```code fences``` for all code blocks.
- Format file names, paths, and function names with `inline code` backticks.
- **For all mathematical expressions, you must use LaTeX with dollar-sign delimiters.**
- Use $...$ for inline math expressions (simple fractions, variables, etc.)
- Use $$...$$ for block/display math (complex equations, integrals, matrices, etc.)
- **Never use bare LaTeX without delimiters** - always wrap in $ or $$
- For integrals, derivatives, sums, products, and complex expressions, use display math $$...$$
- Examples: $\\frac{1}{2}$, $$\\int_{-1}^{1} f(x) dx$$, $$\\sum_{n=1}^{\\infty} \\frac{1}{n^2}$$

Be precise and provide step-by-step solutions when solving mathematical problems."""

        messages = [{"role": "system", "content": system_prompt}]

        if image_base64:
            # Extract base64 data from data URL (remove "data:image/png;base64," prefix)
            if image_base64.startswith("data:image/"):
                image_data = image_base64.split(",", 1)[1]
            else:
                image_data = image_base64

            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": message or "Solve this mathematical problem and show your work with proper LaTeX formatting"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": message})

        # Use appropriate parameters based on model
        model_name = OPENAI_MODELS[model_key]
        if model_name == "gpt-4o" or model_name == "gpt-5-nano":
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_completion_tokens=2000  # For gpt-4o and gpt-5-nano
            )
        else:  # gpt-4o-mini
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=2000  # For gpt-4o-mini
            )

        reply_text = response.choices[0].message.content.strip()
        return reply_text or "I couldn't generate a response."
    except Exception as exc:
        raise RuntimeError(f"Error calling OpenAI API: {exc}")


def _reply_from_openrouter(message: str, model_key: str) -> str:
    """
    Generic function to call OpenRouter API with any supported model.

    Args:
        message: User message
        model_key: Key from OPENROUTER_MODELS dict (e.g., "deepseek")

    Returns:
        Model response text
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OpenRouter API key is not configured. Set OPENROUTER_API_KEY in your environment."
        )

    if model_key not in OPENROUTER_MODELS:
        raise RuntimeError(
            f"Unknown OpenRouter model key: {model_key}. Supported keys: {list(OPENROUTER_MODELS.keys())}"
        )

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        }

        # Standard format for models
        data = {
            "model": OPENROUTER_MODELS[model_key],
            "messages": [{"role": "user", "content": message}],
        }

        response = requests.post(
            url=OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        # Extract response text (OpenRouter uses standard OpenAI format)
        if "choices" in result and len(result["choices"]) > 0:
            reply_text = result["choices"][0]["message"]["content"].strip()
        elif "output" in result:
            # Fallback for different response formats
            if isinstance(result["output"], list) and len(result["output"]) > 0:
                reply_text = result["output"][0].get("content", "").strip()
            else:
                reply_text = str(result["output"]).strip()
        else:
            # Last resort: try to find content in response
            reply_text = str(result).strip()

        return reply_text or "I couldn't generate a response."
    except requests.exceptions.HTTPError as exc:
        # Better error messages for HTTP errors
        error_detail = ""
        try:
            error_response = exc.response.json()
            error_detail = f" - {error_response}"
        except:
            error_detail = f" - {exc.response.text[:200]}"
        raise RuntimeError(f"Error calling OpenRouter API: {exc}{error_detail}")
    except Exception as exc:
        raise RuntimeError(f"Error calling OpenRouter API: {exc}")


@app.post("/api/chat")
def chat():
    """
    Simple chat endpoint for the front-end.
    Expects JSON: {
        "message": "<user message>",
        "provider": "gemini" | "openai-mini" | "openai" | "deepseek",
        "image": "<base64_image_data_url>" (optional, only for openai models)
    }
    Returns: {"reply": "<LLM response>"} or {"error": "..."}.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    provider = (data.get("provider") or "gemini").lower()
    image_base64 = data.get("image")  # Optional base64 image data URL

    # For OpenAI models, allow image-only requests (no text message required)
    if provider not in ["openai-mini", "openai"] and not message:
        return jsonify({"error": "Message is required."}), 400
    # For OpenAI models, require either message or image
    if provider in ["openai-mini", "openai"] and not message and not image_base64:
        return jsonify({"error": "Message or image is required for OpenAI."}), 400

    try:
        if provider in ["openai-mini", "openai"]:
            reply = _reply_from_openai(message, provider, image_base64)
        elif provider == "deepseek":
            reply = _reply_from_openrouter(message, "deepseek")
        else:  # default to Gemini
            reply = _reply_from_gemini(message)

        return jsonify({"reply": reply})
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    # Run on port 8080, listening on all interfaces
    app.run(host="0.0.0.0", port=8080)


