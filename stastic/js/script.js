// Store conversation history
let conversationHistory = [];

// DOM elements
const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");
const fileInput = document.getElementById("csvFile");
const uploadButton = document.getElementById("upload-button");
const uploadResponse = document.getElementById("uploadResponse");

// Initial bot message
window.onload = function () {
    addBotMessage("I'm your business assistant. Upload financial data or ask about revenue, costs, and performance.");
    userInput.focus();
};

// Add user message
function addUserMessage(message) {
    chatContainer.innerHTML += `<div class="message user-message">${message}</div>`;
    scrollToBottom();
    conversationHistory.push({ role: "user", content: message });
}

// Add bot message
function addBotMessage(message) {
    chatContainer.innerHTML += `<div class="message bot-message">${message}</div>`;
    scrollToBottom();
    conversationHistory.push({ role: "assistant", content: message });
}

// Show typing indicator
function showTypingIndicator() {
    chatContainer.innerHTML += `<div class="typing-indicator" id="typing-indicator"><span></span><span></span><span></span></div>`;
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    document.getElementById("typing-indicator")?.remove();
}

// Scroll chat to the bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Send user message to backend
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    userInput.value = "";
    addUserMessage(message);
    showTypingIndicator();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, history: conversationHistory.slice(0, -1) }),
        });

        const data = await response.json();
        removeTypingIndicator();
        addBotMessage(data.response);
    } catch {
        removeTypingIndicator();
        addBotMessage("Error processing request. Try again.");
    }
}

// Upload file
async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) return addBotMessage("Select a file before uploading.");

    showTypingIndicator();
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await response.json();
        removeTypingIndicator();
        addBotMessage(`File uploaded. Insights:\n${data.response}`);
        uploadResponse.innerText = "File uploaded!";
    } catch {
        removeTypingIndicator();
        addBotMessage("Error uploading file.");
        uploadResponse.innerText = "Upload failed.";
    }
}

// Event listeners
sendButton.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => e.key === "Enter" && sendMessage());
uploadButton.addEventListener("click", uploadFile);
