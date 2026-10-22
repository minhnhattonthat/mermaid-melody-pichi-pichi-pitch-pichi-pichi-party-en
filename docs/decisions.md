# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-16 | Honorifics and name order | keep (-san), drop; JP or Western order | Drop honorifics (register carries them); given name first. Pre-approved in the batch brief. |
| D2 | 2026-10-16 | Romanization source for names | official art, earlier patch, Hepburn | Official English anime/manga names (Lucia, Hanon, Rina), else modified Hepburn. |
| D3 | 2026-10-16 | Credits | stay Japanese, translate | English. |
| D4 | 2026-10-16 | Abbreviations | engine work first (default), abbreviate | Full words; abbreviate only as a flagged last resort ("7 left", "Here!", "Guard Rhythm"). |
| D5 | 2026-10-16 | Graphics text left in Japanese | none (default), list | None: all graphics text in scope. Developer test scripts the game never shows stay Japanese. |
| D6 | 2026-10-16 | Specs and plans | need approval, pre-approved | Pre-approved through release; never push or publish without the user. |
| D7 | 2026-10-16 | Song lyrics shared with the prequel | retranslate, reuse | Reuse the prequel's English (its script/text.json) word for word, so both games match. |
| D8 | 2026-10-23 | Repo layout | keep batch layout, fan-translation-template | fan-translation-template, as in the prequel: AGENTS.md, rom.sha1, plugin skill path, issue form. |
| D9 | 2026-10-23 | Fonts for graphics text | Windows fonts (Comic Sans, Arial Rounded/Narrow/Bold, Tahoma, Bauhaus, MS Gothic), open fonts | Open fonts, so every font is redistributable: Nunito (rounded, as the prequel's D8), Roboto Condensed (narrow), DejaVu Sans Condensed (small hinted), Liberation Sans (Arial metrics); name grid in the project's own VWF glyphs. |
