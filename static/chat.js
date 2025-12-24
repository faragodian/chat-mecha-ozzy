// Test if JavaScript is loading
console.log("🚀 JavaScript loaded successfully!");

// Global variables - will be set when DOM is ready
let chatLog, chatInput, sendBtn, statusText, modelSelect, imageInput, imageInputContainer, imagePreview;
let loadingIndicator = null;
let currentImageBase64 = null;

function showLoadingIndicator(providerLabel) {
  if (loadingIndicator) loadingIndicator.remove();
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.id = "loading-indicator-row";
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.textContent = providerLabel || "Assistant";
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "loading-indicator";
  loadingDiv.innerHTML = `
    <span>Processing</span>
    <span class="loading-dots">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
    </span>`;
  bubble.appendChild(meta);
  bubble.appendChild(loadingDiv);
  row.appendChild(bubble);
  chatLog.appendChild(row);
  chatLog.scrollTop = chatLog.scrollHeight;
  loadingIndicator = row;
}

function hideLoadingIndicator() {
  if (loadingIndicator) {
    loadingIndicator.remove();
    loadingIndicator = null;
  }
}

function appendMessage(role, text, isError = false, labelOverride = "", provider = "") {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  if (isError) bubble.classList.add("error");
  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.textContent = (role === "user") ? "You" : (labelOverride || "Assistant");
  const body = document.createElement("div");
  if (role === "assistant" && !isError && typeof marked !== "undefined") {
    body.className = "markdown-content";
    marked.setOptions({ breaks: true, gfm: true });

    // Pre-process text to wrap LaTeX expressions in MathJax delimiters for OpenAI
    let processedText = text;
    // Pre-process text to wrap LaTeX expressions in MathJax delimiters for OpenAI
    if (provider === "openai" || provider === "openai-mini") {
      // First: Clean up existing $$ blocks that contain malformed multiline LaTeX
      processedText = processedText.replace(/\$\$\s*\n\s*((?:.|\n)*?)\s*\n\s*\$\$/g, (match, content) => {
        // Clean up the content inside $$ blocks
        let cleanContent = content
          // Remove excessive whitespace and normalize line breaks
          .replace(/\s*\n\s*\n\s*/g, '\n')  // Multiple newlines to single
          .replace(/\n\s*∫\s*\n/g, ' ∫ ')  // Fix separated integral signs
          .replace(/\n\s*\\int\s*\n/g, ' \\int ')  // Fix separated \int commands
          // Clean up spacing around integrals
          .replace(/∫\s*\n\s*_\{([^}]+)\}\s*\n\s*\^\{([^}]+)\}/g, '∫_{$1}^{$2}')
          .replace(/\\int\s*\n\s*_\{([^}]+)\}\s*\n\s*\^\{([^}]+)\}/g, '\\int_{$1}^{$2}')
          .trim();

        return '\n$$\n' + cleanContent + '\n$$\n';
      });

      // Second: Handle bracketed LaTeX expressions that span multiple lines
      processedText = processedText.replace(/\[\s*\n\s*((?:.|\n)*?)\s*\n\s*\]/g, (match, latexContent) => {
        // Clean up the LaTeX content and wrap in display math
        const cleanLatex = latexContent.trim();
        return '\n$$\n' + cleanLatex + '\n$$\n';
      });

      // Third: Handle bracketed expressions that might not have newlines but contain LaTeX
      processedText = processedText.replace(/\[\s*((?:[^\[\]]|\[[^\]]*\])*?)\s*\]/g, (match, content) => {
        // If the content contains LaTeX commands, wrap in display math
        if (content.match(/\\[a-zA-Z]/)) {
          return '\n$$\n' + content.trim() + '\n$$\n';
        }
        return match; // Leave non-LaTeX brackets alone
      });

      // Fourth: Handle any remaining individual LaTeX expressions
      const latexPattern = /\\(?:frac|sum|int|lim|prod|sqrt|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|tau|phi|omega|partial|nabla|times|div|grad|cdot|cap|cup|subset|supset|subseteq|supseteq|in|notin|forall|exists|equiv|approx|neq|leq|geq|pm|mp|oplus|otimes|perp|parallel|angle|degree|therefore|because|triangle|square|diamond|clubsuit|heartsuit|spadesuit|cdots|vdots|ddots)\\{[^}]*\\}*|\\[a-zA-Z]+(?:\[[^\]]*\])*(?:\{[^}]*\})*/g;

      processedText = processedText.replace(latexPattern, (match) => {
        // If already wrapped in math delimiters, leave as is
        if (match.startsWith('$') && match.endsWith('$')) return match;
        if (match.startsWith('\\(') && match.endsWith('\\)')) return match;
        if (match.startsWith('\\[') && match.endsWith('\\]')) return match;

        // Check if it's a display math expression
        const displayMathIndicators = ['\\frac', '\\int', '\\sum', '\\prod', '\\lim', '\\sqrt'];
        const isDisplayMath = displayMathIndicators.some(indicator => match.includes(indicator)) ||
                             match.length > 30;

        return isDisplayMath ? '\n$$\n' + match + '\n$$\n' : '$' + match + '$';
      });
    }

    body.innerHTML = marked.parse(processedText);
    if (window.MathJax && window.MathJax.typesetPromise) {
      setTimeout(() => {
        MathJax.typesetPromise([body]).catch((err) => {
          console.error("MathJax rendering error:", err);
        });
      }, 0);
    }
  } else {
    body.textContent = text;
  }
  bubble.appendChild(meta);
  bubble.appendChild(body);
  row.appendChild(bubble);
  chatLog.appendChild(row);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function updateImageInputVisibility() {
  if (modelSelect.value === "openai" || modelSelect.value === "openai-mini" || modelSelect.value === "openai-5-nano") {
    imageInputContainer.classList.add("visible");
  } else {
    imageInputContainer.classList.remove("visible");
    clearImage();
  }
}

function imageToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (result && result.startsWith("data:image/")) {
        resolve(result);
      } else {
        reject(new Error("Invalid image format"));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}


function showImagePreview(file) {
  const img = document.createElement("img");
  img.src = currentImageBase64;
  img.alt = "Preview";
  const removeBtn = document.createElement("button");
  removeBtn.textContent = "✕ Remove";
  removeBtn.onclick = clearImage;
  imagePreview.innerHTML = "";
  imagePreview.appendChild(img);
  imagePreview.appendChild(removeBtn);
}

function clearImage() {
  currentImageBase64 = null;
  imageInput.value = "";
  imagePreview.innerHTML = "";
}

async function sendMessage() {
  const message = chatInput.value.trim();
  const provider = modelSelect.value;
  if (provider === "openai" || provider === "openai-mini" || provider === "openai-5-nano") {
    if (!message && !currentImageBase64) {
      alert("Please enter a message or select an image for OpenAI.");
      return;
    }
  } else {
    if (!message) return;
  }
  let providerLabel;
  if (provider === "openai") {
    providerLabel = "OpenAI (GPT-4o)";
  } else if (provider === "openai-mini") {
    providerLabel = "OpenAI (GPT-4o-mini)";
  } else if (provider === "openai-5-nano") {
    providerLabel = "OpenAI (GPT-5-nano)";
  } else if (provider === "deepseek") {
    providerLabel = "DeepSeek";
  } else {
    providerLabel = "Gemini";
  }
  const userMessage = message || (currentImageBase64 ? "[Image]" : "");
  appendMessage("user", userMessage, false, "", provider);
  chatInput.value = "";
  chatInput.focus();
  sendBtn.disabled = true;
  statusText.textContent = "Processing…";
  showLoadingIndicator(providerLabel);
  try {
    const requestBody = { message: message || "", provider: provider };
    if ((provider === "openai" || provider === "openai-mini" || provider === "openai-5-nano") && currentImageBase64) {
      if (!currentImageBase64.startsWith("data:image/")) {
        alert("Error: Image format is invalid. Please select the image again.");
        hideLoadingIndicator();
        sendBtn.disabled = false;
        statusText.textContent = "Ready";
        return;
      }
      requestBody.image = currentImageBase64;
    }
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    const payload = await res.json();
    hideLoadingIndicator();
    if (!res.ok || payload.error) {
      appendMessage(
        "assistant",
        payload.error || "There was an error contacting the model.",
        true,
        providerLabel,
        provider
      );
    } else {
      appendMessage(
        "assistant",
        payload.reply || "[empty response]",
        false,
        providerLabel,
        provider
      );
    }
  } catch (err) {
    hideLoadingIndicator();
    appendMessage(
      "assistant",
      "Network error talking to /api/chat: " + err,
      true,
      "",
      provider
    );
  } finally {
    sendBtn.disabled = false;
    statusText.textContent = "Ready";
    // Optionally: clearImage();
  }
}
// Simple approach: wait for DOM to be ready, then initialize everything
setTimeout(() => {
  // Initialize DOM element references
  chatLog = document.getElementById("chat-log");
  chatInput = document.getElementById("chat-input");
  sendBtn = document.getElementById("send-btn");
  statusText = document.getElementById("status-text");
  modelSelect = document.getElementById("model-select");
  imageInput = document.getElementById("image-input");
  imageInputContainer = document.getElementById("image-input-container");
  imagePreview = document.getElementById("image-preview");

  if (chatInput && sendBtn) {
    // Attach event listeners
    sendBtn.addEventListener("click", sendMessage);

    chatInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        ev.stopPropagation();
        sendMessage();
        return false;
      }
    });

    // Initialize image input visibility
    if (modelSelect) {
      modelSelect.addEventListener("change", updateImageInputVisibility);
      updateImageInputVisibility();
    }

    // Attach image input event listener
    if (imageInput) {
      imageInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (!file.type.startsWith("image/")) {
          alert("Please select an image file.");
          return;
        }
        try {
          currentImageBase64 = await imageToBase64(file);
          showImagePreview(file);
        } catch (err) {
          console.error("Error reading image:", err);
          alert("Error reading image file.");
        }
      });
    }
  }
}, 500); // Wait 500ms for DOM to be fully ready
