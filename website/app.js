const form = document.querySelector("#leadForm");
const formResult = document.querySelector("#formResult");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = Object.fromEntries(new FormData(form));
  formResult.className = "rounded-xl bg-teal-50 p-4 text-sm whitespace-pre-line";
  formResult.textContent = "Submitting...";
  formResult.classList.remove("hidden");

  try {
    const response = await fetch("/api/leads", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to submit your inquiry.");
    formResult.textContent = `Inquiry received.\n${data.lead.summary}${data.lead.humanFollowup ? "\nHuman coordinator review has been requested." : ""}${data.sheetsSync === "failed" ? "\nSaved locally, but Google Sheets sync failed. Admissions can still see your inquiry." : ""}`;
    form.reset();
  } catch (error) {
    formResult.className = "rounded-xl bg-red-50 p-4 text-sm text-red-700 whitespace-pre-line";
    formResult.textContent = error.message || "Unable to submit your inquiry. Please try again.";
  }
});

const panel = document.querySelector("#chatPanel");
const chatToggle = document.querySelector("#chatToggle");

function stopVoice() {
  if (activeRecognition) {
    try {
      activeRecognition.stop();
    } catch {
      // Recognition may already have ended.
    }
    activeRecognition = null;
    recognitionActive = false;
  }
  waveform.classList.remove("listening");
  micButton.setAttribute("aria-pressed", "false");
  if (window.speechSynthesis) window.speechSynthesis.cancel();
}

function closeChat() {
  stopVoice();
  panel.classList.remove("chat-open");
  chatToggle.setAttribute("aria-label", "Open chat");
}

chatToggle.onclick = () => {
  if (panel.classList.contains("chat-open")) closeChat();
  else {
    panel.classList.add("chat-open");
    chatToggle.setAttribute("aria-label", "Close chat");
  }
};
document.querySelector("#chatClose").onclick = closeChat;

function appendMessage(text, className) {
  const message = document.createElement("p");
  message.className = className;
  message.textContent = text;
  const messages = document.querySelector("#messages");
  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
  return message;
}

async function askAssistant(message) {
  appendMessage(message, "ml-8 rounded-xl bg-teal-50 p-3");
  const pending = appendMessage("Checking SkillBridge's verified information...", "mr-8 rounded-xl bg-slate-100 p-3");
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The assistant could not answer right now.");
    if (typeof data.answer !== "string" || !data.answer.trim()) {
      throw new Error("The assistant returned an empty answer.");
    }
    pending.textContent = data.answer + (data.humanEscalated ? " This conversation has been flagged for human coordinator review." : "");
    document.querySelector("#messages").scrollTop = document.querySelector("#messages").scrollHeight;
    return data.answer;
  } catch (error) {
    pending.textContent = `${error.message || "The assistant is temporarily unavailable."} You can contact admissions on WhatsApp at +92 300 0000000 or email admissions@skillbridge.pk.`;
    return null;
  }
}

document.querySelector("#chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#chatInput");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  await askAssistant(message);
});

function setChatMode(mode) {
  const textMode = mode === "text";
  if (textMode) {
    stopVoice();
    setVoiceStatus("Tap to speak");
  }
  document.querySelector("#chatForm").classList.toggle("hidden", !textMode);
  document.querySelector("#voiceArea").classList.toggle("hidden", textMode);
  document.querySelector("#textMode").className = textMode
    ? "rounded-full bg-teal-50 px-3 py-1 text-sm font-bold text-[#0F766E]"
    : "rounded-full px-3 py-1 text-sm";
  document.querySelector("#voiceMode").className = textMode
    ? "rounded-full px-3 py-1 text-sm"
    : "rounded-full bg-teal-50 px-3 py-1 text-sm font-bold text-[#0F766E]";
  if (textMode && window.speechSynthesis) window.speechSynthesis.cancel();
}

document.querySelector("#textMode").onclick = () => setChatMode("text");
document.querySelector("#voiceMode").onclick = () => setChatMode("voice");

const micButton = document.querySelector("#micButton");
const micText = document.querySelector("#micText");
const waveform = document.querySelector(".wave");
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognitionActive = false;

function setVoiceStatus(text, listening = false) {
  micText.textContent = text;
  waveform.classList.toggle("listening", listening);
  micButton.setAttribute("aria-pressed", String(listening));
}

function speakAnswer(answer) {
  if (!answer || !window.speechSynthesis || !window.SpeechSynthesisUtterance) {
    setVoiceStatus("Answer is in chat. Speech playback is unavailable.");
    return;
  }
  try {
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(answer);
    utterance.lang = "en-US";
    utterance.onend = () => setVoiceStatus("Tap to speak");
    utterance.onerror = () => setVoiceStatus("Answer is in chat. Speech playback failed.");
    window.speechSynthesis.speak(utterance);
  } catch {
    setVoiceStatus("Answer is in chat. Speech playback failed.");
  }
}

micButton.onclick = () => {
  if (!SpeechRecognition) {
    setVoiceStatus("Voice input is unavailable in this browser. Switch to Text mode.");
    return;
  }
  if (recognitionActive) return;

  const recognition = new SpeechRecognition();
  activeRecognition = recognition;
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognitionActive = true;
  setVoiceStatus("Listening...", true);

  recognition.onresult = async (event) => {
    const phrase = event.results?.[0]?.[0]?.transcript?.trim();
    if (!phrase) {
      setVoiceStatus("No speech detected. Tap to try again.");
      return;
    }
    setVoiceStatus("Checking your question...");
    const answer = await askAssistant(phrase);
    if (answer) {
      if (document.querySelector("#voiceMode").classList.contains("bg-teal-50") && panel.classList.contains("chat-open")) {
        speakAnswer(answer);
      }
    }
    else setVoiceStatus("Answer is in chat. Tap to ask again.");
  };
  recognition.onerror = (event) => {
    const messages = {
      "not-allowed": "Microphone permission denied. Allow access or switch to Text mode.",
      "service-not-allowed": "Speech service unavailable. Switch to Text mode.",
      "no-speech": "No speech detected. Tap to try again.",
      "network": "Speech recognition needs a network connection. Switch to Text mode."
    };
    setVoiceStatus(messages[event.error] || "Voice input failed. Tap to retry or switch to Text mode.");
  };
  recognition.onend = () => {
    recognitionActive = false;
    if (activeRecognition === recognition) activeRecognition = null;
    if (micText.textContent === "Listening...") {
      setVoiceStatus("No speech detected. Tap to try again.");
    } else {
      waveform.classList.remove("listening");
      micButton.setAttribute("aria-pressed", "false");
    }
  };
  try {
    recognition.start();
  } catch {
    recognitionActive = false;
    activeRecognition = null;
    setVoiceStatus("Could not start voice input. Tap to retry or switch to Text mode.");
  }
};
