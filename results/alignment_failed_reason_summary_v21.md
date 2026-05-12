# Alignment Failed Reason Summary v2.1

- Total ambiguous/failed edges: `113`

| failure_reason | edge_count | source_paper_count |
| --- | --- | --- |
| missing_pdf_or_text | 62 | 38 |
| reference_section_not_found | 9 | 4 |
| target_reference_entry_not_matched | 0 | 0 |
| citation_marker_not_found | 11 | 4 |
| author_year_format_not_supported | 2 | 2 |
| title_fuzzy_match_failed | 27 | 16 |
| grouped_or_range_uncertain | 0 | 0 |
| poor_pdf_text_extraction | 1 | 1 |
| unknown | 1 | 1 |

## Interpretation

- `missing_pdf_or_text` means the source PDF is not locally available, so coverage cannot be improved without adding source files.
- `reference_section_not_found` and `poor_pdf_text_extraction` indicate upstream text availability or PDF parsing limits.
- `author_year_format_not_supported` identifies sources where references and body citations likely use author-year rather than numbered markers.
- `citation_marker_not_found` means the target reference entry was matched, but the body marker could not be aligned confidently.
- `title_fuzzy_match_failed` marks cases where a candidate reference marker exists but title matching remains too weak for formal acceptance.

## v2.2 candidate note

# v2.2 Candidate Coverage Summary

| version | high_confidence | grouped | range | ambiguous | failed | scored_edges | coverage_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v2.1 | 73 | 17 | 1 | 16 | 97 | 91 | 0.446078 |
| v2.2_candidate | 93 | 18 | 1 | 16 | 76 | 112 | 0.549020 |

- Candidate rescues: `21` edges.
- Largest existing bottlenecks remain `missing_pdf_or_text` (`62` edges) and `reference_section_not_found` / `poor_pdf_text_extraction` (`10` edges combined).
- The candidate file is not promoted to the formal semantic layer automatically. It should be used only after manual review of rescued edges, especially those upgraded from fuzzy title matching or author-year support.