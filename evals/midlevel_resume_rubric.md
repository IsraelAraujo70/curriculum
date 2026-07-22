# Mid-Level International Resume Eval

Evaluate the supplied English resume for this target:

- Mid-level backend or full-stack engineering
- International remote roles open to candidates in Brazil/LatAm
- Primary stack: Python, TypeScript, AWS
- Supporting strengths: SaaS, integrations, event-driven systems, AI-assisted workflows

Score each criterion from 0 to 20 and cite exact resume evidence:

1. Positioning clarity: the target role and primary stack are obvious within ten seconds.
2. Credibility: seniority, dates, scope, and metrics are internally consistent and believable.
3. Relevance: experience emphasizes production outcomes aligned with the target role.
4. Evidence: bullets show ownership, architecture, constraints, and results without exposing confidential details.
5. Recruiter usability: concise, skimmable, ATS-friendly, professional English, and no unnecessary keyword list.

Disqualifiers:

- Any unsupported 5+ years or senior-level claim
- Conflicting experience duration
- Vanity metrics based on commits, file counts, or stars of other repositories
- Evasion, bypass, credential, or security-sensitive implementation wording
- More than two PDF pages

Pass threshold: 85/100 and no disqualifier.

Return exactly:

```text
SCORE: <0-100>
VERDICT: PASS|FAIL
DISQUALIFIERS: <none or semicolon-separated list>
EVIDENCE: <one concise paragraph>
TOP_FIX: <single highest-impact fix or none>
```

