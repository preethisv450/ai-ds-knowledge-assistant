# UI Integration Test Checklist — D10

Run after every merge to main. Tick each row; log failures in ui_bug_log.md.

## Navigation
- [ ] All five bottom-nav items switch pages and the active item is highlighted
- [ ] The nav stays fixed and does not cover page content when scrolling
- [ ] Each Home card's Open button lands on the matching page
- [ ] Curriculum choice survives switching pages and coming back

## Curriculum selection
- [ ] Year, Semester, Subject, Module populate from the real JSON
- [ ] Changing Year resets Semester, Subject and Module
- [ ] Every year and semester in the data has selectable subjects

## Syllabus chatbot
- [ ] Syllabus mode shows the selected module in the scope caption
- [ ] With no module picked, the input is disabled and says so
- [ ] An answer appears with a spinner while waiting
- [ ] Sources show document name and page, and the snippet expands
- [ ] History persists across questions; Clear chat empties it
- [ ] Example questions are clickable and send the question

## Regulation chatbot
- [ ] Regulation mode answers without a module selected
- [ ] Answers cite the regulations document, not a syllabus PDF
- [ ] An unanswerable question gives the friendly empty-state message
- [ ] Backend failure shows the friendly error, not a raw traceback

## Module tabs
- [ ] Summary generates and renders headings and bullets
- [ ] Rewrite checkbox skips the cached summary
- [ ] Q&A answers questions scoped to the selected module
- [ ] Questions tab honours type and count; model answers stay hidden
- [ ] Quiz scores correctly and explains each answer
- [ ] Switching module clears or re-scopes each tab's output

## Layout
- [ ] Desktop 1366px, tablet 800px and phone 390px all usable
- [ ] Chat input sits above the bottom nav, never under it
- [ ] No horizontal scrollbar at any width