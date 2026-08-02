# PDFOCR PaddleV3 GitHub Release Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a truthful, source-only GitHub release package for PDFOCR PaddleV3 25-1 and publish it to a new public GitHub repository.

**Architecture:** Keep the verified 25-1 Python program unchanged. Add a Chinese-first README, dependency and repository metadata, and three extracted screenshots; validate all claims against the code before committing. Publish only after local verification and authenticated GitHub access are available.

**Tech Stack:** Markdown, Git, Python AST validation, PaddleOCR 3 / PP-StructureV3 documentation, GitHub.

## Global Constraints

- The release program is `PDFOCR_PaddleV3.py`, and its content must match `PDFOCR-25-1标点宽度调整.py` exactly.
- Do not claim vertical-text support; vertical or complex rotated text is an explicit limitation.
- The current implementation requires `gpu:0`; do not advertise CPU fallback.
- Do not upload Paddle models, CUDA packages, user PDFs, OCR output, caches, or `images.docx`.
- Do not modify OCR algorithms or package an EXE.
- The remote repository is public and named `PDFOCR_PaddleV3` unless GitHub rejects that name.

---

### Task 1: Verify release source and assets

**Files:**
- Verify: `PDFOCR_PaddleV3.py`
- Read: `images.docx`
- Read: `docs/superpowers/specs/2026-08-02-github-release-docs-design.md`

**Interfaces:**
- Consumes: 25-1 source file and three screenshots embedded in `images.docx`
- Produces: verified source identity and three named PNG assets

- [ ] Compare SHA-256 hashes of the release program and the 25-1 source.
- [ ] Parse the release program with Python `ast.parse`.
- [ ] Extract the three embedded PNG files as `docs/images/main-interface.png`, `docs/images/advanced-options.png`, and `docs/images/recognition-preview.png`.
- [ ] Confirm all three PNG files have valid PNG signatures and non-zero dimensions.

### Task 2: Create GitHub release documentation

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `LICENSE`

**Interfaces:**
- Consumes: verified code features, official installation links, and screenshot paths
- Produces: a self-contained source release that a GitHub visitor can understand and install

- [ ] Write a Chinese-first README with a short English summary, screenshots, features, limits, requirements, installation, GUI usage, CLI usage, advanced options, output rules, troubleshooting, credits, and license.
- [ ] Keep PaddlePaddle GPU installation separate and link to the official installer because the wheel depends on the user's CUDA environment.
- [ ] Write `requirements.txt` using `paddleocr[doc-parser]`, `PyMuPDF`, `Pillow`, `numpy`, and `tqdm`; rely on PaddleOCR/PaddleX for `opencv-contrib-python` so `cv2` is not installed by two conflicting OpenCV packages, and do not add the unrelated `fitz` package.
- [ ] Write `.gitignore` for Python caches, virtual environments, models, PDF inputs/outputs, build products, IDE settings, and `images.docx`, while explicitly preserving `docs/images/*.png`.
- [ ] Add the complete GPL-3.0 license text.

### Task 3: Validate and commit the release package

**Files:**
- Verify: all intended repository files

**Interfaces:**
- Consumes: Task 1 assets and Task 2 documentation
- Produces: a locally committed, publication-ready repository

- [ ] Re-run SHA-256 comparison and Python AST parsing.
- [ ] Scan README for prohibited vertical-support claims, missing screenshot paths, CLI parameters absent from the code, placeholder text, and private local paths.
- [ ] Verify every README relative link and image path resolves.
- [ ] Verify no tracked file exceeds 25 MiB and no model/PDF/cache file is staged.
- [ ] Stage only the program, README, requirements, `.gitignore`, license, images, design, and plan.
- [ ] Commit with message `docs: prepare PDFOCR PaddleV3 source release`.

### Task 4: Publish to GitHub

**Files:**
- No additional local files

**Interfaces:**
- Consumes: verified local `main` branch and authenticated GitHub access
- Produces: public `PDFOCR_PaddleV3` repository URL

- [ ] Confirm GitHub CLI is installed and authenticated, or confirm the connected GitHub app can access an existing empty repository.
- [ ] Create a public repository named `PDFOCR_PaddleV3` with description `GUI and CLI PDF OCR tool based on PaddleOCR 3 and PP-StructureV3, with layout-aware margin filtering.`
- [ ] Add the repository as `origin` and push local `main`.
- [ ] Read back the remote repository metadata and README to confirm public visibility and successful upload.
- [ ] Report the repository URL and any remaining release caveats.
