document.getElementById("send-btn").addEventListener("click", async function() {
    const userInput = document.getElementById("user-input").value;
    if (userInput.trim() === "") return;
    
    // Add user message to the chat box
    addMessageToChat(userInput, "user");

    // Clear the input field
    document.getElementById("user-input").value = "";

    // Send the input to the Hugging Face API and get the response
    const response = await fetchAPI(userInput);

    // Add bot message with formatting to the chat box
    addMessageToChat(response, "bot", true);
});

function addMessageToChat(message, sender, isHTML = false) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender);

    const messageContent = document.createElement("p");

    // If the message contains HTML (formatted response), insert it as HTML
    if (isHTML) {
        messageContent.innerHTML = formatMarkdown(message);
    } else {
        messageContent.textContent = message;
    }

    messageElement.appendChild(messageContent);
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
}

function formatMarkdown(text) {
    // Convert **bold** to <strong>bold</strong>
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
               .replace(/\*(.*?)\*/g, "<em>$1</em>"); // Handle *italic* if needed
}

async function fetchAPI(userQuestion) {
    try {
        console.log("Sending request to Hugging Face API...");
        
        // First request to get the event_id
        const response = await fetch('https://faizzabrar-lawyer-test2.hf.space/call/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data: [userQuestion] // Wrap the user question in an array, per the expected format
            })
        });

        console.log("Received raw response:", response);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Full API response (JSON):", result);  // Log the entire response for debugging

        // If event_id is received, make a second request to get the final result
        if (result && result.event_id) {
            console.log("Event ID received:", result.event_id);

            // Second request using the event_id to get the result
            const resultResponse = await fetch(`https://faizzabrar-lawyer-test2.hf.space/call/predict/${result.event_id}`, {
                method: 'GET'
            });

            if (!resultResponse.ok) {
                throw new Error(`Error fetching result! status: ${resultResponse.status}`);
            }

            // Reading the result as text (since it might be SSE text instead of JSON)
            const sseResponseText = await resultResponse.text();
            console.log("SSE Response Text:", sseResponseText);

            // Extract the actual data from the SSE formatted response
            const dataMatch = sseResponseText.match(/data:\s*(.*)/);  // Extracting the "data" line
            if (dataMatch && dataMatch[1]) {
                const finalResult = JSON.parse(dataMatch[1]);
                console.log("Parsed final result:", finalResult);

                if (finalResult && finalResult.length > 0) {
                    return finalResult[0];  // Return the response text
                }
            }

            return "No valid data found in the final response.";
        } else {
            return "No event ID received.";
        }
    } catch (error) {
        console.error("Error fetching API:", error);
        return `Sorry, an error occurred: ${error.message}`;
    }
}
