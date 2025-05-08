const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const statusText = document.getElementById("status");
const progressBar = document.getElementById("progress-bar");
const progressContainer = document.getElementById("progress-container");

fileInput.addEventListener("change", () => {
  preview.innerHTML = ""; // Clear previous preview
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

  const formData = new FormData();
  formData.append("file", file);

  statusText.textContent = "Uploading...";
  progressBar.style.width = "0%";
  progressContainer.style.display = "block";

  try {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload/", true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        progressBar.style.width = percent + "%";
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        statusText.textContent = response.message || "Upload successful!";
      } else {
        statusText.textContent = "Error uploading document.";
      }
      progressContainer.style.display = "none";
    };

    xhr.onerror = () => {
      statusText.textContent = "Upload failed.";
      progressContainer.style.display = "none";
    };

    xhr.send(formData);
  } catch (error) {
    statusText.textContent = "Error uploading document.";
    progressContainer.style.display = "none";
    console.error(error);
  }
}

