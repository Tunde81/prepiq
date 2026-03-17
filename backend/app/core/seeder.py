from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import (
    User, UserRole, LearningModule, Lesson, Quiz,
    SimulationScenario, AssessmentDomain, AssessmentQuestion
)


async def seed_initial_data():
    db = SessionLocal()
    try:
        _seed_superadmin(db)
        _seed_assessment_domains(db)
        _seed_modules(db)
        _seed_simulations(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Seeder] Error: {e}")
    finally:
        db.close()


def _seed_superadmin(db: Session):
    if db.query(User).filter(User.email == settings.FIRST_SUPERADMIN_EMAIL).first():
        return
    admin = User(
        email=settings.FIRST_SUPERADMIN_EMAIL,
        hashed_password=get_password_hash(settings.FIRST_SUPERADMIN_PASSWORD),
        full_name="Platform Administrator",
        role=UserRole.SUPERADMIN,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.flush()
    print(f"[Seeder] Created superadmin: {settings.FIRST_SUPERADMIN_EMAIL}")


def _seed_assessment_domains(db: Session):
    if db.query(AssessmentDomain).count() > 0:
        return

    domains_data = [
        {
            "name": "Network Security",
            "description": "Firewalls, segmentation, monitoring, and intrusion detection.",
            "questions": [
                ("Do you have a firewall configured between your internal network and the internet?", "Consider both hardware and software firewalls."),
                ("Is your network segmented to separate critical systems from general users?", "VLANs or physical separation counts."),
                ("Do you monitor network traffic for suspicious activity?", "Consider SIEM, IDS/IPS systems."),
                ("Are wireless networks secured with WPA3 or WPA2-Enterprise?", "Check your Wi-Fi configuration."),
                ("Do you have a process for reviewing firewall rules quarterly?", "Regular reviews prevent rule bloat and gaps."),
            ]
        },
        {
            "name": "Identity & Access",
            "description": "Authentication, MFA, privileged access, and access reviews.",
            "questions": [
                ("Is Multi-Factor Authentication (MFA) enforced for all remote access and cloud services?", "MFA dramatically reduces account compromise risk."),
                ("Do you have a process for removing access when employees leave?", "Offboarding checklist helps here."),
                ("Are privileged/admin accounts separate from standard user accounts?", "Principle of least privilege."),
                ("Do you conduct quarterly reviews of user access rights?", "Access creep is a common vulnerability."),
                ("Is password complexity enforced (minimum 12 chars, no reuse)?", "Consider a password manager deployment."),
            ]
        },
        {
            "name": "Data Protection",
            "description": "Data classification, encryption, backup, and GDPR compliance.",
            "questions": [
                ("Have you classified your data by sensitivity level (e.g., public, internal, confidential)?", "Data classification is foundational to protection."),
                ("Is sensitive data encrypted at rest and in transit?", "Consider TLS for transit, AES-256 for storage."),
                ("Do you have an automated backup process tested at least quarterly?", "Backups are your last line of defence against ransomware."),
                ("Do you have a GDPR-compliant data retention and deletion policy?", "Retaining data longer than needed increases risk."),
                ("Are personal data processing activities documented in a register?", "Required under GDPR Article 30."),
            ]
        },
        {
            "name": "Incident Response",
            "description": "IR planning, detection capability, and recovery procedures.",
            "questions": [
                ("Do you have a documented Incident Response (IR) plan?", "An IR plan reduces response time and cost significantly."),
                ("Has your IR plan been tested via a tabletop exercise in the last 12 months?", "Untested plans often fail under pressure."),
                ("Can you detect a security incident within 24 hours of occurrence?", "Average detection time is 197 days — reduce yours."),
                ("Do you have a process for notifying affected parties and regulators within 72 hours?", "Required under GDPR and NIS Regulations."),
                ("Is there a designated person or team responsible for cyber incident response?", "Ambiguity during incidents costs time and money."),
            ]
        },
        {
            "name": "Endpoint Security",
            "description": "Device hardening, patching, EDR, and mobile device management.",
            "questions": [
                ("Are all endpoints protected with up-to-date antivirus or EDR software?", "EDR provides significantly more capability than AV."),
                ("Is there a patch management process ensuring critical patches are applied within 14 days?", "Unpatched systems are the most common attack vector."),
                ("Are all endpoints encrypted (full-disk encryption)?", "Protects against physical theft of devices."),
                ("Do you have visibility of all devices connecting to your network?", "Shadow IT and BYOD introduce unmanaged risk."),
                ("Is USB/removable media usage restricted or monitored?", "USB drives are a common malware vector."),
            ]
        },
        {
            "name": "Security Awareness",
            "description": "Training programmes, phishing simulations, and security culture.",
            "questions": [
                ("Do all staff receive security awareness training at least annually?", "Human error causes 88% of breaches."),
                ("Do you run regular phishing simulation exercises?", "Simulations improve real-world phishing resistance."),
                ("Is there a clear process for employees to report suspicious emails or incidents?", "Reporting culture is critical to early detection."),
                ("Do senior leaders visibly support and participate in security training?", "Leadership buy-in drives staff engagement."),
                ("Is security included in the onboarding process for new employees?", "First impressions on security culture matter."),
            ]
        },
        {
            "name": "Vulnerability Management",
            "description": "Scanning, pen testing, patch cadence, and risk prioritisation.",
            "questions": [
                ("Do you conduct regular vulnerability scans of your systems and network?", "Minimum monthly for internet-facing systems."),
                ("Has a penetration test been conducted in the last 12 months?", "Pen tests identify what scanners miss."),
                ("Do you have a process for triaging and prioritising vulnerabilities by risk?", "Not all vulnerabilities are equally critical."),
                ("Are third-party/supplier systems included in your vulnerability management scope?", "Supply chain attacks are increasingly common."),
                ("Do you track vulnerabilities to remediation with defined SLAs?", "Tracking ensures nothing falls through the cracks."),
            ]
        },
        {
            "name": "Third-Party Risk",
            "description": "Supplier assessments, contracts, and ongoing monitoring.",
            "questions": [
                ("Do you assess the security posture of critical suppliers before engagement?", "Third-party risk is your risk."),
                ("Do supplier contracts include security and data protection requirements?", "Contractual obligations provide recourse if breached."),
                ("Do you maintain an inventory of third-party access to your systems and data?", "You cannot manage what you cannot see."),
                ("Is third-party access reviewed and revoked promptly when no longer needed?", "Stale access is a persistent risk."),
                ("Do you have a process for managing security incidents involving third parties?", "Supply chain incidents require coordinated response."),
            ]
        },
    ]

    for idx, domain_data in enumerate(domains_data):
        domain = AssessmentDomain(
            name=domain_data["name"],
            description=domain_data["description"],
            order_index=idx
        )
        db.add(domain)
        db.flush()

        for q_idx, (question_text, guidance) in enumerate(domain_data["questions"]):
            q = AssessmentQuestion(
                domain_id=domain.id,
                question_text=question_text,
                guidance=guidance,
                order_index=q_idx,
            )
            db.add(q)

    print("[Seeder] Assessment domains and questions seeded.")


def _seed_modules(db: Session):
    if db.query(LearningModule).count() > 0:
        return

    modules_data = [
        {
            "title": "Phishing Awareness",
            "slug": "phishing-awareness",
            "description": "Learn to identify and respond to phishing attacks — the #1 cause of data breaches.",
            "category": "phishing",
            "difficulty": "beginner",
            "duration_minutes": 15,
            "order_index": 1,
            "is_published": True,
            "thumbnail_url": "/static/thumbnails/phishing.png",
            "lessons": [
                ("What is Phishing?", "## What is Phishing?\n\nPhishing is a cyberattack technique where attackers impersonate trusted entities to steal sensitive information...\n\n### Types of Phishing\n- **Email Phishing** — Mass emails impersonating brands\n- **Spear Phishing** — Targeted attacks on individuals\n- **Whaling** — Attacks targeting executives\n- **Smishing** — SMS-based phishing\n- **Vishing** — Voice call phishing\n\n### Why It Works\nPhishing exploits human psychology: urgency, fear, authority, and curiosity. Attackers create convincing scenarios that bypass rational thinking.", 7),
                ("Spotting a Phishing Email", "## How to Spot Phishing\n\n### Red Flags to Check\n\n1. **Sender Address** — Does the domain match exactly? `support@paypa1.com` ≠ `support@paypal.com`\n2. **Urgency & Threats** — 'Your account will be suspended in 24 hours'\n3. **Generic Greetings** — 'Dear Customer' instead of your name\n4. **Suspicious Links** — Hover before clicking. Check the actual URL\n5. **Unexpected Attachments** — Never open `.exe`, `.zip` from unknown senders\n6. **Poor Grammar** — Many phishing emails contain spelling errors\n\n### The SLAM Method\n- **S**ender — Is the sender who they claim to be?\n- **L**inks — Where do the links actually go?\n- **A**ttachments — Are attachments expected?\n- **M**essage — Does the message make sense?", 8),
            ],
            "quiz": {
                "title": "Phishing Awareness Check",
                "questions": [
                    {
                        "question": "You receive an email from 'support@paypa1.com' asking you to verify your account. What is the most suspicious element?",
                        "options": ["The word 'verify'", "The domain 'paypa1.com' uses the number 1 instead of 'l'", "The email arrived on a Monday", "The email has a subject line"],
                        "correct_index": 1,
                        "explanation": "The domain substitutes 'l' with '1' — a classic typosquatting technique used in phishing."
                    },
                    {
                        "question": "Which of these is NOT a common phishing red flag?",
                        "options": ["Urgent language threatening account suspension", "An email from your CEO sent during business hours asking for a task", "Poor spelling and grammar", "Generic greeting like 'Dear Customer'"],
                        "correct_index": 1,
                        "explanation": "Emails from known contacts during business hours with normal tasks are not inherently suspicious, though CEO fraud does exist."
                    },
                    {
                        "question": "What does the 'L' in the SLAM phishing detection method stand for?",
                        "options": ["Language", "Links", "Logos", "Login"],
                        "correct_index": 1,
                        "explanation": "L = Links. Always hover over links before clicking to verify the destination URL."
                    },
                ]
            }
        },
        {
            "title": "Password Security",
            "slug": "password-security",
            "description": "Master password hygiene and multi-factor authentication to secure your accounts.",
            "category": "password",
            "difficulty": "beginner",
            "duration_minutes": 12,
            "order_index": 2,
            "is_published": True,
            "thumbnail_url": "/static/thumbnails/password.png",
            "lessons": [
                ("Why Passwords Fail", "## Why Passwords Fail\n\n### The Scale of the Problem\n- Over **24 billion** username/password pairs were exposed in 2022\n- **123456** remains the world's most used password\n- 65% of people reuse passwords across multiple sites\n\n### Common Attack Methods\n1. **Credential Stuffing** — Using leaked passwords from one breach on other sites\n2. **Brute Force** — Systematically trying all combinations\n3. **Dictionary Attacks** — Using lists of common words and patterns\n4. **Password Spraying** — Trying common passwords across many accounts", 6),
                ("Strong Passwords & MFA", "## Creating Strong Passwords\n\n### The Passphrase Method\nInstead of `P@ssw0rd!`, use `correct-horse-battery-staple`\n\nA passphrase is:\n- Easier to remember\n- Harder to crack\n- Naturally long (length = strength)\n\n### Password Manager Best Practices\n- Use a reputable password manager (Bitwarden, 1Password, Dashlane)\n- Generate unique 20+ character passwords for each account\n- Never reuse passwords\n\n### Multi-Factor Authentication (MFA)\nMFA adds a second layer beyond passwords:\n- **Something you know** — Password\n- **Something you have** — Phone/hardware key\n- **Something you are** — Fingerprint/face\n\n**Enable MFA everywhere it's available.** It blocks 99.9% of automated attacks.", 9),
            ],
            "quiz": {
                "title": "Password Security Quiz",
                "questions": [
                    {
                        "question": "Which password is the strongest?",
                        "options": ["P@ssw0rd!", "correct-horse-battery-staple-2024", "CompanyName2024!", "qwerty123"],
                        "correct_index": 1,
                        "explanation": "Length is the primary factor in password strength. The passphrase is longer and harder to crack."
                    },
                    {
                        "question": "What is credential stuffing?",
                        "options": ["Adding special characters to passwords", "Using leaked credentials from one breach to access other accounts", "Storing passwords in a browser", "Changing passwords frequently"],
                        "correct_index": 1,
                        "explanation": "Credential stuffing exploits password reuse across services."
                    },
                    {
                        "question": "MFA blocks approximately what percentage of automated account attacks?",
                        "options": ["50%", "75%", "99.9%", "100%"],
                        "correct_index": 2,
                        "explanation": "Microsoft research shows MFA blocks 99.9% of automated attacks."
                    },
                ]
            }
        },
        {
            "title": "Device & Endpoint Security",
            "slug": "device-security",
            "description": "Protect your devices with patching, encryption, and endpoint controls.",
            "category": "device",
            "difficulty": "intermediate",
            "duration_minutes": 18,
            "order_index": 3,
            "is_published": True,
            "thumbnail_url": "/static/thumbnails/device.png",
            "lessons": [
                ("Device Hardening Fundamentals", "## Device Hardening\n\n### Why Endpoints Are Targeted\nEndpoints (laptops, phones, servers) are the primary entry point for attackers. 70% of successful breaches begin at an endpoint.\n\n### Core Hardening Steps\n\n**1. Keep Everything Updated**\n- Enable automatic updates for OS and applications\n- Critical patches should be applied within 14 days\n- Don't ignore update prompts — they often patch known vulnerabilities\n\n**2. Enable Full-Disk Encryption**\n- Windows: BitLocker\n- macOS: FileVault\n- Linux: LUKS\n- Mobile: Enabled by default on modern iOS/Android\n\n**3. Use EDR (Endpoint Detection & Response)**\nEDR goes beyond antivirus — it detects behavioural anomalies, not just known signatures.", 10),
                ("Patch Management Strategy", "## Patch Management\n\n### The Risk of Unpatched Systems\nThe 2017 WannaCry ransomware attack exploited a vulnerability that Microsoft had patched 2 months earlier. Over 200,000 systems were infected because they weren't patched.\n\n### Patch Management Framework\n1. **Inventory** — Know what you have\n2. **Scan** — Identify missing patches\n3. **Test** — Test critical patches in staging\n4. **Deploy** — Roll out with defined SLAs\n5. **Verify** — Confirm patch application\n\n### SLA Guidelines\n- **Critical** (CVSS 9-10): Patch within 24-72 hours\n- **High** (CVSS 7-8): Patch within 7 days\n- **Medium** (CVSS 4-6): Patch within 30 days\n- **Low** (CVSS 1-3): Patch within 90 days", 8),
            ],
            "quiz": {
                "title": "Endpoint Security Quiz",
                "questions": [
                    {
                        "question": "What is the recommended timeframe for applying critical security patches?",
                        "options": ["Within 90 days", "Within 30 days", "Within 14 days", "Whenever convenient"],
                        "correct_index": 2,
                        "explanation": "Critical patches should be applied within 14 days — or faster for CVSS 9+ vulnerabilities."
                    },
                    {
                        "question": "Which tool provides more advanced protection than traditional antivirus?",
                        "options": ["Firewall", "EDR (Endpoint Detection & Response)", "VPN", "Spam filter"],
                        "correct_index": 1,
                        "explanation": "EDR uses behavioural analysis to detect novel threats that signature-based AV misses."
                    },
                ]
            }
        },
        {
            "title": "Safe Browsing",
            "slug": "safe-browsing",
            "description": "Navigate the web safely, identify malicious sites, and protect your privacy.",
            "category": "browsing",
            "difficulty": "beginner",
            "duration_minutes": 10,
            "order_index": 4,
            "is_published": True,
            "thumbnail_url": "/static/thumbnails/browsing.png",
            "lessons": [
                ("Identifying Malicious Websites", "## Safe Browsing\n\n### HTTPS is Necessary but Not Sufficient\nThe padlock icon means the connection is encrypted — **not** that the site is legitimate. Phishing sites routinely use HTTPS.\n\n### How to Check a Website's Legitimacy\n1. **Check the exact domain** — `microsoft.com` vs `micros0ft.com`\n2. **Use Google Safe Browsing** — [safebrowsing.google.com/safebrowsing/report_phish/](https://safebrowsing.google.com)\n3. **Check WHOIS** — Recently registered domains are suspicious\n4. **Look for trust signals** — Established contact info, privacy policy\n\n### Browser Security Settings\n- Enable popup blockers\n- Use DNS filtering (Quad9, Cloudflare 1.1.1.1)\n- Disable auto-download of files\n- Consider browser isolation for high-risk browsing", 10),
            ],
            "quiz": {
                "title": "Safe Browsing Quiz",
                "questions": [
                    {
                        "question": "A website has a padlock icon (HTTPS). What does this confirm?",
                        "options": ["The website is legitimate and safe", "Your connection to the site is encrypted", "The site has been security audited", "The site is owned by a trusted company"],
                        "correct_index": 1,
                        "explanation": "HTTPS only confirms the connection is encrypted. Phishing sites commonly use HTTPS to appear legitimate."
                    },
                ]
            }
        },
        {
            "title": "Data Handling & GDPR",
            "slug": "data-handling",
            "description": "Understand data protection obligations, GDPR principles, and secure data handling.",
            "category": "data",
            "difficulty": "intermediate",
            "duration_minutes": 20,
            "order_index": 5,
            "is_published": True,
            "thumbnail_url": "/static/thumbnails/data.png",
            "lessons": [
                ("GDPR Fundamentals", "## GDPR Fundamentals\n\n### The 7 Principles (Article 5)\n1. **Lawfulness, Fairness and Transparency** — Have a legal basis; be open about processing\n2. **Purpose Limitation** — Only use data for the stated purpose\n3. **Data Minimisation** — Collect only what you need\n4. **Accuracy** — Keep personal data accurate and up to date\n5. **Storage Limitation** — Don't keep data longer than necessary\n6. **Integrity and Confidentiality** — Protect against unauthorised access\n7. **Accountability** — Demonstrate compliance\n\n### Individual Rights\n- Right to access\n- Right to erasure ('Right to be forgotten')\n- Right to rectification\n- Right to data portability\n- Right to object", 12),
                ("Data Classification & Handling", "## Data Classification\n\n### Classification Levels\n| Level | Examples | Handling |\n|-------|---------|----------|\n| **Public** | Marketing materials | No restrictions |\n| **Internal** | Company policies | Internal use only |\n| **Confidential** | Financial data, contracts | Encrypted, need-to-know |\n| **Restricted** | Personal data, IP | Highest controls, logging |\n\n### Secure Handling Practices\n- **Email** — Never send unencrypted sensitive data via email\n- **Sharing** — Use secure file-sharing platforms (not WhatsApp/personal email)\n- **Disposal** — Securely delete or physically destroy storage media\n- **Printing** — Retrieve confidential prints immediately; shred when done", 8),
            ],
            "quiz": {
                "title": "Data Handling Quiz",
                "questions": [
                    {
                        "question": "How many core principles does the GDPR establish for data processing?",
                        "options": ["5", "7", "10", "12"],
                        "correct_index": 1,
                        "explanation": "GDPR Article 5 establishes 7 core principles for lawful data processing."
                    },
                    {
                        "question": "What is the 'data minimisation' principle?",
                        "options": ["Encrypting data to reduce its size", "Collecting only the data necessary for the stated purpose", "Deleting data after 6 months", "Anonymising all personal data"],
                        "correct_index": 1,
                        "explanation": "Data minimisation means you should only collect the minimum personal data needed for your stated purpose."
                    },
                ]
            }
        },
    ]

    for mod_data in modules_data:
        module = LearningModule(
            title=mod_data["title"],
            slug=mod_data["slug"],
            description=mod_data["description"],
            category=mod_data["category"],
            difficulty=mod_data["difficulty"],
            duration_minutes=mod_data["duration_minutes"],
            order_index=mod_data["order_index"],
            is_published=mod_data["is_published"],
            thumbnail_url=mod_data.get("thumbnail_url"),
        )
        db.add(module)
        db.flush()

        for l_idx, (title, content, duration) in enumerate(mod_data["lessons"]):
            lesson = Lesson(
                module_id=module.id,
                title=title,
                content=content,
                order_index=l_idx,
                duration_minutes=duration,
            )
            db.add(lesson)

        quiz_data = mod_data.get("quiz")
        if quiz_data:
            quiz = Quiz(
                module_id=module.id,
                title=quiz_data["title"],
                questions=quiz_data["questions"],
                pass_threshold=70,
            )
            db.add(quiz)

    print("[Seeder] Learning modules seeded.")


def _seed_simulations(db: Session):
    if db.query(SimulationScenario).count() > 0:
        return

    scenarios = [
        {
            "title": "Phishing Email Investigation",
            "slug": "phishing-email-investigation",
            "description": "Analyse a suspicious email claiming to be from your CEO requesting an urgent wire transfer. Apply the SLAM method to determine if it's legitimate.",
            "category": "phishing",
            "difficulty": "beginner",
            "duration_minutes": 15,
            "is_published": True,
            "objectives": [
                "Apply the SLAM phishing detection method",
                "Identify spoofed email headers",
                "Make a correct accept/reject decision",
                "Document and report the incident appropriately",
            ],
            "steps": [
                {
                    "title": "Examine the sender",
                    "description": "You've received an email: From: ceo@company-corp.co (your company domain is company-corp.com). What's your first action?",
                    "correct_actions": ["check_sender", "inspect_headers"],
                    "feedback": "Correct! The domain .co vs .com is a typosquatting red flag. Never overlook sender domain mismatches.",
                },
                {
                    "title": "Check the request",
                    "description": "The email requests an urgent £45,000 wire transfer to a new supplier. It says 'Don't tell finance — it's a surprise contract.' What do you do?",
                    "correct_actions": ["verify_out_of_band", "contact_ceo_directly"],
                    "feedback": "Perfect. Always verify unusual financial requests via a separate, known communication channel — not by replying to the suspicious email.",
                },
                {
                    "title": "Report the incident",
                    "description": "You've confirmed this is a Business Email Compromise (BEC) attempt. What's your next step?",
                    "correct_actions": ["report_to_it", "report_to_security_team", "do_not_click"],
                    "feedback": "Excellent! Reporting phishing attempts — even ones you didn't fall for — helps protect your entire organisation.",
                },
            ],
            "hints": [
                "Look very carefully at the email domain. Compare every character against the legitimate company domain.",
                "Any request that involves urgency, secrecy, and money is a major red flag. CEO fraud is one of the most costly cybercrimes.",
                "Most organisations have a designated mailbox or button for reporting phishing. Use it — your report helps train filters.",
            ],
        },
        {
            "title": "Ransomware Incident Response",
            "slug": "ransomware-response",
            "description": "A ransomware attack has been detected on a workstation. Follow the incident response playbook to contain, eradicate, and recover.",
            "category": "ransomware",
            "difficulty": "intermediate",
            "duration_minutes": 25,
            "is_published": True,
            "objectives": [
                "Execute the first 4 steps of ransomware incident response",
                "Contain the infection to prevent spread",
                "Preserve forensic evidence correctly",
                "Initiate the recovery process from clean backups",
            ],
            "steps": [
                {
                    "title": "Detect and Confirm",
                    "description": "A user reports their files are being renamed with a .locked extension and a ransom note has appeared. First action?",
                    "correct_actions": ["isolate_machine", "disconnect_network"],
                    "feedback": "Critical first step: Network isolation prevents ransomware from spreading laterally to file shares and other endpoints.",
                },
                {
                    "title": "Containment",
                    "description": "The workstation is isolated. What do you do next?",
                    "correct_actions": ["preserve_logs", "take_memory_snapshot", "notify_ir_team"],
                    "feedback": "Forensic preservation is crucial before any remediation. Memory snapshots can reveal the ransomware strain and attack vector.",
                },
                {
                    "title": "Assess the Blast Radius",
                    "description": "Check which network shares and systems the compromised user had access to. Why?",
                    "correct_actions": ["check_network_shares", "review_access_logs"],
                    "feedback": "Ransomware often encrypts accessible network shares. Identifying the blast radius helps prioritise recovery.",
                },
                {
                    "title": "Recovery from Backup",
                    "description": "Backups are clean and tested. Which recovery approach is correct?",
                    "correct_actions": ["restore_from_backup", "verify_backup_integrity"],
                    "feedback": "Restoring from verified clean backups is the correct approach. Never pay the ransom — it funds further attacks and recovery isn't guaranteed.",
                },
            ],
            "hints": [
                "The MOST important immediate action in any ransomware incident is isolation. Pull the network cable or disable Wi-Fi immediately.",
                "Before you wipe anything, collect evidence. Contact your security team or incident response provider.",
                "Check Active Directory for all shares and drives this user account was mapped to. Ransomware follows the user's access.",
                "Test your backup restore before you need it. An untested backup is not a backup.",
            ],
        },
        {
            "title": "Cloud Misconfiguration: S3 Bucket Exposure",
            "slug": "cloud-s3-misconfiguration",
            "description": "Discover and remediate a publicly exposed AWS S3 bucket containing sensitive company data. Apply cloud security best practices.",
            "category": "cloud",
            "difficulty": "intermediate",
            "duration_minutes": 20,
            "is_published": True,
            "objectives": [
                "Identify a misconfigured public S3 bucket",
                "Assess the data exposure impact",
                "Apply correct access controls and bucket policies",
                "Implement preventive controls going forward",
            ],
            "steps": [
                {
                    "title": "Discovery",
                    "description": "A security scan has flagged an S3 bucket with `Block Public Access` disabled. What's your first step?",
                    "correct_actions": ["check_bucket_policy", "review_acls", "assess_bucket_contents"],
                    "feedback": "Correct. Before remediating, understand what is exposed. Review the bucket policy, ACLs, and the sensitivity of the data.",
                },
                {
                    "title": "Impact Assessment",
                    "description": "The bucket contains customer PII including names, emails and addresses. What regulations are relevant?",
                    "correct_actions": ["identify_gdpr_impact", "check_dpa_2018", "notify_dpo"],
                    "feedback": "PII exposure triggers GDPR obligations. You must notify the ICO within 72 hours if there's a risk to individuals' rights. Notify your DPO immediately.",
                },
                {
                    "title": "Remediation",
                    "description": "How do you secure the bucket immediately?",
                    "correct_actions": ["enable_block_public_access", "remove_public_acls", "apply_restrictive_bucket_policy"],
                    "feedback": "Enable S3 Block Public Access at both the bucket and account level. Apply a bucket policy that denies all public access explicitly.",
                },
                {
                    "title": "Prevention",
                    "description": "How do you prevent this recurring?",
                    "correct_actions": ["enable_aws_config_rules", "enable_security_hub", "set_scp_policy"],
                    "feedback": "AWS Config rules can detect and alert on public buckets automatically. AWS Security Hub provides a centralised security posture view.",
                },
            ],
            "hints": [
                "Use `aws s3api get-bucket-acl` and `aws s3api get-bucket-policy` to review permissions. Look for 'AllUsers' or 'AuthenticatedUsers' grants.",
                "Any exposure of names + emails + addresses is likely a notifiable breach under GDPR Art. 33. Document everything with timestamps.",
                "Run `aws s3api put-public-access-block --bucket BUCKET_NAME --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true`",
                "AWS Config rule `s3-bucket-public-read-prohibited` will automatically flag violations. SCPs can prevent users from ever creating public buckets.",
            ],
        },
    ]

    for s_data in scenarios:
        scenario = SimulationScenario(**s_data)
        db.add(scenario)

    print("[Seeder] Simulation scenarios seeded.")
