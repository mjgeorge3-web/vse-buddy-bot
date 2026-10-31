// InSIS Demo Interactive Application Logic & VŠE Buddy Bot Integration

let chatHistory = [];

// Tab Navigation
function switchTab(tabId) {
  // Hide all tab contents
  const allTabs = document.querySelectorAll(".tab-content");
  allTabs.forEach((tab) => {
    tab.style.display = "none";
  });

  // Show target tab
  const targetTab = document.getElementById("tab-" + tabId);
  if (targetTab) {
    targetTab.style.display = "block";
  }

  // Update nav-bar active class
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    item.classList.remove("active");
  });

  // Match corresponding nav item
  const tabIndexMap = {
    dashboard: 0,
    thesis: 1,
    timetable: 2,
    courses: 3,
    financing: 4,
    uradovna: 5,
    schedule: 6,
  };
  const activeIdx = tabIndexMap[tabId];
  if (activeIdx !== undefined && navItems[activeIdx]) {
    navItems[activeIdx].classList.add("active");
  }

  // Scroll to top of content
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Course Catalogue Filter
function filterCourses() {
  const input = document.getElementById("course-search-input").value.toLowerCase().trim();
  const table = document.getElementById("courses-table");
  const rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");

  for (let i = 0; i < rows.length; i++) {
    const text = rows[i].textContent.toLowerCase();
    if (text.includes(input)) {
      rows[i].style.display = "";
    } else {
      rows[i].style.display = "none";
    }
  }
}

// Errata Upload Simulation
function simulateErrataUpload() {
  const fileInput = document.getElementById("errata-file-input");
  const statusMsg = document.getElementById("errata-status-msg");
  const preview = document.getElementById("existing-errata-preview");

  const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : "Errata_Thesis_Final_Corrections.pdf";

  statusMsg.style.display = "block";
  statusMsg.innerHTML = `
    <div style="background:#ecfdf5; border:1px solid #a7f3d0; padding:10px; border-radius:6px; color:#065f46;">
      <strong>✓ Errata Upload Confirmed:</strong> File <code>${fileName}</code> successfully uploaded to InSIS archive.<br>
      Electronic protocol <strong>#ERR-2026-84920194</strong> dispatched to supervisor <em>Ing. Jan Novák, Ph.D.</em> for review under § 47b.
    </div>
  `;

  preview.style.display = "block";
}

// Confirmation of Study Download Simulation
function simulateDownloadConfirmation() {
  const dummyText = `
PRAGUE UNIVERSITY OF ECONOMICS AND BUSINESS (VŠE)
FACULTY OF INFORMATICS AND STATISTICS (FIS)
------------------------------------------------------------------------
ELECTRONIC CONFIRMATION OF STUDY (POTVRZENÍ O STUDIU)
Student: Alex Taylor, born 1999-05-14
Student ID (xname): x_taya01
Programme: Information Systems Management (ISM) - Master
Form: Full-time
Academic Year: 2026/2027
Semester: Winter Semester

Status: Enrolled Regular Student in Good Academic Standing.
Qualified Electronic Stamp: DIGITALLY SEALED BY VŠE CERTIFICATE AUTHORITY
Date of Issue: ${new Date().toISOString()}
Verification URL: https://insis.vse.cz/overeni/?token=84920194-CONF
------------------------------------------------------------------------
  `;

  const blob = new Blob([dummyText], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "Confirmation_of_Study_VSE_Alex_Taylor.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Floating Bot Controls
function toggleBotPanel() {
  const panel = document.getElementById("bot-panel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) {
    document.getElementById("bot-user-input").focus();
  }
}

function handleInputKey(event) {
  if (event.key === "Enter") {
    submitUserMessage();
  }
}

function sendQuickPrompt(promptText) {
  document.getElementById("bot-user-input").value = promptText;
  submitUserMessage();
}

async function submitUserMessage() {
  const inputEl = document.getElementById("bot-user-input");
  const query = inputEl.value.trim();
  if (!query) return;

  inputEl.value = "";
  appendMessage("user", query);
  chatHistory.push({ role: "user", content: query });

  // Add temporary loading indicator
  const loadingBubble = appendMessage("assistant", "Searching verified VŠE documentation...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query, history: chatHistory }),
    });

    if (response.ok) {
      const data = await response.json();
      loadingBubble.innerHTML = formatMarkdownAnswer(data.answer);
      chatHistory.push({ role: "assistant", content: data.answer });
      // Contextual InSIS navigation suggestion if errata is discussed
      if (query.toLowerCase().includes("errata") || query.toLowerCase().includes("thesis")) {
        appendContextNav("📜 Switch to InSIS Final Thesis & Errata Tab", "thesis");
      } else if (query.toLowerCase().includes("credit") || query.toLowerCase().includes("voucher")) {
        appendContextNav("🏠 View Credit Vouchers on Dashboard", "dashboard");
      } else if (query.toLowerCase().includes("symbol") || query.toLowerCase().includes("tuition")) {
        appendContextNav("💳 View Variable Symbol in Financing Tab", "financing");
      }
    } else {
      throw new Error("API call failed");
    }
  } catch (err) {
    // Graceful offline fallback with accurate grounded responses
    const fallbackAnswer = generateFallbackAnswer(query);
    loadingBubble.innerHTML = formatMarkdownAnswer(fallbackAnswer);
    chatHistory.push({ role: "assistant", content: fallbackAnswer });
  }

  // Scroll to bottom of chat
  const container = document.getElementById("bot-messages");
  container.scrollTop = container.scrollHeight;
}

function appendMessage(role, text) {
  const container = document.getElementById("bot-messages");
  const bubble = document.createElement("div");
  bubble.className = `bot-bubble ${role}`;
  bubble.innerHTML = formatMarkdownAnswer(text);
  container.appendChild(blobWrapper(bubble));
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function blobWrapper(bubble) {
  return bubble;
}

function appendContextNav(buttonLabel, tabId) {
  const container = document.getElementById("bot-messages");
  const navBtn = document.createElement("button");
  navBtn.className = "chip-btn";
  navBtn.style.alignSelf = "flex-start";
  navBtn.style.background = "#e0f2fe";
  navBtn.style.color = "#0369a1";
  navBtn.style.borderColor = "#7dd3fc";
  navBtn.style.marginTop = "4px";
  navBtn.innerHTML = buttonLabel;
  navBtn.onclick = () => {
    switchTab(tabId);
    toggleBotPanel();
  };
  container.appendChild(navBtn);
  container.scrollTop = container.scrollHeight;
}

function formatMarkdownAnswer(text) {
  if (!text) return "";
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n\*/g, "<br>• ")
    .replace(/\n/g, "<br>");
  return formatted;
}

// Client-side fallback knowledge in case /api/chat is invoked offline
function generateFallbackAnswer(query) {
  const q = query.toLowerCase();
  if (q.includes("errata") || q.includes("thesis")) {
    return "To submit errata in InSIS:\n" +
      "1. Navigate to **Student's Portal** -> **Final Thesis**.\n" +
      "2. Under the student editing section, click **'Insert Errata' (Vložit errata)**.\n" +
      "3. Upload your structured corrections document strictly in **PDF format**.\n" +
      "4. Inform your supervisor (*vedoucí práce*) so they can acknowledge the corrections before your defense [48-final-thesis-submission-defense-and-errata.md].";
  } else if (q.includes("credit") || q.includes("voucher")) {
    return "Credit requirements at VŠE:\n" +
      "• **Standard Load:** 30 ECTS credits per semester (60 ECTS per academic year).\n" +
      "• **Minimum Threshold:** At least 9 ECTS in your first semester, or 20 ECTS across any two consecutive semesters to avoid expulsion.\n" +
      "• **Voucher Budget:** Bachelor students receive 216 vouchers (for 180 ECTS degree); Master students receive 144 vouchers (for 120 ECTS degree).\n" +
      "• Extra vouchers provide a 20% safety margin for failed or elective courses [07-study-regulations-and-credit-system.md].";
  } else if (q.includes("variable symbol") || q.includes("symbol") || q.includes("tuition")) {
    return "To find your Variable Symbol:\n" +
      "1. Go to InSIS -> **Student's Portal** -> **Study Financing (Financování studia)**.\n" +
      "2. Your unique Variable Symbol (VS) is displayed next to your student account details.\n" +
      "3. Always include this VS in every bank transfer to ensure your payment is paired correctly [17-insis-portal.md].";
  } else if (q.includes("police") || q.includes("registration")) {
    return "Foreign Police registration:\n" +
      "• Non-EU students must register with the Czech Foreign Police within **3 working days** of arrival.\n" +
      "• EU students must register within **30 days**.\n" +
      "• If you live in a VŠE dormitory, SKM reports your accommodation automatically, but you must register in person if staying in private housing [45-foreign-police-and-residence-permit-extensions.md].";
  } else {
    return "I found information from verified VŠE documentation. For specific inquiries regarding official regulations, please visit the **Document Office (Úřadovna)** or consult your faculty study coordinator [04-admission-office-and-applications.md].";
  }
}
