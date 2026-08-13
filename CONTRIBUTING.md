# Contributing

Corrections and improvements are welcome. This is a course, so accuracy matters more than volume.

## The fastest way to fix something

Every page on [the site](https://dnakhoa.github.io/everything-data-structures/) has a pencil icon in the top right that opens the source file directly in the GitHub editor. Fix the typo, describe the change, submit. That's it.

## What's most useful

**Technical corrections.** A wrong complexity bound, an incorrect invariant, code that doesn't do what the prose says it does. These are the highest-value contributions — please include a source (a paper, a reference implementation, or a reproducible test) so the fix can be verified rather than taken on faith.

**Clearer explanations.** If a passage took you three reads to understand, that's a bug in the writing. Say what confused you, even if you don't have a rewrite in mind — an issue that just says "18.3 loses me at the helping pattern" is genuinely useful.

**Worked examples.** Concrete traces through an algorithm, with real numbers, tend to teach better than prose.

**Real-world usage.** If you know a production system that uses a structure in a way the book doesn't mention, that's worth adding — especially with a link to source or a design doc.

## What to check before submitting

**Complexity claims** should state whether they're average, worst-case, or amortized, and say so explicitly. Several bugs in the first draft came from tables that silently mixed the three.

**Code** should run. Python examples are syntax-checked in CI; if you add one, make sure it parses. Illustrative pseudocode is fine, but label it as such — the `cas()` example in Chapter 18 is a cautionary tale about pseudocode that looks executable.

**Voice.** The book states tradeoffs plainly and says when a structure loses in practice despite winning on paper. Keep that. Avoid hedging, and avoid marketing language about structures.

## Building locally

```bash
cargo install mdbook && mdbook serve --open
```

Live-reloads at `http://localhost:3000`. Chapters live in `src/`, diagrams in `src/images/`, and the sidebar is generated from `src/SUMMARY.md` — a new chapter needs an entry there or it won't appear.

Diagrams are inline SVG using `currentColor` for strokes and text so they work in both light and dark themes. They're pulled in with `{{#include ../images/name.svg}}` inside a `<figure>`. Two constraints: no blank lines inside an SVG file (a blank line ends the raw-HTML block in Markdown), and don't hard-code black or white.

## Scope

The book covers data structures and the systems built from them. Things that are out of scope: general algorithm tutorials with no structural angle, language-specific API documentation, and interview-question collections.

## License

Contributions are accepted under the same terms as the book — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for prose, MIT for code.
