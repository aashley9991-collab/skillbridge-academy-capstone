const form = document.querySelector("#leadForm");
const formResult = document.querySelector("#formResult");
const LOCAL_LEADS_KEY = "skillbridge_leads_v1";
const SAMPLE_LEADS = [
  {
    id: "sample-ai",
    name: "Sample Student",
    email: "sample.ai@example.com",
    phone: "",
    track: "AI & Prompting Bootcamp",
    query: "Demo inquiry — replace this sample with a real inquiry.",
    summary: "AI & Prompting Bootcamp",
    status: "New",
    humanFollowup: false,
    createdAt: "Demo sample"
  },
  {
    id: "sample-scholarship",
    name: "Sample Scholarship Student",
    email: "sample.scholarship@example.com",
    phone: "",
    track: "Scholarship Inquiry",
    query: "Demo scholarship request — replace this sample with a real inquiry.",
    summary: "Scholarship - Human Review",
    status: "Scholarship Escalated",
    humanFollowup: true,
    createdAt: "Demo sample"
  }
];

const EMBEDDED_KNOWLEDGE_BASE = {
  client: "SkillBridge Academy",
  description: "Online ed-tech institute offering weekend, mentor-led bootcamps for Pakistani university students and fresh graduates to start freelancing and remote work careers.",
  programs: [
    {name: "AI & Prompting Bootcamp", duration: "4 weeks", fee_pkr: 8000},
    {name: "Freelance Digital Marketing", duration: "6 weeks", fee_pkr: 12000}
  ],
  schedule: "Live Zoom sessions on Saturdays and Sundays, 7:00 PM to 9:00 PM PKT",
  recordings: "Lifetime access to session recordings",
  support: "Verified completion certificate and portfolio review included",
  contact: {
    whatsapp: "+92 300 0000000",
    whatsapp_url: "https://wa.me/923000000000",
    email: "admissions@skillbridge.pk"
  },
  scholarships: "Scholarship requests require human coordinator review",
  compliance: "Never promise guaranteed jobs, fixed monthly dollar income, or overnight freelancing success"
};

function getLocalLeads() {
  const saved = localStorage.getItem(LOCAL_LEADS_KEY);
  if (saved !== null) {
    const leads = JSON.parse(saved);
    if (!Array.isArray(leads)) throw new Error("Saved browser inquiries are invalid.");
    if (leads.length) return leads;
  }
  const samples = SAMPLE_LEADS.map((lead) => ({...lead}));
  localStorage.setItem(LOCAL_LEADS_KEY, JSON.stringify(samples));
  return samples;
}

function saveLocalLead(lead) {
  const leads = getLocalLeads();
  leads.unshift(lead);
  localStorage.setItem(LOCAL_LEADS_KEY, JSON.stringify(leads));
  return lead;
}

function scholarshipRequested(text) {
  return /scholar|financial aid|financial assistance|tuition assistance|tuition support/i.test(text);
}

function createLocalLead(body, source = "Website inquiry") {
  const humanFollowup = scholarshipRequested(body.query || "");
  const track = (body.track || "").trim();
  const tags = [];
  if (humanFollowup) tags.push("Scholarship - Human Review");
  if (track) tags.push(track);
  return {
    id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: (body.name || source).trim(),
    email: (body.email || "").trim(),
    phone: (body.phone || "").trim(),
    track: track || (humanFollowup ? "Scholarship Inquiry" : "General Inquiry"),
    query: (body.query || "").trim(),
    summary: tags.join(" | ") || "General Inquiry",
    status: humanFollowup ? "Scholarship Escalated" : "New",
    humanFollowup,
    createdAt: new Date().toISOString()
  };
}

async function loadKnowledgeBase() {
  try {
    const url = new URL("../data/knowledge_base.json", window.location.href);
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Knowledge base request failed (${response.status}).`);
    const knowledge = await response.json();
    if (!knowledge.client || !Array.isArray(knowledge.programs) || !knowledge.contact) {
      throw new Error("Knowledge base is missing required verified facts.");
    }
    return knowledge;
  } catch {
    return EMBEDDED_KNOWLEDGE_BASE;
  }
}

function resolveLocalAnswer(message, knowledge) {
  const text = message.toLowerCase();
  const scholarship = scholarshipRequested(text);
  const compliance = /guarantee|guaranteed|fixed income|fixed monthly|fixed dollar|monthly dollar|monthly income|dollar income|income|salary|earnings|overnight success|job placement|employment guarantee|how much can i earn|how much will i earn|how many dollars/.test(text)
    || (text.includes("job") && /(promise|guarantee|placement)/.test(text));
  const program = knowledge.programs.find((item) =>
    (item.name.toLowerCase().includes("ai") && (/\bai\b|prompt/.test(text)))
    || (item.name.toLowerCase().includes("marketing") && /(marketing|digital)/.test(text))
  );
  const parts = [];

  if (compliance) {
    parts.push(`${knowledge.client} cannot promise guaranteed jobs, fixed monthly dollar income, or overnight freelancing success.`);
  }
  if (scholarship) {
    parts.push(`${knowledge.scholarships}. Contact admissions on WhatsApp at ${knowledge.contact.whatsapp} (${knowledge.contact.whatsapp_url}) or email ${knowledge.contact.email}.`);
  } else if (!compliance && /(contact|whatsapp|email|follow.?up|reach|admissions)/.test(text)) {
    parts.push(`Contact ${knowledge.client} on WhatsApp at ${knowledge.contact.whatsapp} (${knowledge.contact.whatsapp_url}) or email ${knowledge.contact.email}.`);
  } else if (!compliance && /(fee|fees|price|cost|how much)/.test(text)) {
    parts.push(knowledge.programs.map((item) => `${item.name}: ${item.duration}, PKR ${item.fee_pkr.toLocaleString("en-PK")}`).join(". ") + ".");
  } else if (!compliance && /(schedule|timing|weekend|saturday|sunday|class|zoom|recording)/.test(text)) {
    parts.push(`${knowledge.schedule}. ${knowledge.recordings}.`);
  } else if (!compliance && /(certificate|portfolio|review|support)/.test(text)) {
    parts.push(`${knowledge.support}. ${knowledge.scholarships}.`);
  } else if (!compliance && program) {
    parts.push(`${program.name} is ${program.duration} and costs PKR ${program.fee_pkr.toLocaleString("en-PK")}. ${knowledge.schedule}.`);
  } else if (!compliance) {
    parts.push(`${knowledge.description} Programs: ${knowledge.programs.map((item) => `${item.name} (${item.duration}, PKR ${item.fee_pkr.toLocaleString("en-PK")})`).join("; ")}. ${knowledge.schedule}. ${knowledge.recordings}. ${knowledge.support}.`);
  }

  return {answer: parts.join(" "), humanEscalated: scholarship};
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = Object.fromEntries(new FormData(form));
  formResult.className = "rounded-xl bg-teal-50 p-4 text-sm whitespace-pre-line";
  formResult.textContent = "Submitting...";
  formResult.classList.remove("hidden");

  try {
    let response;
    try {
      response = await fetch("/api/leads", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
      });
    } catch (error) {
      if (!(error instanceof TypeError)) throw error;
    }

    if (!response || [404, 405, 501].includes(response.status)) {
      const lead = saveLocalLead(createLocalLead(body));
      formResult.textContent = `Saved in this browser only.\n${lead.summary}${lead.humanFollowup ? "\nScholarship requests require human coordinator review. Please follow up with admissions using the contacts below." : ""}\nStatic hosting does not send this inquiry to SkillBridge.`;
      form.reset();
      return;
    }

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
    let response;
    try {
      response = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
      });
    } catch (error) {
      if (!(error instanceof TypeError)) throw error;
    }

    let data;
    if (!response || [404, 405, 501].includes(response.status)) {
      const knowledge = await loadKnowledgeBase();
      data = resolveLocalAnswer(message, knowledge);
      if (data.humanEscalated) {
        try {
          saveLocalLead(createLocalLead({
            name: "Website Chat Visitor",
            track: "Scholarship Inquiry",
            query: message
          }, "Website Chat Visitor"));
          data.answer += " This scholarship request is flagged in this browser's Admin Panel only; please contact admissions directly to request human follow-up.";
        } catch {
          data.answer += " This static site could not save the request in this browser. Please contact admissions directly for human follow-up.";
        }
      }
    } else {
      data = await response.json();
      if (!response.ok) throw new Error(data.error || "The assistant could not answer right now.");
    }
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
let activeRecognition = null;

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
