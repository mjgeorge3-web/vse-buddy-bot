// =============================================================================
// Authentic InSIS Multi-URL Router, Session Controller & VŠE Buddy Bot Logic
// Supports all 195 InSIS URLs with persistent login across all pages
// =============================================================================

let allUrlsList = [];
let chatHistory = [];
let hasEnteredInfo = false;
let hasUploadedPdf = false;
let isThesisSubmitted = false;

// -----------------------------------------------------------------------------
// 1. Session & Login Controller
// -----------------------------------------------------------------------------
function getLoginSession() {
  const loggedIn = localStorage.getItem("insis_logged_in");
  const userName = localStorage.getItem("insis_user_name") || "George Joseph";
  // Default to logged in as George Joseph if not explicitly logged out
  if (loggedIn === null) {
    localStorage.setItem("insis_logged_in", "true");
    localStorage.setItem("insis_user_name", "George Joseph");
    return { loggedIn: true, userName: "George Joseph" };
  }
  return { loggedIn: loggedIn === "true", userName };
}

function updateSessionUI() {
  const session = getLoginSession();
  const loggedInBar = document.getElementById("user-info-logged-in");
  const loggedOutBar = document.getElementById("user-info-logged-out");
  const displayUser = document.getElementById("display-user-name");

  if (session.loggedIn) {
    if (loggedInBar) loggedInBar.style.display = "flex";
    if (loggedOutBar) loggedOutBar.style.display = "none";
    if (displayUser) displayUser.textContent = session.userName;
  } else {
    if (loggedInBar) loggedInBar.style.display = "none";
    if (loggedOutBar) loggedOutBar.style.display = "flex";
  }
}

function performLogout() {
  localStorage.setItem("insis_logged_in", "false");
  updateSessionUI();
  showLoginView();
  alert("You have been logged out of InSIS. The session has been terminated.");
}

function handleLoginSubmit(event) {
  if (event) event.preventDefault();
  const usernameInput = document.getElementById("login-username");
  const name = usernameInput && usernameInput.value.trim() ? usernameInput.value.trim() : "George Joseph";
  localStorage.setItem("insis_logged_in", "true");
  localStorage.setItem("insis_user_name", name);
  updateSessionUI();

  // Redirect to target URL or default Personal administration
  const pendingUrl = sessionStorage.getItem("insis_pending_url") || "https://insis.vse.cz/auth/?lang=en";
  sessionStorage.removeItem("insis_pending_url");
  navigateToUrl(pendingUrl);
  alert(`Welcome, ${name}! You are now logged in to InSIS. This session is active across all pages.`);
}

function showLoginView() {
  hideAllViews();
  const loginView = document.getElementById("view-login");
  if (loginView) loginView.style.display = "block";
  document.getElementById("insis-url-input").value = "https://insis.vse.cz/auth/login";
  document.getElementById("breadcrumb-dynamic").innerHTML = "&raquo; Log in to InSIS";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function hideAllViews() {
  const views = [
    "view-personal-admin",
    "view-student-portal",
    "view-master-thesis",
    "view-generic-page",
    "view-login"
  ];
  views.forEach((v) => {
    const el = document.getElementById(v);
    if (el) el.style.display = "none";
  });
}

// -----------------------------------------------------------------------------
// 2. URL Navigator & Fast Selector (All 195 URLs)
// -----------------------------------------------------------------------------
async function loadInsisUrls() {
  try {
    const resp = await fetch("/api/insis-links");
    if (resp.ok) {
      allUrlsList = await resp.json();
    } else {
      // Fallback
      const resp2 = await fetch("all_urls.json");
      allUrlsList = await resp2.json();
    }
  } catch (e) {
    console.warn("Could not load /api/insis-links, using embedded list:", e);
  }

  populateUrlDropdown();
}

function populateUrlDropdown() {
  const select = document.getElementById("insis-url-select");
  if (!select || !allUrlsList.length) return;

  select.innerHTML = '<option value="">-- Jump to any of 195 InSIS URLs --</option>';

  // Group by category
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
    "Admissions & Applications": [],
    "People, Departments & Cards": [],
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
      groups["Admissions & Applications"].push(item);
    } else if (u.includes("/katalog") || u.includes("syllabus")) {
      groups["Course Catalogue & Syllabi"].push(item);
    } else if (u.includes("/lide") || u.includes("/pracoviste") || u.includes("/karty")) {
      groups["People, Departments & Cards"].push(item);
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
  if (url) {
    navigateToUrl(url);
  }
}

function handleGoUrl() {
  const url = document.getElementById("insis-url-input").value.trim();
  if (url) {
    navigateToUrl(url);
  }
}

function handleUrlKey(event) {
  if (event.key === "Enter") {
    handleGoUrl();
  }
}

// -----------------------------------------------------------------------------
// 3. Central Page Router
// -----------------------------------------------------------------------------
function navigateToUrl(fullUrl) {
  const inputEl = document.getElementById("insis-url-input");
  if (inputEl) inputEl.value = fullUrl;

  const session = getLoginSession();

  // If navigating to an authenticated URL while logged out: prompt login
  if (fullUrl.includes("/auth/") && !session.loggedIn) {
    sessionStorage.setItem("insis_pending_url", fullUrl);
    showLoginView();
    return;
  }

  // Find metadata from allUrlsList
  const matched = allUrlsList.find((x) => x.url === fullUrl) || {
    title: "InSIS Application",
    url: fullUrl,
    access: fullUrl.includes("/auth/") ? "AUTHENTICATED" : "PUBLIC",
  };

  hideAllViews();

  // Clean pathname
  const cleanPath = fullUrl.replace("https://insis.vse.cz", "").split("?")[0];

  // Specific high-fidelity views matching screenshots
  if (cleanPath === "/auth/" || cleanPath === "/auth") {
    document.getElementById("view-personal-admin").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML = "&raquo; Personal administration";
  } else if (cleanPath === "/auth/student/studium.pl") {
    document.getElementById("view-student-portal").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML = '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/student/studium.pl?lang=en\')">My College</a>';
  } else if (cleanPath === "/auth/student/zp.pl") {
    document.getElementById("view-master-thesis").style.display = "block";
    document.getElementById("breadcrumb-dynamic").innerHTML = '&raquo; <a href="#" onclick="navigateToUrl(\'https://insis.vse.cz/auth/student/studium.pl?lang=en\')">My College</a> &raquo; <strong>Master\'s thesis</strong>';
  } else {
    // Render dynamic generic InSIS view
    renderGenericInsisPage(cleanPath, fullUrl, matched);
  }

  // Sync browser address bar without reload
  try {
    const localPath = cleanPath + (fullUrl.includes("?") ? "?" + fullUrl.split("?")[1] : "");
    window.history.pushState({}, matched.title, localPath);
  } catch (e) {}

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// -----------------------------------------------------------------------------
// 4. Dynamic InSIS Page Content Generator for All Other 54 Path Types
// -----------------------------------------------------------------------------
function renderGenericInsisPage(path, fullUrl, meta) {
  const genericView = document.getElementById("view-generic-page");
  const titleEl = document.getElementById("generic-page-title");
  const subEl = document.getElementById("generic-page-sub");
  const contentEl = document.getElementById("generic-page-content");
  const breadcrumbEl = document.getElementById("breadcrumb-dynamic");

  genericView.style.display = "block";
  titleEl.textContent = meta.title;
  subEl.textContent = `InSIS VŠE • ${meta.access === "AUTHENTICATED" ? "Authenticated Application (George Joseph)" : "Public Portal"}`;
  breadcrumbEl.innerHTML = `&raquo; <a href="#" onclick="navigateToUrl('https://insis.vse.cz/auth/?lang=en')">InSIS</a> &raquo; <strong>${meta.title}</strong>`;

  let html = "";

  if (path.includes("kontrola_planu.pl")) {
    html = `
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #e2e8f0; padding-bottom:8px; margin-bottom:14px;">
        <h3 style="font-size:16px; color:#004b87;">Check of Study Plan &amp; Credit Vouchers</h3>
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
  } else if (path.includes("rozvrhy_view.pl")) {
    html = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <h3 style="font-size:16px; color:#004b87;">Weekly Timetable &amp; Schedule (Winter Semester 2026/2027)</h3>
        <button onclick="alert('iCal subscription feed link copied!')" style="background:#005596; color:white; border:none; padding:6px 12px; border-radius:4px; font-weight:700; cursor:pointer;">🔗 iCal Feed Export</button>
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
        Study: <strong>FIS C-ISM-MBI pres</strong> • Academic Year: 2026/2027. Registration for defense slots and oral state examination dates opens following final thesis approval.
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
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Study Financing &amp; Payments</h3>
      <table class="thesis-info-table" style="margin-bottom:18px;">
        <tr><td class="label-cell">Bank Account (CZK):</td><td class="value-cell"><strong>19-2696090207 / 0100</strong> (Komerční banka)</td></tr>
        <tr><td class="label-cell">IBAN:</td><td class="value-cell"><code>CZ04 0100 0000 1926 9609 0207</code></td></tr>
        <tr><td class="label-cell">Your Variable Symbol (VS):</td><td class="value-cell"><strong style="color:#005596; font-size:15px;">84920194</strong> <em>(Mandatory to identify your student account!)</em></td></tr>
        <tr><td class="label-cell">Payment Status:</td><td class="value-cell"><span style="color:#16a34a; font-weight:700;">All Tuition &amp; Obligations Cleared (0.00 CZK balance)</span></td></tr>
      </table>
      <button onclick="alert('Card payment gateway 3DS Secure: 0.00 CZK outstanding')" style="background:#005596; color:white; border:none; padding:8px 14px; border-radius:4px; font-weight:700; cursor:pointer;">💳 Open Card Payment Gateway</button>
    `;
  } else if (path.includes("potvrzeni.pl")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Electronic Confirmation of Study (Potvrzení o studiu)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Generate an official digitally signed PDF document bearing the qualified electronic stamp of VŠE. Accepted by Foreign Police, OAMP MVČR, transit authorities (PID / Lítačka), banks, and embassies.
      </p>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:16px; margin-bottom:14px;">
        <strong>Student:</strong> George Joseph (FIS ISM Master)<br>
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
  } else if (path.includes("katalog")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Course Catalogue Search (/katalog/)</h3>
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
  } else if (path.includes("prihlaska")) {
    html = `
      <h3 style="font-size:16px; color:#004b87; margin-bottom:10px;">Electronic Application to Study at VŠE (/prihlaska/)</h3>
      <p style="font-size:12px; color:#475569; margin-bottom:14px;">
        Official admission application portal for Bachelor's, Master's, and Doctoral programmes at the Prague University of Economics and Business.
      </p>
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:16px;">
        <h4 style="font-size:13px; color:#004b87; margin-bottom:6px;">Degree Programmes Offered in English:</h4>
        <ul style="font-size:12px; line-height:1.7; margin-left:20px;">
          <li>Master in Information Systems Management (ISM) &bull; Faculty of Informatics and Statistics</li>
          <li>Master in Finance and Accounting (MIFA) &bull; Faculty of Finance and Accounting</li>
          <li>International Management (CEMS / MIM) &bull; Faculty of Business Administration</li>
          <li>International and Diplomatic Studies (IDS) &bull; Faculty of International Relations</li>
        </ul>
      </div>
    `;
  } else {
    // Default authentic InSIS module template
    html = `
      <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:18px;">
        <h4 style="font-size:14px; color:#004b87; margin-bottom:8px;">${meta.title}</h4>
        <p style="font-size:12px; color:#475569; line-height:1.6; margin-bottom:12px;">
          Official InSIS service endpoint: <code>${meta.url}</code><br>
          Access Level: <strong>${meta.access}</strong> &bull; User Context: <strong>${session.loggedIn ? session.userName + " (Authenticated)" : "Public User"}</strong>
        </p>
        <div style="font-size:12px; color:#334155; line-height:1.6;">
          This InSIS application is fully integrated into the Master's Thesis research environment. Use the top URL navigator to jump across any of the 195 scraped URLs, or ask the embedded VŠE Buddy Bot for assistance!
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
  const text = `
PRAGUE UNIVERSITY OF ECONOMICS AND BUSINESS (VŠE)
FACULTY OF INFORMATICS AND STATISTICS (FIS)
------------------------------------------------------------------------
ELECTRONIC CONFIRMATION OF STUDY (POTVRZENÍ O STUDIU)
Student: George Joseph
Student ID: x_jose01
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
  a.download = "Confirmation_of_Study_George_Joseph_VSE.txt";
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

function openSearchModal() {
  const q = prompt("Thematic search across InSIS (e.g. thesis, errata, credits, timetable):");
  if (q) {
    const ql = q.toLowerCase();
    if (ql.includes("errata") || ql.includes("thesis")) {
      navigateToUrl("https://insis.vse.cz/auth/student/zp.pl?lang=en");
    } else if (ql.includes("credit") || ql.includes("voucher")) {
      navigateToUrl("https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en");
    } else if (ql.includes("rozvrh") || ql.includes("timetable")) {
      navigateToUrl("https://insis.vse.cz/auth/katalog/rozvrhy_view.pl?lang=en");
    } else {
      navigateToUrl("https://insis.vse.cz/katalog/?lang=en");
    }
  }
}

function openHelpModal() {
  alert("InSIS Help: Click the floating VŠE Buddy Bot in the bottom right corner for immediate verified guidance!");
}

// -----------------------------------------------------------------------------
// 6. Floating VŠE Buddy Bot Logic
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

      // Contextual action button linking to current InSIS page
      const ql = query.toLowerCase();
      if (ql.includes("errata") || ql.includes("thesis")) {
        appendContextLink("📜 Open Master's Thesis & Errata Page in InSIS", () => {
          navigateToUrl("https://insis.vse.cz/auth/student/zp.pl?lang=en");
          toggleBotDrawer();
        });
      } else if (ql.includes("voucher") || ql.includes("credit")) {
        appendContextLink("📊 Open Credit Voucher Wallet (120/144)", () => {
          navigateToUrl("https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en");
          toggleBotDrawer();
        });
      } else if (ql.includes("confirm") || ql.includes("study")) {
        appendContextLink("📄 Open Electronic Confirmation of Study", () => {
          navigateToUrl("https://insis.vse.cz/auth/student/potvrzeni.pl?lang=en");
          toggleBotDrawer();
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
      "• You must earn at least **9 ECTS** in your first semester, or **20 ECTS** across any two consecutive semesters [07-study-regulations-and-credit-system.md].";
  } else {
    return "I found information from verified VŠE documentation. Feel free to explore the modules in InSIS or ask for specific details!";
  }
}

// -----------------------------------------------------------------------------
// 7. Initial Startup & History Listener
// -----------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  updateSessionUI();
  loadInsisUrls();

  // Route initial URL
  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const initialUrl = "https://insis.vse.cz" + (currentPath === "/" ? "/auth/?lang=en" : currentPath + currentSearch);
  navigateToUrl(initialUrl);
});

window.addEventListener("popstate", () => {
  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const url = "https://insis.vse.cz" + (currentPath === "/" ? "/auth/?lang=en" : currentPath + currentSearch);
  navigateToUrl(url);
});
