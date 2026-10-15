# Translator brief - Mermaid Melody Pichi Pichi Pitch: Pichi Pichi Party (GBA, Konami 2003)

You translate part of the Japanese script of this board game into English for a fan patch. Lucia, Hanon and Rina
(mermaid princesses from the anime) move around a town board; each of the 32 episodes is a short story told in
dialogue boxes, with board events, cards, items and mini-game "battles". Audience: young fans; warm, light tone.
Work only on the batch named in your dispatch. Do all translation yourself; no subagents. Never edit glossary.md,
tools/ or any file except your own output file.

## Read first
1. `docs/style-reference.md` - approved pairs and character voices. Match them.
2. `work/tl/<batch>.terms.txt` - binding glossary rows for this batch (full table: `glossary.md`, section
   "Pichi Pichi Party terms" for this game; card/item names: use them exactly as written there).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`, in game order (neighbours give context). ` / ` = line break.
- speaker: a hint from the script (Lucia/Hanon/Rina/Kaito/Hippo/Taro Mitsuki); `?` or `-` = unknown; read the line.
  Note the same line often comes three times in a row, one per heroine (Lucia, Hanon, Rina versions).
- form: `dlg` dialogue box, `msg` message box, `menu` one-line menu label, `banner` title banner (leading
  full-width spaces centre it: you may use plain leading spaces to centre roughly), `choice` answer option,
  `fit` other UI text.
- limit: `212px x2` = max pixel width per line and max number of lines. The English font is proportional: about
  5 px per character (space 3, i/l/!/. 2-3, m/w/M/W 6). Measure with
  `python -X utf8 tools/batches.py fit "line one / line two"` (prints px per line).

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Use ` / ` for the line break inside a box (at most the
limit's line count; one line is fine). Plain ASCII; these extras are allowed when the Japanese has them: ♪ ♥ ★ ☆ … é ×.
No Japanese, no full-width characters, no tabs inside the text.

## Tokens - copy exactly, same count
- `[XXXX]` raw codes (e.g. `[4000]` = a digit the game fills in) and `{iXXX}` icons (`{i20C}`..: stat icons,
  `{i223}` = "Lv"). Keep them, in a sensible place in the English sentence.
- `{h }` in the Japanese is only a narrow space between words: write a normal space.
- Lines that start with a particle (を/が/に..., e.g. "をつかったよ") are endings the game glues after an item or card
  name: write them so they read after a name ("was used!", " broke!"); never start with a lowercase article.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root; fix every reported id until it prints OK.

## Style
- Faithful: keep meaning and order of ideas; adapt idiom, not meaning. No added details, no summaries, no omissions.
- Names/terms exactly as in the glossary: Lucia, Hanon, Rina, Kaito, Hippo, Taro Mitsuki ("Mr. Mitsuki" from
  students; Hanon says "Taro"), Nikora, Pearl Piari, water demon(s), Mermaid Princess. Honorifics dropped (ちゃん,
  くん, さん, 先生 after a name -> nothing, except 海月先生 -> Mr. Mitsuki). Western name order.
- Jokes, puns and teasing keep their punch even if the literal words change.
- Numbers: never glue a suffix to a [4000]-style token ("1th"); rephrase ("Turn [4000]").
- Punctuation: 「」『』 -> "...", ‥‥/… -> ..., ！ -> !, ？ -> ?, 〜 lengthening -> stretched letters (Whaaat).
- Never abbreviate to fit. If a line cannot fit without losing meaning, keep the meaning, shorten wording elsewhere,
  and report `LONG: id`.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
