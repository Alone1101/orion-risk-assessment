# ORION

An auditable AI-assisted pipeline for structured authorization risk assessment.

ORION processes application metadata and supporting PDF, DOCX, and XLSX documents for firms seeking authorization to provide high-risk financial or digital infrastructure services. It extracts risk-relevant evidence, assesses predefined risk dimensions, identifies missing or contradictory information, calculates deterministic risk scores, and produces a structured reviewer-ready result.

## Design Principle

> **LLMs interpret evidence; deterministic policy logic makes the risk calculation.**

The LLM is used only where interpretation of unstructured evidence is required. It extracts risk findings, identifies missing or inconsistent information, and links each finding to source evidence. Risk scores, ratings, composite scores, and authorization recommendations are calculated by deterministic Python policy logic.

This separation keeps material decisions auditable and prevents the LLM from directly determining the final authorization outcome.

## Pipeline

```text
Application JSON + referenced documents
                  │
                  ▼
        Multi-format ingestion
        PDF / DOCX / XLSX
                  │
                  ▼
          Bounded chunking
                  │
                  ▼
     Dimension-aware retrieval
                  │
                  ▼
       Structured LLM extraction
                  │
                  ▼
       Provenance verification
                  │
                  ▼
    Deterministic policy scoring
                  │
                  ▼
       ReviewerResult payload
                  │
                  ▼
        External review API
```

The five assessed risk dimensions are:

- Governance and ownership
- Financial resilience
- Operational resilience
- Cybersecurity and data protection
- Compliance and integrity

## Quick Start

### Requirements

- Python 3.12+
- [Ollama](https://ollama.com/)
- Docker (optional, for containerized execution)

ORION uses `qwen3:8b` through Ollama as the default local LLM.

Pull the model:

```bash
ollama pull qwen3:8b
```

### Local Setup

Create and activate a Python 3.12 environment, then install ORION and its development dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest
```

Run the included example:

```bash
orion examples/application.json
```

The command processes the application metadata and referenced documents, runs the assessment pipeline, and prints the structured `ReviewerResult` as JSON.

### Docker

Build the image:

```bash
docker build -t orion-risk-assessment .
```

When Ollama is running on a Windows host with Docker Desktop, run:

```powershell
docker run --rm `
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
  -v "${PWD}/examples:/data:ro" `
  orion-risk-assessment `
  /data/application.json
```

The `examples` directory is mounted read-only at `/data`. `OLLAMA_BASE_URL` directs the container to the Ollama service running on the host machine.

## Architecture and Design Decisions

### 1. Evidence Interpretation vs. Policy Decisions

ORION deliberately separates probabilistic evidence interpretation from deterministic policy logic.

The LLM is responsible for:

- Interpreting unstructured application evidence
- Extracting risk-relevant findings
- Identifying missing or contradictory information
- Assigning extraction confidence
- Linking findings to supporting evidence

Deterministic Python logic is responsible for:

- Mapping finding severity to risk scores
- Calculating dimension ratings
- Applying dimension weights
- Calculating the composite risk score
- Selecting the authorization recommendation
- Generating required clarification questions

This boundary makes the final decision path inspectable and prevents an LLM response from directly determining an authorization outcome.

### 2. Structured and Validated Outputs

Pydantic models define the contracts between ingestion, extraction, scoring, and delivery. Risk scores and confidence values are range-constrained, while enums restrict dimensions, ratings, severities, statuses, and recommendations to known values.

LLM output is parsed and validated before entering the scoring pipeline. Invalid source references or evidence excerpts that cannot be matched to the supplied source text are rejected rather than silently accepted.

### 3. Evidence Provenance

Each material finding carries an `EvidenceReference` containing:

- Document identifier
- Document name
- Page or section where available
- Supporting excerpt

PDF evidence retains page-level provenance. DOCX and XLSX inputs retain structural provenance such as paragraph or worksheet-row identifiers.

This allows a reviewer to trace an extracted finding back to the evidence supplied to the model.

### 4. Missing Evidence Is Not Low Risk

ORION distinguishes between an assessed low-risk dimension and a dimension for which sufficient evidence was not available.

If required evidence is missing, the dimension receives an `insufficient_evidence` status rather than an artificial low score. The composite score is withheld and the pipeline returns `request_clarification` together with deterministic follow-up questions.

This prevents absence of information from being interpreted as evidence of low risk.

### 5. Bounded Document Processing

Large documents are processed through bounded chunking followed by dimension-aware retrieval. Only the highest-ranked relevant chunks are supplied to the LLM for each risk dimension.

This design reduces unnecessary model context, latency, and inference cost while keeping retrieval deterministic and inspectable. If retrieval finds no relevant evidence for a dimension, ORION skips the LLM call and records the required evidence as missing.

### 6. LLM Provider Boundary

LLM access is defined behind an `LLMProvider` interface. The included implementation uses Ollama with `qwen3:8b`, allowing the pipeline to run locally without embedding model-specific behavior throughout the assessment logic.

The default generation temperature is `0` to reduce sampling variability. Exact reproducibility can still depend on the model, inference runtime, and environment.

### 7. Auditability and Logging

The reviewer payload includes audit metadata identifying the pipeline version, policy version, LLM provider, and model.

Runtime tracing records major pipeline stages, retrieved chunk counts, extraction counts, model latency, and overall assessment latency. Raw prompts, document contents, and model responses are not written to application logs.

### 8. External Review Boundary

Assessment results are represented as a structured `ReviewerResult` and can be POSTed to an external review API. HTTP delivery failures are surfaced rather than silently treated as successful.

The pipeline produces recommendations rather than performing an irreversible authorization action. The structured result and source evidence are intended to support downstream human validation and override.

## Evaluation

ORION includes both behavioral evaluation cases and a preprocessing benchmark. The evaluation suite is intentionally synthetic and is designed to test specific pipeline behaviors rather than claim production-level regulatory accuracy.

### Behavioral Evaluation

The behavioral suite exercises five scenarios:

| Case | Expected behavior |
| --- | --- |
| Missing disaster recovery evidence | Detect missing operational-resilience evidence and request clarification |
| High-risk cybersecurity evidence | Detect a high-severity cybersecurity finding |
| Contradictory disaster recovery evidence | Detect the inconsistency and request clarification |
| Irrelevant and redundant material | Retain the relevant risk signal despite surrounding noise |
| Complete low-risk application | Assess all five dimensions and produce a composite score |

A baseline run using the local `qwen3:8b` provider passed all five synthetic cases:

```text
Cases passed: 5 / 5
Pass rate: 100%
```

This result demonstrates expected behavior on the included fixtures only; it should not be interpreted as a general measure of regulatory assessment accuracy.

Run the behavioral evaluation with:

```bash
python evals/run_evals.py
```

### Large-Document Preprocessing Benchmark

A separate benchmark exercises the deterministic preprocessing path on a synthetic 41-page DOCX regulatory application containing administrative noise, repeated material, and planted evidence across the five risk dimensions.

The fixture contained:

```text
Ingested chunks:       298
Chunks after splitting: 298
Total characters:      100,231
```

Dimension-aware retrieval produced:

| Risk dimension | Retrieved chunks | Characters selected | Text reduction | Expected evidence retained |
| --- | ---: | ---: | ---: | --- |
| Governance and ownership | 10 | 2,814 | 97.2% | PASS |
| Financial resilience | 3 | 275 | 99.7% | PASS |
| Operational resilience | 4 | 406 | 99.6% | PASS |
| Cybersecurity and data protection | 3 | 338 | 99.7% | PASS |
| Compliance and integrity | 4 | 292 | 99.7% | PASS |

On this fixture, the retrieval stage retained all planted dimension-specific evidence while reducing the text selected for each dimension by **97.2% to 99.7%** relative to the complete 100,231-character input.

The unchanged `298 -> 298` chunk count indicates that DOCX paragraph-level ingestion had already produced units below the configured chunk-size limit; the subsequent bounded splitter therefore did not need to divide them further.

Run the preprocessing benchmark with:

```bash
python evals/preprocessing_efficiency.py
```

### Evaluation Scope

These evaluations target engineering properties of the pipeline: structured-output behavior, risk-signal detection, missing-information handling, contradiction handling, retrieval under irrelevant material, and bounded preprocessing.

The fixtures and policy are synthetic. A production deployment would require evaluation against representative ORION applications, domain-expert labels, approved policy thresholds, and a substantially larger test set.

## Limitations and Production Considerations

This repository is a bounded reference implementation rather than a production regulatory decision system. The following areas would require additional work before deployment.

### 1. Object Storage

The demo submission uses local file paths so the pipeline can be executed directly or in Docker. In production, `DocumentReference` resolution would be backed by the authority's object-storage service, such as S3, Azure Blob Storage, or GCS.

The downstream ingestion interface can remain unchanged: retrieved objects are converted into the same `DocumentChunk` representation before entering the processing pipeline.

### 2. Document Extraction

PDF extraction currently supports text-based PDFs and does not perform OCR. Scanned or image-only documents would require an OCR stage.

DOCX provenance is recorded at paragraph level rather than rendered page number because page boundaries depend on document rendering. XLSX provenance is recorded using worksheet and row information.

### 3. Retrieval

The current retrieval layer uses deterministic dimension-specific keyword matching. This is inexpensive, inspectable, and suitable as a baseline, but it can miss semantically relevant evidence that does not contain configured terminology.

A production system could evaluate hybrid lexical and embedding-based retrieval against a representative labeled corpus before increasing retrieval complexity.

### 4. LLM Reliability

LLM extraction is schema-validated and evidence references are checked against supplied source text, but these controls do not guarantee that every interpretation is correct.

`temperature = 0` reduces sampling variability but does not guarantee bit-for-bit reproducibility across model versions, inference runtimes, or hardware.

Human review therefore remains part of the intended workflow.

### 5. Policy Calibration

The included severity scores, dimension weights, rating thresholds, and authorization thresholds are illustrative demonstration policy.

Production values must be defined and versioned by the relevant policy and regulatory stakeholders and validated against representative historical or expert-labeled cases.

### 6. Execution Time

Document retrieval is bounded and dimensions without relevant evidence do not trigger LLM calls. However, dimensions requiring interpretation are currently processed sequentially.

LLM inference is therefore the primary latency bottleneck. A production serverless implementation could evaluate bounded concurrent model requests, batching, caching, and checkpointing against the platform's execution and rate limits.

### 7. External API Delivery

The delivery adapter validates HTTP success and surfaces failed responses. Production integration would additionally require endpoint authentication, retry and backoff policy, idempotency controls, timeout policy, and appropriate handling of transient failures.

## Repository Structure

```text
.
├── src/orion/
│   ├── models.py       # Domain models and validated data contracts
│   ├── ingestion.py    # PDF, DOCX, and XLSX extraction
│   ├── chunking.py     # Bounded text chunking
│   ├── retrieval.py    # Dimension-aware evidence retrieval
│   ├── llm.py          # LLM provider abstraction and Ollama provider
│   ├── extraction.py   # Structured evidence extraction and provenance checks
│   ├── policy.py       # Versioned risk policy and thresholds
│   ├── scoring.py      # Deterministic scoring and recommendations
│   ├── pipeline.py     # End-to-end assessment orchestration
│   ├── submission.py   # Submission loading and document resolution
│   ├── delivery.py     # External review API delivery
│   └── cli.py          # Command-line entry point
├── examples/           # Self-contained runnable example
├── tests/              # Unit and integration tests
├── evals/              # Behavioral and preprocessing evaluations
├── Dockerfile
├── pyproject.toml
└── README.md
```