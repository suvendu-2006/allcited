# Security Policy

Allcited is an enterprise legal research and statutory citation platform. We prioritize the security of sensitive legal documents, client confidentiality, and platform integrity. This document explains our security posture, how to report vulnerabilities responsibly, our response SLAs, our threat model safeguards, and our safe harbor pledge for ethical researchers.

---

## Supported Versions

We provide security updates and patches for the following versions of Allcited:

| Version | Supported | Status | Security Updates |
|:-------:|:---------:|:------:|:-----------------|
| `main` (trunk) | :white_check_mark: | Active Development | Immediate continuous deployment |
| `0.2.x` | :white_check_mark: | Current Release | Supported for critical and high vulnerabilities |
| `0.1.x` | :x: | Deprecated | Unsupported; please upgrade to `>= 0.2.0` |
| `< 0.1.0` | :x: | End of Life | Unsupported |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities via public GitHub issues, discussions, or pull requests.**

If you discover a potential vulnerability, security bypass, or data leakage flaw in Allcited, report it privately using one of the following channels:

1. **GitHub Private Vulnerability Reporting (Preferred):**
   Navigate to the [Security Advisories tab](https://github.com/suvendu-2006/allcited/security/advisories) on GitHub and select **"Report a vulnerability"**. This creates an encrypted, private advisory accessible only to maintainers.
2. **Direct Security Contact:**
   If GitHub Private Vulnerability Reporting is unavailable, email our security team directly at **[iitsuvendu@gmail.com](mailto:iitsuvendu@gmail.com)** with the subject line:
   `[SECURITY VULNERABILITY] Allcited - <Brief Vulnerability Summary>`.

### Information to Include in Your Report

To help us triage and remediate the issue quickly, include:
- A clear description of the vulnerability and its potential impact.
- Affected component(s) (e.g., FastAPI backend, Next.js frontend, document parser, retrieval pipeline).
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Any prerequisites, environmental requirements, or specific configurations needed to trigger the flaw.
- If applicable, suggested remediation or mitigation steps.

---

## Vulnerability Response SLA & Timelines

We take security reports seriously and commit to the following response timeline:

| Milestone | Target SLA | Description |
|:----------|:-----------|:------------|
| **Initial Acknowledgment** | **Within 48 hours** | Maintainer acknowledges receipt of the report and begins triage. |
| **Triage & Severity Assessment** | **Within 3 to 5 business days** | Vulnerability reproduced, impact validated, CVSS score assigned. |
| **Regular Status Updates** | **Every 7 business days** | Reporter receives progress updates until resolution. |
| **Critical Severity Patch** | **<= 7 calendar days** | Remote code execution (RCE), unauthenticated data exposure, privilege escalation. |
| **High Severity Patch** | **<= 14 calendar days** | SSRF, authentication bypass, tenant isolation breach. |
| **Medium / Low Severity Patch** | **<= 30 calendar days** | Delimiter leakage, rate-limiting flaws, low-impact XSS/CSRF. |
| **Public Disclosure & Advisory** | **Coordinated Release** | CVE assigned and public release notes published once patches are verified. |

---

## Threat Model Summary & Security Architecture

Allcited incorporates defense-in-depth controls specifically designed for enterprise legal workloads:

### 1. Air-Gapped & Local Privacy Mode
- When `AIR_GAPPED_MODE=true` is enabled, Allcited disables all outbound network calls to cloud LLM providers (e.g., OpenAI, NVIDIA NIM).
- All document processing, vector embeddings, and generation tasks run entirely on local offline models or self-hosted container endpoints within the private subnet.
- Zero telemetry, analytics, or document payloads are emitted to external servers.

### 2. Server-Side Request Forgery (SSRF) Defense
- All user-supplied URLs for external judgments or statutory sources pass through rigorous validation (`is_safe_url`).
- **Private IP Blocklist:** All IPv4 and IPv6 private, reserved, and loopback CIDRs are blocked (RFC 1918, RFC 4193, `127.0.0.0/8`, `::1`).
- **Cloud Metadata Endpoint Blocking:** Explicit blocks for AWS, GCP, Azure, and OpenStack metadata services (`169.254.169.254`, `metadata.google.internal`, `100.100.100.200`).
- **DNS Resolution Pinning:** DNS resolution is performed before requests to prevent DNS rebinding attacks.

### 3. Prompt Injection & Delimiter Isolation
- User document texts and search queries are encapsulated in strict XML-style boundary delimiters (e.g., `<document_context>` / `</document_context>`).
- System instructions enforce strict role isolation: user-provided text cannot alter statutory verification rules or override safety guardrails.
- LLM outputs are programmatically verified against cited statutes and grounded text before display to prevent hallucination injection.

### 4. PII Redaction & Confidentiality
- Automated pre-inference regex and NLP sanitizers detect and mask Personally Identifiable Information (PII) including email addresses, phone numbers, Indian PAN cards, Aadhaar numbers, Social Security Numbers, and API credentials.
- Redaction runs prior to document vectorization and prior to LLM context construction.

### 5. Authentication & Tenant Isolation
- **Clerk JWT Authentication:** Strict verification of JWT signatures using Clerk's public RSA key set (`jwks.json`), validating issuer (`iss`), audience (`aud`), and expiration (`exp`).
- **Tenant Scoping:** All database records, document embeddings, and query histories are partitioned by `user_id` / `org_id` with Row Level Security (RLS) enforcement. Cross-tenant data leakage is prevented at the database query layer.

---

## Safe Harbor Policy for Ethical Security Researchers

We consider ethical security research vital to maintaining the safety of Allcited. We support and protect researchers who conduct security evaluations in good faith:

### Safe Harbor Commitments

If you act in good faith and adhere to the following rules:
- **No Legal Action:** We will not initiate or support legal action (including under the Computer Fraud and Abuse Act or DMCA anti-circumvention provisions) against you for accidental or good-faith security research.
- **Support & Collaboration:** We will work with you to understand, reproduce, and resolve any valid vulnerabilities you discover.
- **Attribution & Recognition:** If you are the first to report an unknown vulnerability and adhere to responsible disclosure, we will publicly acknowledge your contribution in our release notes and Security Hall of Fame (unless you request anonymity).

### Ground Rules for Research

To qualify for safe harbor:
- Make a good-faith effort to avoid privacy violations, data destruction, service degradation, or denial-of-service (DoS/DDoS).
- Do not access, modify, or exfiltrate data belonging to other users or organizations. Only interact with test accounts you own or have explicit authorization to inspect.
- Give us reasonable time to investigate and remediate the issue before sharing any information publicly (coordinated vulnerability disclosure).
- Do not exploit a vulnerability beyond the minimum necessary proof of concept to demonstrate impact.
