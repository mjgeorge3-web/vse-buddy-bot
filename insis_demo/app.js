// =============================================================================
// Authentic InSIS Multi-URL Router, Public/Auth Session Controller & Buddy Bot
// Supports:
//   1. No-Login Public InSIS Portal (https://insis.vse.cz/?lang=en)
//   2. Custom Name + Password ("ism_mastersthesis") Login across all 195 URLs
//   3. Clean Session Wipe on Logout (both Portal & Bot switch to Public Mode)
//   4. Context-Aware Page Co-Pilot (Idea 1), Personalised Profile (Idea 2),
//      Smart Topic Switch (Visas/Stay/Campus), & Interactive Checklist (Idea 3)
// =============================================================================

const REQUIRED_INSIS_PASSWORD = "ism_mastersthesis";

let allUrlsList = [];
let chatHistory = [];
let hasEnteredInfo = false;
let hasUploadedPdf = false;
let isThesisSubmitted = false;

let currentPageKey = "public_home";
let currentPageTitle = "Public Information Portal";
let currentPageUrl = "https://insis.vse.cz/?lang=en";
let isPersonalisedEnabled = true;

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// -----------------------------------------------------------------------------
// 1. Session & Login Controller
// -----------------------------------------------------------------------------
function cleanupLegacySessionKeys() {
  // Remove any legacy keys from older prototypes so stale names never persist
  localStorage.removeItem("insis_logged_in");
  localStorage.removeItem("insis_auth_active");
  localStorage.removeItem("insis_user_name");
}

function getLoginSession() {
  cleanupLegacySessionKeys();
  const isAuth = localStorage.getItem("insis_session_v3") === "true";
  const storedName = (localStorage.getItem("insis_session_user_v3") || "").trim();
  const prefPers = localStorage.getItem("insis_bot_personalised");
  if (prefPers !== null) {
    isPersonalisedEnabled = prefPers === "true";
  }

  if (!isAuth || !storedName) {
    return { loggedIn: false, userName: "" };
  }
  return { loggedIn: true, userName: storedName };
}

function resetBotConversationForSession() {
  chatHistory = [];
  const session = getLoginSession();
  const area = document.getElementById("bot-messages-area");
  const chipsBox = document.getElementById("bot-quick-chips");
  if (chipsBox) chipsBox.innerHTML = "";
  if (!area) return;

  if (!session.loggedIn) {
    area.innerHTML = `
      <div class="bot-hero-container">
        <div class="bot-hero-badge">🌍 Public Guest Access • Demo Prototype</div>
        <div class="bot-hero-title">How can I help you today?</div>
        <div class="bot-hero-sub">Direct AI guidance on VŠE studies, visa rules, dormitories, and InSIS navigation &mdash; no login required.</div>
        <div class="bot-hero-cards">
          <div class="bot-starter-card" onclick="sendBotPrompt('What are the visa and 3-day Foreign Police registration rules for international students?')">
            <div class="starter-icon">🛂</div>
            <div class="starter-text">
              <div class="starter-title">Visa &amp; Police Registration</div>
              <div class="starter-desc">3-day arrival rule, MOI appointments, accommodation confirmations</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('How do I find accommodation in VŠE dormitories or private flats in Prague?')">
            <div class="starter-icon">🏢</div>
            <div class="starter-text">
              <div class="starter-title">Dormitories &amp; Accommodation</div>
              <div class="starter-desc">ISKaM reservations, Jarov/Blanice dorms, leases</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('How do admissions and the E-application work at VŠE?')">
            <div class="starter-icon">🎓</div>
            <div class="starter-text">
              <div class="starter-title">Admissions &amp; E-Application</div>
              <div class="starter-desc">Programmes, deadlines, entrance exams, and first login</div>
            </div>
          </div>
        </div>
        <div class="bot-hero-research-note">
          🔬 <em>Academic Master's Thesis Prototype (ISM VŠE) • Not an official university service</em>
        </div>
      </div>
    `;
  } else {
    const safeName = escapeHtml(session.userName);
    area.innerHTML = `
      <div class="bot-hero-container">
        <div class="bot-hero-badge">🎓 Student Mode • Demo Prototype</div>
        <div class="bot-hero-title">Welcome back, ${safeName}!</div>
        <div class="bot-hero-sub">I have direct context of your simulated InSIS profile, credit vouchers, thesis progress, and study policies.</div>
        <div class="bot-hero-cards">
          <div class="bot-starter-card" onclick="sendBotPrompt('How many credit vouchers and credits do I have left?')">
            <div class="starter-icon">📊</div>
            <div class="starter-text">
              <div class="starter-title">Check My Credit Vouchers</div>
              <div class="starter-desc">Check your remaining voucher balance (120/144) and minimum progression rules</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('What do the 3 red Xs mean on my Master\\'s Thesis page and how do I submit errata?')">
            <div class="starter-icon">📗</div>
            <div class="starter-text">
              <div class="starter-title">Master's Thesis Workflow</div>
              <div class="starter-desc">Resolving the 3 red Xs, abstract entry, and submitting § 47b errata PDF</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('What are the visa and 3-day Foreign Police registration rules for international students?')">
            <div class="starter-icon">🛂</div>
            <div class="starter-text">
              <div class="starter-title">Visa &amp; Accommodation Rules</div>
              <div class="starter-desc">Foreign Police 3-day registration, ISKaM dormitory check-in</div>
            </div>
          </div>
        </div>
        <div class="bot-hero-research-note">
          🔬 <em>Academic Master's Thesis Prototype (ISM VŠE) • Simulated Student Records</em>
        </div>
      </div>
    `;
  }
}

function updateSessionUI() {
  const session = getLoginSession();
  const loggedInBar = document.getElementById("user-info-logged-in");
  const loggedOutBar = document.getElementById("user-info-logged-out");
  const closeBtn = document.getElementById("user-bar-close");
  const displayUser = document.getElementById("display-user-name");
  const breadcrumbTools = document.getElementById("breadcrumb-tools");
  const thesisAuthorLink = document.getElementById("thesis-author-link");

  if (session.loggedIn) {
    if (loggedInBar) loggedInBar.style.display = "flex";
    if (loggedOutBar) loggedOutBar.style.display = "none";
    if (closeBtn) closeBtn.style.display = "block";
    if (displayUser) displayUser.textContent = session.userName;
    if (breadcrumbTools) breadcrumbTools.style.display = "flex";
    if (thesisAuthorLink) {
      thesisAuthorLink.textContent = session.userName;
      thesisAuthorLink.onclick = () => {
        alert(`Author: ${session.userName}`);
        return false;
      };
    }
  } else {
    if (loggedInBar) loggedInBar.style.display = "none";
    if (closeBtn) closeBtn.style.display = "none";
    if (displayUser) displayUser.textContent = "";
    if (thesisAuthorLink) {
      thesisAuthorLink.textContent = "Not logged in";
      thesisAuthorLink.onclick = () => false;
    }

    // Keep the pale-blue strip completely clean on the Public InSIS homepage
    if (currentPageKey === "public_home") {
      if (loggedOutBar) loggedOutBar.style.display = "none";
      if (breadcrumbTools) breadcrumbTools.style.display = "none";
    } else {
      if (loggedOutBar) loggedOutBar.style.display = "flex";
      if (breadcrumbTools) breadcrumbTools.style.display = "flex";
    }
  }

  updateBotContextUI();
}

function goHome() {
  const session = getLoginSession();
  if (session.loggedIn) {
    navigateToUrl("https://insis.vse.cz/auth/?lang=en");
  } else {
    navigateToUrl("https://insis.vse.cz/?lang=en");
  }
}

function performLogout() {
  cleanupLegacySessionKeys();
  localStorage.setItem("insis_session_v3", "false");
  localStorage.removeItem("insis_session_user_v3");
  sessionStorage.removeItem("insis_pending_url");

  // Clear login inputs for next user
  const userInp = document.getElementById("login-username");
  const passInp = document.getElementById("login-password");
  const errBox = document.getElementById("login-error-msg");
  if (userInp) userInp.value = "";
  if (passInp) passInp.value = "";
  if (errBox) errBox.style.display = "none";

  // Immediately wipe bot chat history & switch bot back to Public (Not Logged In) state
  resetBotConversationForSession();
  navigateToUrl("https://insis.vse.cz/?lang=en");
}

function handleLoginSubmit(event) {
  if (event) event.preventDefault();
  const usernameInput = document.getElementById("login-username");
  const passwordInput = document.getElementById("login-password");
  const errorBox = document.getElementById("login-error-msg");

  const name = usernameInput ? usernameInput.value.trim() : "";
  const pwd = passwordInput ? passwordInput.value.trim() : "";

  if (!name) {
    if (errorBox) {
      errorBox.textContent = "Please enter your name to log in.";
      errorBox.style.display = "block";
    }
    if (usernameInput) usernameInput.focus();
    return;
  }

  if (pwd !== REQUIRED_INSIS_PASSWORD) {
    if (errorBox) {
      errorBox.textContent = "Invalid password. Please enter password: ism_mastersthesis";
      errorBox.style.display = "block";
    }
    if (passwordInput) {
      passwordInput.value = "";
      passwordInput.focus();
    }
    return;
  }

  if (errorBox) errorBox.style.display = "none";
  if (passwordInput) passwordInput.value = "";

  cleanupLegacySessionKeys();
  localStorage.setItem("insis_session_v3", "true");
  localStorage.setItem("insis_session_user_v3", name);

  // Reset bot conversation cleanly for this newly authenticated user
  resetBotConversationForSession();

  const pendingUrl =
    sessionStorage.getItem("insis_pending_url") ||
    "https://insis.vse.cz/auth/?lang=en";
  sessionStorage.removeItem("insis_pending_url");
  navigateToUrl(pendingUrl);
}

function showLoginView() {
  hideAllViews();
  currentPageKey = "login";
  currentPageTitle = "Log in to InSIS";
  currentPageUrl = "https://insis.vse.cz/auth/login";

  const errBox = document.getElementById("login-error-msg");
  if (errBox) errBox.style.display = "none";

  const loginView = document.getElementById("view-login");
  if (loginView) loginView.style.display = "block";
  document.getElementById("insis-url-input").value =
    "https://insis.vse.cz/auth/?lang=en";
  document.getElementById("breadcrumb-dynamic").innerHTML =
    "&raquo; <strong>Log in to InSIS</strong>";
  updateSessionUI();

  const usernameInput = document.getElementById("login-username");
  if (usernameInput) usernameInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function hideAllViews() {
  const views = [
    "view-public-home",
    "view-personal-admin",
    "view-student-portal",
    "view-master-thesis",
    "view-coursework-submissions",
    "view-generic-page",
    "view-login",
  ];
  views.forEach((v) => {
    const el = document.getElementById(v);
    if (el) el.style.display = "none";
  });
}

// -----------------------------------------------------------------------------
// 2. URL Navigator & Fast Selector (Public Home + All 195 InSIS URLs)
// -----------------------------------------------------------------------------
async function loadInsisUrls() {
  try {
    const resp = await fetch("/api/insis-links");
    if (resp.ok) {
      allUrlsList = await resp.json();
    } else {
      const resp2 = await fetch("all_urls.json");
      allUrlsList = await resp2.json();
    }
  } catch (e) {
    console.warn("Could not load /api/insis-links:", e);
  }

  populateUrlDropdown();
}

function populateUrlDropdown() {
  const select = document.getElementById("insis-url-select");
  if (!select) return;

  select.innerHTML =
    '<option value="">-- Jump to Public Home or any of 195 InSIS URLs --</option>' +
    '<option value="https://insis.vse.cz/?lang=en">🌐 Public InSIS Homepage (No Login)</option>';

  if (!allUrlsList.length) return;

  const groups = {
    "Personal Administration & Home": [],
    "Student's Portal & Active Study": [],
    "Final Thesis & Errata (§ 47b)": [],
    "Timetable & Calendars": [],
    "Course Catalogue & Syllabi": [],
    "Study Regulations & Vouchers": [],
    "Course Registration & Enrollment": [],
    "Coursework & Continuous Grades": [],
    "Examinations & Retakes": [],
    "Financing, Scholarships & Variable Symbol": [],
    "Document Office & Confirmations": [],
    "Admissions & Applications (Public)": [],
    "People, Departments & Cards (Public)": [],
    "Documentation & Document Server": [],
  };

  allUrlsList.forEach((item) => {
    const u = item.url;
    if (u.includes("/auth/student/zp.pl") || u.includes("temata_zp") || u.includes("szz")) {
      groups["Final Thesis & Errata (§ 47b)"].push(item);
    } else if (u.includes("rozvrhy") || u.includes("harmonogram")) {
      groups["Timetable & Calendars"].push(item);
    } else if (u.includes("/auth/student/studium.pl")) {
      groups["Student's Portal & Active Study"].push(item);
    } else if (u.includes("/auth/student/kontrola_planu.pl") || u.includes("arch_studia")) {
      groups["Study Regulations & Vouchers"].push(item);
    } else if (u.includes("/auth/student/registrace.pl")) {
      groups["Course Registration & Enrollment"].push(item);
    } else if (u.includes("odevzdavarna") || u.includes("zaznamnik") || u.includes("anketa")) {
      groups["Coursework & Continuous Grades"].push(item);
    } else if (u.includes("zkousky")) {
      groups["Examinations & Retakes"].push(item);
    } else if (u.includes("financovani") || u.includes("stipendia")) {
      groups["Financing, Scholarships & Variable Symbol"].push(item);
    } else if (u.includes("uradovna") || u.includes("potvrzeni") || u.includes("uschovna")) {
      groups["Document Office & Confirmations"].push(item);
    } else if (u.includes("/prihlaska") || u.includes("/navratka") || u.includes("/kurzy")) {
      groups["Admissions & Applications (Public)"].push(item);
    } else if (u.includes("/katalog") || u.includes("syllabus")) {
      groups["Course Catalogue & Syllabi"].push(item);
    } else if (u.includes("/lide") || u.includes("/pracoviste") || u.includes("/karty")) {
      groups["People, Departments & Cards (Public)"].push(item);
    } else if (u.includes("/auth/")) {
      groups["Personal Administration & Home"].push(item);
    } else {
      groups["Documentation & Document Server"].push(item);
    }
  });

  for (const [groupName, items] of Object.entries(groups)) {
    if (!items.length) continue;
    const optgroup = document.createElement("optgroup");
    optgroup.label = `${groupName} (${items.length})`;
    items.forEach((item) => {
      const opt = document.createElement("option");
      opt.value = item.url;
      opt.textContent = `${item.access === "AUTHENTICATED" ? "🔒 " : "🌐 "} ${item.title}`;
      optgroup.appendChild(opt);
    });
    select.appendChild(optgroup);
  }
}

function handleSelectUrl(url) {
  if (url) navigateToUrl(url);
}

function handleGoUrl() {
  const url = document.getElementById("insis-url-input").value.trim();
  if (url) navigateToUrl(url);
}

function handleUrlKey(event) {
  if (event.key === "Enter") handleGoUrl();
}

// -----------------------------------------------------------------------------
// 3. Central Page Router (Supports Public Root + 195 InSIS Routes)
// -----------------------------------------------------------------------------
function navigateToUrl(fullUrl) {
  const inputEl = document.getElementById("insis-url-input");
  if (inputEl) inputEl.value = fullUrl;

  const session = getLoginSession();

  // Require login ONLY for /auth/ URLs
  if (fullUrl.includes("/auth/") && !session.loggedIn) {
    sessionStorage.setItem("insis_pending_url", fullUrl);
    showLoginView();
    return;
  }

  const matched = allUrlsList.find((x) => x.url === fullUrl) || {
    title: "Integrated Study Information System",
    url: fullUrl,
    access: fullUrl.includes("/auth/") ? "AUTHENTICATED" : "PUBLIC",
  };

  hideAllViews();

  const cleanPath = fullUrl.replace("https://insis.vse.cz", "").split("?")[0];

  // If user is NOT logged in and attempts to access any public submodules,
  // show the prototype scope notice instead of misleading fake pages!
  if (!session.loggedIn && cleanPath !== "" && cleanPath !== "/" && cleanPath !== "/index.pl") {
    handlePublicOutOfScope(matched.title, fullUrl);
    currentPageKey = "public_home";
    currentPageTitle = "Public Information Portal";
    currentPageUrl = "https://insis.vse.cz/?lang=en";
    document.getElementById("view-public-home").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      "&raquo; <strong>Integrated Study Information System</strong>";
    updateSessionUI();
    return;
  }

  // 0. Public InSIS Root (No Login Required - Screenshots 1 & 2)
  if (cleanPath === "" || cleanPath === "/" || cleanPath === "/index.pl") {
    currentPageKey = "public_home";
    currentPageTitle = "Public Information Portal";
    currentPageUrl = "https://insis.vse.cz/?lang=en";
    document.getElementById("view-public-home").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      "&raquo; <strong>Integrated Study Information System</strong>";
  } else if (cleanPath === "/auth/" || cleanPath === "/auth") {
    currentPageKey = "personal_admin";
    currentPageTitle = "Personal Administration";
    currentPageUrl = fullUrl;
    document.getElementById("view-personal-admin").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      "&raquo; <strong>Personal administration</strong>";
  } else if (cleanPath === "/auth/student/studium.pl") {
    currentPageKey = "student_portal";
    currentPageTitle = "Student's Portal";
    currentPageUrl = fullUrl;
    document.getElementById("view-student-portal").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/student/studium.pl?lang=en\'); return false;">My College</a>';
  } else if (cleanPath === "/auth/student/zp.pl") {
    currentPageKey = "master_thesis";
    currentPageTitle = "Master's Thesis";
    currentPageUrl = fullUrl;
    document.getElementById("view-master-thesis").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/student/studium.pl?lang=en\'); return false;">My College</a> &raquo; <strong>Master\'s thesis</strong>';
  } else if (cleanPath === "/auth/student/odevzdavarna.pl") {
    currentPageKey = "coursework_submissions";
    currentPageTitle = "Coursework Submissions";
    currentPageUrl = fullUrl;
    document.getElementById("view-coursework-submissions").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/student/studium.pl?lang=en\'); return false;">My College</a> &raquo; <strong>Coursework submissions</strong>';
    if (fullUrl.includes("course=4IT445")) {
      setTimeout(() => {
        const c = document.getElementById("vault-4it445");
        if (c) {
          c.scrollIntoView({ behavior: "smooth" });
          c.classList.add("insis-highlight-pulse");
          setTimeout(() => c.classList.remove("insis-highlight-pulse"), 3500);
        }
      }, 100);
    } else if (fullUrl.includes("course=4SA421")) {
      setTimeout(() => {
        const c = document.getElementById("vault-4sa421");
        if (c) {
          c.scrollIntoView({ behavior: "smooth" });
          c.classList.add("insis-highlight-pulse");
          setTimeout(() => c.classList.remove("insis-highlight-pulse"), 3500);
        }
      }, 100);
    }
  } else {
    currentPageKey = cleanPath;
    currentPageTitle = matched.title;
    currentPageUrl = fullUrl;
    renderGenericInsisPage(cleanPath, fullUrl, matched);
  }

  updateSessionUI();

  try {
    const querySuffix = fullUrl.includes("?") ? "?" + fullUrl.split("?")[1] : "";
    const localPath = (cleanPath || "/") + querySuffix;
    window.history.pushState({}, matched.title, localPath);
  } catch (e) {}

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// -----------------------------------------------------------------------------
// 4. Dynamic InSIS Page Content Generator (Public & Authenticated Modules)
// -----------------------------------------------------------------------------
function renderGenericInsisPage(path, fullUrl, meta) {
  const session = getLoginSession();
  const safeUser = escapeHtml(session.userName || "Public Visitor");
  const genericView = document.getElementById("view-generic-page");
  const titleEl = document.getElementById("generic-page-title");
  const subEl = document.getElementById("generic-page-sub");
  const contentEl = document.getElementById("generic-page-content");
  const breadcrumbEl = document.getElementById("breadcrumb-dynamic");

  genericView.style.display = "block";
  titleEl.textContent = meta.title;
  subEl.textContent = `InSIS VŠE • ${
    session.loggedIn
      ? `Authenticated Session (${session.userName})`
      : "Public Portal (No Login Required)"
  }`;

  const homeUrl = session.loggedIn
    ? "https://insis.vse.cz/auth/?lang=en"
    : "https://insis.vse.cz/?lang=en";
  breadcrumbEl.innerHTML = `&raquo; <a href="#" onclick="navigateToUrl('${homeUrl}'); return false;">Integrated Study Information System</a> &raquo; <strong>${escapeHtml(
    meta.title
  )}</strong>`;

  let html = "";

  if (path.includes("navod")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">First Log In to InSIS Instructions (/navod/)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Public guide for newly admitted degree and exchange students before their first login to VŠE systems.
      </p>
      <ol style="font-size:12px; line-height:1.75; margin-left:20px; color:#1e293b;">
        <li><strong>Receive Credentials:</strong> After official enrollment, your <strong>xname</strong> and initial password are sent to your admission email or handed over by your Study Coordinator.</li>
        <li><strong>Change Initial Password:</strong> Log in via <a href="#" onclick="showLoginView(); return false;" style="color:#005596; font-weight:700;">Log in to the Personal administration of InSIS</a> and set a strong university password (also used for Eduroam Wi-Fi, Office 365, and ISKaM dorms).</li>
        <li><strong>Activate Two-Factor Authentication (OTP):</strong> Pair an authenticator app (Microsoft/Google Authenticator) under <em>Information system set-up &rarr; OTP authentication</em>.</li>
        <li><strong>Don't have an account yet?</strong> Prospective applicants can apply via the <a href="#" onclick="navigateToUrl('https://insis.vse.cz/prihlaska/?lang=en'); return false;" style="color:#005596; font-weight:700;">E-application form</a> or ask the <strong>🎓 VŠE Buddy Bot</strong> in the bottom-right corner!</li>
      </ol>
    `;
  } else if (path.includes("plany.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Public Recommended Study Plans (/katalog/plany.pl)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Browse official curriculum structures and ECTS requirements for VŠE degree programmes without logging in.
      </p>
      <table class="insis-study-table">
        <thead><tr><th>Programme Code</th><th>Programme Title</th><th>Faculty</th><th>Degree</th><th>Total Credits</th><th>Language</th></tr></thead>
        <tbody>
          <tr><td><strong>C-ISM-MBI</strong></td><td>Information Systems Management</td><td>FIS</td><td>Master (Ing.)</td><td>120 ECTS</td><td>English</td></tr>
          <tr><td><strong>C-EDA</strong></td><td>Economic Data Analysis</td><td>FIS</td><td>Bachelor (Bc.)</td><td>180 ECTS</td><td>English</td></tr>
          <tr><td><strong>C-MIFA</strong></td><td>Finance and Accounting</td><td>FFÚ</td><td>Master (Ing.)</td><td>120 ECTS</td><td>English</td></tr>
          <tr><td><strong>C-IDS</strong></td><td>International and Diplomatic Studies</td><td>FMV</td><td>Master (Ing.)</td><td>120 ECTS</td><td>English</td></tr>
          <tr><td><strong>C-BBA</strong></td><td>Bachelor of Business Administration</td><td>FPH</td><td>Bachelor (Bc.)</td><td>180 ECTS</td><td>English</td></tr>
        </tbody>
      </table>
    `;
  } else if (path.includes("kontrola_planu.pl")) {
    html = `
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #e2e8f0; padding-bottom:8px; margin-bottom:14px;">
        <h3 style="font-size:16px; color:#004b87;">Check of Study Plan &amp; Credit Vouchers (${safeUser})</h3>
        <span style="background:#e6f4ea; color:#137333; padding:3px 10px; border-radius:12px; font-weight:700;">Active Enrollment</span>
      </div>
      <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:20px;">
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px; text-align:center;">
          <div style="font-size:11px; color:#64748b; text-transform:uppercase; font-weight:700;">Initial Voucher Budget</div>
          <div style="font-size:24px; font-weight:800; color:#004b87;">144 Vouchers</div>
          <div style="font-size:11px; color:#16a34a;">Master's (120 ECTS + 20% margin)</div>
        </div>
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px; text-align:center;">
          <div style="font-size:11px; color:#64748b; text-transform:uppercase; font-weight:700;">Remaining Balance</div>
          <div style="font-size:24px; font-weight:800; color:#16a34a;">120 Vouchers</div>
          <div style="font-size:11px; color:#64748b;">24 used in WS 2026/2027</div>
        </div>
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px; text-align:center;">
          <div style="font-size:11px; color:#64748b; text-transform:uppercase; font-weight:700;">Current Study Average</div>
          <div style="font-size:24px; font-weight:800; color:#004b87;">1.42</div>
          <div style="font-size:11px; color:#64748b;">Scale: 1 (Výborně) to 4 (Fail)</div>
        </div>
      </div>
      <p style="font-size:12px; color:#475569; line-height:1.6;">
        <strong>Study Regulation Rules:</strong> You must earn at least 9 ECTS credits in your first semester, or 20 ECTS across any two consecutive semesters to maintain active enrollment.
      </p>
    `;
  } else if (path.includes("rozvrhy")) {
    html = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <h3 style="font-size:16px; color:#004b87;">Timetables &amp; Lecture Rooms (Winter Semester 2026/2027)</h3>
        ${
          session.loggedIn
            ? '<button onclick="alert(\'iCal subscription feed link copied!\')" style="background:#005596; color:white; border:none; padding:6px 12px; border-radius:4px; font-weight:700; cursor:pointer;">🔗 iCal Feed Export</button>'
            : '<span style="font-size:11px; color:#0369a1; font-weight:700;">🌐 Public Timetable View</span>'
        }
      </div>
      <table class="insis-study-table">
        <thead>
          <tr><th>Day</th><th>Time</th><th>Course</th><th>Type</th><th>Room</th><th>Campus Building</th><th>Teacher</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>Monday</strong></td><td>09:15 &ndash; 12:30</td><td>4IT445 Advanced Data Analytics</td><td>Lecture + Lab</td><td><strong>RB 101</strong></td><td>Žižkov, Rajská budova (1st floor)</td><td>Doc. Kovář</td></tr>
          <tr><td><strong>Tuesday</strong></td><td>14:30 &ndash; 17:45</td><td>4SA421 Info Systems Management</td><td>Seminar</td><td><strong>SB 204</strong></td><td>Žižkov, Stará budova (2nd floor)</td><td>Prof. Voříšek</td></tr>
          <tr><td><strong>Thursday</strong></td><td>11:00 &ndash; 14:15</td><td>2SE411 European Integration</td><td>Lecture</td><td><strong>NB 403</strong></td><td>Žižkov, Nová budova (4th floor)</td><td>Doc. Dvořák</td></tr>
          <tr><td><strong>Friday</strong></td><td>09:15 &ndash; 10:45</td><td>1PE401 Business Ethics</td><td>Lecture</td><td><strong>JM 310</strong></td><td>Jižní Město (3rd floor)</td><td>Mgr. Horáková</td></tr>
        </tbody>
      </table>
    `;
  } else if (path.includes("szz.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">State Final Examinations &amp; Defense (Státní závěrečné zkoušky a obhajoby)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Student: <strong>${safeUser}</strong> • Study: <strong>FIS C-ISM-MBI pres</strong> • Academic Year: 2026/2027.
      </p>
      <table class="insis-study-table">
        <thead><tr><th>Exam Part</th><th>Supervisor</th><th>Opponent</th><th>Defense Slot</th><th>State</th></tr></thead>
        <tbody>
          <tr>
            <td><strong>Diploma Thesis Defense</strong></td>
            <td>Ing. Pavel Sládek, Ph.D.</td>
            <td>Doc. Ing. O. Černý, Ph.D.</td>
            <td>June 2027 (Scheduled upon thesis locking)</td>
            <td><span style="color:#d97706; font-weight:700;">Awaiting Thesis Lock</span></td>
          </tr>
          <tr>
            <td><strong>State Exam in Informatics Management</strong></td>
            <td>Exam Board FIS 01</td>
            <td>&ndash;</td>
            <td>June 2027 Regular Period</td>
            <td><span style="color:#2563eb; font-weight:700;">Prerequisites in Progress</span></td>
          </tr>
        </tbody>
      </table>
      <div style="margin-top:14px;">
        <button onclick="navigateToUrl('https://insis.vse.cz/auth/student/zp.pl?lang=en')" style="background:#005596; color:white; border:none; padding:8px 14px; border-radius:4px; font-weight:700; cursor:pointer;">Go to Master's Thesis &amp; Errata Submission ➔</button>
      </div>
    `;
  } else if (path.includes("financovani")) {
    if (session.loggedIn) {
      html = `
        <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Study Financing &amp; Personal Payments (${safeUser})</h3>
        <table class="thesis-info-table" style="margin-bottom:18px;">
          <tr><td class="label-cell">Bank Account (CZK):</td><td class="value-cell"><strong>19-2696090207 / 0100</strong> (Komerční banka)</td></tr>
          <tr><td class="label-cell">IBAN:</td><td class="value-cell"><code>CZ04 0100 0000 1926 9609 0207</code></td></tr>
          <tr><td class="label-cell">Your Variable Symbol (VS):</td><td class="value-cell"><strong style="color:#005596; font-size:15px;">84920194</strong> <em>(Mandatory to identify your student account!)</em></td></tr>
          <tr><td class="label-cell">Payment Status:</td><td class="value-cell"><span style="color:#16a34a; font-weight:700;">All Tuition &amp; Obligations Cleared (0.00 CZK balance)</span></td></tr>
        </table>
        <button onclick="alert('Card payment gateway 3DS Secure: 0.00 CZK outstanding')" style="background:#005596; color:white; border:none; padding:8px 14px; border-radius:4px; font-weight:700; cursor:pointer;">💳 Open Card Payment Gateway</button>
      `;
    } else {
      html = `
        <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Study Financing, Tuition Fees &amp; Scholarships (Public Information)</h3>
        <p style="font-size:12px; color:#475569; margin-bottom:14px;">
          General financing rules for international English-taught Bachelor's and Master's programmes at VŠE Prague.
        </p>
        <ul style="font-size:12px; line-height:1.75; margin-left:20px; margin-bottom:14px;">
          <li><strong>English Degree Tuition Fee:</strong> Standard fee is <strong>EUR 2,500 per semester</strong> (EUR 5,000 / academic year).</li>
          <li><strong>Application Fee:</strong> EUR 50 electronic application fee paid during E-application submission.</li>
          <li><strong>Scholarships:</strong> Merit scholarships (GPA &le; 1.50) and quarterly accommodation grants are available to eligible full-time students.</li>
        </ul>
        <button onclick="showLoginView()" style="background:#005596; color:white; border:none; padding:7px 14px; border-radius:4px; font-weight:700; cursor:pointer;">🔒 Log in to view your personal Variable Symbol</button>
      `;
    }
  } else if (path.includes("potvrzeni.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Electronic Confirmation of Study (Potvrzení o studiu)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Generate an official digitally signed PDF document bearing the qualified electronic stamp of VŠE. Accepted by Foreign Police, OAMP MVČR, transit authorities (PID / Lítačka), banks, and embassies.
      </p>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:16px; margin-bottom:14px;">
        <strong>Student:</strong> ${safeUser} (FIS ISM Master)<br>
        <strong>Academic Year:</strong> 2026/2027 &bull; Winter Semester<br>
        <strong>Electronic Seal:</strong> Qualified Electronic Timestamp &bull; Verification Token #CONF-84920194
      </div>
      <button onclick="downloadConfirmationPdf()" style="background:#16a34a; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:700; cursor:pointer;">📥 Download Signed Confirmation of Study (PDF)</button>
    `;
  } else if (path.includes("harmonogram.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Academic Year Schedule 2026/2027</h3>
      <table class="insis-study-table">
        <thead><tr><th>Milestone / Period</th><th>Dates</th><th>Details</th></tr></thead>
        <tbody>
          <tr><td><strong>Winter Semester Teaching</strong></td><td>Sep 21, 2026 &ndash; Dec 18, 2026</td><td>13 weeks of lectures and seminars</td></tr>
          <tr><td><strong>Winter Exam Period</strong></td><td>Jan 04, 2027 &ndash; Feb 05, 2027</td><td>5 weeks of regular and retake examination slots</td></tr>
          <tr><td><strong>Summer Course Registration</strong></td><td>Jan 15, 2027 &ndash; Jan 26, 2027</td><td>Round 1 course registration for SS 2026/2027</td></tr>
          <tr><td><strong>Summer Semester Teaching</strong></td><td>Feb 15, 2027 &ndash; May 14, 2027</td><td>13 weeks of teaching</td></tr>
          <tr><td><strong>Summer Exam Period &amp; SZZ</strong></td><td>May 17, 2027 &ndash; Jun 25, 2027</td><td>Exam period, defense and state exams</td></tr>
        </tbody>
      </table>
    `;
  } else if (path.includes("katalog") || path.includes("kurzy")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Public Course Catalogue &amp; Syllabi (/katalog/)</h3>
      <div style="display:flex; gap:10px; margin-bottom:15px;">
        <input type="text" id="course-filter-input" placeholder="Search by course code (e.g. 4IT, 4SA) or title..." style="flex:1; padding:8px 10px; border:1px solid #cbd5e1; border-radius:4px; font-size:13px;" onkeyup="filterCourseList()">
      </div>
      <table class="insis-study-table" id="dyn-courses-table">
        <thead><tr><th>Code</th><th>Course Name</th><th>Faculty</th><th>ECTS</th><th>Language</th><th>Semester</th></tr></thead>
        <tbody>
          <tr><td><strong>4IT445</strong></td><td>Advanced Data Analytics</td><td>Faculty of Informatics and Statistics (FIS)</td><td>6</td><td>English</td><td>WS</td></tr>
          <tr><td><strong>4SA421</strong></td><td>Information Systems Management</td><td>Faculty of Informatics and Statistics (FIS)</td><td>6</td><td>English</td><td>WS</td></tr>
          <tr><td><strong>2SE411</strong></td><td>European Economic Integration</td><td>Faculty of International Relations (FMV)</td><td>6</td><td>English</td><td>WS/SS</td></tr>
          <tr><td><strong>1PE401</strong></td><td>Business Ethics &amp; Governance</td><td>Faculty of Business Administration (FBA)</td><td>6</td><td>English</td><td>WS</td></tr>
          <tr><td><strong>4IT101</strong></td><td>Introduction to Python Programming</td><td>Faculty of Informatics and Statistics (FIS)</td><td>3</td><td>English</td><td>WS/SS</td></tr>
        </tbody>
      </table>
    `;
  } else if (path.includes("prihlaska") || path.includes("navratka")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Electronic Application to Study at VŠE (/prihlaska/) &ndash; No Student Account Required</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Prospective international applicants can submit a new admission application here without an existing VŠE InSIS login.
      </p>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:16px; margin-bottom:14px;">
        <h4 style="font-size:13px; color:#004b87; margin-bottom:6px;">Degree Programmes Offered in English:</h4>
        <ul style="font-size:12px; line-height:1.7; margin-left:20px;">
          <li>Master in Information Systems Management (ISM) &bull; Faculty of Informatics and Statistics</li>
          <li>Master in Finance and Accounting (MIFA) &bull; Faculty of Finance and Accounting</li>
          <li>International Management (CEMS / MIM) &bull; Faculty of Business Administration</li>
          <li>International and Diplomatic Studies (IDS) &bull; Faculty of International Relations</li>
        </ul>
      </div>
      <button onclick="alert('New E-Application Wizard started! Application PIN generated for applicant access.')" style="background:#005596; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:700; cursor:pointer;">📝 Start New E-Application (No Login Needed)</button>
    `;
  } else {
    html = `
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:18px;">
        <h4 style="font-size:14px; color:#004b87; margin-bottom:8px;">${escapeHtml(meta.title)}</h4>
        <p style="font-size:12px; color:#475569; line-height:1.6; margin-bottom:12px;">
          Official InSIS service endpoint: <code>${escapeHtml(meta.url)}</code><br>
          Access Level: <strong>${escapeHtml(meta.access)}</strong> &bull; User Context: <strong>${
      session.loggedIn
        ? safeUser + " (Authenticated)"
        : "Public Visitor (Not Logged In)"
    }</strong>
        </p>
        <div style="font-size:12px; color:#334155; line-height:1.6;">
          Need help with this page, visas, dormitories, or VŠE policies? Click <strong>🎓 VŠE Buddy Bot</strong> in the bottom-right corner!
        </div>
      </div>
    `;
  }

  contentEl.innerHTML = html;
}

function filterCourseList() {
  const query = document.getElementById("course-filter-input").value.toLowerCase();
  const table = document.getElementById("dyn-courses-table");
  if (!table) return;
  const rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
  for (let i = 0; i < rows.length; i++) {
    const text = rows[i].textContent.toLowerCase();
    rows[i].style.display = text.includes(query) ? "" : "none";
  }
}

function downloadConfirmationPdf() {
  const session = getLoginSession();
  const studentName = session.userName || "Authenticated Student";
  const fileSafeName = studentName.replace(/[^a-zA-Z0-9_-]+/g, "_");
  const text = `
PRAGUE UNIVERSITY OF ECONOMICS AND BUSINESS (VŠE)
FACULTY OF INFORMATICS AND STATISTICS (FIS)
------------------------------------------------------------------------
ELECTRONIC CONFIRMATION OF STUDY (POTVRZENÍ O STUDIU)
Student: ${studentName}
Programme: Information Systems Management (ISM) - Master
Academic Year: 2026/2027 (Winter Semester)
Status: Active Enrolled Student in Good Academic Standing.
Digitally sealed with Qualified Electronic Stamp under Act No. 297/2016 Coll.
Date of Issue: ${new Date().toISOString()}
Verification: https://insis.vse.cz/overeni/?token=84920194-CONF
------------------------------------------------------------------------
  `;
  const blob = new Blob([text], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `Confirmation_of_Study_${fileSafeName}_VSE.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// -----------------------------------------------------------------------------
// 5. Modals & Errata Handlers (§ 47b)
// -----------------------------------------------------------------------------
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.style.display = "flex";
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.style.display = "none";
}

let currentOutOfScopeTopic = "Selected Module";
let currentOutOfScopeUrl = "https://insis.vse.cz/?lang=en";

function handlePublicOutOfScope(title, url) {
  currentOutOfScopeTopic = (title || "Selected InSIS Module").trim();
  currentOutOfScopeUrl = url || "https://insis.vse.cz/?lang=en";
  const titleEl = document.getElementById("out-of-scope-feature-title");
  if (titleEl) {
    titleEl.textContent = `"${currentOutOfScopeTopic}" is outside research scope`;
  }
  const linkEl = document.getElementById("btn-out-of-scope-real-link");
  if (linkEl) {
    linkEl.href = currentOutOfScopeUrl;
  }
  openModal("out-of-scope-modal");
}

function setupPublicLinkInterceptors() {
  const container = document.getElementById("view-public-home");
  if (!container) return;
  const links = container.querySelectorAll("a");
  links.forEach((a) => {
    // Keep primary login link completely functional
    if (a.id === "pub-link-login") return;
    const title = a.textContent.trim();
    const onclickStr = a.getAttribute("onclick") || "";
    let url = "https://insis.vse.cz/?lang=en";
    const m = onclickStr.match(/navigateToUrl\('([^']+)'\)/);
    if (m) url = m[1];

    a.onclick = function (e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      handlePublicOutOfScope(title, url);
      return false;
    };
  });
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
    bannerText.innerHTML =
      "<strong>Thesis entered and locked (Odevzdáno).</strong> File registered in InSIS archive. Theses.cz protocol: 2.1% similarity.";
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
  const session = getLoginSession();
  const safeSlug = (session.userName || "Student").replace(/[^a-zA-Z0-9_-]+/g, "_");
  const picker = document.getElementById("errata-file-picker");
  const fileName =
    picker && picker.files.length > 0
      ? picker.files[0].name
      : `Errata_Thesis_Corrections_${safeSlug}.pdf`;

  closeModal("errata-modal");

  const badgeErrata = document.getElementById("badge-errata");
  if (badgeErrata) {
    badgeErrata.className = "status-badge-above badge-green-check";
    badgeErrata.textContent = "✓";
  }

  const fnCode = document.getElementById("errata-uploaded-filename");
  if (fnCode) fnCode.textContent = fileName;

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

function openSearchModal() {
  const q = prompt("Thematic search across InSIS (e.g. apply, courses, thesis, credits, timetable):");
  if (q) {
    const ql = q.toLowerCase();
    const session = getLoginSession();
    if (ql.includes("apply") || ql.includes("admission")) {
      navigateToUrl("https://insis.vse.cz/prihlaska/?lang=en");
    } else if ((ql.includes("errata") || ql.includes("thesis")) && session.loggedIn) {
      navigateToUrl("https://insis.vse.cz/auth/student/zp.pl?lang=en");
    } else if ((ql.includes("credit") || ql.includes("voucher")) && session.loggedIn) {
      navigateToUrl("https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en");
    } else if (ql.includes("rozvrh") || ql.includes("timetable")) {
      navigateToUrl("https://insis.vse.cz/katalog/rozvrhy.pl?lang=en");
    } else {
      navigateToUrl("https://insis.vse.cz/katalog/?lang=en");
    }
  }
}

function openHelpModal() {
  toggleBotDrawer(true);
}

// -----------------------------------------------------------------------------
// 6. Floating VŠE Buddy Bot (No-Login Public Mode + Logged-In Co-Pilot)
// -----------------------------------------------------------------------------
function togglePersonalisedMode(checked) {
  isPersonalisedEnabled = Boolean(checked);
  localStorage.setItem("insis_bot_personalised", String(isPersonalisedEnabled));
}

function updateBotContextUI() {
  const session = getLoginSession();
  const statusText = document.getElementById("bot-status-text");
  const statusRight = document.getElementById("bot-status-right");
  const chipsBox = document.getElementById("bot-quick-chips");

  if (!statusText || !statusRight) return;

  if (!session.loggedIn) {
    statusText.textContent = "Demo Prototype • Guest Access";
    statusRight.innerHTML =
      '<a class="bot-status-link" onclick="showLoginView()">Log in ➔</a>';

    if (chipsBox) {
      if (chatHistory.length > 0) {
        chipsBox.innerHTML = `
          <button class="mini-chip" onclick="showInteractiveChecklist()">📋 Arrival Checklist</button>
          <button class="mini-chip" onclick="sendBotPrompt('How to find accomodation')">🏢 Dorms &amp; Housing</button>
        `;
      } else {
        chipsBox.innerHTML = "";
      }
    }
  } else {
    statusText.textContent = `${session.userName} • Demo Prototype`;
    statusRight.innerHTML = `
      <label class="bot-gdpr-toggle" title="GDPR Opt-In: Allow bot to use your credits, vouchers & thesis status">
        <input type="checkbox" ${isPersonalisedEnabled ? "checked" : ""} onchange="togglePersonalisedMode(this.checked)">
        Personalised
      </label>
    `;

    if (chipsBox) {
      if (chatHistory.length > 0) {
        if (currentPageKey === "master_thesis") {
          chipsBox.innerHTML = `
            <button class="mini-chip" onclick="sendBotPrompt('What do the 3 red X icons on this page mean for my thesis?')">❓ 3 Red Xs</button>
            <button class="mini-chip" onclick="sendBotPrompt('How do I submit errata for my Master\\'s thesis on this page?')">📝 Submit Errata</button>
          `;
        } else {
          chipsBox.innerHTML = `
            <button class="mini-chip" onclick="sendBotPrompt('how many credit vouchers i have left')">📊 My Vouchers</button>
            <button class="mini-chip" onclick="sendBotPrompt('Where is the nearest washroom in Rajská Building?')">🚽 Nearest WC</button>
          `;
        }
      } else {
        chipsBox.innerHTML = "";
      }
    }
  }
}

function performBotReset() {
  resetBotConversationForSession();
  const inputEl = document.getElementById("bot-input-field");
  if (inputEl) {
    inputEl.value = "";
    inputEl.focus();
  }
  toggleTopicsPopover(false);
}

function toggleTopicsPopover(forceState) {
  const popover = document.getElementById("bot-topics-popover");
  if (!popover) return;
  if (typeof forceState === "boolean") {
    if (forceState) popover.classList.remove("hidden");
    else popover.classList.add("hidden");
  } else {
    popover.classList.toggle("hidden");
  }
  if (!popover.classList.contains("hidden")) {
    renderPopoverTopics();
  }
}

function renderPopoverTopics() {
  const list = document.getElementById("popover-topics-list");
  if (!list) return;
  const session = getLoginSession();
  let items = [];
  if (!session.loggedIn) {
    items = [
      { icon: "🛂", text: "Foreign Police 3-day registration rule", prompt: "What are the visa and 3-day Foreign Police registration rules for international students?" },
      { icon: "🏢", text: "How to find accommodation & dorms (ISKaM)", prompt: "How do I find accommodation in VŠE dormitories or private flats in Prague?" },
      { icon: "📝", text: "How does the E-application form work?", prompt: "How do admissions and the E-application work at VŠE?" },
      { icon: "📚", text: "Where can I view the course catalogue?", prompt: "Where can I view the course catalogue and syllabi?" },
      { icon: "📋", text: "Open Interactive Arrival Checklist", action: "showInteractiveChecklist" }
    ];
  } else {
    items = [
      { icon: "📊", text: "How many credit vouchers I have left", prompt: "how many credit vouchers i have left" },
      { icon: "📗", text: "What do the 3 red Xs mean on Thesis page?", prompt: "What do the 3 red Xs mean on my Master's Thesis page and how do I submit errata?" },
      { icon: "📄", text: "How to get Confirmation of Study in InSIS", prompt: "Where do I download electronic confirmation of study?" },
      { icon: "🏢", text: "How to find accommodation & dormitory ISKaM", prompt: "How do I find accommodation in VŠE dormitories or private flats in Prague?" },
      { icon: "🚽", text: "Find nearest washroom in Rajská Building", prompt: "Where is the nearest washroom in Rajská Building?" },
      { icon: "📋", text: "Open Interactive Arrival Checklist", action: "showInteractiveChecklist" }
    ];
  }
  list.innerHTML = items.map((item) => {
    if (item.action === "showInteractiveChecklist") {
      return `<div class="popover-item" onclick="toggleTopicsPopover(false); showInteractiveChecklist();"><span>${item.icon}</span> <span>${escapeHtml(item.text)}</span></div>`;
    }
    const escapedPrompt = escapeHtml(item.prompt).replace(/'/g, "\\'");
    return `<div class="popover-item" onclick="toggleTopicsPopover(false); sendBotPrompt('${escapedPrompt}');"><span>${item.icon}</span> <span>${escapeHtml(item.text)}</span></div>`;
  }).join("");
}

function toggleBotDrawer(forceOpen) {
  const drawer = document.getElementById("bot-drawer");
  if (forceOpen === true) {
    drawer.classList.remove("hidden");
  } else {
    drawer.classList.toggle("hidden");
  }
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
  toggleBotDrawer(true);
  document.getElementById("bot-input-field").value = text;
  submitBotMessage();
}

function highlightElementOnPage(elementIds) {
  document.querySelectorAll(".insis-highlight-pulse").forEach((el) => {
    el.classList.remove("insis-highlight-pulse");
  });

  const ids = Array.isArray(elementIds) ? elementIds : [elementIds];
  let firstEl = null;
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add("insis-highlight-pulse");
      if (!firstEl) firstEl = el;
      setTimeout(() => el.classList.remove("insis-highlight-pulse"), 6000);
    }
  });

  if (firstEl) {
    firstEl.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

async function showInteractiveChecklist(
  origin = "non_eu",
  housing = "dorm",
  stage = "pre_arrival",
  existingCard = null
) {
  toggleBotDrawer(true);
  const container = document.getElementById("bot-messages-area");
  let card = existingCard;
  if (!card) {
    card = document.createElement("div");
    card.className = "bot-checklist-card";
    container.appendChild(card);
  }
  card.innerHTML = "<em>Loading tailored checklist...</em>";

  try {
    const url = `/api/vse/checklist?origin=${encodeURIComponent(
      origin
    )}&housing=${encodeURIComponent(housing)}&stage=${encodeURIComponent(stage)}`;
    const resp = await fetch(url);
    const data = await resp.json();
    const items = data.items || [];

    const rowsHtml = items
      .map(
        (item) => `
        <div class="bot-checklist-item">
          <label>
            <input type="checkbox">
            <span>${escapeHtml(item.task)}</span>
          </label>
          <button class="bot-checklist-ask" data-prompt="${escapeHtml(
            item.prompt
          )}" onclick="sendBotPrompt(this.dataset.prompt)">Ask ➔</button>
        </div>
      `
      )
      .join("");

    card.innerHTML = `
      <div style="font-weight:700; color:#004b87; display:flex; justify-content:space-between; align-items:center;">
        <span>📋 International Student Checklist</span>
        <span style="font-size:10px; color:#0369a1;">Works without login</span>
      </div>
      <div class="bot-checklist-controls">
        <select onchange="showInteractiveChecklist(this.value, '${housing}', '${stage}', this.closest('.bot-checklist-card'))">
          <option value="non_eu" ${origin === "non_eu" ? "selected" : ""}>🌏 Non-EU</option>
          <option value="eu" ${origin === "eu" ? "selected" : ""}>🇪🇺 EU / EEA</option>
        </select>
        <select onchange="showInteractiveChecklist('${origin}', this.value, '${stage}', this.closest('.bot-checklist-card'))">
          <option value="dorm" ${housing === "dorm" ? "selected" : ""}>🏢 VŠE Dorm</option>
          <option value="flat" ${housing === "flat" ? "selected" : ""}>🏠 Private Flat</option>
        </select>
        <select onchange="showInteractiveChecklist('${origin}', '${housing}', this.value, this.closest('.bot-checklist-card'))">
          <option value="pre_arrival" ${stage === "pre_arrival" ? "selected" : ""}>✈️ Before Arrival</option>
          <option value="arrival" ${stage === "arrival" ? "selected" : ""}>🛬 First Week</option>
          <option value="studies" ${stage === "studies" ? "selected" : ""}>🎓 Studies &amp; Thesis</option>
        </select>
      </div>
      <div>${rowsHtml}</div>
    `;
  } catch (e) {
    card.innerHTML = "Could not load checklist right now.";
  }

  container.scrollTop = container.scrollHeight;
}

async function submitBotMessage() {
  const inputEl = document.getElementById("bot-input-field");
  const query = inputEl.value.trim();
  if (!query) return;

  inputEl.value = "";
  toggleTopicsPopover(false);

  // If initial hero container is present, clean it up for conversation flow
  const heroEl = document.querySelector(".bot-hero-container");
  if (heroEl) heroEl.remove();

  appendBotBubble("user", query);
  chatHistory.push({ role: "user", content: query });

  const session = getLoginSession();
  const userContext = {
    logged_in: session.loggedIn,
    personalised: session.loggedIn ? isPersonalisedEnabled : false,
    user_name: session.loggedIn ? session.userName : "Guest",
    page_key: currentPageKey,
    page_title: currentPageTitle,
    page_url: currentPageUrl,
  };

  const loadingBubble = appendBotBubble(
    "assistant",
    '<div class="typing-dots"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>'
  );

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: query,
        history: chatHistory,
        user_context: userContext,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      loadingBubble.innerHTML = formatBotMarkdown(data.answer);
      chatHistory.push({ role: "assistant", content: data.answer });
      handleContextualPageActions(query, session.loggedIn);
    } else {
      throw new Error("API call failed");
    }
  } catch (err) {
    const fallback = getContextualFallback(query, session.loggedIn);
    loadingBubble.innerHTML = formatBotMarkdown(fallback);
    chatHistory.push({ role: "assistant", content: fallback });
    handleContextualPageActions(query, session.loggedIn);
  }

  updateBotContextUI();

  const container = document.getElementById("bot-messages-area");
  container.scrollTop = container.scrollHeight;
}

function handleContextualPageActions(query, loggedIn) {
  const ql = query.toLowerCase();

  // 1. NO-LOGIN PUBLIC USER ACTIONS (Highlights & opens PUBLIC InSIS items without forcing login!)
  if (!loggedIn) {
    if (
      ql.includes("apply") ||
      ql.includes("admission") ||
      ql.includes("e-application") ||
      ql.includes("prihlaska")
    ) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-eapp", "pub-link-preenroll"]);
      }
      appendContextLink("📝 Open Public E-Application Form (/prihlaska/)", () => {
        navigateToUrl("https://insis.vse.cz/prihlaska/?lang=en");
      });
    } else if (
      ql.includes("course") ||
      ql.includes("catalogue") ||
      ql.includes("study plan") ||
      ql.includes("syllabus")
    ) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-catalogue", "pub-link-plans"]);
      }
      appendContextLink("📚 Open Public Course Catalogue (/katalog/)", () => {
        navigateToUrl("https://insis.vse.cz/katalog/?lang=en");
      });
    } else if (ql.includes("timetable") || ql.includes("schedule") || ql.includes("calendar")) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-schedule", "pub-link-timetables"]);
      }
      appendContextLink("📅 Open Public Academic Schedule", () => {
        navigateToUrl("https://insis.vse.cz/harmonogram/harmonogram.pl?lang=en");
      });
    } else if (ql.includes("first log") || ql.includes("password") || ql.includes("otp") || ql.includes("log in")) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-first-login", "pub-link-login"]);
      }
      appendContextLink("🔑 Open First Log In Instructions (/navod/)", () => {
        navigateToUrl("https://insis.vse.cz/navod/?lang=en");
      });
    } else if (ql.includes("visa") || ql.includes("police") || ql.includes("dorm") || ql.includes("arrive")) {
      appendContextLink("📋 Open Tailored Pre-Arrival Checklist", () => {
        showInteractiveChecklist();
      });
    }
    return;
  }

  // 2. LOGGED-IN STUDENT ACTIONS
  if (ql.includes("red x") || ql.includes("3 red")) {
    if (currentPageKey === "master_thesis") {
      highlightElementOnPage([
        "action-add-info",
        "action-upload-thesis",
        "action-submit-thesis",
      ]);
    }
  } else if (ql.includes("errata")) {
    if (currentPageKey === "master_thesis") {
      highlightElementOnPage("action-errata");
    } else {
      appendContextLink("📜 Open Master's Thesis & Errata Page", () => {
        navigateToUrl("https://insis.vse.cz/auth/student/zp.pl?lang=en");
      });
    }
  } else if (ql.includes("thesis")) {
    if (currentPageKey !== "master_thesis") {
      appendContextLink("📗 Open Master's Thesis in InSIS", () => {
        navigateToUrl("https://insis.vse.cz/auth/student/zp.pl?lang=en");
      });
    }
  } else if (ql.includes("voucher") || ql.includes("credit")) {
    appendContextLink("📊 Open Credit Voucher Check (120/144)", () => {
      navigateToUrl("https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en");
    });
  } else if (ql.includes("confirm") && ql.includes("study")) {
    appendContextLink("📄 Open Electronic Confirmation of Study", () => {
      navigateToUrl("https://insis.vse.cz/auth/student/potvrzeni.pl?lang=en");
    });
  }
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
  btn.style.marginTop = "2px";
  btn.style.alignSelf = "flex-start";
  btn.innerHTML = label;
  btn.onclick = actionFn;
  container.appendChild(btn);
  container.scrollTop = container.scrollHeight;
}

function formatBotMarkdown(text) {
  if (!text) return "";

  let formatted = text;
  let sourcesHtml = "";

  // 1. Extract source citations and transform them into sleek badge pills
  const sourcesMatch = formatted.match(/(?:\n|^)\*\*Sources:\*\*\s*([\s\S]*)$/i);
  if (sourcesMatch) {
    formatted = formatted.substring(0, sourcesMatch.index).trim();
    const sourcesRaw = sourcesMatch[1].trim();
    const sourceLinks = [];
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
    let m;
    while ((m = linkRegex.exec(sourcesRaw)) !== null) {
      const label = escapeHtml(m[1]);
      const url = m[2];
      const safeUrl = url.replace(/'/g, "\\'");
      if (url.startsWith("https://insis.vse.cz")) {
        sourceLinks.push(`<a class="source-pill-link insis-src" href="${url}" onclick="navigateToUrl('${safeUrl}'); return false;"><span class="src-icon">🏛️</span><span>${label}</span></a>`);
      } else {
        sourceLinks.push(`<a class="source-pill-link ext-src" href="${url}" target="_blank" rel="noopener noreferrer"><span class="src-icon">🌐</span><span>${label}</span></a>`);
      }
    }
    if (sourceLinks.length > 0) {
      sourcesHtml = `<div class="bot-sources-list"><span class="bot-sources-header">Verified Sources & References:</span>${sourceLinks.join("")}</div>`;
    }
  }

  // 2. Format bulleted/colon labeled URLs (e.g., "* InSIS Public Portal (English): https://insis.vse.cz/?lang=en [2]")
  // Matches: [optional bullet] [optional **] Label [optional **]: URL [optional cite]
  formatted = formatted.replace(
    /(^|\n)([•\*\-]?\s*)(?:\*\*)?([^\n\:\*\[\(\)]+?)(?:\*\*)?:\s*(https?:\/\/[^\s<\]\)\<\>]+)(\s*\[[\d\s,]+\])?/g,
    (match, linePre, bullet, rawLabel, rawUrl, cite) => {
      const label = rawLabel.trim();
      const safeUrl = rawUrl.replace(/'/g, "\\'");
      const isInsis = rawUrl.startsWith("https://insis.vse.cz");
      const icon = isInsis ? "🏛️" : (rawUrl.includes("o365") || rawUrl.includes("microsoft") ? "💼" : (rawUrl.includes("mvcr") || rawUrl.includes("frs") ? "🛂" : (rawUrl.includes("map") ? "📍" : "🌐")));
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      const citeHtml = cite ? ` <span class="bot-cite-ref">${cite.trim()}</span>` : "";

      const bulletPrefix = bullet.trim() ? `${bullet}` : "• ";
      return `${linePre}${bulletPrefix}<a class="${pillClass}" href="${rawUrl}" ${clickAttr} title="${escapeHtml(label)}"><span class="link-icon">${icon}</span><span class="link-label">${escapeHtml(label)}</span><span class="link-arrow">↗</span></a>${citeHtml}`;
    }
  );

  // 3. Format standard markdown links [Label](url)
  formatted = formatted.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (match, label, url) => {
      const isAction = label.includes("Go to") || label.includes("📂") || label.includes("🎓") || label.includes("📑") || label.includes("Jump to") || label.includes("View Full") || label.includes("Submission");
      const safeUrl = url.replace(/'/g, "\\'");
      const isInsis = url.startsWith("https://insis.vse.cz");
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;

      if (isAction) {
        return `<a class="bot-action-button" href="${url}" ${clickAttr}>${label}</a>`;
      }
      const icon = isInsis ? "🏛️" : (url.includes("o365") || url.includes("microsoft") ? "💼" : (url.includes("mvcr") || url.includes("frs") ? "🛂" : (url.includes("map") ? "📍" : "🌐")));
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      return `<a class="${pillClass}" href="${url}" ${clickAttr} title="${escapeHtml(label)}"><span class="link-icon">${icon}</span><span class="link-label">${label}</span><span class="link-arrow">↗</span></a>`;
    }
  );

  // 4. Format any remaining bare URLs (not inside an href attribute)
  formatted = formatted.replace(
    /(?<!href=["'])(https?:\/\/[^\s<\]\)\<\>]+)/g,
    (match, url) => {
      const safeUrl = url.replace(/'/g, "\\'");
      const isInsis = url.startsWith("https://insis.vse.cz");
      const icon = isInsis ? "🏛️" : "🌐";
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      
      let displayLabel = url.replace(/^https?:\/\/(?:www\.)?/, "");
      if (displayLabel.length > 30) {
        displayLabel = displayLabel.substring(0, 28) + "…";
      }
      return `<a class="${pillClass}" href="${url}" ${clickAttr}><span class="link-icon">${icon}</span><span class="link-label">${escapeHtml(displayLabel)}</span><span class="link-arrow">↗</span></a>`;
    }
  );

  // 5. Format inline citation brackets [1], [2], [1, 2] as neat citation tags
  formatted = formatted.replace(
    /(?<=\s|^)\[(\d+(?:\s*,\s*\d+)*)\](?=[,\.\s]|$)/g,
    '<span class="bot-cite-ref">[$1]</span>'
  );

  // 6. Markdown typography formatting
  formatted = formatted
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n- /g, "<br>• ")
    .replace(/\n\* /g, "<br>• ")
    .replace(/\n/g, "<br>");

  return formatted + sourcesHtml;
}

function handleAssignmentUpload(courseCode, fileInputId, statusSpanId) {
  const input = document.getElementById(fileInputId);
  const status = document.getElementById(statusSpanId);
  if (!input || !input.files || input.files.length === 0) {
    alert("Please select a file to submit (e.g. PDF or ZIP report).");
    return;
  }
  const file = input.files[0];
  const protocol = "SUB-" + courseCode + "-" + Math.floor(1000 + Math.random() * 9000);
  if (status) {
    status.style.background = "#dcfce7";
    status.style.color = "#15803d";
    status.innerHTML = `✓ Submitted: <strong>${escapeHtml(file.name)}</strong> (Protocol #${protocol})`;
  }
  alert(`Confirmation of Coursework Submission:\n\nCourse: ${courseCode}\nFile: ${file.name} (${(file.size / 1024).toFixed(1)} KB)\nProtocol: #${protocol}\nTimestamp: ${new Date().toLocaleString()}\n\nStatus: Registered in InSIS Coursework Vault.`);
}

function downloadDeadlinesIcs() {
  const icsContent = 
    "BEGIN:VCALENDAR\r\n" +
    "VERSION:2.0\r\n" +
    "PRODID:-//VSE Prague//Coursework Deadlines//EN\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:4IT445 Milestone 2 - Machine Learning Pipeline Report\r\n" +
    "DESCRIPTION:Submit into InSIS Coursework Vault. Weight 25 pts.\r\n" +
    "DTSTART:20261115T215900Z\r\n" +
    "DTEND:20261115T225900Z\r\n" +
    "END:VEVENT\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:4SA421 Enterprise Architecture Case Study\r\n" +
    "DESCRIPTION:Submit TOGAF ADM document into InSIS. Weight 30 pts.\r\n" +
    "DTSTART:20261122T215900Z\r\n" +
    "DTEND:20261122T225900Z\r\n" +
    "END:VEVENT\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:Master's Thesis Abstract & PDF Submission Deadline\r\n" +
    "DESCRIPTION:Required by § 47b in InSIS.\r\n" +
    "DTSTART:20261130T215900Z\r\n" +
    "DTEND:20261130T225900Z\r\n" +
    "END:VEVENT\r\n" +
    "END:VCALENDAR\r\n";
  const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "VSE_Semester_Deadlines.ics";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  alert("VSE_Semester_Deadlines.ics downloaded! You can import this file directly into Google Calendar, Apple Calendar, or Outlook.");
}

function getContextualFallback(query, loggedIn) {
  const q = query.toLowerCase();
  if (q.includes("assignment") || q.includes("homework") || q.includes("deadline") || q.includes("due") || q.includes("submission") || q.includes("odevzdavarna")) {
    if (loggedIn) {
      return (
        "**Upcoming Coursework Assignments for WS 2026/2027 (2 urgent)**:\n\n" +
        "- 🔴 **4IT445 Advanced Data Analytics**: *Milestone 2 - Machine Learning Pipeline Report* (25 pts)\n" +
        "  **Due**: Nov 15, 2026 (23:59) • 3 days left\n" +
        "  [📂 Go to 4IT445 Submission Page](https://insis.vse.cz/auth/student/odevzdavarna.pl?course=4IT445&lang=en)\n\n" +
        "- 🟡 **4SA421 Information Systems Management**: *Enterprise Architecture Case Study* (30 pts)\n" +
        "  **Due**: Nov 22, 2026 (23:59) • 10 days left\n" +
        "  [📂 Go to 4SA421 Submission Page](https://insis.vse.cz/auth/student/odevzdavarna.pl?course=4SA421&lang=en)\n\n" +
        "- 🎓 **Master's Thesis Project**: *Final Abstracts & Full-Text PDF Upload*\n" +
        "  **Due**: Nov 30, 2026 (23:59) • Thesis Requirement (§ 47b)\n" +
        "  [🎓 Go to Master's Thesis Submission Area](https://insis.vse.cz/auth/student/zp.pl?lang=en)\n\n" +
        "*(2 more assignments due in December)*\n\n" +
        "<button class=\"bot-action-secondary-btn\" onclick=\"downloadDeadlinesIcs()\">📅 Add Deadlines to Google/Apple Calendar (.ics)</button>"
      );
    } else {
      return (
        "**InSIS Coursework Submissions (Odevzdávárna)**:\n\n" +
        "At VŠE, student assignments and seminar papers are submitted electronically in InSIS under:\n" +
        "**Student's Portal ➔ Coursework submissions (Odevzdávárna)** (`/auth/student/odevzdavarna.pl`).\n\n" +
        "- Each enrolled course provides dedicated submission drop-boxes with instructions, accepted formats (.pdf, .zip), and file size limits.\n" +
        "- Once uploaded, InSIS generates a submission timestamp and protocol.\n\n" +
        "💡 *To view your personal active assignments and direct submission buttons, please log in with your student credentials using the button above.*"
      );
    }
  } else if (q.includes("credit") || q.includes("voucher") || q.includes("left") || q.includes("remaining") || q.includes("progress")) {
    if (loggedIn) {
      return (
        "**Degree Progress & Credit Breakdown (ISM Master's)**:\n\n" +
        "- 📊 **Degree Target**: **120 ECTS** (Master in Information Systems Management)\n" +
        "- ✅ **Credits Earned**: **90 ECTS** (75% completed)\n" +
        "- ⏳ **Enrolled This Semester**: **24 ECTS** across 4 courses in progress\n" +
        "- 🎯 **Remaining After Current Term**: **Only 6 ECTS!** (Master's Thesis & State Final Exam)\n" +
        "- 🛡️ **Credit Vouchers Safety**: You have **120 spare vouchers left** (out of 144 initial). Even if you were to retake a course, your voucher safety buffer is completely safe.\n\n" +
        "[📑 View Full E-Study Record in InSIS](https://insis.vse.cz/auth/student/studium.pl?lang=en)"
      );
    } else {
      return (
        "**Master's Credit Voucher System at VŠE**:\n\n" +
        "- Master's students receive **144 vouchers** for a 120 ECTS degree (24 extra vouchers buffer).\n" +
        "- You must earn at least **9 ECTS** in your first semester, or **20 ECTS** across two consecutive semesters to maintain enrollment.\n\n" +
        "💡 *To view your individual earned credits and remaining voucher balance, please log in with your student account.*"
      );
    }
  } else if (q.includes("accomodation") || q.includes("accommodation") || q.includes("dorm") || q.includes("flat") || q.includes("housing")) {
    return (
      "Accommodation at VŠE Prague:\n" +
      "- **VŠE Dormitories (SUZ)**: Applied via the ISKaM system (dorms at Jarov, Blanice, Vltava, Rooseveltova).\n" +
      "- **Accommodation Voucher/Confirmation**: SUZ issues the required housing proof for visa applications.\n" +
      "- **Foreign Police Rule**: Dormitory administration automatically reports your stay. If living in private accommodation, you must register within 3 working days."
    );
  } else if (!loggedIn && (q.includes("apply") || q.includes("admission"))) {
    return (
      "You can apply without an InSIS student account right from this Public InSIS page:\n" +
      "- Under **Admission procedure**, click **E-application form to study at VŠE** (`/prihlaska/?lang=en`).\n" +
      "- Create a new electronic application, select your English programme, and pay the EUR 50 admission fee.\n" +
      "- For questions, contact the Admission Office (`admissions@vse.cz`, RB 527)."
    );
  } else if (q.includes("errata") || q.includes("thesis")) {
    return (
      "To submit errata for your Master's thesis in InSIS:\n" +
      "- Navigate to **My College** -> **Master's thesis**.\n" +
      "- Under the editing application, click **Insert errata (Vložit errata)**.\n" +
      "- Upload your corrections PDF under § 47b."
    );
  }
  return "I found information from verified VŠE documentation. Click 💡 for suggested topics or explore any section on the Public InSIS page!";
}

// -----------------------------------------------------------------------------
// 7. Initial Startup & Browser History Listener
// -----------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  cleanupLegacySessionKeys();
  resetBotConversationForSession();
  loadInsisUrls();

  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const session = getLoginSession();

  let initialUrl;
  if (currentPath === "/" || currentPath === "" || currentPath === "/index.html") {
    initialUrl = session.loggedIn
      ? "https://insis.vse.cz/auth/?lang=en"
      : "https://insis.vse.cz/?lang=en";
  } else {
    initialUrl = "https://insis.vse.cz" + currentPath + currentSearch;
  }

  navigateToUrl(initialUrl);
  setupPublicLinkInterceptors();
});

window.addEventListener("popstate", () => {
  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const session = getLoginSession();
  const url =
    currentPath === "/" || currentPath === ""
      ? session.loggedIn
        ? "https://insis.vse.cz/auth/?lang=en"
        : "https://insis.vse.cz/?lang=en"
      : "https://insis.vse.cz" + currentPath + currentSearch;
  navigateToUrl(url);
});
