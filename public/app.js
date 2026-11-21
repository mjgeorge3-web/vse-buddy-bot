// =============================================================================
// Authentic InSIS Multi-URL Router, Public/Auth Session Controller & Buddy Bot
// Supports:
//   1. No-Login Public InSIS Portal (https://insis.vse.cz/?lang=en)
//   2. Custom Name + Password ("ism_mastersthesis") Login across all 195 URLs
//   3. Clean Session Wipe on Logout (both Portal & Bot switch to Public Mode)
//   4. Opt-In Personalised Study Context, Smart Topic Isolation
//      (Visas/Stay/Campus), & Interactive Stage Onboarding Checklist
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
          <div class="bot-starter-card" onclick="sendBotPrompt('How do I book and reserve a VŠE dormitory room in ISKaM, pay the deposit, and what are the dormitory campuses and contacts?')">
            <div class="starter-icon">🏢</div>
            <div class="starter-text">
              <div class="starter-title">VŠE Dormitory Booking &amp; Reservations</div>
              <div class="starter-desc">ISKaM online room booking, kauce deposit, campuses &amp; SÚZ contacts</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('What are the visa, dormitory accommodation, and 3-day Foreign Police registration rules for international students?')">
            <div class="starter-icon">🛂</div>
            <div class="starter-text">
              <div class="starter-title">Visa, Insurance &amp; 3-Day Police Rules</div>
              <div class="starter-desc">Study visas, comprehensive Czech health insurance &amp; Foreign Police reporting</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('How do I submit the E-application form to study at VŠE?')">
            <div class="starter-icon">🎓</div>
            <div class="starter-text">
              <div class="starter-title">Admissions &amp; E-Application (No Login)</div>
              <div class="starter-desc">Apply online without an account, fees, and public course catalogue</div>
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
        <div class="bot-hero-sub">Ask about InSIS navigation, student portlets, credit vouchers, thesis stages, visas, or VŠE policies.</div>
        <div class="bot-hero-cards">
          <div class="bot-starter-card" onclick="sendBotPrompt('How many credit vouchers and credits do I have left?')">
            <div class="starter-icon">📊</div>
            <div class="starter-text">
              <div class="starter-title">Check My Credit Vouchers &amp; ECTS</div>
              <div class="starter-desc">Remaining voucher balance (30/144), earned ECTS, and degree progress</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('Walk me through the complete Master\\'s Thesis workflow at VŠE from topic approval to submission, defense, and errata.')">
            <div class="starter-icon">📗</div>
            <div class="starter-text">
              <div class="starter-title">Master's Thesis 4-Stage Workflow</div>
              <div class="starter-desc">Topic approval, 3 Red ✗ steps, PDF/A upload, defense reviews &amp; § 47b errata</div>
            </div>
          </div>
          <div class="bot-starter-card" onclick="sendBotPrompt('How do I enable the Navigation bar for students portlet in InSIS?')">
            <div class="starter-icon">🧭</div>
            <div class="starter-text">
              <div class="starter-title">Student Sidebar Portlet &amp; Navigation</div>
              <div class="starter-desc">Pin quick-access student links onto your InSIS Personal administration home</div>
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
    "view-contact-centre",
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
  if (fullUrl && !fullUrl.startsWith("https://insis.vse.cz") && fullUrl.startsWith("http")) {
    window.open(fullUrl, "_blank", "noopener,noreferrer");
    return;
  }

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

  // Allow all modeled public modules (E-application, Catalogue, Study Plans, Timetables,
  // Academic Calendar, First Login Guide, Public Financing, Document Server) without login;
  // show prototype scope notice only for unmodeled secondary public pages.
  const isSupportedPublicRoute =
    cleanPath === "" ||
    cleanPath === "/" ||
    cleanPath === "/index.pl" ||
    cleanPath.includes("/prihlaska") ||
    cleanPath.includes("/navratka") ||
    cleanPath.includes("/katalog") ||
    cleanPath.includes("/kurzy") ||
    cleanPath.includes("plany.pl") ||
    cleanPath.includes("rozvrhy") ||
    cleanPath.includes("harmonogram") ||
    cleanPath.includes("/navod") ||
    cleanPath.includes("/financovani") ||
    cleanPath.includes("/dok_server");

  if (!session.loggedIn && !isSupportedPublicRoute) {
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
  } else if (cleanPath === "/auth/eagenda/kontaktni_centrum.pl" || cleanPath.includes("kontaktni_centrum") || cleanPath.includes("uradovna")) {
    currentPageKey = "contact_centre";
    currentPageTitle = "Contact Centre & General Application";
    currentPageUrl = fullUrl;
    const viewEl = document.getElementById("view-contact-centre");
    if (viewEl) viewEl.style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML =
      '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/?lang=en\'); return false;">Personal administration</a> &raquo; <strong>Contact centre</strong>';
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
          <tr><td><strong>C-EDS</strong></td><td>Economic Data Science</td><td>FIS</td><td>Bachelor (Bc.)</td><td>180 ECTS</td><td>English</td></tr>
          <tr><td><strong>C-EDA</strong></td><td>Economic Data Analysis</td><td>FIS</td><td>Master (Ing.)</td><td>120 ECTS</td><td>English</td></tr>
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
          <div style="font-size:24px; font-weight:800; color:#16a34a;">30 Vouchers</div>
          <div style="font-size:11px; color:#64748b;">90 earned + 24 enrolled (114 used)</div>
        </div>
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px; text-align:center;">
          <div style="font-size:11px; color:#64748b; text-transform:uppercase; font-weight:700;">Current Study Average</div>
          <div style="font-size:24px; font-weight:800; color:#004b87;">1.42</div>
          <div style="font-size:11px; color:#64748b;">Scale: 1 (Výborně) to 4 (Fail)</div>
        </div>
      </div>
      <p style="font-size:12px; color:#475569; line-height:1.6;">
        <strong>Study Regulation Rules:</strong> You must earn at least 9 ECTS credits in your first semester and maintain cumulative progress of at least 20 ECTS per active semester to stay on track without voucher penalties.
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
          <tr><td><strong>Monday</strong></td><td>09:15 &ndash; 12:30</td><td>4IT445 Advanced Data Analytics</td><td>Lecture + Lab</td><td><strong>RB 101</strong></td><td>Žižkov, Rajská budova (1st floor)</td><td>Sample FIS Lecturer A</td></tr>
          <tr><td><strong>Tuesday</strong></td><td>14:30 &ndash; 17:45</td><td>4SA421 Info Systems Management</td><td>Seminar</td><td><strong>SB 204</strong></td><td>Žižkov, Stará budova (2nd floor)</td><td>Sample FIS Lecturer B</td></tr>
          <tr><td><strong>Thursday</strong></td><td>11:00 &ndash; 14:15</td><td>2SE411 European Integration</td><td>Lecture</td><td><strong>NB A</strong></td><td>Žižkov, Nová budova (1st floor)</td><td>Sample FMV Lecturer</td></tr>
          <tr><td><strong>Friday</strong></td><td>09:15 &ndash; 10:45</td><td>3PE401 Business Ethics</td><td>Lecture</td><td><strong>JM 310</strong></td><td>Jižní Město (3rd floor)</td><td>Sample FBA Lecturer</td></tr>
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
            <td>Sample FIS Thesis Supervisor</td>
            <td>Sample Thesis Opponent</td>
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
          <tr><td class="label-cell">Official Bank Account:</td><td class="value-cell"><strong>24242442 / 0800</strong> (Česká spořitelna, a.s.)</td></tr>
          <tr><td class="label-cell">IBAN / SWIFT:</td><td class="value-cell"><code>CZ39 0800 0000 0000 2424 2442</code> &bull; SWIFT: <code>GIBACZPX</code></td></tr>
          <tr><td class="label-cell">Your Variable Symbol (VS):</td><td class="value-cell"><strong style="color:#005596; font-size:15px;">00000000 (Demo)</strong> <em>(Mandatory to identify your student account!)</em></td></tr>
          <tr><td class="label-cell">Payment Status:</td><td class="value-cell"><span style="color:#16a34a; font-weight:700;">All Tuition &amp; Obligations Cleared (Demo Record)</span></td></tr>
        </table>
        <button onclick="alert('Card payment gateway 3DS Secure (Demo): 0.00 CZK outstanding')" style="background:#005596; color:white; border:none; padding:8px 14px; border-radius:4px; font-weight:700; cursor:pointer;">💳 Open Card Payment Gateway</button>
      `;
    } else {
      html = `
        <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Study Financing, Tuition Fees &amp; Scholarships (Public Information)</h3>
        <p style="font-size:12px; color:#475569; margin-bottom:14px;">
          General financing rules for international English-taught Bachelor's and Master's programmes at VŠE Prague.
        </p>
        <ul style="font-size:12px; line-height:1.75; margin-left:20px; margin-bottom:14px;">
          <li><strong>English Degree Tuition Fee:</strong> Typically approx. <strong>EUR 5,000 / academic year</strong> (confirm exact faculty tuition &amp; payment dates on <a href="https://admissions.vse.cz/" target="_blank" rel="noopener noreferrer">admissions.vse.cz</a>).</li>
          <li><strong>Official Tuition Account:</strong> Česká spořitelna (<code>24242442/0800</code>, IBAN <code>CZ39 0800 0000 0000 2424 2442</code>, SWIFT <code>GIBACZPX</code>) with your personal InSIS Variable Symbol.</li>
          <li><strong>Scholarships:</strong> Merit scholarships and quarterly accommodation grants are governed by the official <a href="https://www.vse.cz/english/about-vse/information-and-regulations/scholarship-regulations/" target="_blank" rel="noopener noreferrer">VŠE Scholarship Regulations</a>.</li>
        </ul>
        <button onclick="showLoginView()" style="background:#005596; color:white; border:none; padding:7px 14px; border-radius:4px; font-weight:700; cursor:pointer;">🔒 Log in to view your personal Variable Symbol</button>
      `;
    }
  } else if (path.includes("stipendia")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:6px;">Scholarships &amp; Accommodation Grant (Žádosti o stipendia)</h3>
      <div style="font-size:12px; color:#475569; margin-bottom:14px;">
        <strong>Breadcrumb Trail:</strong> Personal administration &gt; Financing of study and scholarships &gt; Scholarships (Žádosti o stipendia)
      </div>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px; margin-bottom:16px;">
        <h4 style="font-size:14px; color:#005596; margin-bottom:8px;">Accommodation Scholarship (Ubytovací stipendium)</h4>
        <p style="font-size:12px; color:#334155; line-height:1.6; margin-bottom:10px;">
          Available to full-time enrolled students whose permanent residence is outside Prague. Payouts are transferred quarterly into your registered Czech bank account.
        </p>
        <div style="font-size:12px; color:#1e293b; margin-bottom:10px;">
          <strong>Application Window:</strong> <span style="color:#16a34a; font-weight:700;">OPEN (Autumn 2026 / Spring 2027)</span><br>
          <strong>Eligibility Check:</strong> Permanent residence outside Prague (Eligible)<br>
          <strong>Disbursement Target:</strong> Registered Czech Bank Account
        </div>
        <button onclick="alert('Your accommodation scholarship application has been registered successfully! Payouts will be deposited to your registered Czech bank account.')" style="background:#005596; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:700; cursor:pointer;">📝 Submit Accommodation Scholarship Application</button>
      </div>
      <div style="font-size:12px; color:#64748b;">
        <em>Note: To receive payments, verify that your active Czech bank account is saved under <a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/financovani/index.pl?lang=en'); return false;" style="color:#005596; font-weight:600;">Student Study Financing, Bank Accounts &amp; Variable Symbol</a>.</em>
      </div>
    `;
  } else if (path.includes("potvrzeni.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Electronic Confirmation of Study (Potvrzení o studiu)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Generate an official digitally signed PDF document bearing the qualified electronic stamp of VŠE. Accepted by Foreign Police, OAMP MVČR, transit authorities (PID / Lítačka), banks, and embassies.
      </p>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:16px; margin-bottom:14px;">
        <strong>Student:</strong> ${safeUser} (FIS ISM Master)<br>
        <strong>Academic Year:</strong> 2026/2027 &bull; Winter Semester<br>
        <strong>Electronic Seal:</strong> Qualified Electronic Timestamp &bull; Verification Token #CONF-DEMO-0001
      </div>
      <button onclick="downloadConfirmationPdf()" style="background:#16a34a; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:700; cursor:pointer;">📥 Download Demo Confirmation Sample (.txt)</button>
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
          <tr><td><strong>3PE401</strong></td><td>Business Ethics &amp; Governance</td><td>Faculty of Business Administration (FBA)</td><td>6</td><td>English</td><td>WS</td></tr>
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
  } else if (path.includes("portlety.pl")) {
    html = `
      <div style="display:grid; grid-template-columns:190px 1fr; gap:20px; align-items:start;">
        <div style="background:#f4fce3; border:1px solid #82c91e; border-radius:4px; padding:10px 12px; font-size:12px; line-height:1.8;">
          <div style="font-weight:700; color:#1e293b; border-bottom:1px solid #c0eb75; padding-bottom:4px; margin-bottom:6px;">Student</div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/posta/slozka.pl?lang=en'); return false;" style="color:#005596;">Mail box</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/dok_server/?lang=en'); return false;" style="color:#005596;">Documents</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/katalog/rozvrhy_view.pl?lang=en'); return false;" style="color:#005596;">Timetables</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/terminy_seznam.pl?lang=en'); return false;" style="color:#005596;">Exams</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en'); return false;" style="color:#005596;">Plan of study</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/arch_studia.pl?lang=en'); return false;" style="color:#005596;">Results</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/anketa/?lang=en'); return false;" style="color:#005596;">Survey</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/registrace.pl?lang=en'); return false;" style="color:#005596;">Registration/enrollment</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/zp.pl?lang=en'); return false;" style="color:#005596;">Final thesis assignment</a></div>
          <div><a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/student/odevzdavarna.pl?lang=en'); return false;" style="color:#005596;">Coursework submissions</a></div>
        </div>
        <div>
          <h3 style="font-size:16px; color:#004b87; margin-bottom:8px;">Portlets in InSIS (/auth/system/portlety.pl)</h3>
          <p style="font-size:12px; color:#475569; margin-bottom:12px;">
            This application enables users to place pre-prepared portlets into InSIS pages (e.g. pinning the <strong>Navigation bar for students</strong> sidebar).
          </p>
          <div style="background:#eff6ff; border:1px solid #93c5fd; border-radius:4px; padding:10px 12px; font-size:12px; color:#1e40af; margin-bottom:14px;">
            <strong>Recovery Note:</strong> If a configured portlet causes display issues, log in via <code>https://insis.vse.cz/quick</code> to remove the non-functional portlet.
          </div>
          <table class="insis-study-table" style="margin-bottom:14px;">
            <thead><tr><th>Portlet</th><th>Position</th><th>Status</th><th>Changed by</th></tr></thead>
            <tbody>
              <tr>
                <td><strong>Navigation bar for students</strong></td>
                <td>Basic &ndash; to the left from the page content</td>
                <td><span style="color:#16a34a; font-weight:700;">Active</span></td>
                <td>${safeUser}</td>
              </tr>
            </tbody>
          </table>
          <p style="font-size:12px; color:#64748b;">
            <em>Note: Scholarships, Study Financing &amp; Bank Accounts, Electronic Confirmation of Study, and Contact Centre are not listed in this sidebar &mdash; open them via Student's portal or ask VŠE Buddy Bot.</em>
          </p>
        </div>
      </div>
    `;
  } else if (path.includes("dok_server")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Official University Document Server (/dok_server/)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Public repository of VŠE Study and Examination Regulations, Rector's Measures, Faculty Decrees, and Tuition Schedules.
      </p>
      <ul style="font-size:12px; line-height:1.8; margin-left:20px; color:#1e293b;">
        <li><strong>Study and Examination Regulations of VŠE</strong> (ECTS credit voucher system, exam retakes, § 47b thesis publication)</li>
        <li><strong>Disciplinary Code &amp; Academic Integrity Rules</strong> (Plagiarism &amp; AI disclosure rules)</li>
        <li><strong>Scholarship Regulations of VŠE</strong> (Merit &amp; Accommodation scholarship rules)</li>
      </ul>
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
========================================================================
*** ACADEMIC PROTOTYPE SIMULATION — NOT AN OFFICIAL VŠE DOCUMENT ***
========================================================================
Simulated Demo Preview of Electronic Confirmation of Study (Potvrzení o studiu)
Student (Demo): ${studentName}
Programme: Information Systems Management (ISM) - Master (Demo Profile)
Status: Simulated Demonstration Record (NOT legally valid)
Generated: ${new Date().toISOString()}

For a genuine digitally sealed PDF confirmation accepted by Czech
authorities (OAMP/MVČR, PID), log into official InSIS:
https://insis.vse.cz/auth/student/potvrzeni.pl?lang=en
========================================================================
  `;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `DEMO_Confirmation_Sample_${fileSafeName}.txt`;
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
  const modeledIds = new Set([
    "pub-link-login",
    "pub-link-eapp",
    "pub-link-preenroll",
    "pub-link-catalogue",
    "pub-link-plans",
    "pub-link-timetables",
    "pub-link-schedule",
    "pub-link-first-login",
  ]);
  const links = container.querySelectorAll("a");
  links.forEach((a) => {
    // Keep primary login and modeled public portal modules directly navigable
    if (modeledIds.has(a.id)) return;
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
      `Protocol: #ERR-DEMO-0001\n` +
      `Notification dispatched to the assigned thesis supervisor under § 47b (Demo).`
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
      navigateToUrl("https://insis.vse.cz/katalog/rozvrhy_view.pl?lang=en");
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
          <button class="mini-chip" onclick="sendBotPrompt('How do I book and reserve a VŠE dormitory room in ISKaM, pay the deposit, and what are the dormitory campuses and contacts?')">🏢 Book Dorm (ISKaM)</button>
          <button class="mini-chip" onclick="sendBotPrompt('What are the visa, dormitory accommodation, and 3-day Foreign Police registration rules for international students?')">🛂 Visa &amp; Police</button>
          <button class="mini-chip" onclick="showInteractiveChecklist()">📋 Arrival Checklist</button>
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
            <button class="mini-chip" onclick="sendBotPrompt('What are the required steps to submit my Master\\'s thesis in InSIS?')">📤 Thesis Steps</button>
            <button class="mini-chip" onclick="sendBotPrompt('Where do I submit errata for my Master\\'s thesis in InSIS?')">📝 Submit Errata</button>
          `;
        } else {
          chipsBox.innerHTML = `
            <button class="mini-chip" onclick="sendBotPrompt('How many credit vouchers and credits do I have left?')">📊 My Vouchers</button>
            <button class="mini-chip" onclick="sendBotPrompt('How do I apply for the accommodation scholarship in InSIS?')">💰 Housing Grant</button>
            <button class="mini-chip" onclick="sendBotPrompt('How do I enable the Navigation bar for students portlet in InSIS?')">🧭 Student Sidebar</button>
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
      { icon: "🏢", text: "VŠE Dormitory Booking, Deposit & Campuses (ISKaM)", prompt: "How do I book and reserve a VŠE dormitory room in ISKaM, pay the deposit, and what are the dormitory campuses and contacts?" },
      { icon: "🛂", text: "Visa, Health Insurance & 3-Day Police Rules", prompt: "What are the visa, dormitory accommodation, and 3-day Foreign Police registration rules for international students?" },
      { icon: "📝", text: "Submit VŠE E-Application Form (No Login)", prompt: "How do I submit the E-application form to study at VŠE?" },
      { icon: "🎓", text: "Foreign Diploma Assessment & Recognition", prompt: "How does foreign diploma recognition (nostrification) work at VŠE?" },
      { icon: "📚", text: "Browse Public Course Catalogue & Study Plans", prompt: "Can I browse the Course catalogue and Study plans without an account?" },
      { icon: "📋", text: "Open Interactive Pre-Arrival & Onboarding Checklist", action: "showInteractiveChecklist" }
    ];
  } else {
    items = [
      { icon: "📊", text: "Check My Remaining Credit Vouchers & ECTS Progress", prompt: "How many credit vouchers and credits do I have left?" },
      { icon: "📗", text: "Complete 4-Stage Master's Thesis Workflow & § 47b Errata", prompt: "Walk me through the complete Master's Thesis workflow at VŠE from topic approval to submission, defense, and errata." },
      { icon: "🧭", text: "Enable 'Navigation bar for students' Sidebar Portlet", prompt: "How do I enable the Navigation bar for students portlet in InSIS?" },
      { icon: "💰", text: "Apply for Accommodation Scholarship in InSIS", prompt: "How do I apply for the accommodation scholarship in InSIS?" },
      { icon: "🏢", text: "VŠE Dormitory Booking, Deposit & ISKaM Guide", prompt: "How do I book and reserve a VŠE dormitory room in ISKaM, pay the deposit, and what are the dormitory campuses and contacts?" },
      { icon: "📋", text: "Open Interactive Student Onboarding Checklist", action: "showInteractiveChecklist" }
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
    '<div style="display:flex; align-items:center; gap:8px;"><div class="typing-dots"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div><span style="font-size:11px; color:#64748b; font-style:italic;">Generating live Gemini answer from VŠE knowledge base...</span></div>',
    true
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
      loadingBubble.innerHTML = formatBotMarkdown(data.answer, data.mode || "normal");
      chatHistory.push({ role: "assistant", content: data.answer });
      handleContextualPageActions(query, session.loggedIn, data.answer);
    } else {
      throw new Error("API call failed");
    }
  } catch (err) {
    const errMsg = "⚠️ **API Rate Limit or Connection Issue:** The live Google Gemini API is temporarily busy. Please wait a few seconds and try your question again.";
    loadingBubble.innerHTML = formatBotMarkdown(errMsg, "error");
  }
  updateBotContextUI();
  const container = document.getElementById("bot-messages-area");
  container.scrollTop = container.scrollHeight;
}
function handleContextualPageActions(query, loggedIn, answerText = "") {
  const ql = query.toLowerCase();

  // Visual co-pilot highlighting on the active InSIS page without appending duplicate link chips
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
    } else if (
      ql.includes("course") ||
      ql.includes("catalogue") ||
      ql.includes("study plan") ||
      ql.includes("syllabus")
    ) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-catalogue", "pub-link-plans"]);
      }
    } else if (ql.includes("timetable") || ql.includes("schedule") || ql.includes("calendar")) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-schedule", "pub-link-timetables"]);
      }
    } else if (ql.includes("first log") || ql.includes("password") || ql.includes("otp") || ql.includes("log in")) {
      if (currentPageKey === "public_home") {
        highlightElementOnPage(["pub-link-first-login", "pub-link-login"]);
      }
    }
    return;
  }

  // Logged-in visual highlights on the active Master's Thesis page
  if (ql.includes("red x") || ql.includes("3 red")) {
    if (currentPageKey === "master_thesis") {
      highlightElementOnPage([
        "action-add-info",
        "action-upload-thesis",
        "action-submit-thesis",
      ]);
    }
  } else if (ql.includes("errata") && currentPageKey === "master_thesis") {
    highlightElementOnPage("action-errata");
  }
}

function appendBotBubble(role, text, isRawHtml = false) {
  const container = document.getElementById("bot-messages-area");
  const bubble = document.createElement("div");
  bubble.className = `bot-msg-bubble ${role}`;
  bubble.innerHTML = isRawHtml ? text : (role === "user" ? escapeHtml(text) : formatBotMarkdown(text));
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

function formatBotMarkdown(text, mode = "normal") {
  if (!text) return "";
  let formatted = text.replace(/\r\n/g, "\n");
  let sourcesHtml = "";
  const hasUnverifiedWarning = /unverified|may be outdated|don't have verified|do not have verified/i.test(formatted);
  // 0. Unwrap any backticks directly surrounding URLs so backticks never get consumed by URL tokens
  formatted = formatted.replace(/`(https?:\/\/[^`\s]+)`/g, "$1");
  // 1. Extract source citations and transform them into sleek badge pills (skipping URLs already in the body)
  const sourcesMatch = formatted.match(/(?:\n|^)\*\*Sources:\*\*\s*([\s\S]*)$/i);
  if (sourcesMatch) {
    formatted = formatted.substring(0, sourcesMatch.index).trim();
    const bodyUrls = new Set(
      Array.from(formatted.matchAll(/https?:\/\/[^\s<\]\)`"']+/g)).map((m) =>
        m[0].replace(/[.,;]+$/, "").replace(/\/+$/, "")
      )
    );
    const sourcesRaw = sourcesMatch[1].trim();
    const sourceLinks = [];
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
    let m;
    while ((m = linkRegex.exec(sourcesRaw)) !== null) {
      const label = escapeHtml(m[1]);
      const url = m[2];
      if (bodyUrls.has(url.replace(/\/+$/, ""))) {
        continue;
      }
      const safeUrl = url.replace(/'/g, "\\'");
      if (url.startsWith("https://insis.vse.cz")) {
        sourceLinks.push(`<a class="source-pill-link insis-src" href="${url}" onclick="navigateToUrl('${safeUrl}'); return false;"><span class="src-icon">🏛️</span><span>${label}</span></a>`);
      } else {
        sourceLinks.push(`<a class="source-pill-link ext-src" href="${url}" target="_blank" rel="noopener noreferrer"><span class="src-icon">🌐</span><span>${label}</span></a>`);
      }
    }
    if (sourceLinks.length > 0) {
      sourcesHtml = `<div class="bot-sources-list"><span class="bot-sources-header">Verified Official Sources</span>${sourceLinks.join("")}</div>`;
    }
  }
  // Token store to isolate HTML links/buttons and prevent nested regex collisions
  const tokens = [];
  function saveToken(htmlSnippet) {
    const id = tokens.length;
    tokens.push(htmlSnippet);
    return `%%BOT_TOKEN_${id}%%`;
  }
  // 2. Format standard markdown links: [Label](url) FIRST
  formatted = formatted.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (match, label, url) => {
      const isAction =
        label.includes("Go to") ||
        label.includes("📂") ||
        label.includes("🎓") ||
        label.includes("📑") ||
        label.includes("Jump to") ||
        label.includes("View Full") ||
        label.includes("Submission") ||
        label.includes("Download ") ||
        label.includes("Open ") ||
        label.startsWith("Official ") ||
        label.startsWith("VŠE ");
      const safeUrl = url.replace(/'/g, "\\'");
      const isInsis = url.startsWith("https://insis.vse.cz");
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;
      if (isAction) {
        return saveToken(`<a class="bot-action-button" href="${url}" ${clickAttr}><span>${escapeHtml(label)}</span><span class="btn-ext-arrow">↗</span></a>`);
      }
      const icon = isInsis ? "🏛️" : (url.includes("o365") || url.includes("microsoft") ? "💼" : (url.includes("mvcr") || url.includes("frs") || url.includes("ipc.gov") ? "🛂" : (url.includes("map") ? "📍" : "🌐")));
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      return saveToken(`<a class="${pillClass}" href="${url}" ${clickAttr} title="${escapeHtml(label)}"><span class="link-icon">${icon}</span><span class="link-label">${escapeHtml(label)}</span><span class="link-arrow">↗</span></a>`);
    }
  );
  // 3. Format bulleted/colon labeled URLs
  formatted = formatted.replace(
    /(^|\n)([•\*\-]?\s*)(?:\*\*)?([^\n\:\*\[]+?)(?:\*\*)?:\s*(https?:\/\/[^\s<\]\)\<\>`"']+)(\s*\[[\d\s,]+\])?/g,
    (match, linePre, bullet, rawLabel, rawUrl, cite) => {
      const label = rawLabel.trim();
      const cleanUrl = rawUrl.replace(/[.,;]+$/, "");
      const safeUrl = cleanUrl.replace(/'/g, "\\'");
      const isInsis = cleanUrl.startsWith("https://insis.vse.cz");
      const icon = isInsis ? "🏛️" : (cleanUrl.includes("o365") || cleanUrl.includes("microsoft") ? "💼" : (cleanUrl.includes("mvcr") || cleanUrl.includes("frs") || cleanUrl.includes("ipc.gov") ? "🛂" : (cleanUrl.includes("map") ? "📍" : "🌐")));
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      const citeHtml = cite ? ` <span class="bot-cite-ref">${cite.trim()}</span>` : "";
      const bulletPrefix = bullet.trim() ? `${bullet}` : "- ";
      const linkSnippet = `<a class="${pillClass}" href="${cleanUrl}" ${clickAttr} title="${escapeHtml(label)}"><span class="link-icon">${icon}</span><span class="link-label">${escapeHtml(label)}</span><span class="link-arrow">↗</span></a>`;
      return `${linePre}${bulletPrefix}${saveToken(linkSnippet)}${citeHtml}`;
    }
  );
  // 4. Format any remaining bare URLs (never consuming backticks or trailing punctuation)
  formatted = formatted.replace(
    /(https?:\/\/[^\s<\]\)\<\>`"']+)/g,
    (match, rawUrl) => {
      let trailing = "";
      let url = rawUrl;
      const trailMatch = url.match(/([.,;:]+)$/);
      if (trailMatch) {
        trailing = trailMatch[1];
        url = url.slice(0, -trailing.length);
      }
      const safeUrl = url.replace(/'/g, "\\'");
      const isInsis = url.startsWith("https://insis.vse.cz");
      const icon = isInsis ? "🏛️" : "🌐";
      const clickAttr = isInsis
        ? `onclick="navigateToUrl('${safeUrl}'); return false;"`
        : `target="_blank" rel="noopener noreferrer"`;
      const pillClass = isInsis ? "bot-link-pill insis-link" : "bot-link-pill ext-link";
      let displayLabel = url.replace(/^https?:\/\/(?:www\.)?/, "").replace(/\/+$/, "");
      if (displayLabel.length > 30) {
        displayLabel = displayLabel.substring(0, 28) + "…";
      }
      return saveToken(`<a class="${pillClass}" href="${url}" ${clickAttr}><span class="link-icon">${icon}</span><span class="link-label">${escapeHtml(displayLabel)}</span><span class="link-arrow">↗</span></a>`) + trailing;
    }
  );
  // 5. Helper for inline typography (HTML-escaped first to prevent XSS, then markdown formatting)
  function formatInline(str) {
    return escapeHtml(str)
      .replace(/(?<=\s|^)\[(\d+(?:\s*,\s*\d+)*)\](?=[,\.\s]|$)/g, '<span class="bot-cite-ref">[$1]</span>')
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^\*\n]+)\*/g, "<em>$1</em>")
      .replace(/`([^`\n]{1,50})`/g, '<span class="bot-inline-tag">$1</span>')
      .replace(/`/g, "");
  }
  // 6. Structured, block-aligned layout parser (Headers, Numbered Steps, Sub-bullets, Callouts, Action Bars)
  const rawLines = formatted.split("\n");
  const blocks = [];
  let currentStep = null;
  function flushStep() {
    if (currentStep) {
      const subHtml = currentStep.subItems.length > 0
        ? `<div class="bot-subbullet-list">${currentStep.subItems.join("")}</div>`
        : "";
      blocks.push(
        `<div class="bot-step-row">` +
          `<div class="bot-step-num">${currentStep.num}</div>` +
          `<div class="bot-step-body">` +
            `<div class="bot-step-title">${currentStep.titleHtml}</div>` +
            `${subHtml}` +
          `</div>` +
        `</div>`
      );
      currentStep = null;
    }
  }
  for (let i = 0; i < rawLines.length; i++) {
    const rawLine = rawLines[i];
    const trimmed = rawLine.trim();
    if (!trimmed) {
      continue;
    }
    // Check if this is the very first line and is a main title (**Title** or ### Title)
    if (blocks.length === 0 && !currentStep && (
      /^\*\*[^\*]+\*\*(?:\s*\(\*[^\)]+\*\))?$/.test(trimmed) ||
      /^#{1,3}\s+/.test(trimmed)
    )) {
      const cleanTitle = trimmed.replace(/^#{1,3}\s+/, "");
      let badgeHtml = "";
      if (mode === "normal" && !hasUnverifiedWarning) {
        badgeHtml = `<div class="bot-ans-verified-badge"><span class="v-dot">✓</span> Grounded VŠE Guidance</div>`;
      } else if (mode === "crisis") {
        badgeHtml = `<div class="bot-ans-verified-badge" style="background:#fee2e2;color:#991b1b;">⚠️ Emergency Support Resources</div>`;
      } else if (mode === "no_context" || hasUnverifiedWarning) {
        badgeHtml = `<div class="bot-ans-verified-badge" style="background:#fef3c7;color:#92400e;">ℹ️ Confirm With Official VŠE Office</div>`;
      } else if (mode === "error") {
        badgeHtml = `<div class="bot-ans-verified-badge" style="background:#fee2e2;color:#991b1b;">⚠️ Service Notice</div>`;
      }
      blocks.push(
        `<div class="bot-ans-header">` +
          `${badgeHtml}` +
          `<div class="bot-ans-title">${formatInline(cleanTitle)}</div>` +
        `</div>`
      );
      continue;
    }
    // Check if line is purely action buttons (e.g., %%BOT_TOKEN_0%% • %%BOT_TOKEN_1%%)
    if (/^(?:%%BOT_TOKEN_\d+%%(?:\s*[•·|\-]\s*)?)+$/.test(trimmed)) {
      flushStep();
      const btnTokens = trimmed.replace(/\s*[•·|\-]\s*/g, " ");
      blocks.push(`<div class="bot-actions-bar">${btnTokens}</div>`);
      continue;
    }
    // Check if line is a numbered step: "1. ..."
    const stepMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (stepMatch) {
      flushStep();
      currentStep = {
        num: stepMatch[1],
        titleHtml: formatInline(stepMatch[2]),
        subItems: [],
      };
      continue;
    }
    // Check if line is an indented sub-bullet or continuation inside an active numbered step
    const isIndented = /^\s{2,}/.test(rawLine);
    const bulletMatch = trimmed.match(/^[\-\*•]\s+(.*)$/);
    if (currentStep && (isIndented || bulletMatch)) {
      const content = bulletMatch ? bulletMatch[1] : trimmed;
      currentStep.subItems.push(
        `<div class="bot-subbullet-row">` +
          `<span class="bot-subbullet-dot">•</span>` +
          `<div class="bot-subbullet-text">${formatInline(content)}</div>` +
        `</div>`
      );
      continue;
    }
    // Top-level bullet item: "- ..." or "• ..."
    if (bulletMatch) {
      flushStep();
      blocks.push(
        `<div class="bot-bullet-row">` +
          `<span class="bot-bullet-dot">•</span>` +
          `<div class="bot-bullet-text">${formatInline(bulletMatch[1])}</div>` +
        `</div>`
      );
      continue;
    }
    // Italicized note / disclaimer line: "*Note: ...*" or "*Please confirm...*"
    if (/^\*[^\*]+\*$/.test(trimmed)) {
      flushStep();
      blocks.push(`<div class="bot-note-callout">${formatInline(trimmed)}</div>`);
      continue;
    }
    // Section sub-heading: "### Heading" or standalone "**Heading**"
    if (/^#{1,3}\s+/.test(trimmed) || /^\*\*[^\*]+\*\*$/.test(trimmed)) {
      flushStep();
      const cleanSub = trimmed.replace(/^#{1,3}\s+/, "");
      blocks.push(`<div class="bot-section-subheading">${formatInline(cleanSub)}</div>`);
      continue;
    }
    // Standard paragraph
    flushStep();
    blocks.push(`<div class="bot-paragraph">${formatInline(trimmed)}</div>`);
  }
  flushStep();
  let finalHtml = `<div class="bot-structured-response">${blocks.join("")}</div>`;
  // 7. Safely restore all link tokens without risk of re-processing
  finalHtml = finalHtml.replace(/%%BOT_TOKEN_(\d+)%%/g, (match, id) => {
    return tokens[parseInt(id, 10)] || "";
  });
  return finalHtml + sourcesHtml;
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
  const pad = (n) => String(n).padStart(2, "0");
  const fmtUtc = (daysAhead, hourUtc) => {
    const d = new Date(Date.now() + daysAhead * 86400000);
    return `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}T${pad(hourUtc)}5900Z`;
  };
  const icsContent =
    "BEGIN:VCALENDAR\r\n" +
    "VERSION:2.0\r\n" +
    "PRODID:-//VSE Prague//Demo Coursework Deadlines//EN\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:4IT445 Milestone 2 - Data Pipeline Report (Demo)\r\n" +
    "DESCRIPTION:Demo coursework vault submission in InSIS. Weight 25 pts.\r\n" +
    `DTSTART:${fmtUtc(3, 21)}\r\n` +
    `DTEND:${fmtUtc(3, 22)}\r\n` +
    "END:VEVENT\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:4SA421 Enterprise Architecture Case Study (Demo)\r\n" +
    "DESCRIPTION:Demo TOGAF ADM submission in InSIS. Weight 30 pts.\r\n" +
    `DTSTART:${fmtUtc(10, 21)}\r\n` +
    `DTEND:${fmtUtc(10, 22)}\r\n` +
    "END:VEVENT\r\n" +
    "BEGIN:VEVENT\r\n" +
    "SUMMARY:Master's Thesis Abstract & PDF/A Submission Deadline (Demo)\r\n" +
    "DESCRIPTION:Required by § 47b in InSIS.\r\n" +
    `DTSTART:${fmtUtc(18, 21)}\r\n` +
    `DTEND:${fmtUtc(18, 22)}\r\n` +
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

// -----------------------------------------------------------------------------
// 7. Initial Startup & Browser History Listener
// -----------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  const clockEl = document.getElementById("demo-live-clock");
  if (clockEl) {
    const now = new Date();
    clockEl.textContent = "🕒 " + now.toLocaleString("en-US", {
      month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit"
    });
  }
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
