# Literature search and update: 2023–2026

Search cutoff: **2026-10-04**. Baseline: `b27fc2b`. This is a bibliography
coverage audit based on primary bibliographic records and available abstracts;
it is not a full-text systematic review or a ranking of paper quality.

## Update totals

| Publication year | New publications | Preprints moved to formal venues | Metadata corrections |
| --- | ---: | ---: | ---: |
| 2023 | 645 | 1 | 4 |
| 2024 | 583 | 10 | 10 |
| 2025 | 690 | 49 | 8 |
| 2026 | 675 | 67 | 7 |

The update adds **2,593 publications**, promotes
**127 preprints**, and corrects **29 existing records**.
The collection now contains **4,514 publication entries**. Existing code, dataset and
website links are retained when an entry is promoted or corrected. Repeated venue
headings within each year have been consolidated.

The canonical 2023–2026 lists are [annual Markdown files](../papers/2026.md),
with year and venue links in the README. Earlier years remain in the README.
This keeps each rendered file below [GitHub’s 500 KiB README limit](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
Future additions should be made in the corresponding annual file, followed by
an update to its README counts.

### TMI and Medical Image Analysis

| Year | TMI before | TMI after | MedIA before | MedIA after |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 0 | 28 | 2 | 33 |
| 2024 | 2 | 24 | 4 | 32 |
| 2025 | 7 | 36 | 7 | 40 |
| 2026 | 1 | 37 | 5 | 68 |

## Search strategy

Searches were run separately for 2023, 2024, 2025 and 2026. Exact PubMed queries,
hit counts, retrieval counts and paper-level provenance are available in the
[machine-readable update manifest](literature-update-2023-2026.json).

### Terminology

- Tissue and diagnosis: histopathology, histology, histopathologic, histologic,
  histomorphology, pathomics, cytology, cytopathology, hematopathology, morphometry.
- Slides and preparation: whole-slide / whole slide, WSI, gigapixel, tissue
  microarray, digital microscopy, hematoxylin / haematoxylin and eosin, H&E,
  immunohistochemistry, virtual staining, stain transfer and normalization.
- Structures and tasks: nuclei / nucleus, gland segmentation, mitoses / mitotic
  figures, glomeruli, blood cells, blood smears, bone marrow, Pap smears, Gleason.
- Molecular context: spatial transcriptomics, spatial proteomics, tumor / tumour
  microenvironment, image-omics fusion and gene-expression prediction.
- Methods: deep learning, machine learning, artificial intelligence, neural
  networks, foundation models, vision-language models, computer vision, automated
  image analysis, multiple-instance learning, survival prediction and graphs.

Generic titles were also screened through official conference abstracts where
available. A paper can be included when its experiments use histopathology even
if its title does not contain “pathology”. For example, the update includes
[Improving Representation Learning for Histopathologic Images with Cluster Constraints](https://openaccess.thecvf.com/content/ICCV2023/html/Wu_Improving_Representation_Learning_for_Histopathologic_Images_with_Cluster_Constraints_ICCV_2023_paper.html)
under ICCV 2023, and HiDisc / hierarchical discriminative learning under CVPR 2023.

### Journal sources

1. **TMI and MedIA:** all annual PubMed records were retrieved without a pathology
   keyword filter, then screened by title and abstract. Crossref journal corpora
   were checked independently to cover records absent from PubMed.
2. **General technical journals:** Crossref corpora for Pattern Recognition,
   TPAMI, TNNLS and IJCV were screened. PubMed searches also covered JBHI,
   Computers in Biology and Medicine, Computerized Medical Imaging and Graphics,
   Artificial Intelligence in Medicine, Computer Methods and Programs in
   Biomedicine, Journal of Medical Imaging, Journal of Pathology Informatics,
   Bioinformatics, Briefings in Bioinformatics, Neurocomputing and Biomedical
   Signal Processing and Control.
3. **Biomedical and pathology journals:** expanded annual PubMed searches covered
   Nature / Cell / Lancet families, clinical oncology, computational biology and
   pathology journals. The manifest preserves the complete journal expressions.
   Histopathology, Human Pathology, Virchows Archiv, surgical / clinical pathology
   journals, Acta Neuropathologica, Diagnostic Pathology, Cytopathology, Cancer
   Cytopathology and Leukemia were searched in supplementary passes.

| Annual PubMed query family | 2023 hits | 2024 hits | 2025 hits | 2026 hits |
| --- | ---: | ---: | ---: | ---: |
| core | 662 | 716 | 920 | 906 |
| technical | 171 | 175 | 218 | 166 |
| biomedical | 240 | 314 | 433 | 362 |
| expanded | 568 | 725 | 1061 | 848 |
| additional | 339 | 305 | 479 | 478 |
| pathology_journals | 67 | 103 | 112 | 100 |
| pathology_supplement | 28 | 18 | 29 | 37 |

Query families overlap. Hit counts are discovery counts, not unique included
papers. PubMed publication-date searches may retrieve the same article for its
online year and issue year. Deduplication occurs before inclusion. Crossref was
queried from 2022 as a buffer for online-first papers assigned to 2023 issues.

### Conference sources

- MICCAI 2023: official proceedings titles and available abstracts. MICCAI
  2024–2026 remains covered by the preceding [MICCAI update](https://github.com/wyh196646/Awesome-AI-Pathology/pull/5).
- CVPR 2023–2026, ICCV 2023/2025 and WACV 2023–2026: CVF Open Access.
- ECCV 2024: ECVA proceedings and official program; ECCV 2026: official accepted
  program records and linked papers.
- MIDL 2023–2026, ICML 2023–2026 and ML4H 2023–2025: PMLR proceedings.
- ICLR 2023–2026, NeurIPS 2023–2025, ICML, CVPR, ICCV 2025 and ECCV:
  official virtual-program metadata enabled searches across available abstracts,
  including papers with generic titles. NeurIPS 2025 links were reconciled
  against the final main-conference proceedings.
- AAAI 2023–2026: Crossref metadata for the proceedings ISSN 2374-3468, including
  available abstracts. IJCAI 2023–2026: official annual title directories, with
  abstracts retrieved for broadly relevant titles.

## Inclusion and deduplication

Included records concern computational analysis of histology / cytology / tissue
images, virtual staining, image-based molecular prediction, pathology reports,
relevant datasets, methods, reviews and clinical validation. Methods using
pathology images as a substantial experimental setting can also be included.
Quantitative tissue-image analysis and multiplex tissue imaging are in scope.

Excluded records include radiology-only “pathology” prediction, nuclear-magnetic
resonance, nucleic-acid sequence methods, spatial-omics methods without verified
tissue-image involvement, unrelated clinical prediction, corrections, retractions,
comments and editorials. AAAI student abstracts and workshop records are outside
the main-conference screen in this update.

Identifiers (DOI / PMID), normalized titles and manually reviewed title variants
were used to match publications. Changed preprint titles were checked against
author lists and primary records. Similar titles alone do not justify merging.
The MICCAI 2025 and MedIA 2026 versions of PTCMIL are separate publications and
are both retained. Two distinct Nature Biomedical Engineering papers on
generalizable multiple-instance learning are also retained separately.

Journal entries use the assigned issue year where available; otherwise they use
the online publication year. The DOI suffix is not treated as a publication year.
For conflicting metadata, publisher issue labels take precedence. For example,
[THItoGene belongs to volume 25, issue 1, January 2024](https://academic.oup.com/bib/article/25/1/bbad464/7494746),
despite misleading 2023 issue-date fields in PubMed and Crossref. The same issue
check resolves several [volume 26, issue 1](https://academic.oup.com/bib/issue/26/1)
records to 2025. Conferences use the event year, including PMLR proceedings
published in a later calendar year.

## Coverage limits

This is a broad, source-verified expansion rather than a claim of exhaustive
coverage. PubMed indexing delays, incomplete Crossref abstracts, terminology
variation and inaccessible publisher records can still leave gaps. Title-only
records with clear pathology scope are included even when an abstract is missing.
Conference program arrays can repeat oral/poster presentations; these are
deduplicated by title and venue.

Full virtual-program metadata was unavailable for CVPR 2026 and ICCV 2023;
the CVF proceedings title screen and linked candidate abstracts were used instead.
The NeurIPS 2026 accepted program was unavailable at the cutoff, so no paper is
promoted to that venue without confirmation. ACM MM, WWW, workshops, smaller
meetings and journals outside the recorded search expressions were not subjected
to a new complete annual-directory screen. Existing entries are preserved.

## Validation

- The collection contains 4,514 entries, matching the manifest and annual counts.
- No duplicate DOI remains. The repeated PTCMIL title refers to its verified
  MICCAI 2025 and MedIA 2026 publications.
- Unchanged original paper entries and auxiliary code, dataset and website links
  were checked for preservation.
- Local navigation, annual venue headings and paper-link syntax were checked.
- GitHub's Markdown renderer returned all 688 / 920 / 1,328 / 1,440 entries in the
  2023 / 2024 / 2025 / 2026 files. The README and annual files are below 500 KiB.
- Paper identities were verified against bibliographic records or official
  proceedings. This does not claim that every publisher URL is freely accessible.

## Final venue counts for 2023–2026

| Venue | 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: |
| AAAI | 4 | 10 | 12 | 22 |
| ACM MM 2024 | 0 | 2 | 0 | 0 |
| ACM MM 2025 | 0 | 0 | 12 | 0 |
| Acta Neuropathologica | 1 | 1 | 0 | 0 |
| Acta Neuropathologica Communications | 2 | 2 | 1 | 0 |
| Advanced Science | 1 | 1 | 6 | 14 |
| American Journal of Clinical Pathology | 2 | 3 | 7 | 2 |
| Annual Review of Biomedical Data Science | 0 | 0 | 1 | 0 |
| Annual Review of Cancer Biology | 1 | 1 | 0 | 0 |
| Annual Review of Pathology | 0 | 1 | 0 | 0 |
| Archives of Pathology & Laboratory Medicine | 6 | 6 | 7 | 6 |
| Artificial Intelligence in Medicine | 3 | 5 | 8 | 8 |
| Artificial Intelligence Review | 0 | 0 | 1 | 0 |
| arXiv | 1 | 138 | 312 | 331 |
| Bioinformatics | 5 | 6 | 7 | 10 |
| Biomedical Signal Processing and Control | 0 | 0 | 1 | 1 |
| bioRxiv | 0 | 0 | 1 | 65 |
| BMC Bioinformatics | 3 | 2 | 3 | 2 |
| BMC Cancer | 4 | 10 | 9 | 6 |
| BMC Medicine | 0 | 1 | 1 | 1 |
| Breast Cancer Research and Treatment | 0 | 1 | 0 | 0 |
| Briefings in Bioinformatics | 2 | 8 | 15 | 13 |
| Cancer Cell | 1 | 0 | 0 | 3 |
| Cancer Cytopathology | 7 | 4 | 6 | 11 |
| Cancer Medicine | 8 | 9 | 4 | 5 |
| Cancer Research | 2 | 5 | 4 | 7 |
| Cancers | 43 | 29 | 23 | 28 |
| Cell | 0 | 1 | 0 | 2 |
| Cell Reports Medicine | 8 | 5 | 1 | 2 |
| Cell Systems | 1 | 1 | 1 | 0 |
| Clinical Cancer Research | 2 | 3 | 3 | 8 |
| Communications Medicine | 3 | 6 | 7 | 4 |
| Computational and Structural Biotechnology Journal | 0 | 1 | 0 | 0 |
| Computer Methods and Programs in Biomedicine | 27 | 16 | 20 | 20 |
| Computerized Medical Imaging and Graphics | 13 | 13 | 9 | 9 |
| Computers in Biology and Medicine | 33 | 35 | 56 | 9 |
| CVPR | 13 | 21 | 23 | 38 |
| Cytopathology | 5 | 3 | 3 | 8 |
| Diagnostic Pathology | 6 | 6 | 5 | 9 |
| Diagnostics | 43 | 21 | 33 | 34 |
| eBioMedicine | 7 | 4 | 4 | 1 |
| ECCV | 0 | 17 | 0 | 19 |
| EMNLP 2025 | 0 | 0 | 1 | 0 |
| European Journal of Cancer | 0 | 0 | 1 | 0 |
| Genome Biology | 0 | 1 | 1 | 3 |
| Harvard Thesis | 0 | 0 | 1 | 0 |
| Histology and Histopathology | 0 | 1 | 1 | 2 |
| Histopathology | 9 | 10 | 9 | 8 |
| Human Pathology | 3 | 3 | 6 | 7 |
| ICCV | 10 | 0 | 21 | 0 |
| ICLR | 3 | 3 | 5 | 11 |
| ICML | 0 | 1 | 9 | 16 |
| IEEE Journal of Biomedical and Health Informatics | 14 | 17 | 20 | 22 |
| IEEE Transactions on Artificial Intelligence | 0 | 1 | 0 | 0 |
| IEEE Transactions on Medical Imaging | 28 | 24 | 36 | 37 |
| IEEE Transactions on Neural Networks and Learning Systems | 0 | 1 | 2 | 0 |
| IEEE Transactions on Pattern Analysis and Machine Intelligence | 1 | 0 | 1 | 1 |
| IJCAI | 1 | 1 | 9 | 4 |
| International Journal of Cancer | 2 | 3 | 0 | 0 |
| International Journal of Computer Vision | 0 | 1 | 1 | 4 |
| INTERSPEECH 2024 | 0 | 1 | 0 | 0 |
| iScience | 9 | 2 | 5 | 9 |
| JAMA Dermatology | 0 | 1 | 0 | 0 |
| JAMA Oncology | 1 | 0 | 2 | 1 |
| Journal of Biomedical Informatics | 1 | 2 | 2 | 2 |
| Journal of Clinical Oncology | 0 | 1 | 2 | 2 |
| Journal of Medical Imaging | 9 | 8 | 13 | 6 |
| Journal of Pathology Informatics | 36 | 37 | 28 | 52 |
| Journal of Translational Medicine | 2 | 12 | 14 | 11 |
| Laboratory Investigation | 14 | 8 | 19 | 12 |
| Leukemia | 1 | 0 | 2 | 2 |
| Light: Science & Applications | 1 | 2 | 0 | 2 |
| Med | 1 | 0 | 0 | 0 |
| Medical Image Analysis | 33 | 32 | 40 | 68 |
| medRxiv | 1 | 0 | 1 | 39 |
| MICCAI | 67 | 81 | 88 | 93 |
| MIDL | 16 | 15 | 13 | 23 |
| ML4H | 0 | 3 | 3 | 0 |
| MLMI 2024 | 0 | 1 | 0 | 0 |
| Modern Pathology | 34 | 26 | 29 | 12 |
| Nature | 0 | 3 | 2 | 2 |
| Nature Biomedical Engineering | 1 | 1 | 4 | 12 |
| Nature Cancer | 1 | 4 | 1 | 7 |
| Nature Communications | 20 | 24 | 31 | 17 |
| Nature Computational Science | 0 | 0 | 1 | 3 |
| Nature Machine Intelligence | 0 | 1 | 2 | 0 |
| Nature Medicine | 3 | 9 | 2 | 6 |
| Nature Methods | 1 | 2 | 3 | 4 |
| Nature Reviews Bioengineering | 1 | 0 | 0 | 0 |
| NeurIPS | 7 | 11 | 20 | 0 |
| Neurocomputing | 0 | 1 | 0 | 0 |
| npj Digital Medicine | 1 | 10 | 31 | 27 |
| npj Imaging | 0 | 5 | 1 | 0 |
| npj Precision Oncology | 12 | 22 | 30 | 21 |
| Nucleic Acids Research | 0 | 0 | 3 | 1 |
| Optics & Laser Technology | 0 | 0 | 1 | 0 |
| Pathobiology | 0 | 2 | 3 | 1 |
| Pathology | 2 | 3 | 2 | 0 |
| Pathology - Research and Practice | 3 | 11 | 16 | 9 |
| Pattern Recognition | 1 | 5 | 3 | 13 |
| Patterns | 3 | 0 | 4 | 1 |
| PLOS Computational Biology | 0 | 1 | 3 | 7 |
| Science Advances | 0 | 3 | 3 | 0 |
| Scientific Data | 6 | 11 | 9 | 11 |
| Scientific Reports | 45 | 69 | 131 | 88 |
| TechRxiv | 0 | 0 | 0 | 1 |
| The American Journal of Surgical Pathology | 0 | 3 | 0 | 0 |
| The Journal of Pathology | 9 | 4 | 6 | 9 |
| The Lancet Digital Health | 4 | 5 | 5 | 4 |
| The Lancet Oncology | 1 | 0 | 1 | 3 |
| The Web Conference 2026 | 0 | 0 | 0 | 1 |
| Theranostics | 1 | 1 | 0 | 3 |
| Translational Oncology | 1 | 3 | 1 | 6 |
| Virchows Archiv | 5 | 4 | 10 | 24 |
| WACV | 6 | 5 | 8 | 12 |
