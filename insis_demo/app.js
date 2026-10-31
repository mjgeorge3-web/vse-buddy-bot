// Authentic InSIS Demo Application & Embedded VŠE Buddy Bot Logic

let chatHistory = [];
let hasEnteredInfo = false;
let hasUploadedPdf = false;
let isThesisSubmitted = false;

// -----------------------------------------------------------------------------
// 1. Navigation Between InSIS Views
// -----------------------------------------------------------------------------
function navigateTo(viewId) {
  const views = ["personal-admin", "student-portal", "master-thesis"];
  views.forEach((v) => {
    const el = document.getElementById("view-" + v);
    if (el) el.style.display = "none";
  });

  const target = document.getElementById("view-" + viewId);
  if (target) {
    target.style.display = "block";
  }

  // Update Breadcrumb Path
  const breadcrumbEl = document.getElementById("breadcrumb-dynamic");
  if (viewId === "personal-admin") {
    breadcrumbEl.innerHTML = "&raquo; Personal administration";
  } else if (viewId === "student-portal") {
    breadcrumbEl.innerHTML = '&raquo; <a href="#" onclick="navigateTo(\'student-portal\')">My College</a>';
  } else if (viewId === "master-thesis") {
    breadcrumbEl.innerHTML = '&raquo; <a href="#" onclick="navigateTo(\'student-portal\')">My College</a> &raquo; <strong>Master\'s thesis</strong>';
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// -----------------------------------------------------------------------------
// 2. Modal Handlers
// -----------------------------------------------------------------------------
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "flex";
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "none";
}

function openHelpModal() {
  alert(
    "InSIS Help & Support:\n\n" +
    "• For course enrollment assistance, contact the study coordinator at FIS.\n" +
    "• For technical login issues, visit the IT Helpdesk at Žižkov Old Building (SB).\n" +
    "• Or ask the VŠE Buddy Bot in the bottom right corner!"
  );
}

function openSearchModal() {
  const q = prompt("Thematic search across InSIS (e.g. thesis, timetable, credits):");
  if (q) {
    if (q.toLowerCase().includes("thesis") || q.toLowerCase().includes("errata")) {
      navigateTo("master-thesis");
    } else if (q.toLowerCase().includes("credit") || q.toLowerCase().includes("voucher")) {
      openPlanProgressCheck();
    } else {
      alert(`Search results for "${q}": Found 3 relevant applications in InSIS.`);
    }
  }
}

function openInstructionsModal() {
  alert(
    "Instructions for Submission Process of Final Thesis:\n\n" +
    "1. Fill in English and Czech title, abstract, and keywords.\n" +
    "2. Upload the thesis full text in PDF format (and optional ZIP attachments).\n" +
    "3. Confirm final electronic submission before the semester deadline.\n" +
    "4. Note: Once submitted, the file is locked and routed to Theses.cz for plagiarism check.\n" +
    "5. If errors are found post-submission, use 'Insert Errata' (Vložit errata) under § 47b."
  );
}

function openAddInfoModal() {
  openModal("add-info-modal");
}

function saveAdditionalInfo() {
  hasEnteredInfo = true;
  closeModal("add-info-modal");
  const badge = document.getElementById("badge-add-info");
  if (badge) {
    badge.className = "status-badge-above badge-green-check";
    badge.textContent = "✓";
  }
  alert("Abstracts and keywords successfully saved into InSIS!");
}

function openUploadThesisModal() {
  openModal("upload-thesis-modal");
}

function saveThesisUpload() {
  hasUploadedPdf = true;
  closeModal("upload-thesis-modal");
  const badge = document.getElementById("badge-upload");
  if (badge) {
    badge.className = "status-badge-above badge-green-check";
    badge.textContent = "✓";
  }
  alert("Master's thesis PDF and supplementary files uploaded. Plagiarism check scheduled via Theses.cz.");
}

function confirmThesisSubmission() {
  if (!hasEnteredInfo || !hasUploadedPdf) {
    const proceed = confirm(
      "Notice: You haven't completed both preliminary steps (Abstracts & PDF). Would you like to automatically populate sample files and submit?"
    );
    if (!proceed) return;
    saveAdditionalInfo();
    saveThesisUpload();
  }

  isThesisSubmitted = true;
  const badge = document.getElementById("badge-submit");
  if (badge) {
    badge.className = "status-badge-above badge-green-check";
    badge.textContent = "✓";
  }

  const alertBanner = document.getElementById("thesis-alert-banner");
  const bannerText = document.getElementById("thesis-banner-text");
  if (alertBanner && bannerText) {
    alertBanner.className = "insis-banner-alert locked-success";
    bannerText.innerHTML = "<strong>Thesis entered and locked (Odevzdáno).</strong> File registered in InSIS archive. Theses.cz protocol: 2.1% similarity.";
  }

  alert(
    "Confirmation:\n\n" +
    "Elektronická verze závěrečné práce byla odevzdána a bylo potvrzeno její korektní vložení.\n" +
    "Proces vkládání je tímto ukončen. Práci již nelze modifikovat.\n\n" +
    "If you need to submit corrections, use the 'Insert errata' option."
  );
}

function openErrataModal() {
  openModal("errata-modal");
}

function submitErrataFile() {
  const picker = document.getElementById("errata-file-picker");
  const fileName = picker && picker.files.length > 0 ? picker.files[0].name : "Errata_Thesis_Corrections_George_Joseph.pdf";

  closeModal("errata-modal");

  const badgeErrata = document.getElementById("badge-errata");
  if (badgeErrata) {
    badgeErrata.className = "status-badge-above badge-green-check";
    badgeErrata.textContent = "✓";
  }

  const panel = document.getElementById("errata-active-panel");
  if (panel) {
    panel.style.display = "block";
    panel.scrollIntoView({ behavior: "smooth" });
  }

  alert(
    `✓ Errata Upload Confirmed!\n\n` +
    `File: ${fileName}\n` +
    `Protocol: #ERR-2026-84920194\n` +
    `Notification dispatched to thesis supervisor Ing. Pavel Sládek, Ph.D. under § 47b.`
  );
}

function openPlanProgressCheck() {
  openModal("plan-check-modal");
}

// -----------------------------------------------------------------------------
// 3. Floating VŠE Buddy Bot Logic
// -----------------------------------------------------------------------------
function toggleBotDrawer() {
  const drawer = document.getElementById("bot-drawer");
  drawer.classList.toggle("hidden");
  if (!drawer.classList.contains("hidden")) {
    document.getElementById("bot-input-field").focus();
  }
}

function handleBotKey(event) {
  if (event.key === "Enter") {
    submitBotMessage();
  }
}

function sendBotPrompt(text) {
  document.getElementById("bot-input-field").value = text;
  submitBotMessage();
}

async function submitBotMessage() {
  const inputEl = document.getElementById("bot-input-field");
  const query = inputEl.value.trim();
  if (!query) return;

  inputEl.value = "";
  appendBotBubble("user", query);
  chatHistory.push({ role: "user", content: query });

  // Add temporary loading indicator
  const loadingBubble = appendBotBubble("assistant", "Searching verified VŠE documentation...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query, history: chatHistory }),
    });

    if (response.ok) {
      const data = await response.json();
      loadingBubble.innerHTML = formatBotMarkdown(data.answer);
      chatHistory.push({ role: "assistant", content: data.answer });

      // InSIS contextual deep link triggers based on query
      const qLower = query.toLowerCase();
      if (qLower.includes("errata") || qLower.includes("thesis")) {
        appendContextLink("📜 Open Master's Thesis & Errata Page in InSIS", () => {
          navigateTo("master-thesis");
          toggleBotDrawer();
        });
      } else if (qLower.includes("voucher") || qLower.includes("credit")) {
        appendContextLink("📊 Open Credit Voucher Wallet (120/144)", () => {
          openPlanProgressCheck();
          toggleBotDrawer();
        });
      } else if (qLower.includes("confirm") || qLower.includes("study")) {
        appendContextLink("📄 Open Electronic Confirmation of Study", () => {
          alert("Opening Electronic Confirmation of Study dialog...");
        });
      }
    } else {
      throw new Error("API call failed");
    }
  } catch (err) {
    const fallback = getContextualFallback(query);
    loadingBubble.innerHTML = formatBotMarkdown(fallback);
    chatHistory.push({ role: "assistant", content: fallback });
  }

  const container = document.getElementById("bot-messages-area");
  container.scrollTop = container.scrollHeight;
}

function appendBotBubble(role, text) {
  const container = document.getElementById("bot-messages-area");
  const bubble = document.createElement("div");
  bubble.className = `bot-msg-bubble ${role}`;
  bubble.innerHTML = formatBotMarkdown(text);
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function appendContextLink(label, actionFn) {
  const container = document.getElementById("bot-messages-area");
  const btn = document.createElement("button");
  btn.className = "mini-chip";
  btn.style.background = "#e0f2fe";
  btn.style.color = "#004b87";
  btn.style.borderColor = "#90cdf4";
  btn.style.fontWeight = "700";
  btn.style.marginTop = "4px";
  btn.innerHTML = label;
  btn.onclick = actionFn;
  container.appendChild(btn);
  container.scrollTop = container.scrollHeight;
}

function formatBotMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n\*/g, "<br>• ")
    .replace(/\n/g, "<br>");
}

function getContextualFallback(query) {
  const q = query.toLowerCase();
  if (q.includes("errata") || q.includes("thesis")) {
    return "To submit errata for your Master's thesis in InSIS:\n" +
      "1. Navigate to **My College** -> **Master's thesis**.\n" +
      "2. Under the editing application, click **'Insert errata' (Vložit errata)**.\n" +
      "3. Upload your structured corrections PDF.\n" +
      "4. Your supervisor **Ing. Pavel Sládek, Ph.D.** will receive notification to acknowledge it prior to your defense under § 47b [48-final-thesis-submission-defense-and-errata.md].";
  } else if (q.includes("credit") || q.includes("voucher")) {
    return "Master's Credit Voucher System at VŠE:\n" +
      "• Master's students receive **144 vouchers** for a standard 120 ECTS degree.\n" +
      "• Standard pace is **30 ECTS** per semester.\n" +
      "• You must earn at least **9 ECTS** in your first semester, or **20 ECTS** across any two consecutive semesters to maintain active enrollment [07-study-regulations-and-credit-system.md].";
  } else {
    return "I found information from verified VŠE documentation. Feel free to explore the modules in InSIS or ask for specific details!";
  }
}
