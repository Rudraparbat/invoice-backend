/**
 * Simple S3 File Upload using Presigned URL
 * Use presigned URL obtained from Swagger/Backend API
 */

// Configuration
const API_BASE_URL = "http://localhost:8000/api/users"; // Update to your backend URL
// const JWT_TOKEN = localStorage.getItem("jwt_token"); // Retrieve JWT token from localStorage

/**
 * Upload file directly to S3 using presigned URL
 * @param {string} presignedUrl - Presigned PUT URL from backend Swagger
 * @param {File} file - File object to upload
 * @returns {Promise} - Upload success/failure
 */
async function uploadFileToS3(presignedUrl, file) {
  try {
    console.log(`Uploading file: ${file.name} (${file.size} bytes)...`);

    const response = await fetch(presignedUrl, {
      method: "PUT",
      headers: {
        "Content-Type": file.type || "application/octet-stream",
      },
      body: file,
    });

    if (!response.ok) {
      throw new Error(`S3 upload failed: ${response.statusText}`);
    }

    console.log("✅ File uploaded to S3 successfully!");
    return true;
  } catch (error) {
    console.error("❌ Error uploading to S3:", error);
    throw error;
  }
}

/**
 * Notify backend about successful upload
 * @param {number} invoiceId - Invoice ID
 * @param {string} objectKey - S3 object key (e.g., "invoices/1/filename.pdf")
 * @returns {Promise} - Contains file_url (presigned GET URL)
 */
async function notifyBackendFileUploaded(invoiceId, objectKey) {
  try {
    const response = await fetch(`${API_BASE_URL}/update-invoice-file/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${JWT_TOKEN}`,
      },
      body: JSON.stringify({
        invoice_id: invoiceId,
        object_key: objectKey,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update invoice: ${response.statusText}`);
    }

    const data = await response.json();
    console.log("✅ Invoice updated with file URL:", data);
    return data;
  } catch (error) {
    console.error("❌ Error notifying backend:", error);
    throw error;
  }
}

/**
 * Main function - Upload file and notify backend
 * @param {string} presignedUrl - Presigned URL from Swagger/Backend
 * @param {string} objectKey - S3 object key (from Swagger response)
 * @param {File} file - File to upload
 * @param {number} invoiceId - Invoice ID
 * @returns {Promise} - Upload result
 */
async function uploadFile(presignedUrl, objectKey, file, invoiceId) {
  try {
    // Validate file size (< 5MB)
    const maxFileSize = 5 * 1024 * 1024;
    if (file.size > maxFileSize) {
      throw new Error(
        `File size exceeds 5MB. Current: ${(file.size / 1024 / 1024).toFixed(
          2
        )}MB`
      );
    }

    // Upload to S3
    await uploadFileToS3(presignedUrl, file);

    // Notify backend
    const result = await notifyBackendFileUploaded(invoiceId, objectKey);

    return {
      success: true,
      message: result.message,
      file_url: result.file_url,
    };
  } catch (error) {
    console.error("Upload failed:", error.message);
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * USAGE EXAMPLE:
 *
 * 1. Get presigned URL from Swagger:
 *    POST /api/users/get-presigned-url/
 *    Body: { "invoice_id": 1, "filename": "invoice.pdf" }
 *    Response: { "presigned_url": "https://...", "object_key": "invoices/1/invoice.pdf", "invoice_id": 1 }
 *
 * 2. Use the uploadFile() function:
 *    const file = document.getElementById('fileInput').files[0];
 *    const presignedUrl = "paste-presigned-url-from-swagger";
 *    const objectKey = "invoices/1/invoice.pdf"; // from Swagger response
 *
 *    const result = await uploadFile(presignedUrl, objectKey, file, 1);
 *    if (result.success) {
 *      console.log('File uploaded! Download URL:', result.file_url);
 *    }
 */
