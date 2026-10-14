# AU Accounting Services — website

Static, no-build website for AU Accounting Services (AU Services (Pty) Ltd), built from the brand mockup in the "AU Accounting Services - Website" project. Plain HTML/CSS — no framework, no build step, so it's easy to edit and safe to host on GitHub Pages.

## Structure

```
au-accounting-website/
├── index.html          Home
├── services.html        Services
├── about.html            About
├── reviews.html          Reviews
├── contact.html          Contact
├── assets/
│   ├── css/style.css     Shared styles (colours, buttons, nav, footer, cards, etc.)
│   └── img/              Logo, Gold Journey photos, and other local images
└── README.md
```

Each page is a full, independent HTML file (nav + footer duplicated in each, since there's no server-side templating). Shared look-and-feel lives in `assets/css/style.css` — change a colour or button style there and it updates on every page.

## Brand reference

- Gold `#D4AF37` — accents, highlights, borders
- Navy `#0A1F44` — headers, nav/footer background, body copy
- Charcoal `#4B4B4B` — secondary text
- Light grey `#E5E5E5` — section backgrounds, dividers

Icons are [Tabler Icons](https://tabler.io/icons), loaded from a CDN in each page's `<head>`.

## Known placeholders to revisit

- **Contact form and "Leave a review" form**: wired up to submit via [Web3Forms](https://web3forms.com) (`assets/js/form-submit.js`) — but this needs a one-time, free access key before it's actually live. Go to web3forms.com, enter your email, and paste the key it emails you into the `WEB3FORMS_ACCESS_KEY` placeholder near the top of `assets/js/form-submit.js`. Until that's done, both forms automatically fall back to `mailto:` (opens the visitor's email client instead of submitting silently) — so nothing is broken either way, it just won't submit in-place until the key is added.
- **Open Graph / Twitter Card tags and the structured-data (`AccountingService`) block**, both in every page's `<head>`: `url` and `image` use `https://www.auservices.co.za/` as a best-guess domain (matching your practice email), since the site wasn't deployed yet when these were added. Once you know the real live URL — your own domain, or the default GitHub Pages URL if you don't attach a custom domain — update the `og:url`/`og:image`/`twitter:image` meta tags and the JSON-LD `url`/`image` fields in all five pages to match, or social-media link previews and Google's rich-result data will point at the wrong address.
- **Body corporates & HOAs service photo** (`services.html`/homepage card 01): still a stock photo — none of the real photos you've sent so far showed a complex/HOA-type scene. Swap in a real one whenever you have one; same filename convention as the other five service photos.
- **About page bio**: intentionally brief and factual. Add more career detail or further qualifications whenever you're ready — it's marked with an HTML comment in `about.html`.
- **Adding more reviews**: `reviews.html` (plus the homepage teaser) now shows your 3 real client reviews — there's no limit on how many more can go in. To add one, copy an existing `.card.testimonial` block, set its quote/name/role, pick the matching `karat-plate-XX.png` tier image (24/22/18/14/9) and the matching `data-tier` attribute together, and add the same card to the homepage teaser if you want it featured there too. The Client Assay Report panel above the grid updates its counts and bar chart automatically — nothing else to touch.

## Previewing locally

No build tools needed. Either:

- Open `index.html` directly in a browser, or
- Run a tiny local server from this folder so relative links behave exactly like they will on GitHub Pages:

  ```bash
  python3 -m http.server 8000
  ```

  then visit `http://localhost:8000`.

## Deploying to GitHub Pages

1. Create a new repository on GitHub (e.g. `au-accounting-website`).
2. From this folder:

   ```bash
   git init
   git add .
   git commit -m "Initial website"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

3. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main`, folder `/ (root)`. Save.
4. GitHub gives you a live URL, typically `https://<your-username>.github.io/<repo-name>/`, within a minute or two.
5. Optional: add a custom domain (e.g. `auaccounting.co.za`) under the same Pages settings once you've set up the domain's DNS.

## Making edits

Everything is plain HTML/CSS — no build step, so any change is just editing the file and refreshing the browser:

- **Text/copy**: edit directly in the relevant `.html` file.
- **Colours/spacing/fonts site-wide**: edit `assets/css/style.css`.
- **Nav or footer**: these are duplicated across all five pages — if you add/rename a page, update the `.nav-links` block and the footer `Navigation` block in *all five* files.
