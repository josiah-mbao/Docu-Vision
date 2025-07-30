const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const statusText = document.getElementById("status");
const progressBar = document.getElementById("progress-bar");
const progressContainer = document.getElementById("progress-container");
const resultContainer = document.getElementById("result-container"); // Add this element in your HTML
const extractedText = document.getElementById("extracted-text"); // Add this element in your HTML

fileInput.addEventListener("change", () => {
  preview.innerHTML = ""; // Clear previous preview
  resultContainer.style.display = "none"; // Hide results when new file selected
  const file = fileInput.files[0];
  if (!file) return;

  const fileType = file.type;

  if (fileType.startsWith("image/")) {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.onload = () => URL.revokeObjectURL(img.src); // Clean up memory
    preview.appendChild(img);
  } else if (fileType === "application/pdf") {
    const pdfIcon = document.createElement("div");
    pdfIcon.className = "pdf-icon";
    pdfIcon.textContent = "📄 PDF Selected";
    preview.appendChild(pdfIcon);
  } else {
    const message = document.createElement("p");
    message.textContent = "Unsupported file type.";
    preview.appendChild(message);
  }
});

async function uploadDocument() {
  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file first.");
    return;
  }

  // Validate file size (OCR.space free tier has 1MB limit)
  if (file.size > 1000000) {
    statusText.textContent = "File too large (max 1MB for free tier)";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  statusText.textContent = "Processing document...";
  progressBar.style.width = "0%";
  progressContainer.style.display = "block";
  resultContainer.style.display = "none";

  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to process document");
    }

    const data = await response.json();
    
    // Update UI with results
    statusText.textContent = data.message || "Processing complete!";
    extractedText.textContent = data.text || "No text could be extracted";
    resultContainer.style.display = "block";
    
    // Optional: Format text (preserve line breaks)
    extractedText.innerHTML = data.text.replace(/\n/g, "<br>");
    
  } catch (error) {
    statusText.textContent = error.message || "Error processing document";
    console.error("Processing error:", error);
  } finally {
    progressContainer.style.display = "none";
  }
}

// Add this to your HTML:
/*
<div id="result-container" style="display: none; margin-top: 20px;">
  <h3>Extracted Text:</h3>
  <div id="extracted-text" style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;"></div>
</div>
*/