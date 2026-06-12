const searchInput = document.querySelector("#loop-search");
const filterButtons = [...document.querySelectorAll("[data-filter]")];
const loopCards = [...document.querySelectorAll(".loop-card")];
const resultsCount = document.querySelector("#results-count");
const emptyState = document.querySelector("#empty-state");
const toast = document.querySelector("#toast");

let activeFilter = "all";
let toastTimer;

function normalize(value) {
  return value.toLowerCase().trim();
}

function updateLibrary() {
  const query = normalize(searchInput.value);
  let visibleCount = 0;

  loopCards.forEach((card) => {
    const matchesType =
      activeFilter === "all" || card.dataset.type === activeFilter;
    const searchableText = `${card.dataset.search} ${card.textContent}`;
    const matchesSearch =
      query.length === 0 || normalize(searchableText).includes(query);
    const isVisible = matchesType && matchesSearch;

    card.hidden = !isVisible;
    if (isVisible) {
      visibleCount += 1;
    }
  });

  resultsCount.textContent = `Showing ${visibleCount} ${
    visibleCount === 1 ? "loop" : "loops"
  }`;
  emptyState.hidden = visibleCount !== 0;
}

searchInput.addEventListener("input", updateLibrary);

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;

    filterButtons.forEach((candidate) => {
      const isActive = candidate === button;
      candidate.classList.toggle("is-active", isActive);
      candidate.setAttribute("aria-pressed", String(isActive));
    });

    updateLibrary();
  });
});

filterButtons.forEach((button) => {
  button.setAttribute(
    "aria-pressed",
    String(button.classList.contains("is-active")),
  );
});

function showToast(message) {
  window.clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2200);
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";
  document.body.append(textArea);
  textArea.select();
  document.execCommand("copy");
  textArea.remove();
}

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const card = button.closest(".loop-card");
    const prompt = card.querySelector("[data-prompt]").textContent.trim();
    const label = button.querySelector("span");

    try {
      await copyText(prompt.replace(/\s+/g, " "));
      label.textContent = "Copied";
      showToast("Loop copied to clipboard.");
      window.setTimeout(() => {
        label.textContent = "Copy loop";
      }, 1800);
    } catch {
      showToast("Copy failed. Select the prompt text instead.");
    }
  });
});

document.querySelectorAll("textarea[maxlength]").forEach((textarea) => {
  const counter = document.querySelector(
    `[data-counter-for="${textarea.name}"]`,
  );

  if (!counter) {
    return;
  }

  const updateCounter = () => {
    counter.textContent = `${textarea.value.length} / ${textarea.maxLength}`;
  };

  textarea.addEventListener("input", updateCounter);
  updateCounter();
});

const form = document.querySelector("#loop-form");
const formStatus = document.querySelector("#form-status");
const submitButton = form.querySelector(".submit-button");
const submitButtonLabel = submitButton.querySelector("span");

let formStartedAt = performance.now();
let idempotencyKey = makeIdempotencyKey();

function makeIdempotencyKey() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function setFormStatus(message, kind = "") {
  formStatus.textContent = message;
  formStatus.classList.toggle("is-success", kind === "success");
  formStatus.classList.toggle("is-error", kind === "error");
}

function optionalValue(formData, name) {
  const value = String(formData.get(name) || "").trim();
  return value || undefined;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFormStatus("");

  if (!form.checkValidity()) {
    form.reportValidity();
    setFormStatus("Complete the required fields before submitting.", "error");
    return;
  }

  const formData = new FormData(form);
  const honeypot = String(formData.get("company") || "").trim();

  if (honeypot) {
    form.reset();
    setFormStatus("Thanks. Your suggestion is in review.", "success");
    return;
  }

  if (performance.now() - formStartedAt < 1200) {
    setFormStatus(
      "Take a moment to review the loop, then submit it again.",
      "error",
    );
    return;
  }

  const payload = {
    name: String(formData.get("name")).trim(),
    loop_title: String(formData.get("loop_title")).trim(),
    loop_type: String(formData.get("loop_type")).trim(),
    instructions: String(formData.get("instructions")).trim(),
  };

  const email = optionalValue(formData, "email");
  const whyItWorks = optionalValue(formData, "why_it_works");
  const sourceUrl = optionalValue(formData, "source_url");

  if (email) {
    payload.email = email;
  }

  if (whyItWorks) {
    payload.why_it_works = whyItWorks;
  }

  if (sourceUrl) {
    payload.source_url = sourceUrl;
  }

  submitButton.disabled = true;
  submitButtonLabel.textContent = "Sending";

  try {
    const response = await fetch("./.herenow/data/suggestions", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(payload),
    });

    let responseBody = {};
    try {
      responseBody = await response.json();
    } catch {
      responseBody = {};
    }

    if (!response.ok) {
      if (response.status === 429) {
        throw new Error(
          "This connection has reached the submission limit. Try again later.",
        );
      }

      throw new Error(
        responseBody.message ||
          responseBody.error ||
          "The suggestion could not be submitted.",
      );
    }

    form.reset();
    document.querySelectorAll("textarea[maxlength]").forEach((textarea) => {
      textarea.dispatchEvent(new Event("input"));
    });
    setFormStatus(
      "Received. The loop is now in the private review queue.",
      "success",
    );
    idempotencyKey = makeIdempotencyKey();
    formStartedAt = performance.now();
  } catch (error) {
    setFormStatus(
      error.message || "Something went wrong. Try again in a moment.",
      "error",
    );
  } finally {
    submitButton.disabled = false;
    submitButtonLabel.textContent = "Send for review";
  }
});
