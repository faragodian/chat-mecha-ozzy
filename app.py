import json
import os

import google.generativeai as genai
import requests
from flask import Flask, jsonify, render_template, request
from xai_sdk import Client
from xai_sdk.chat import user

app = Flask(__name__)


# --- Gemini configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
else:
    gemini_model = None


# --- Grok (xAI) configuration ---
# See https://console.x.ai for API keys.
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4")
# Initialize xAI client if API key is available
xai_client = Client(api_key=GROK_API_KEY) if GROK_API_KEY else None


# --- OpenRouter configuration ---
# Uses OpenRouter API for accessing various models (DeepSeek, Amazon Nova, etc.)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
# Model mappings for OpenRouter models
OPENROUTER_MODELS = {
    "deepseek": os.getenv("OPENROUTER_DEEPSEEK_MODEL", "nex-agi/deepseek-v3.1-nex-n1:free"),
    "amazon-nova": os.getenv("OPENROUTER_AMAZON_NOVA_MODEL", "amazon/nova-2-lite-v1:free"),
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
            "version": "1.0.0",
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


def _reply_from_grok(message: str) -> str:
    if not xai_client:
        raise RuntimeError(
            "Grok API key is not configured. Set GROK_API_KEY in your environment."
        )

    try:
        # Create a chat session with Grok using xAI SDK
        chat = xai_client.chat.create(model=GROK_MODEL)
        chat.append(user(message))
        response = chat.sample()
        reply_text = response.content.strip()
        return reply_text or "I couldn't generate a response."
    except Exception as exc:
        raise RuntimeError(f"Error calling Grok API: {exc}")


def _reply_from_openrouter(message: str, model_key: str, image_base64: str = None) -> str:
    """
    Generic function to call OpenRouter API with any supported model.
    
    Args:
        message: User message
        model_key: Key from OPENROUTER_MODELS dict (e.g., "deepseek", "amazon-nova")
        image_base64: Optional base64-encoded image (data URL format: "data:image/png;base64,...")
    
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
        
        # Build request data
        if model_key == "amazon-nova":
            # Amazon Nova format with special content structure for images
            system_message = {
                "role": "system",
                "content": "You are Nova 2 Lite (free), a large language model from amazon.\n\nFormatting Rules:\n- Use Markdown for lists, tables, and styling.\n- Use ```code fences``` for all code blocks.\n- Format file names, paths, and function names with `inline code` backticks.\n- **For all mathematical expressions, you must use dollar-sign delimiters. Use $...$ for inline math and $$...$$ for block math. Do not use (...) or [...] delimiters.**"
            }
            
            if image_base64:
                # Amazon Nova with image support
                # Verify image_base64 is a valid data URL
                if not image_base64.startswith("data:image/"):
                    raise ValueError("Image must be in data URL format (data:image/...)")
                
                # Amazon Nova requires at least one non-empty text message
                # Use provided message or a default prompt if none provided
                text_content = message.strip() if message and message.strip() else "What do you see in this image?"
                
                # Use OpenRouter's standard format for multimodal content
                # According to OpenRouter docs: ContentPart[] with type 'text' and 'image_url'
                user_content = [
                    {
                        "type": "text",
                        "text": text_content
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64
                        }
                    }
                ]
                
                messages_array = [
                    system_message,
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            else:
                # Amazon Nova text-only
                messages_array = [
                    system_message,
                    {"role": "user", "content": message}
                ]
            
            data = {
                "model": OPENROUTER_MODELS[model_key],
                "messages": messages_array,
            }
        else:
            # Standard format for other models
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
        "provider": "gemini" | "grok" | "deepseek" | "amazon-nova",
        "image": "<base64_image_data_url>" (optional, only for amazon-nova)
    }
    Returns: {"reply": "<LLM response>"} or {"error": "..."}.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    provider = (data.get("provider") or "gemini").lower()
    image_base64 = data.get("image")  # Optional base64 image data URL

    # For Amazon Nova, allow image-only requests (no text message required)
    if provider != "amazon-nova" and not message:
        return jsonify({"error": "Message is required."}), 400
    # For Amazon Nova, require either message or image
    if provider == "amazon-nova" and not message and not image_base64:
        return jsonify({"error": "Message or image is required for Amazon Nova."}), 400

    try:
        if provider == "grok":
            reply = _reply_from_grok(message)
        elif provider == "deepseek":
            reply = _reply_from_openrouter(message, "deepseek")
        elif provider == "amazon-nova":
            reply = _reply_from_openrouter(message or "", "amazon-nova", image_base64)
        else:  # default to Gemini
            reply = _reply_from_gemini(message)

        return jsonify({"reply": reply})
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    # Run on port 8080, listening on all interfaces
    app.run(host="0.0.0.0", port=8080)


