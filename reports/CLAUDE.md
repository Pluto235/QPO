# Reports Guidelines

This directory holds rendered project reports and their Markdown companion files.

## GitHub Pages Publishing

- Public reports are published through `git@github.com:Pluto235/any-reports.git`.
- GitHub Pages URL root: `https://pluto235.github.io/any-reports/`.
- For QPO periodicity reports, publish under the stable slug `qpo-periodicity-v1/` unless the user explicitly asks for a new slug.
- Copy only the report HTML/Markdown and required static assets into the publishing repository. Do not publish raw event files, private data, credentials, tokens, or unnecessary intermediate products.
- Keep report assets source-scoped when multiple sources are shown, for example:
  - `qpo-periodicity-v1/assets/mkn421/`
  - `qpo-periodicity-v1/assets/mkn501/`
- Update the publishing repository homepage `index.html` whenever a report title, date, description, or URL changes.
- After publishing, verify the GitHub Pages URL and at least one image asset. Pages/CDN cache can lag briefly; a cache-busting query such as `?v=<commit>` is acceptable for verification.

## Bilingual Reports

- Reports intended for GitHub Pages should include a Chinese/English toggle when requested, and QPO comparison reports should default to Chinese.
- Implement the language toggle in-page with static HTML/CSS/JavaScript; keep the report usable as a static GitHub Pages page without a build step.
- Persist the chosen language with `localStorage` when practical.
- The report should remain readable if JavaScript is unavailable; default Chinese content should be present in the HTML.

## Local Report Outputs

- Keep the local source report at `reports/periodicity_v1_report.html` and the Markdown companion at `reports/periodicity_v1_report.md`.
- Local report image paths may point to `data/processed/periodicity/...`; published copies must use relative paths inside the publishing repository.
