import {
    isAuthenticated,
    authHeader
} from './auth.js';

function showToast(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    alert(message);
}

// DOM Elements
const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const statusText = document.getElementById("status");
const progressBar = document.getElementById("progress-bar");
const progressContainer = document.getElementById("progress-container");
const resultContainer = document.getElementById("result-container");
const extractedText = document.getElementById("extracted-text");
const summaryText = document.getElementById("summary-text");
const uploadBtn = document.getElementById("upload-btn");

// File input handler
fileInput.addEventListener("change", handleFileSelect);

function handleFileSelect() {
    preview.innerHTML = "";
    resultContainer.style.display = "none";
    statusText.textContent = "Status: Ready to upload";
    statusText.className = "";
    
    const file = fileInput.files[0];
    if (!file) return;

    const fileType = file.type;
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);

    // File size validation
    if (file.size > 10 * 1024 * 1024) { // 10MB
        statusText.textContent = `File too large (${fileSizeMB}MB). Max 10MB allowed.`;
        statusText.className = "error";
        fileInput.value = "";
        return;
    }

    // File type validation
    const validTypes = ["image/jpeg", "image/png", "application/pdf"];
    if (!validTypes.includes(fileType)) {
        statusText.textContent = "Unsupported file type. Please upload JPEG, PNG, or PDF.";
        statusText.className = "error";
        fileInput.value = "";
        return;
    }

    // Preview
    if (fileType.startsWith("image/")) {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        img.alt = "Document preview";
        img.onload = () => URL.revokeObjectURL(img.src);
        preview.appendChild(img);
    } else if (fileType === "application/pdf") {
        const pdfIcon = document.createElement("div");
        pdfIcon.className = "pdf-icon";
        pdfIcon.innerHTML = '<i class="fas fa-file-pdf"></i>';
        const fileName = document.createElement("p");
        fileName.textContent = file.name;
        preview.appendChild(pdfIcon);
        preview.appendChild(fileName);
    }

    statusText.textContent = `Ready: ${file.name} (${fileSizeMB}MB)`;
    statusText.className = "success";
}

// Upload document
async function uploadDocument() {
    if (!isAuthenticated()) {
        showToast('Please login to upload documents', 'error');
        return;
    }

    const file = fileInput.files[0];
    if (!file) {
        showToast("Please select a file first", "error");
        return;
    }

    // UI state
    uploadBtn.setAttribute("aria-busy", "true");
    uploadBtn.disabled = true;
    statusText.textContent = "Processing document...";
    statusText.className = "";
    progressBar.style.width = "0%";
    progressContainer.style.display = "block";
    resultContainer.style.display = "none";

    try {
        const formData = new FormData();
        formData.append("file", file);

        // Simulate progress for better UX
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            progressBar.style.width = `${Math.min(progress, 90)}%`;
            if (progress >= 90) clearInterval(progressInterval);
        }, 200);

        const response = await fetch("/api/documents/", {
            method: "POST",
            headers: authHeader(),
            body: formData
        });

        clearInterval(progressInterval);
        progressBar.style.width = "100%";

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message || "Failed to process document");
        }

        const data = await response.json();
        
        // Update UI with results
        statusText.textContent = data.message || "Processing complete!";
        statusText.className = "success";
        
        extractedText.textContent = data.data?.ocr_text || "No text could be extracted";
        summaryText.textContent = data.data?.analysis?.summary || "No summary generated.";
        
        resultContainer.style.display = "block";
        showToast("Document processed successfully!");

    } catch (error) {
        console.error("Processing error:", error);
        statusText.textContent = error.message || "Error processing document";
        statusText.className = "error";
        showToast(error.message || "Error processing document", "error");
    } finally {
        uploadBtn.removeAttribute("aria-busy");
        uploadBtn.disabled = false;
        setTimeout(() => {
            progressContainer.style.display = "none";
        }, 500);
    }
}

// Copy to clipboard
function copyToClipboard() {
    const textToCopy = extractedText.textContent;
    if (!textToCopy) return;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const copyBtn = document.querySelector(".copy-btn");
        copyBtn.classList.add("copied");
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        showToast("Text copied to clipboard");
        
        setTimeout(() => {
            copyBtn.classList.remove("copied");
            copyBtn.innerHTML = '<i class="far fa-copy"></i> Copy Text';
        }, 2000);
    }).catch(err => {
        console.error("Failed to copy text: ", err);
        showToast("Failed to copy text", "error");
    });
}

// Clear all and reset
function clearAll() {
    fileInput.value = "";
    preview.innerHTML = '<i class="fas fa-file-upload"></i><p>No document selected</p>';
    resultContainer.style.display = "none";
    statusText.textContent = "Status: Ready to upload";
    statusText.className = "";
}

// Event listeners
uploadBtn.addEventListener("click", uploadDocument);

// Keyboard accessibility
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && document.activeElement === uploadBtn) {
        uploadDocument();
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Service Worker for PWA
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/sw.js').then(registration => {
                console.log('ServiceWorker registration successful');
            }).catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
        });
    }
});