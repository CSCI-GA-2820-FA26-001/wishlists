"use strict";

const statusMessage = document.getElementById("status");
const result = document.getElementById("result");

async function submitWishlist(form, url, options) {
    const button = form.querySelector("button");
    button.disabled = true;
    result.hidden = true;
    statusMessage.textContent = "Working…";
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `Request failed (${response.status}).`);
        }
        // Treat all API values as text, including user-provided names and notes.
        document.getElementById("result-id").textContent = data.id;
        document.getElementById("result-name").textContent = data.name;
        document.getElementById("result-customer").textContent = data.customer_id;
        document.getElementById("result-note").textContent = data.note || "—";
        document.getElementById("wishlist-id").value = data.id;
        result.hidden = false;
        statusMessage.textContent = "Wishlist loaded.";
    } catch (error) {
        statusMessage.textContent = `Unable to complete request: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

document.getElementById("create-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const data = {
        name: document.getElementById("name").value,
        customer_id: Number(document.getElementById("customer-id").value),
        note: document.getElementById("note").value || null,
    };
    submitWishlist(event.currentTarget, "/wishlists", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data),
    });
});

document.getElementById("retrieve-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const id = document.getElementById("wishlist-id").value;
    submitWishlist(event.currentTarget, `/wishlists/${encodeURIComponent(id)}`);
});
