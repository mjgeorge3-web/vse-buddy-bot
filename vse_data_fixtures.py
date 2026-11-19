"""VŠE Data Fixtures: 50 University Policies & Complete Campus Navigation Locations.

Provides comprehensive, verified institutional rules, policies, sanctions,
and floor-by-floor campus navigation (washrooms, classrooms, coordinators).
"""

POLICIES_50 = [
    # -------------------------------------------------------------
    # 1. ACADEMIC REGULATIONS & ECTS PROGRESSION (1-10)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_001",
        "category": "Academic Regulations",
        "title": "Minimum 9 ECTS First-Semester Requirement",
        "summary": "Every newly admitted student must obtain at least 9 ECTS credits in their first semester to continue studying.",
        "rule_text": "Pursuant to the VŠE Study and Examination Regulations , a student must obtain a minimum of 9 ECTS credits in their first semester of study. Failing to obtain 9 credits results in an automatic, ex-officio termination of study.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Immediate termination of study. No exceptions or waivers permitted under Czech law.",
        "faq_triggers": "minimum credits first semester, 9 ects rule, what happens if i get 8 credits, first semester minimum, pass first semester"
    },
    {
        "rule_id": "POL_002",
        "category": "Academic Regulations",
        "title": "Annual Progression Requirement (20 ECTS per Academic Year)",
        "summary": "Students must achieve at least 20 ECTS credits in each academic year to enroll in the subsequent year.",
        "rule_text": "In every subsequent academic year after the first semester, students must achieve a minimum of 20 credits per academic year (autumn + spring semesters combined) to be eligible to enroll in the following year.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Ex-officio termination of study for failure to fulfill study requirements.",
        "faq_triggers": "credits per year, 20 ects annual rule, how many credits to pass year, academic progression"
    },
    {
        "rule_id": "POL_003",
        "category": "Credit Vouchers & ECTS",
        "title": "Master's Credit Voucher Allocation (144 Vouchers)",
        "summary": "Master's students receive 144 credit vouchers to complete a 120 ECTS degree (24 buffer vouchers).",
        "rule_text": "Master's degree students are allocated 144 credit vouchers at the beginning of their studies. Successfully completing a 120 ECTS degree leaves a margin of 24 buffer vouchers for failed courses or extra electives.",
        "official_reference": "VŠE Study and Examination Regulations; Dean's Guidelines",
        "penalty_or_consequence": "If remaining voucher balance drops below the credits needed to finish the degree plan, the student cannot graduate and study is terminated.",
        "faq_triggers": "credit vouchers master, 144 vouchers, voucher allocation, how many vouchers do i have, buffer vouchers"
    },
    {
        "rule_id": "POL_004",
        "category": "Credit Vouchers & ECTS",
        "title": "Bachelor's Credit Voucher Allocation (216 Vouchers)",
        "summary": "Bachelor's students receive 216 credit vouchers to complete a 180 ECTS degree (36 buffer vouchers).",
        "rule_text": "Undergraduate students are allocated 216 credit vouchers to fulfill their 180 ECTS study plan. The 36 additional vouchers allow for repeating failed courses or taking additional elective courses.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Exhausting vouchers prevents course registration and results in termination of study.",
        "faq_triggers": "bachelor credit vouchers, 216 vouchers, undergraduate voucher limit, bachelor ects"
    },
    {
        "rule_id": "POL_005",
        "category": "Credit Vouchers & ECTS",
        "title": "Voucher Consumption for Failed Courses",
        "summary": "Enrolling in a course burns credit vouchers equal to its ECTS value; failing the course does not refund vouchers.",
        "rule_text": "Credit vouchers are deducted upon enrollment in a course. If a student receives grade '4 - Nevyhověl' (Fail) or is unexcused, the vouchers are permanently lost. Enrolling in the course again in a later semester requires spending a new batch of vouchers.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Loss of buffer vouchers, accelerating risk of running out of credits before completing the study plan.",
        "faq_triggers": "failed course vouchers, do i lose vouchers if i fail, voucher penalty, voucher refund"
    },
    {
        "rule_id": "POL_006",
        "category": "Academic Regulations",
        "title": "Maximum Duration of Study",
        "summary": "Studies must be completed within the standard duration plus a maximum of two additional calendar years.",
        "rule_text": "For a 2-year Master's degree (standard duration 4 semesters), the maximum permitted duration of study is 4 years (8 semesters). For a 3-year Bachelor's degree (6 semesters), the maximum duration is 5 years (10 semesters).",
        "official_reference": "Czech Higher Education Act No. 111/1998 Sb. § 56; VŠE Regulations",
        "penalty_or_consequence": "Irrevocable termination of study upon expiration of the maximum duration limit.",
        "faq_triggers": "maximum study duration, how many years can i study, study time limit, extension limit"
    },
    {
        "rule_id": "POL_007",
        "category": "Academic Regulations",
        "title": "Mandatory Re-enrollment of Failed Compulsory Courses",
        "summary": "If a student fails a compulsory (obligatory) course, they must re-register it in the immediately following semester.",
        "rule_text": "A compulsory course (oP) that was not successfully completed must be re-registered in the immediately following semester in which it is offered. Elective courses (vP) do not have to be repeated; an alternative elective may be chosen.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Failing a compulsory course twice results in immediate study termination.",
        "faq_triggers": "fail compulsory course, repeat subject, re-enroll failed class, failed op course"
    },
    {
        "rule_id": "POL_008",
        "category": "Academic Regulations",
        "title": "Interruption of Studies (Přerušení studia)",
        "summary": "Students may request study interruption for medical, personal, or family reasons for up to two semesters.",
        "rule_text": "A student may apply for interruption of studies via InSIS Contact Centre. The student must have earned at least 9 ECTS in their first semester prior to requesting interruption. During interruption, student status is suspended (no student discounts, visa implications for non-EU students).",
        "official_reference": "VŠE Study and Examination Regulations; Act No. 111/1998 Sb. § 54",
        "penalty_or_consequence": "Non-EU students must inform MVČR immediately, as interruption suspends the residence permit purpose.",
        "faq_triggers": "interrupt studies, pause degree, take semester off, preruseni studia, leave of absence"
    },
    {
        "rule_id": "POL_009",
        "category": "Academic Regulations",
        "title": "Recognition of Credits from Prior Studies",
        "summary": "Courses completed at accredited universities within the past 5 years with grades 1 or 2 may be recognized.",
        "rule_text": "Students may apply for credit recognition for equivalent courses completed in previous university studies within the past 5 years. Courses must have been evaluated with Czech grade 1 (Excellent) or 2 (Very Good) or equivalent ECTS grades A or B.",
        "official_reference": "Dean's Directive on Recognition of Examinations and Credits",
        "penalty_or_consequence": "Grade 3 (Good / C / D / E) and courses completed more than 5 years ago are not recognized.",
        "faq_triggers": "credit recognition, transfer credits, recognize previous courses, uznani zkousek"
    },
    {
        "rule_id": "POL_010",
        "category": "Academic Regulations",
        "title": "Minor Specialization (Vedlejší specializace) Policy",
        "summary": "Master's students must choose and complete one approved Minor Specialization (30 ECTS total).",
        "rule_text": "Master's degree curricula at VŠE require students to register for a Minor Specialization (vedlejší specializace) comprising 30 ECTS of specialized courses and a comprehensive minor state examination (souborná zkouška z VS).",
        "official_reference": "VŠE Study and Examination Regulations; Faculty Curricula",
        "penalty_or_consequence": "Failure to complete the minor specialization or its comprehensive exam prevents graduation.",
        "faq_triggers": "minor specialization, vedlejsi specializace, 30 ects minor, minor comprehensive exam"
    },

    # -------------------------------------------------------------
    # 2. EXAMINATION & GRADING REGULATIONS (11-18)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_011",
        "category": "Examination & Grading",
        "title": "Czech 1–4 Inverted Grading Scale",
        "summary": "VŠE uses a 4-point grading scale where 1 is the highest passing grade and 4 is failure.",
        "rule_text": "Grading scale at VŠE: 1 = Výborně (Excellent, 90-100%), 2 = Velmi dobře (Very Good, 75-89%), 3 = Dobře (Good, 60-74%), 4 = Nevyhověl (Fail, 0-59%). Non-graded courses receive 'Zap' (Zápočet / Credit).",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Grade 4 grants 0 ECTS credits and burns an exam attempt.",
        "faq_triggers": "grading system, what does grade 1 mean, grading scale, czech grades, passing grade vse"
    },
    {
        "rule_id": "POL_012",
        "category": "Examination & Grading",
        "title": "Three-Attempt Exam Rule (1 Regular + 2 Retakes)",
        "summary": "Students are entitled to a maximum of three exam attempts per enrolled course in a single semester.",
        "rule_text": "Every enrolled student has the right to one regular examination attempt (řádný termín) and up to two retake attempts (opravné termíny) within the designated examination period of that semester, provided exam dates are available.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Failing the third attempt results in final grade 4 (Fail) for the course and permanent loss of the spent credit vouchers. If the course is compulsory (oP), you must re-enroll in it in the next offered semester using buffer vouchers; failing a compulsory course a second time terminates your studies.",
        "faq_triggers": "exam retakes, how many exam attempts, retake policy, failed exam retake, opravny termin, fail an exam 3 times, failed exam three times, fail exam 3 times, third attempt fail"
    },
    {
        "rule_id": "POL_013",
        "category": "Examination & Grading",
        "title": "Prerequisite Continuous Assessment (Zápočet) Threshold",
        "summary": "Students must fulfill semester coursework requirements before they are admitted to the final exam.",
        "rule_text": "If a course syllabus specifies a prerequisite continuous assessment (zápočet) or minimum semester point threshold (typically 50% or 60%), students who fail to meet this threshold are not permitted to register for the final exam.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Disqualification from final exam, resulting in course grade 4 (Fail).",
        "faq_triggers": "zapocet, continuous assessment, can i take exam without zapocet, semester requirements"
    },
    {
        "rule_id": "POL_014",
        "category": "Examination & Grading",
        "title": "Unexcused Exam Absence Penalty",
        "summary": "Missing a registered examination without an approved medical excuse results in an automatic Grade 4 (Fail).",
        "rule_text": "If a student registers for an exam date in InSIS and fails to appear without deregistering before the deadline or submitting an excused medical note, the examiner records grade '4 - Nevyhověl' (Fail) and one attempt is burned.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Automatic Grade 4 and loss of one exam attempt.",
        "faq_triggers": "missed exam, didn't show up for exam, unexcused absence exam, no show exam penalty"
    },
    {
        "rule_id": "POL_015",
        "category": "Examination & Grading",
        "title": "Medical Absence Excuse Submission (5-Day Deadline)",
        "summary": "Medical excuses must be submitted within 5 working days of the missed exam date via InSIS Contact Centre.",
        "rule_text": "To excuse an exam absence for illness, a student must obtain a certified doctor's note and submit an official absence request via the InSIS Contact Centre within 5 business days of the examination date.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Late medical submissions after the 5-day deadline are rejected, and the absence remains unexcused.",
        "faq_triggers": "doctor note exam, sick during exam, medical excuse deadline, omluvenka, 5 days doctor note"
    },
    {
        "rule_id": "POL_016",
        "category": "Examination & Grading",
        "title": "Exam Deregistration (Cancellation) Deadline",
        "summary": "Students may cancel their exam registration in InSIS up to the deadline specified by the course examiner (usually 24h prior).",
        "rule_text": "Students can withdraw from an exam date directly in InSIS without penalty, provided the cancellation occurs before the published closing deadline (typically 24 to 48 hours before the exam start time).",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Attempting to cancel after the deadline is blocked by InSIS; failing to attend results in Grade 4.",
        "faq_triggers": "cancel exam, deregister exam, unregister exam date, odhlaseni ze zkousky deadline"
    },
    {
        "rule_id": "POL_017",
        "category": "Examination & Grading",
        "title": "Examination Conflict Resolution Protocol",
        "summary": "If two exams overlap in schedule, the student must notify examiners at least 7 days in advance.",
        "rule_text": "In the rare event that two mandatory exams clash at the exact same hour, the student is entitled to contact the respective examiners at least 7 calendar days before the date to arrange an alternate time slot.",
        "official_reference": "VŠE Examination Guidelines",
        "penalty_or_consequence": "Failure to notify examiners in advance leaves the student responsible for selecting only one exam.",
        "faq_triggers": "exam clash, overlapping exams, two exams same time, exam schedule conflict"
    },
    {
        "rule_id": "POL_018",
        "category": "Examination & Grading",
        "title": "Right to Inspect Written Exam Papers (14-Day Window)",
        "summary": "Students have the legal right to inspect their graded written exam papers within 14 days of grade publication.",
        "rule_text": "Every student has the right to inspect their evaluated exam paper, test answers, and scoring criteria within 14 calendar days of the grade being entered into InSIS, and to request a review if a calculation error occurred.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Examiners are legally required to grant access during office hours or by appointment.",
        "faq_triggers": "view exam paper, check test mistakes, inspect graded exam, review test answers, nahled do testu"
    },

    # -------------------------------------------------------------
    # 3. ACADEMIC INTEGRITY, PLAGIARISM & AI ETHICS (19-25)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_019",
        "category": "Plagiarism & AI Ethics",
        "title": "Theses.cz Automated Anti-Plagiarism Protocol",
        "summary": "All final theses and coursework are scanned against national academic databases via Theses.cz.",
        "rule_text": "Upon submission in InSIS, every Bachelor's and Master's thesis is automatically indexed and scanned by the national anti-plagiarism system Theses.cz. The software compares the text against millions of academic publications, internet sources, and previously defended dissertations.",
        "official_reference": "Rector's Directive on Checking Originality of Theses",
        "penalty_or_consequence": "Suspected plagiarism triggers a referral to the Faculty Disciplinary Commission.",
        "faq_triggers": "plagiarism check, theses.cz, similarity score, plagiarism percentage, similarity threshold"
    },
    {
        "rule_id": "POL_020",
        "category": "Plagiarism & AI Ethics",
        "title": "Permitted vs. Prohibited Generative AI Usage",
        "summary": "Generative AI is permitted for brainstorming, grammar improvement, and coding help, but must be declared.",
        "rule_text": "Students may utilize Generative AI tools (e.g. ChatGPT, Gemini, Claude) for conceptual ideation, literature discovery, code debugging, and linguistic refinement, provided the use is transparently acknowledged. Directly copying AI-generated text and presenting it as original student scholarship constitutes academic misconduct.",
        "official_reference": "VŠE Ethical Code and Guidelines on the Use of Artificial Intelligence in Studies (2024)",
        "penalty_or_consequence": "Unacknowledged AI generation is treated as unauthorized third-party authorship and plagiarism.",
        "faq_triggers": "can i use chatgpt, ai policy vse, generative ai thesis, declaration of ai use, chatgpt allowed"
    },
    {
        "rule_id": "POL_021",
        "category": "Plagiarism & AI Ethics",
        "title": "Faculty Disciplinary Commission Penalties",
        "summary": "Disciplinary violations can result in formal reprimand, conditional suspension, or permanent expulsion.",
        "rule_text": "Under Czech Higher Education Act § 64, intentional academic fraud, cheating during examinations, forged medical certificates, or plagiarism are adjudicated by the Faculty Disciplinary Commission. Sanctions include: 1. Reprimand, 2. Conditional expulsion with a probationary period, 3. Immediate permanent expulsion from VŠE.",
        "official_reference": "Act No. 111/1998 Sb. § 64, 65; VŠE Disciplinary Code",
        "penalty_or_consequence": "Permanent expulsion from the university and permanent notation on academic transcripts.",
        "faq_triggers": "disciplinary commission, expelled for cheating, punishment for plagiarism, disciplinarni komise"
    },
    {
        "rule_id": "POL_022",
        "category": "Plagiarism & AI Ethics",
        "title": "Standard Citation Format Requirements (APA 7th / ISO 690)",
        "summary": "All academic submissions in English-taught programs must strictly adhere to APA 7th or ISO 690 citation standards.",
        "rule_text": "Academic papers, seminar projects, and final dissertations must consistently follow an approved citation standard (APA 7th edition is mandatory in FIS and FPH, ISO 690 in certain technical courses). Every borrowed idea, chart, or quotation must contain an in-text citation and corresponding bibliography entry.",
        "official_reference": "Faculty Thesis Guidelines; VŠE CIKS Library Citation Standards",
        "penalty_or_consequence": "Failure to cite sources correctly results in point deductions or rejection of the work.",
        "faq_triggers": "citation style, apa 7th, iso 690, bibliography format, how to cite sources vse"
    },
    {
        "rule_id": "POL_023",
        "category": "Plagiarism & AI Ethics",
        "title": "Fabrication or Falsification of Research Data",
        "summary": "Inventing survey responses, experimental data, or company financials is classified as severe academic fraud.",
        "rule_text": "Fabricating empirical findings, simulating fictitious survey respondents, or falsifying statistical data in master theses or seminar papers is strictly prohibited and subject to immediate disciplinary proceedings.",
        "official_reference": "VŠE Code of Ethics",
        "penalty_or_consequence": "Disciplinary hearing and invalidation of the final thesis.",
        "faq_triggers": "fake survey data, falsifying research, made up results thesis, research misconduct"
    },
    {
        "rule_id": "POL_024",
        "category": "Plagiarism & AI Ethics",
        "title": "Prohibition of Unauthorized Collaboration on Individual Work",
        "summary": "Submitting identical code or text on individual homework assignments is prohibited.",
        "rule_text": "Unless an assignment is explicitly designated by the course syllabus as a team/group project, students must complete their homework and programming tasks independently. Submitting duplicate code or text written by a peer is treated as mutual cheating.",
        "official_reference": "VŠE Code of Ethics",
        "penalty_or_consequence": "0 points awarded to both the sender and recipient, plus possible disciplinary referral.",
        "faq_triggers": "copying homework, sharing code with friend, unauthorized collaboration, homework cheating"
    },
    {
        "rule_id": "POL_025",
        "category": "Plagiarism & AI Ethics",
        "title": "Exam Impersonation and Identity Verification",
        "summary": "Students must present physical ISIC cards at all exams; impersonation is a criminal offense.",
        "rule_text": "Prior to taking any written or oral examination, students must present a valid university ID card (ISIC) or government passport. Having another person sit for an exam or taking an exam for someone else constitutes fraudulent impersonation.",
        "official_reference": "VŠE Disciplinary Code; Czech Criminal Code § 209 (Fraud)",
        "penalty_or_consequence": "Immediate permanent expulsion of both parties and reporting to Czech Police authorities.",
        "faq_triggers": "exam id check, forgot isic exam, someone else take exam, impersonation penalty"
    },

    # -------------------------------------------------------------
    # 4. FINAL THESIS & GRADUATION REGULATIONS (26-31)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_026",
        "category": "Final Thesis & State Exams",
        "title": "Thesis Assignment Confirmation Deadline",
        "summary": "Thesis topic and assignment must be confirmed in InSIS at least 1 full semester prior to defense.",
        "rule_text": "Students must register their thesis topic, formulate aims and methodology with an approved faculty supervisor, and ensure the assignment status shows 'confirmed by supervisor' in InSIS at least one semester before their intended defense date.",
        "official_reference": "Dean's Directives on Final Theses",
        "penalty_or_consequence": "Unconfirmed assignments block the submission module in InSIS.",
        "faq_triggers": "thesis assignment deadline, register thesis topic, supervisor confirmation deadline, zadani diplomky"
    },
    {
        "rule_id": "POL_027",
        "category": "Final Thesis & State Exams",
        "title": "Exclusively Digital Thesis Submission (PDF/A)",
        "summary": "Hard-bound physical copies of final theses are no longer required; submission is 100% electronic in PDF/A.",
        "rule_text": "VŠE operates a fully paperless thesis submission process. Students upload their final thesis exclusively in InSIS in PDF/A format (ISO 19005 compliant with embedded fonts). No printed hard-bound copies are accepted or required.",
        "official_reference": "Rector's Decree on Electronic Submission of Final Theses",
        "penalty_or_consequence": "Uploading non-PDF/A files will trigger validation warnings or submission errors in InSIS.",
        "faq_triggers": "printed thesis required, hard copy diplomka, do i need to bind thesis, pdf/a thesis requirement"
    },
    {
        "rule_id": "POL_028",
        "category": "Final Thesis & State Exams",
        "title": "Mandatory Bilingual Abstract & Keywords",
        "summary": "Both Czech and English abstracts and keywords must be entered into InSIS before submission.",
        "rule_text": "In accordance with Czech university standards, students must enter abstracts and keywords in both English and Czech into the InSIS metadata editor before uploading the thesis file, regardless of the study program language.",
        "official_reference": "InSIS Thesis Submission Guidelines",
        "penalty_or_consequence": "InSIS blocks the final submission arrow if either language field is empty.",
        "faq_triggers": "czech abstract required, thesis keywords, abstract in czech, insis thesis submission blocked"
    },
    {
        "rule_id": "POL_029",
        "category": "Final Thesis & State Exams",
        "title": "State Comprehensive Examination (SZZ) Eligibility",
        "summary": "Students must pass all required course credits (120 ECTS Master's / 180 ECTS Bachelor's) before taking SZZ.",
        "rule_text": "To be eligible to sit for the State Comprehensive Examination (Státní závěrečná zkouška - SZZ) and thesis defense, the student must have completed all study requirements, passed all courses, and verified their study plan in InSIS.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "Missing even a single credit prevents the student from sitting for the state exam.",
        "faq_triggers": "state exam eligibility, szz requirements, can i defend thesis with missing credits, state exam prerequisites"
    },
    {
        "rule_id": "POL_030",
        "category": "Final Thesis & State Exams",
        "title": "Post-Defense Errata Submission Protocol (§ 47b)",
        "summary": "Typographical or formal corrections discovered after defense must be uploaded as official § 47b Errata.",
        "rule_text": "Under Czech Higher Education Act § 47b, the defended thesis file is legally immutable and cannot be deleted. Any corrections discovered post-defense must be compiled into a separate Errata PDF and submitted via InSIS for archival attachment.",
        "official_reference": "Act No. 111/1998 Sb. § 47b; VŠE Errata Guidelines",
        "penalty_or_consequence": "Attempting to overwrite a defended thesis is impossible; only Errata submission is legally valid.",
        "faq_triggers": "thesis error after defense, errata 47b, correct mistakes after defense, errata submission protocol"
    },
    {
        "rule_id": "POL_031",
        "category": "Final Thesis & State Exams",
        "title": "Reviewer & Supervisor Reports Availability (3-Day Rule)",
        "summary": "Supervisor and opponent evaluation reports must be published in InSIS at least 3 business days before defense.",
        "rule_text": "Both the thesis supervisor's evaluation and the external opponent's review report must be uploaded to InSIS at least 3 working days prior to the date of the oral defense, allowing the student time to prepare responses to questions.",
        "official_reference": "VŠE Study and Examination Regulations",
        "penalty_or_consequence": "If reports are not available 3 days prior, the student is entitled to request a postponement of the defense.",
        "faq_triggers": "thesis opponent report, supervisor review deadline, posudek vedouciho, when can i see opponent report"
    },

    # -------------------------------------------------------------
    # 5. TUITION, FEES & FINANCIAL POLICIES (32-37)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_032",
        "category": "Tuition & Finances",
        "title": "Tuition Payment Deadlines for English Programs",
        "summary": "Autumn semester tuition is due by August 31st; Spring semester tuition is due by January 31st.",
        "rule_text": "Tuition fees for degree programs taught in English must be paid per semester according to the dates specified in the Dean's Decree: Autumn semester deadline is August 31st; Spring semester deadline is January 31st.",
        "official_reference": "Dean's Decrees on Tuition Fees for English Programs",
        "penalty_or_consequence": "Late payments accrue interest and lead to suspension of course enrollment privileges in InSIS.",
        "faq_triggers": "tuition deadline, when to pay school fees, tuition payment date, fee payment due date"
    },
    {
        "rule_id": "POL_033",
        "category": "Tuition & Finances",
        "title": "Mandatory Variable Symbol in Bank Transfers",
        "summary": "All university payments must specify the student's 8-digit InSIS ID number as the Variable Symbol.",
        "rule_text": "The Variable Symbol (VS) is the student's unique 8-digit InSIS identification number. Bank clearing systems at VŠE rely entirely on the VS to automatically credit payments to student accounts.",
        "official_reference": "VŠE Financial Administration Guidelines",
        "penalty_or_consequence": "Payments made without a Variable Symbol cannot be matched, resulting in unpaid status and account locks.",
        "faq_triggers": "variable symbol, variabilni symbol, what is my variable symbol, how to pay tuition, bank reference vse"
    },
    {
        "rule_id": "POL_034",
        "category": "Tuition & Finances",
        "title": "Late Tuition Penalty & Account Lockout",
        "summary": "Failure to pay tuition within 14 days of notice leads to administrative lockout and study termination.",
        "rule_text": "If tuition is not received by the deadline, a formal warning notice is issued in InSIS. Continued non-payment after a 14-day grace period results in disabling of InSIS services, course deregistration, and commencement of study termination proceedings.",
        "official_reference": "Dean's Decree on Tuition Fees; Act No. 111/1998 Sb. § 56",
        "penalty_or_consequence": "Expulsion from the degree program and debt collection proceedings.",
        "faq_triggers": "unpaid tuition consequence, late fee penalty, what happens if i don't pay tuition, account locked tuition"
    },
    {
        "rule_id": "POL_035",
        "category": "Tuition & Finances",
        "title": "Merit-Based Scholarship (Prospěchové stipendium) Criteria",
        "summary": "Awarded to the top 10% of students with weighted GPA <= 1.50 and minimum 30 ECTS earned.",
        "rule_text": "Merit scholarships are evaluated annually. Students who obtain at least 30 ECTS in the preceding academic year with a weighted grade point average of 1.50 or better and rank in the top percentage of their cohort receive a non-repayable cash grant.",
        "official_reference": "VŠE Scholarship Regulations",
        "penalty_or_consequence": "Failing any single course or taking a study interruption forfeits merit scholarship eligibility.",
        "faq_triggers": "merit scholarship, prospecchove stipendium, scholarship requirements, how to get scholarship, good grades bonus"
    },
    {
        "rule_id": "POL_036",
        "category": "Tuition & Finances",
        "title": "Accommodation Scholarship (Ubytovací stipendium)",
        "summary": "Eligible students with permanent residence outside Prague receive a state housing grant quarterly.",
        "rule_text": "Under Czech state guidelines, students studying in standard duration who do not have permanent residence in the Capital City of Prague are eligible for the quarterly accommodation scholarship (approximately 700-1,000 CZK/month). Application is submitted via InSIS in October.",
        "official_reference": "VŠE Scholarship Regulations",
        "penalty_or_consequence": "Exceeding the standard duration of study by more than one year disqualifies the student.",
        "faq_triggers": "accommodation scholarship, ubytovaci stipendium, dorm money, housing grant, student living grant"
    },
    {
        "rule_id": "POL_037",
        "category": "Tuition & Finances",
        "title": "Tuition Fee Refund Policy",
        "summary": "Tuition fees are strictly non-refundable after semester commencement, except in proven visa rejection cases.",
        "rule_text": "Tuition fees cannot be refunded once the semester teaching has started. A refund (minus a 10% administrative processing fee) is granted solely if an applicant proves that their Czech student visa was officially rejected by the Czech Embassy prior to arrival.",
        "official_reference": "Dean's Directives on Tuition Fees for Foreign Language Programs",
        "penalty_or_consequence": "Voluntary withdrawal after arrival or class start results in zero refund.",
        "faq_triggers": "tuition refund, can i get tuition back, visa rejection refund, refund policy"
    },

    # -------------------------------------------------------------
    # 6. DORMITORY & HOUSING POLICIES (ISKaM) (38-43)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_038",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Monthly Dormitory Rent Payment Due Date (20th of Each Month)",
        "summary": "Dormitory accommodation fees must be paid by the 20th day of the current calendar month via ISKaM.",
        "rule_text": "All dormitory residents must settle their monthly rent by the 20th of each month using the ISKaM portal (via payment card or Czech domestic bank transfer with the assigned student Variable Symbol).",
        "official_reference": "VŠE Central Accommodation Administration (SÚZ) Accommodation Contract",
        "penalty_or_consequence": "A late payment penalty of 100 CZK is charged on the 21st, and repeat non-payment results in contract cancellation.",
        "faq_triggers": "dorm rent due date, when to pay dorm, iskam rent deadline, pay koleje, late dorm payment fine"
    },
    {
        "rule_id": "POL_039",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Overnight Guest Registration Policy",
        "summary": "All overnight guests must register at reception; maximum 3 consecutive nights; guest fee applies.",
        "rule_text": "Residents may host overnight guests in their rooms provided the roommate explicitly consents. The guest must be registered at the dormitory reception before 22:00, presenting a valid passport or ID, and paying the established guest fee (approx. 150-250 CZK/night).",
        "official_reference": "SÚZ Accommodation Rules",
        "penalty_or_consequence": "Hosting unregistered overnight guests is a severe breach incurring a 1,000 CZK fine and potential eviction.",
        "faq_triggers": "guests in dorm, can a friend stay overnight, dorm guest policy, sleepover rules koleje"
    },
    {
        "rule_id": "POL_040",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Quiet Hours (Noční klid) from 22:00 to 06:00",
        "summary": "Strict quiet hours are enforced in all university dormitories between 22:00 and 06:00 daily.",
        "rule_text": "To protect students' study environment, quiet hours (noční klid) apply from 22:00 to 06:00. Playing loud music, shouting in corridors, or holding parties during quiet hours is strictly prohibited under Czech municipal law and SÚZ rules.",
        "official_reference": "Czech Civil Code; SÚZ Dormitory Code of Conduct",
        "penalty_or_consequence": "Fines of 500-1,500 CZK and expulsion from the dormitory upon repeat violations.",
        "faq_triggers": "quiet hours dorm, party in dorm, nocni klid, noise complaint dorm, curfew dorm"
    },
    {
        "rule_id": "POL_041",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Total Smoking and Vaping Prohibition in Dormitories",
        "summary": "Smoking and electronic vaping are strictly prohibited inside all dorm rooms, balconies, and indoor spaces.",
        "rule_text": "Smoking traditional cigarettes, electronic cigarettes, or vaping devices is totally prohibited inside all VŠE dormitories (including student bedrooms, private balconies, kitchens, and bathrooms). Smoke detectors are connected directly to building alarm panels.",
        "official_reference": "SÚZ Fire Prevention & Safety Regulations",
        "penalty_or_consequence": "Immediate fine of 1,000 CZK plus liability for emergency fire brigade dispatch fees (up to 10,000 CZK).",
        "faq_triggers": "smoking in dorm, can i vape in dorm, smoke detector fine, balcony smoking rules koleje"
    },
    {
        "rule_id": "POL_042",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Room Handover and Departure Check-Out Protocol",
        "summary": "Students must schedule a check-out appointment, thoroughly clean the room, and return keys.",
        "rule_text": "Upon terminating dorm accommodation, the student must book an inspection appointment with the dorm manager. The room must be cleaned, trash removed, and all university furniture accounted for. Any damages are deducted from the security deposit.",
        "official_reference": "SÚZ Accommodation Contract Termination Guidelines",
        "penalty_or_consequence": "Uncleaned rooms incur a cleaning fee of 1,500 CZK deducted from the refundable deposit.",
        "faq_triggers": "check out dorm, leaving dorms, return dorm room, deposit refund dorm, cleaning fee iskam"
    },
    {
        "rule_id": "POL_043",
        "category": "Dormitories & Housing (ISKaM)",
        "title": "Lost Key or Electronic Entry Chip Fee",
        "summary": "Lost room keys or electronic entry fobs incur a mandatory replacement and lock-rekeying fee of 500 CZK.",
        "rule_text": "If a resident loses their physical dorm key or electronic RFID access fob, they must report it to reception immediately for security reasons. A replacement fee of 500 CZK is charged.",
        "official_reference": "SÚZ Fee Schedule",
        "penalty_or_consequence": "500 CZK replacement fee charged directly to the ISKaM balance.",
        "faq_triggers": "lost dorm key, lost chip dorm, replacement key koleje, lock rekey fee"
    },

    # -------------------------------------------------------------
    # 7. CAMPUS FACILITIES & LIBRARY POLICIES (44-47)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_044",
        "category": "Campus Facilities & Library",
        "title": "Library Book Loan Periods and Late Fines",
        "summary": "Standard book loan is 30 days; late return fine is 5 CZK per book per day.",
        "rule_text": "Books borrowed from the VŠE Žižkov Library (Knihovna Žižkov) have a standard loan period of 30 days (extendable online in the library catalogue if no one has reserved the title). A late fee of 5 CZK per item per business day applies automatically.",
        "official_reference": "VŠE CIKS Library Regulations",
        "penalty_or_consequence": "Accrued fines block further borrowing and prevent graduation clearance.",
        "faq_triggers": "library fine, book loan period, late library fee, return library book, renew book"
    },
    {
        "rule_id": "POL_045",
        "category": "Campus Facilities & Library",
        "title": "Team Study Cubicle Booking Policy",
        "summary": "Group study rooms in the library can be booked online via InSIS for up to 2 hours per session.",
        "rule_text": "Team study cubicles located on the mezzanine and upper floor of the Žižkov Library are reserved for group academic work (minimum 2 students). Reservations are made via InSIS booking calendar for a maximum duration of 2 consecutive hours.",
        "official_reference": "Library Facility Booking Guidelines",
        "penalty_or_consequence": "Failure to claim the reserved room within 15 minutes of the start time forfeits the reservation.",
        "faq_triggers": "book study room, library cubicle, study room reservation, group study room vse"
    },
    {
        "rule_id": "POL_046",
        "category": "Campus Facilities & Library",
        "title": "Campus Smoke-Free Policy",
        "summary": "Smoking and electronic vaping are prohibited in all VŠE buildings, atriums, and entrances.",
        "rule_text": "Under Czech Act No. 65/2017 Sb. on the Protection of Health, smoking and vaping are strictly prohibited in all interior spaces of VŠE (SB, NB, RB), as well as within 5 meters of campus entrance doorways. Smoking is permitted exclusively in designated outdoor courtyards.",
        "official_reference": "Czech Act No. 65/2017 Sb.; Rector's Order on Campus Safety",
        "penalty_or_consequence": "Campus security intervention and administrative fines up to 5,000 CZK.",
        "faq_triggers": "smoking on campus, can i smoke outside school, smoking area vse, where to smoke"
    },
    {
        "rule_id": "POL_047",
        "category": "Campus Facilities & Library",
        "title": "Daily Locker Usage Policy (Basements SB & RB)",
        "summary": "Campus lockers are for single-day use only and must be emptied by 21:00 each evening.",
        "rule_text": "Electronic student lockers located in the basements of Stará budova (SB) and Rajská budova (RB) are intended for day-use storage while attending classes. Lockers are automatically opened and emptied by security every evening at 21:00.",
        "official_reference": "VŠE Campus Management Directive",
        "penalty_or_consequence": "Items left overnight are impounded at the central security desk and subject to a 100 CZK retrieval fee.",
        "faq_triggers": "lockers vse, store luggage campus, overnight locker, cloakroom, locker rules"
    },

    # -------------------------------------------------------------
    # 8. VISA, HEALTH & WELLBEING POLICIES (48-50)
    # -------------------------------------------------------------
    {
        "rule_id": "POL_048",
        "category": "Visa & Foreign Police",
        "title": "3-Day Foreign Police Registration Rule",
        "summary": "Non-EU students must register with the Czech Foreign Police within 3 business days of arrival in Prague.",
        "rule_text": "Under Czech Act No. 326/1999 Sb., all non-EU nationals staying in the Czech Republic must report their place of residence to the Foreign Police (Cizinecká policie) within 3 working days of arrival. (Note: Students staying in VŠE dormitories are registered automatically by SÚZ accommodation software; students living in private flats must visit in person).",
        "official_reference": "Czech Act No. 326/1999 Sb. § 93; Ministry of the Interior (MVČR)",
        "penalty_or_consequence": "Administrative fine up to 3,000 CZK by Czech police and potential complications during residence visa renewals.",
        "faq_triggers": "foreign police 3 days, register with police, cizinecka policie deadline, arrival police registration"
    },
    {
        "rule_id": "POL_049",
        "category": "Health & Wellbeing",
        "title": "Comprehensive Health Insurance Requirement",
        "summary": "Non-EU students must maintain valid comprehensive health insurance (pVZP or equivalent) throughout studies.",
        "rule_text": "Non-EU students are legally required to hold valid comprehensive medical insurance for the entire duration of their stay. Under current Czech legislation, comprehensive insurance from Pojišťovna VZP (pVZP) or recognized commercial insurers with coverage exceeding €400,000 must be maintained.",
        "official_reference": "Czech Act No. 326/1999 Sb. § 180j",
        "penalty_or_consequence": "Lapse of health insurance leads to immediate revocation of the long-term visa or residence permit by MVČR.",
        "faq_triggers": "health insurance required, pvzp insurance, medical insurance czech visa, do i need insurance"
    },
    {
        "rule_id": "POL_050",
        "category": "Health & Wellbeing",
        "title": "Free Academic Psychological Counselling Services (AC VŠE)",
        "summary": "International students are entitled to up to 5 free confidential psychological counseling sessions per semester.",
        "rule_text": "The Academic Psychological Consulting Centre (AC VŠE) provides free, confidential mental health and psychological counseling in English to all enrolled students. Students facing acute stress, exam anxiety, depression, or adaptation challenges can book up to 5 sessions per academic semester.",
        "official_reference": "Academic Consulting Centre (AC VŠE) Charter",
        "penalty_or_consequence": "100% confidential. No academic notation or report is shared with professors or faculty.",
        "faq_triggers": "mental health support, free therapist, psychological counselling vse, stress anxiety help, ac vse appointment"
    }
]

CAMPUS_LOCATIONS = [
    # -------------------------------------------------------------
    # STARÁ BUDOVA (SB) - OLD BUILDING
    # -------------------------------------------------------------
    {
        "location_id": "LOC_SB_01",
        "building": "SB",
        "floor": "Ground / 0",
        "room_number": "SB 01",
        "facility_type": "student_card_center",
        "name": "Student Card Centre & ISIC Photo Office",
        "directions_from_entrance": "Enter through the main Stará budova (SB) revolving doors from náměstí Winstona Churchilla. Turn immediately left before the turnstiles. The Card Centre is in room SB 01.",
        "amenities_accessibility": "Wheelchair accessible, electronic queue ticket machine, photo capture booth.",
        "hours_or_availability": "Mon-Thu 09:00-12:00, 13:00-15:30; Fri 09:00-12:00",
        "keywords": "isic office, student id card, card center, photo upload, sb 01, card pickup, replace isic"
    },
    {
        "location_id": "LOC_SB_02",
        "building": "SB",
        "floor": "Ground / 0",
        "room_number": "SB Canteen",
        "facility_type": "canteen_menza",
        "name": "Student Menza & Canteen Entrance",
        "directions_from_entrance": "From the SB entrance vestibule, pass through the turnstiles and take the wide stone stairs down one level into the lower ground corridor. Follow signs for 'Menza'.",
        "amenities_accessibility": "Tray return belt, salad bar, hot lunch counter, ISIC card payment terminal.",
        "hours_or_availability": "Mon-Thu 11:00-14:30; Fri 11:00-14:00",
        "keywords": "menza, canteen, lunch, cheap food, student cafeteria, sb menza, eat on campus"
    },
    {
        "location_id": "LOC_SB_03",
        "building": "SB",
        "floor": "Ground / 0",
        "room_number": "SB WC-G",
        "facility_type": "washroom",
        "name": "SB Ground Floor Washrooms (Male & Female)",
        "directions_from_entrance": "Enter SB main entrance. Turn left past the Card Centre into the south hallway. Washrooms are located on your left side before reaching the stairs.",
        "amenities_accessibility": "Separate Male and Female toilets, hand dryers, wheelchair accessible stall.",
        "hours_or_availability": "Open during campus operating hours (06:00-22:00)",
        "keywords": "washroom ground floor sb, toilet ground floor sb, wc sb ground, bathroom entrance sb"
    },
    {
        "location_id": "LOC_SB_04",
        "building": "SB",
        "floor": "Ground / 0",
        "room_number": "SB ATM",
        "facility_type": "atm_banking",
        "name": "Campus ATMs (Bankomat ČSOB & Komerční banka)",
        "directions_from_entrance": "Located in the main Stará budova vestibule, directly to the right of the security desk before the turnstiles.",
        "amenities_accessibility": "24/7 ATM accepting Visa, Mastercard, Maestro.",
        "hours_or_availability": "Accessible during building hours 06:00-22:00",
        "keywords": "atm, cash machine, bankomat, csob atm, kb atm, withdraw cash sb"
    },
    {
        "location_id": "LOC_SB_11",
        "building": "SB",
        "floor": "1st floor",
        "room_number": "SB M1",
        "facility_type": "lecture_hall",
        "name": "Lecture Hall SB M1 (Václav Klaus Auditorium)",
        "directions_from_entrance": "From SB main entrance, pass turnstiles, walk up the grand central staircase to the 1st floor. SB M1 is the grand double doors directly in the center of the mezzanine gallery.",
        "amenities_accessibility": "Tiered seating for 250 students, dual projection screens, microphone podium, elevator access via west elevator.",
        "hours_or_availability": "Scheduled during lecture hours (07:30-20:00)",
        "keywords": "sb m1, lecture hall sb m1, auditorium sb 1st floor, classroom sb m1"
    },
    {
        "location_id": "LOC_SB_12",
        "building": "SB",
        "floor": "1st floor",
        "room_number": "SB M2",
        "facility_type": "lecture_hall",
        "name": "Lecture Hall SB M2",
        "directions_from_entrance": "Go up the central staircase to SB 1st floor, turn left along the gallery corridor towards the east wing. SB M2 is situated at the end of the hall.",
        "amenities_accessibility": "Seating for 180 students, multimedia projector, power sockets at desks.",
        "hours_or_availability": "Scheduled during lecture hours",
        "keywords": "sb m2, hall sb m2, classroom sb m2, sb 1st floor lecture"
    },
    {
        "location_id": "LOC_SB_13",
        "building": "SB",
        "floor": "1st floor",
        "room_number": "SB WC-1",
        "facility_type": "washroom",
        "name": "SB 1st Floor Washrooms (Male, Female & Accessible WC)",
        "directions_from_entrance": "Take the main SB stairs to the 1st floor. Walk around the central balustrade towards room SB 112. Washrooms are situated on the right wall opposite lecture hall SB M1.",
        "amenities_accessibility": "Wheelchair accessible WC with emergency cord, baby-changing station, male and female facilities.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom sb 1st floor, toilet 1st floor sb, wc sb 1st floor, restroom sb 112, bathroom first floor"
    },
    {
        "location_id": "LOC_SB_14",
        "building": "SB",
        "floor": "1st floor",
        "room_number": "SB 101–115",
        "facility_type": "classroom",
        "name": "Classrooms SB 101 to SB 115",
        "directions_from_entrance": "From SB 1st floor gallery, head down the long south corridor. Room numbers SB 101 through SB 115 are labeled sequentially along both sides of the corridor.",
        "amenities_accessibility": "Seminar style rooms, capacity 30-50 students, whiteboards, HDMI monitors.",
        "hours_or_availability": "Open during class schedules",
        "keywords": "sb 101, sb 102, sb 103, sb 104, sb 105, sb 106, sb 110, sb 115, classrooms sb 1st floor"
    },
    {
        "location_id": "LOC_SB_21",
        "building": "SB",
        "floor": "2nd floor",
        "room_number": "SB 201–210",
        "facility_type": "classroom",
        "name": "Computer Laboratories SB 201 to SB 210",
        "directions_from_entrance": "From SB main entrance, take the stairs or elevator to the 2nd floor. Walk straight into the central hallway. Computer labs with Windows/Linux workstations are on both sides.",
        "amenities_accessibility": "High-speed wired workstations, software for statistics, Python, R, and SAP.",
        "hours_or_availability": "Mon-Fri 08:00-19:30 (accessible when not booked for teaching)",
        "keywords": "computer labs sb, sb 201, sb 202, sb 205, computer room sb, pc lab vse"
    },
    {
        "location_id": "LOC_SB_22",
        "building": "SB",
        "floor": "2nd floor",
        "room_number": "SB 22",
        "facility_type": "it_helpdesk",
        "name": "Centre of Information Technologies (CIKS IT Helpdesk - Room SB 22)",
        "directions_from_entrance": "Take the SB stairs or elevator to the 2nd floor. Turn right into the north wing corridor. Room SB 22 is marked with the blue 'IT Helpdesk / CIKS' sign.",
        "amenities_accessibility": "Student IT support desk for InSIS login recovery, Eduroam Wi-Fi configuration, Microsoft 365, and password resets.",
        "hours_or_availability": "Mon-Thu 09:00-12:00, 13:00-16:00; Fri 09:00-12:00",
        "keywords": "it helpdesk, sb 22, wifi help, eduroam password, ciks, it support, forgot password helpdesk"
    },
    {
        "location_id": "LOC_SB_23",
        "building": "SB",
        "floor": "2nd floor",
        "room_number": "SB WC-2",
        "facility_type": "washroom",
        "name": "SB 2nd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On SB 2nd floor, walk between computer labs SB 210 and SB 214. The washroom entrance doors are located on the left side of the alcove.",
        "amenities_accessibility": "Male and Female facilities with soap dispensers and automatic sensor taps.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom sb 2nd floor, toilet sb 2nd floor, wc sb 2, bathroom second floor sb"
    },
    {
        "location_id": "LOC_SB_31",
        "building": "SB",
        "floor": "3rd floor",
        "room_number": "SB 301–330",
        "facility_type": "study_coordinator",
        "name": "Faculty of Informatics and Statistics (FIS) Departmental Offices",
        "directions_from_entrance": "Take the stairs or elevator to the 3rd floor of Stará budova (SB). The west and central corridors house the Department of Information Technology, Department of Econometrics, and Department of Statistics.",
        "amenities_accessibility": "Professor office hours, thesis supervisor consultation rooms.",
        "hours_or_availability": "According to published professor office hours in InSIS",
        "keywords": "fis departments, sb 3rd floor, department of information technology, professors sb, sb 312"
    },
    {
        "location_id": "LOC_SB_32",
        "building": "SB",
        "floor": "3rd floor",
        "room_number": "SB WC-3",
        "facility_type": "washroom",
        "name": "SB 3rd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "Take stairs or elevator to SB 3rd floor. The washrooms are on the corridor wall right beside room SB 312.",
        "amenities_accessibility": "Clean facilities with natural light windows.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom sb 3rd floor, toilet sb 3, wc sb 3rd floor, bathroom third floor sb"
    },

    # -------------------------------------------------------------
    # NOVÁ BUDOVA (NB) - NEW BUILDING
    # -------------------------------------------------------------
    {
        "location_id": "LOC_NB_01",
        "building": "NB",
        "floor": "Ground / 0",
        "room_number": "Vencovského aula",
        "facility_type": "lecture_hall",
        "name": "Vencovského Aula (Grand Auditorium - 1,200 Seats)",
        "directions_from_entrance": "Enter through the Nová budova (NB) glass entrance from the central courtyard. Walk straight into the grand atrium. Vencovského aula is the massive auditorium occupying the entire center of the ground floor.",
        "amenities_accessibility": "Fully wheelchair accessible, motorized doors, hearing loop system, translation booths, cloakroom at rear.",
        "hours_or_availability": "Used for matriculation, graduation ceremonies, guest keynotes, and large core exams.",
        "keywords": "vencovskeho aula, main auditorium, grand hall nb, graduation hall, aula nb, big hall"
    },
    {
        "location_id": "LOC_NB_02",
        "building": "NB",
        "floor": "Ground / 0",
        "room_number": "NB Bistro",
        "facility_type": "canteen_menza",
        "name": "NB Atrium Bistro & Coffee Bar",
        "directions_from_entrance": "In the NB ground floor atrium, to the right of the glass panoramic elevators and opposite the student lounge sofas.",
        "amenities_accessibility": "Fresh coffee, sandwiches, pastries, cold drinks, cashless card payment.",
        "hours_or_availability": "Mon-Fri 08:00-18:00",
        "keywords": "coffee nb, bistro nb, snack bar, cafe novy budova, coffee atrium"
    },
    {
        "location_id": "LOC_NB_03",
        "building": "NB",
        "floor": "Ground / 0",
        "room_number": "NB WC-G",
        "facility_type": "washroom",
        "name": "NB Ground Floor Washrooms (Male, Female, Wheelchair Accessible)",
        "directions_from_entrance": "From the NB atrium, walk past the left side of Vencovského aula towards the cloakroom (šatna). The washrooms are situated in the illuminated hallway on the left.",
        "amenities_accessibility": "Large wheelchair accessible cubicle, baby changing station, automatic soap and water dispensers.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom nb ground, toilet ground floor nb, wc nb ground, bathroom vencovskeho aula"
    },
    {
        "location_id": "LOC_NB_11",
        "building": "NB",
        "floor": "1st floor",
        "room_number": "NB A & NB B",
        "facility_type": "lecture_hall",
        "name": "Lecture Halls NB A and NB B",
        "directions_from_entrance": "Take the panoramic glass elevators or stairs from the NB atrium to the 1st floor. Turn left into the north wing corridor. Hall NB A is on the left, Hall NB B is on the right.",
        "amenities_accessibility": "Capacity 150 each, high definition projectors, wheelchair desks in front row.",
        "hours_or_availability": "Scheduled during lectures (07:30-19:30)",
        "keywords": "nb a, nb b, hall nb a, hall nb b, lecture hall nb a, classroom nb b"
    },
    {
        "location_id": "LOC_NB_12",
        "building": "NB",
        "floor": "1st floor",
        "room_number": "NB C & NB D",
        "facility_type": "lecture_hall",
        "name": "Lecture Halls NB C and NB D",
        "directions_from_entrance": "From NB 1st floor landing, turn right into the south wing corridor. Hall NB C is on the right, Hall NB D is on the left.",
        "amenities_accessibility": "Tiered desks with power sockets, document cameras, dual screens.",
        "hours_or_availability": "Scheduled during lecture hours",
        "keywords": "nb c, nb d, hall nb c, hall nb d, classroom nb c, lecture room nb d"
    },
    {
        "location_id": "LOC_NB_13",
        "building": "NB",
        "floor": "1st floor",
        "room_number": "NB WC-1",
        "facility_type": "washroom",
        "name": "NB 1st Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On NB 1st floor, washrooms are located in two convenient spots: Wing 1 is next to Hall NB B, and Wing 2 is immediately adjacent to Hall NB D.",
        "amenities_accessibility": "High-capacity multi-stall washrooms with Dyson hand dryers.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom nb 1st floor, toilet nb 1, wc nb a nb b, bathroom nb first floor"
    },
    {
        "location_id": "LOC_NB_14",
        "building": "NB",
        "floor": "1st floor",
        "room_number": "NB 113 / NB 114",
        "facility_type": "study_coordinator",
        "name": "FIS Study Department & International Coordinators (Room NB 113/114)",
        "directions_from_entrance": "Take the NB elevators to the 1st floor. Walk into the central administrative hallway between the north and south corridors. Rooms NB 113 and NB 114 are clearly marked 'Faculty of Informatics and Statistics - Study Department'.",
        "amenities_accessibility": "Study coordinator office for ISM (Information Systems Management), Applied Informatics, Data Analytics, and English-taught Master/Bachelor degrees.",
        "hours_or_availability": "Mon 09:00-11:30, 13:00-15:00; Wed 09:00-11:30, 13:00-16:00",
        "keywords": "study coordinator fis, nb 113, nb 114, ism coordinator, study department fis, studijni oddeleni fis, course enrollment help"
    },
    {
        "location_id": "LOC_NB_15",
        "building": "NB",
        "floor": "1st floor",
        "room_number": "NB 110",
        "facility_type": "study_coordinator",
        "name": "FMV Study Department (Faculty of International Relations - Room NB 110)",
        "directions_from_entrance": "Located on NB 1st floor, right side of the central hallway in room NB 110.",
        "amenities_accessibility": "International Relations and International Business program officers.",
        "hours_or_availability": "Mon & Wed 09:00-11:30, 13:00-15:00",
        "keywords": "fmv study department, nb 110, international relations coordinator, fmv studijni"
    },
    {
        "location_id": "LOC_NB_21",
        "building": "NB",
        "floor": "2nd floor",
        "room_number": "NB 201–220",
        "facility_type": "study_coordinator",
        "name": "Dean's Offices & Faculty Secretariats (FIS & FMV)",
        "directions_from_entrance": "Take NB elevator to the 2nd floor. Central corridor leads to the Dean's Offices and Academic Senate chambers.",
        "amenities_accessibility": "Executive administration, formal appeal submissions.",
        "hours_or_availability": "Mon-Fri 09:00-15:00 by appointment",
        "keywords": "dean office, dekanat, nb 2nd floor, fis dean, appeal dean"
    },
    {
        "location_id": "LOC_NB_22",
        "building": "NB",
        "floor": "2nd floor",
        "room_number": "NB WC-2",
        "facility_type": "washroom",
        "name": "NB 2nd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "Directly facing the central glass elevators on the 2nd floor landing.",
        "amenities_accessibility": "Wheelchair accessible, touchless sinks.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom nb 2nd floor, toilet nb 2, wc novy budova 2"
    },
    {
        "location_id": "LOC_NB_31",
        "building": "NB",
        "floor": "3rd floor",
        "room_number": "NB 380",
        "facility_type": "study_coordinator",
        "name": "International Office (OZS - Oddělení zahraničních styků - Room NB 380)",
        "directions_from_entrance": "Take the NB glass elevators up to the 3rd floor. Follow signs towards the west corridor. Room NB 380 is the Central International Office (OZS).",
        "amenities_accessibility": "Handles Erasmus+, bilateral university exchange partnerships, incoming international exchange students, and overseas learning agreements.",
        "hours_or_availability": "Mon-Thu 09:00-12:00; Wed afternoon 13:00-15:00",
        "keywords": "ozs, international office, nb 380, erasmus office, exchange coordinator, oddeleni zahranicnich styku"
    },
    {
        "location_id": "LOC_NB_32",
        "building": "NB",
        "floor": "3rd floor",
        "room_number": "NB WC-3",
        "facility_type": "washroom",
        "name": "NB 3rd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On NB 3rd floor, located in the corridor hallway adjacent to room NB 375 near the fire exit stairs.",
        "amenities_accessibility": "Male and Female facilities.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom nb 3rd floor, toilet nb 3, wc ozs floor, bathroom third floor nb"
    },
    {
        "location_id": "LOC_NB_41",
        "building": "NB",
        "floor": "4th floor",
        "room_number": "NB 410",
        "facility_type": "study_coordinator",
        "name": "Academic Psychological Counselling Centre (AC VŠE - Room NB 410)",
        "directions_from_entrance": "Take the NB elevators to the 4th floor. Turn right into the quiet north corridor. Room NB 410 is the confidential consultation suite.",
        "amenities_accessibility": "Private, soundproofed room for individual counseling sessions and stress management.",
        "hours_or_availability": "By confirmed appointment booked online via AC VŠE portal",
        "keywords": "psychologist office, ac vse room, nb 410, mental health clinic vse, counselling room"
    },
    {
        "location_id": "LOC_NB_42",
        "building": "NB",
        "floor": "4th floor",
        "room_number": "NB WC-4",
        "facility_type": "washroom",
        "name": "NB 4th Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On NB 4th floor, directly opposite the north stairs landing.",
        "amenities_accessibility": "Restroom facilities with clean amenities.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom nb 4th floor, toilet nb 4, wc 4th floor novy budova"
    },

    # -------------------------------------------------------------
    # RAJSKÁ BUDOVA (RB) - RAJSKÁ BUILDING
    # -------------------------------------------------------------
    {
        "location_id": "LOC_RB_01",
        "building": "RB",
        "floor": "Ground / 0",
        "room_number": "RB Library",
        "facility_type": "library",
        "name": "University Main Library Žižkov (Knihovna Žižkov Entrance)",
        "directions_from_entrance": "Enter Rajská budova from náměstí Winstona Churchilla or via the internal connecting bridge from NB. Walk into the bright, modern RB ground floor atrium. The Library glass entrance turnstiles are clearly visible on the right.",
        "amenities_accessibility": "Book checkout desks, self-service RFID borrowing kiosks, quiet study halls, computer terminals, printers and scanners.",
        "hours_or_availability": "Mon-Thu 08:00-19:00; Fri 08:00-17:00; Sat 09:00-14:00",
        "keywords": "library entrance, knihovna zizkov, rb library, study in library, borrow books, print in library"
    },
    {
        "location_id": "LOC_RB_02",
        "building": "RB",
        "floor": "Ground / 0",
        "room_number": "Bibliobox",
        "facility_type": "library",
        "name": "24/7 Library Book Return Drop Box (Bibliobox)",
        "directions_from_entrance": "Located just outside the Library turnstiles in the RB ground atrium. Look for the large silver metal drop box marked 'Bibliobox'.",
        "amenities_accessibility": "Deposit borrowed books at any hour without needing to enter the library.",
        "hours_or_availability": "24 hours a day, 7 days a week",
        "keywords": "return book after hours, bibliobox, drop box library, return book late"
    },
    {
        "location_id": "LOC_RB_03",
        "building": "RB",
        "floor": "Ground / 0",
        "room_number": "RB Cafe",
        "facility_type": "canteen_menza",
        "name": "RB Atrium Cafeteria & Lounge (Caffe Della Serra)",
        "directions_from_entrance": "Situated in the central RB atrium beneath the glass skylights, featuring open seating, tables with power outlets, and espresso bar.",
        "amenities_accessibility": "Espresso, freshly baked pastries, salads, paninis, card payment.",
        "hours_or_availability": "Mon-Fri 08:00-18:30",
        "keywords": "cafe rb, cafeteria rajska, coffee rajska budova, caffe della serra"
    },
    {
        "location_id": "LOC_RB_04",
        "building": "RB",
        "floor": "Ground / 0",
        "room_number": "RB WC-G",
        "facility_type": "washroom",
        "name": "RB Ground Floor Washrooms (Male, Female & Accessible WC)",
        "directions_from_entrance": "In the RB ground floor atrium, walk past the main security reception desk into the corridor on the left. The washroom entrance is on your right.",
        "amenities_accessibility": "Accessible toilet with automated door opener, mirror lights, clean modern stalls.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom rb ground, toilet rajska ground, wc rb atrium, bathroom ground floor rb"
    },
    {
        "location_id": "LOC_RB_11",
        "building": "RB",
        "floor": "1st floor",
        "room_number": "RB 101",
        "facility_type": "lecture_hall",
        "name": "Grand Lecture Hall RB 101 (400 Seats)",
        "directions_from_entrance": "Take the RB escalators or open glass stairs from the atrium up to the 1st floor. Hall RB 101 is the imposing curved lecture hall situated right in front of you.",
        "amenities_accessibility": "Capacity 400 seats, triple high-lumen laser projectors, desk microphones, front and rear entrances.",
        "hours_or_availability": "Used for major university lectures and introductory courses",
        "keywords": "rb 101, lecture hall rb 101, auditorium rb 101, rajska 101"
    },
    {
        "location_id": "LOC_RB_12",
        "building": "RB",
        "floor": "1st floor",
        "room_number": "RB WC-1",
        "facility_type": "washroom",
        "name": "RB 1st Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On RB 1st floor landing, walk past the right exit doors of Hall RB 101 towards the glass facade. Washrooms are situated in the hallway alcove.",
        "amenities_accessibility": "Male and Female facilities with high-speed hand dryers.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom rb 1st floor, toilet rb 101, wc rajska 1, bathroom 1st floor rb"
    },
    {
        "location_id": "LOC_RB_21",
        "building": "RB",
        "floor": "2nd floor",
        "room_number": "RB 201",
        "facility_type": "lecture_hall",
        "name": "Lecture Hall RB 201 (250 Seats)",
        "directions_from_entrance": "Take the escalators or stairs to RB 2nd floor. Hall RB 201 is the large auditorium located directly on the central landing.",
        "amenities_accessibility": "Tiered amphitheatre seating, charging outlets under chairs, dual HD projection.",
        "hours_or_availability": "Scheduled during lecture hours",
        "keywords": "rb 201, lecture hall rb 201, hall rb 201, auditorium rajska 201"
    },
    {
        "location_id": "LOC_RB_22",
        "building": "RB",
        "floor": "2nd floor",
        "room_number": "RB 209, 211, 212",
        "facility_type": "classroom",
        "name": "Classrooms RB 209, RB 211, and RB 212",
        "directions_from_entrance": "From RB 2nd floor landing, turn left down the west corridor overlooking the internal atrium. Classrooms RB 209, 211, and 212 are along the outer windowed wall.",
        "amenities_accessibility": "Modern seminar classrooms, capacity 40 students each, interactive smart boards, air conditioning.",
        "hours_or_availability": "Open for scheduled seminars and student study when vacant",
        "keywords": "rb 211, rb 209, rb 212, classroom rb 211, room rb 211, seminar rooms rajska"
    },
    {
        "location_id": "LOC_RB_23",
        "building": "RB",
        "floor": "2nd floor",
        "room_number": "RB WC-2",
        "facility_type": "washroom",
        "name": "RB 2nd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On RB 2nd floor, walk past classroom RB 208 towards the elevator lobby. The washrooms are on the left side.",
        "amenities_accessibility": "Wheelchair accessible, spacious and modern.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom rb 2nd floor, toilet near rb 211, wc rb 2, bathroom second floor rb"
    },
    {
        "location_id": "LOC_RB_31",
        "building": "RB",
        "floor": "3rd floor",
        "room_number": "RB 301–330",
        "facility_type": "study_coordinator",
        "name": "Faculty of Business Administration (FPH) Study Department & Offices",
        "directions_from_entrance": "Take the RB elevators to the 3rd floor. The south corridor houses the FPH Study Department, handling CEMS, MIB, and Business Administration programs.",
        "amenities_accessibility": "FPH international program coordinators, student consultation desks.",
        "hours_or_availability": "Mon & Wed 09:00-11:30, 13:00-15:00",
        "keywords": "fph study department, cems coordinator, mib coordinator, rb 3rd floor, business administration coordinator"
    },
    {
        "location_id": "LOC_RB_32",
        "building": "RB",
        "floor": "3rd floor",
        "room_number": "RB WC-3",
        "facility_type": "washroom",
        "name": "RB 3rd Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On RB 3rd floor, located in the central elevator lobby alcove.",
        "amenities_accessibility": "Male and Female facilities.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom rb 3rd floor, toilet rb 3, wc rajska 3"
    },
    {
        "location_id": "LOC_RB_41",
        "building": "RB",
        "floor": "4th floor",
        "room_number": "RB 401–415",
        "facility_type": "classroom",
        "name": "Executive Seminar Rooms RB 401 to RB 415",
        "directions_from_entrance": "Take RB elevators to the 4th floor. Classrooms with executive roundtables and presentation displays.",
        "amenities_accessibility": "High-end seminar rooms, power hubs on tables.",
        "hours_or_availability": "Scheduled for master seminars and state exam defense committees",
        "keywords": "rb 401, rb 405, rb 410, classrooms rb 4th floor, rajska 4th floor"
    },
    {
        "location_id": "LOC_RB_42",
        "building": "RB",
        "floor": "4th floor",
        "room_number": "RB WC-4",
        "facility_type": "washroom",
        "name": "RB 4th Floor Washrooms (Male & Female)",
        "directions_from_entrance": "On RB 4th floor, directly next to the central elevator landing.",
        "amenities_accessibility": "Clean, quiet washrooms.",
        "hours_or_availability": "Open daily 06:00-22:00",
        "keywords": "washroom rb 4th floor, toilet rb 4, wc rajska 4"
    },

    # -------------------------------------------------------------
    # VENUES & SPORTS FACILITIES
    # -------------------------------------------------------------
    {
        "location_id": "LOC_LIKES_AULA",
        "building": "NB/SB",
        "floor": "1st floor walkway",
        "room_number": "Likešova aula",
        "facility_type": "lecture_hall",
        "name": "Likešova Aula (Connecting Bridge Lecture Hall)",
        "directions_from_entrance": "Located in the enclosed 1st-floor bridge that connects Nová budova (NB) and Stará budova (SB). Walk past NB Lecture Hall NB B through the glass corridor; Likešova aula entrance is on your right.",
        "amenities_accessibility": "Tiered seating for 300 students, modern multimedia podium, wheelchair accessible from NB elevator.",
        "hours_or_availability": "Scheduled for large faculty lectures and academic events",
        "keywords": "likesova aula, likes hall, bridge hall, aula between nb and sb, lecture room likesova"
    },
    {
        "location_id": "LOC_JAROV_SPORTS",
        "building": "Jarov",
        "floor": "Ground",
        "room_number": "Sports Hall",
        "facility_type": "classroom",
        "name": "VŠE Sports Hall & Fitness Centre (Na Třebešíně / Jarov)",
        "directions_from_entrance": "Located off the main Žižkov campus at Na Třebešíně, Prague 3 (near Jarov dormitories). From Žižkov campus, take tram 9, 26, or 31 from Husinecká to 'Kněžská luka' or 'Nákladové nádraží Žižkov', then walk 4 minutes.",
        "amenities_accessibility": "Indoor basketball/volleyball courts, fitness gym, aerobics studio, outdoor tennis courts, changing rooms with showers.",
        "hours_or_availability": "Mon-Fri 07:00-21:30; weekends during tournaments",
        "keywords": "sports hall, gym vse, fitness centre, trebesin, jarov sports, pe classes, tennis courts vse"
    }
]
