# Citation policy

`docs/ENTRY-TEMPLATE.md` is the contract for what an entry must contain.
This file is the contract for what a citation is. The two agree. Where they
look different, the template wins and this file should be corrected.

## What must be sourced

Anything a reader could check and find wrong.

1. Who named the pattern, when, and in which publication.
2. Any statement about what a named library, language, or specification does.
3. Any named production use.
4. Any claim about a language feature, a memory model, or an API contract.
5. Any historical or attribution claim.

## What may stay judgement

Forces, the degree of a cost, a failure symptom drawn from practice, a test
approach, an observability signal, and a security implication may be
engineering judgement. Say so. Do not dress judgement up as a sourced fact,
and do not invent a citation to make judgement look sourced.

## Source order

Prefer the source closest to the claim.

1. A primary specification, standard, or the paper that named the idea.
2. The book edition and the page or chapter, when the pattern comes from a book.
3. The vendor's or project's own documentation for a claim about that product.
4. A secondary write-up only when the primary source is unavailable, and say
   that the citation is secondary.

A catalogue of patterns may be used as a checklist of names. It is not a
source of prose. See `ATTRIBUTION.md`.

## What a green citation check means

`tools/validate-refs.py` requests each URL and records the status. A success
status means the URL answered. It does not mean the page supports the
sentence next to it. That second check is still a human read. There is no
classifier in this repository that pretends otherwise.

An optional evidence grade may close dimension 18, as the template describes.
Old entries are not required to carry it.

## Dates

Web citations include the full URL and the date the page was checked. The
frontmatter `verified` date is the entry-level date, `YYYY-MM-DD`, not a
boolean.
