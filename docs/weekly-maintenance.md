# Scope and weekly maintenance

Scope updated: **2026-10-08**. This policy supersedes the image-input restriction
used in the [2023–2026 search audit](literature-search-2023-2026.md).
The first expanded search is documented in the [2026-10-05 update](updates/2026-10-05.md).
The collection covers computational pathology and adjacent computational tissue,
spatial and single-cell omics. Spatial/single-cell methods do not need a
histopathology image input to qualify.

## Keyword set

The editable [keyword configuration](../config/literature-keywords.json) is the
canonical source for future searches. Search both titles and abstracts; titles
alone miss methods evaluated on tissue or cell data.

| Family | Representative keywords |
| --- | --- |
| Histology and cytology | histopathologic, histologic, pathomics, WSI, whole slide, H&E, virtual staining, nuclei, glands, mitoses, blood smear, bone marrow |
| Spatial omics | spatial transcriptomics/proteomics/multiomics, spatially variable genes, spatial domains, deconvolution, spatial chromatin, MERFISH, seqFISH, Visium, Xenium, CosMx, Stereo-seq |
| Single-cell methods | scRNA-seq, scATAC-seq, multiome, cell type annotation, cell atlas, cross-modal annotation, representation learning, cell-state mapping, CellProfiler, Cell Painting, cell phenotyping |
| Tissue microenvironment | tumor/tumour microenvironment, spatial niches, tissue architecture, cell-cell communication, ligand-receptor, tumor-stroma |
| Cancer multimodal omics | multiomics, radiogenomics, genomics-guided imaging, molecular prediction, cross-modal imputation, missing modality, survival, pan-cancer |

Method terms include machine/deep learning, foundation models, graph models,
contrastive/self-supervised learning, diffusion, flows, optimal transport,
Bayesian inference, clustering, integration, annotation, imputation, benchmarks,
atlases and software. Platform acronyms, generic `cell`, `spatial`, `pathology`,
`WSI` and `missing modality` are retrieval clues, not automatic inclusion rules.

Include computational methods, resources, benchmarks, substantial spatial or
single-cell tissue/disease analyses, and relevant reviews. Cancer multimodal
omics includes genomics-guided radiomics and survival modeling. Exclude unrelated
radiology-only, drug/protein-sequence-only and wet-lab-only studies, editorials,
comments, retractions and duplicate versions. Read abstracts to resolve context.
For adjacent non-spatial omics, require a reusable computational method/resource
or a substantive cell/tissue analysis; routine bulk biomarker association alone
does not qualify. Plant-only applications and unrelated microbial studies are
outside the biomedical tissue scope, although general methods can use them as
additional benchmarks. New backfill entries start in 2023; revisions of older
papers already in the collection can still be checked and updated.

## Journal eligibility

Every formal journal entry, including older years, must be **SCIE indexed** and
**zone 1 in the major category of the CAS 2025 upgraded edition**. CAS stopped
publishing editions from 2026, so 2025 is the latest available edition. The
[2026-10-08 cleanup](updates/2026-10-08-cas-zone1.md) records the institutional
sources, title matching and exclusions. JCR Q1, CAS minor-category zone 1,
the Top label and the separate 2026 Xinrui table do not satisfy this rule.

Use [config/journal-policy.json](../config/journal-policy.json) as the journal
allowlist. A new journal requires verified title/ISSN, CAS major-zone-1 evidence
and SCIE membership before adding it to that file or to the bibliography.
Unranked, non-SCIE and unverifiable journals remain excluded. Conferences,
workshops, unpublished preprints and existing technical reports retain their
separate topical screening rules. Book-series chapters are not eligible as
journal publications.

Do not reintroduce an excluded formal journal paper under a preprint heading.
The collector flags matching identities from
[data/excluded-journal-identities.json](../data/excluded-journal-identities.json).
Resolve these flags before inclusion, including revised titles and cross-postings.
If a candidate has a formal journal version, check its journal eligibility even
when its title or preprint ID is absent from that file. A verified subsequent
conference publication can qualify independently under the conference policy.
When such a version is added, retain its identity links and document the decision.

## Yearly conference and journal search

Search each publication year separately, starting with 2023. Use primary
publisher records, official proceedings/programs, PubMed and Crossref. Recheck
previous exclusions under the expanded scope. Include titles without pathology
terms when their abstracts or experiments demonstrate a qualifying contribution.

In addition to the venues in the README, search Nature Computational Science,
Genome Biology, Genome Medicine, Nature Genetics, Nature Biotechnology, Nature
Methods, Nature Communications, Cell Systems, Science Advances and other journals
in the verified allowlist. Apply the journal eligibility rule before inclusion.
Search ICLR, ICML, NeurIPS, CVPR, ICCV, ECCV, AAAI, IJCAI, MICCAI, MIDL and
relevant ISMB proceedings without an image-input prerequisite.

Assign the formal publication year using the journal issue/publisher or official
conference year. Check online-first versus issue dates and retain their evidence.
Do not label submitted papers as accepted or invent unavailable future proceedings.

## Weekly preprint workflow

The local scheduled task runs **Mondays at 09:00 Asia/Shanghai** and returns to
the maintenance chat. It searches **arXiv, bioRxiv and medRxiv**. It is configured
in the desktop app; this repository documents its workflow, not its scheduler.
For local scheduled work, the computer must be on, the desktop app running and
this checkout available. See the [official scheduling documentation](https://learn.chatgpt.com/docs/automations?surface=app).

1. Fetch the latest repository state and inspect local changes. Preserve user
   edits. Use a separate checkout/branch if the active checkout is dirty.
2. Run `python scripts/search_preprints.py --until YYYY-MM-DD`, with the previous
   UTC day as the end date. Python 3.10+ and the standard library suffice.
   The initial window begins 2026-09-21. Later runs begin 14 days before each
   source's last successful checkpoint, so interruptions and indexing delays can
   be recovered. Longer outages extend the window from the saved checkpoint.
3. Read `.cache/preprint-candidates.json`. The collector uses the
   [arXiv Atom API](https://info.arxiv.org/help/api/user-manual.html), ordered by
   last update to catch revised older papers, and the
   [bioRxiv/medRxiv date-interval API](https://api.biorxiv.org/), paginating every
   result in the requested interval. It records errors and exits with a nonzero
   status if any source failed. It never edits papers or advances checkpoints.
4. Review each candidate's title and abstract. Verify ambiguous papers using
   their primary abstract/full text. Record exclusions and duplicates. Resolve
   DOI, arXiv ID, title variants, cross-postings and formal publication links.
   A preprint revision updates its existing record instead of adding a paper.
   For bioRxiv/medRxiv revisions, verify the first-posted date from the DOI's
   version history; the collector's `posted`/`year` is the version date returned
   in the requested window and is provisional. Keep new preprints explicitly
   under their server headings. Exclude candidates with an ineligible formal
   journal version and resolve every `journal_policy_exclusion` flag. Promote
   verified formal versions only to an eligible journal or a verified conference
   and publication year while preserving code/data/site links.
   Retain the previous server URL as a `[[preprint](URL)]` badge on a promoted
   entry. The collector compares these identity links as well as the main paper
   link, so a conference title change does not turn a revision into a new paper.
5. Edit `papers/YYYY.md` in the established one-paper-per-line format. Create a
   new annual file when needed. Run `python scripts/journal_policy.py` and
   `python scripts/refresh_index.py`; the latter validates journal eligibility
   before changing the index. Check unique identities, correct venue/year,
   preserved original entries/links and
   README counts/anchors. Do not claim exhaustive coverage from keyword matches.
   Keep each rendered file below 500 KiB. If an annual list outgrows that limit,
   split it into linked venue/topic lists and adapt both scripts to read/count
   all companion lists before publishing the change. Run
   `python -m unittest discover -s tests` before publication.
6. Save a dated audit in `docs/updates/`: intervals, source status, exact query
   links, retrieval/candidate counts, inclusion/exclusion decisions and verified
   additions/promotions/corrections. Do not commit large unfiltered API caches.
7. Publish a focused commit and push to the owned GitHub repository. Follow the
   existing branch/PR review-and-merge workflow, attach any created PR to the
   chat and merge after applicable checks. Do not force-push user branches.
   Publish checkpoint changes with the reviewed update. Advance a source's
   `last_successful_until` in `data/weekly-update-state.json` only after its whole
   interval has been retrieved and reviewed and the update is published. Failed
   or incompletely screened sources retain their previous checkpoint. If Git
   publication fails, retain candidates and restore the previous checkpoint in
   the active checkout. Retry publication before scanning a newer window.
8. Give one Chinese weekly summary: added/promoted/corrected counts, highlights,
   covered dates, source failures and GitHub update links. A completed search
   with zero new papers should say so explicitly.

Future maintenance can use another installed Python runtime if `python` is not
available on the machine. Credentials are supplied by the existing Git setup;
never save tokens in this repository.
