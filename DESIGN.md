# DESIGN — UX and API Design

> Version 0.1 (DRAFT). Covers user experience and API contracts. System internals are in ARCHITECTURE.md.

## 1. Design Principles
1. **Trust through evidence:** no claim without a clickable source.
2. **Privacy visible:** the user always sees which sources are public and which are private.
3. **Honest uncertainty:** show "not found" and abstentions clearly.
4. **Calm and dense:** lawyers read a lot; prioritise readability over decoration.
5. **No silent failure:** denied or quarantined content produces a safe, generic message.

## 2. Key Screens
| Screen | Purpose | Main elements |
|---|---|---|
| Sign in | Authenticate | Email/password (v1), OAuth later |
| Workspace home | Choose matter or public search | Matter list, "Public law only" option, recent queries |
| Ask | Main query screen | Query box, matter selector (multi), filters (court, year, statute), Ask button |
| Answer | Results | Key issues, statutes, precedents, claims table, counter-arguments, verification badges |
| Source viewer | Check evidence | Passage with highlighted paragraph, court, date, citation, public/private label |
| Matter files | Manage uploads | Upload, processing status, quarantined files |
| Members | Manage access | Add/remove member, role, change takes effect immediately |
| Audit | Security events | Time, request ID, decision, document ID (no text) |

## 3. Answer Layout
```
┌ Query ───────────────────────────────────────────────┐
│ [ describe the case ........................ ] [Ask] │
│ Scope: [x] Public law  [x] Matter A  [ ] Matter B     │
└──────────────────────────────────────────────────────┘
Key issues
Relevant statutes and sections
Precedents            (court weight: SC > HC > lower)
Claims and evidence   | Claim | Source | Status |
Counter-arguments / adverse precedents
Not found / insufficient evidence
Note: research support only, not legal advice.
```

## 4. Verification Badges
| Badge | Meaning |
|---|---|
| Supported | Cited passage backs the claim |
| Partially supported | Passage is related but incomplete |
| Not found | No authorized evidence located |
| Good law check | Overruled / amended / repealed warning shown on the citation |

## 5. Source Labels
- **Public** (grey tag)
- **Private: Matter X** (lock icon + matter name)

Mixed answers always show both labels. Exports keep the labels.

## 6. States and Messages
| State | Message style |
|---|---|
| No authorized evidence | "No supporting material found in the sources you can access." (does not reveal whether other matters exist) |
| Policy changed mid-request | "Your access changed. Please run the query again." |
| Parse failure on upload | File shown as "Needs review", never searchable |
| Slow generation | Stream text; show retrieval results first |

## 7. Accessibility and Language
- Keyboard-navigable, readable contrast, scalable text
- English first; Hindi/Marathi is a v2 item **(ASSUMPTION)**

## 8. API Design (REST, JSON)
| Method | Path | Description |
|---|---|---|
| POST | /auth/login | Returns session token |
| GET | /matters | Matters the user can access |
| POST | /matters/{id}/documents | Upload file to matter |
| GET | /matters/{id}/documents | List documents and status |
| POST | /matters/{id}/members | Add member (admin) |
| DELETE | /matters/{id}/members/{user} | Revoke member (admin) |
| POST | /query | Ask a question (see below) |
| GET | /sources/{chunk_id} | Fetch source passage if authorized |
| GET | /audit | Security events (admin) |

**POST /query**
```json
{
  "question": "string",
  "scope": { "public": true, "matter_ids": ["m1"] },
  "filters": { "court": ["SC"], "year_from": 2000 },
  "stream": true
}
```
**Response**
```json
{
  "request_id": "r-123",
  "answer": { "issues": [], "statutes": [], "precedents": [], "claims": [
    { "text": "...", "status": "supported",
      "citations": [{ "chunk_id": "c-9", "tier": "public", "court": "SC", "date": "YYYY-MM-DD", "paragraph": 14 }] }
  ], "counter_arguments": [], "not_found": [] },
  "abstained": false
}
```
Rules: requested matter IDs outside the user's permissions are ignored or rejected with a generic error; errors never include document text; all responses carry `request_id`.

## 9. Visual Style (starting point, ASSUMPTION)
Neutral palette, one accent colour for verification badges, serif for legal text, sans-serif for UI, generous line spacing.
