async function uploadDocument() {
  const fileInput = document.getElementById("file-input");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select a file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  document.getElementById("status").textContent = "Uploading...";

  try {
    const response = await fetch("http://127.0.0.1:8000/upload/", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    document.getElementById("status").textContent = data.message || "File uploaded successfully!";
  } catch (error) {
    document.getElementById("status").textContent = "Error uploading document.";
    console.error(error);
  }
}

