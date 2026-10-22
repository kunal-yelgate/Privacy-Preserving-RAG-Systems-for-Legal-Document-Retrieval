# Security Policy: Privacy-Preserving Offline Legal RAG

## 1. Reporting Vulnerabilities
This system is developed as an offline-first research prototype for privacy-preserving legal document intelligence.
If you identify a security issue, vulnerability, or unexpected network leak, please report details locally or open a confidential issue without posting confidential legal texts or sensitive tokens.

## 2. Security Boundaries & Assumptions
- **Host System Security**: The application assumes the Windows host operating system is trusted. Physical disk encryption (such as Windows BitLocker) is recommended to protect plaintext SQLite and ChromaDB data at rest.
- **Network Isolation**: By design, the application binds only to loopback interfaces (`127.0.0.1`). It does not initiate connections to external clouds. When verifying strict air-gapped performance, disable the host machine's external network adapter or configure Windows Firewall outbound block rules.
- **Access Control**: Authorization rules are strictly enforced at the backend service and repository layers. Frontend UI restrictions are present for usability, not security enforcement.
