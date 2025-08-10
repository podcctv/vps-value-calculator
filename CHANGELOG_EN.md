# Changelog

[简体中文](./CHANGELOG_CN.md) | English

## 2025-08-07
### UI
- Replaced the plain red favicon with an animated color-shifting diamond for a more playful feel.

## 2025-08-06
### Performance
- Introduced a 10-minute cache for server status requests to reduce repeated network calls.
- IP country lookups now run asynchronously during VPS page loads to prevent blocking the page render.
- Streamlined asset loading by bundling and minifying resources for better performance.

### Other
- Fixed deploy script to display the latest commit hash after deployment so operators can verify the running version.
- Added a spinner animation while the VPS list page fetches data, improving user feedback during loads.
- Favicon is now generated and served dynamically, eliminating the need for a static binary icon file.

## 2025-08-05
### Features
- Added a markdown copy button for one-click sharing of generated posts.
- Calculated the final sale price using transfer premiums and refreshed the sale premium UI and inputs.
- Supported TCP ping with an optional port and hid port numbers in VPS IP displays.

### Fixes
- Corrected the Cloudflare beacon script path and aligned the sale calculator logic with the backend.
- Fixed remaining value calculation in the edit form, addressed premium calculator layout issues, and resolved negative sign display.
- Wrapped the React script in a raw block to prevent Jinja parsing and encoded special characters in copied SVG URLs.

### Documentation
- Recorded recent updates in the project documentation.

### Styling
- Beautified the premium calculation section and aligned related input fields for a consistent appearance.

## 2025-08-04
### Performance & UI
- Adjusted VPS card and container widths to accommodate varying content and viewport sizes.
- Enabled wheel-based scaling for VPS cards and refined layout spacing.
- Displayed ISP information for VPS and scoped SVG styles to prevent global effects.
- Various fixes to ensure cards fit the viewport and maintain consistent layout.

## 2025-08-03
### Infrastructure & Performance
- Served Tailwind locally and reduced card container margins for faster loads.
- Optimized VPS card layout with responsive styles and mobile support.
- Added IP flag lookup using ip-api and improved async handling for network status.
- Enhanced VPS forms, dashboards, and SVG display for better usability.

### Earlier
- Initial Dockerized release with CLI utilities, migrations, and templates.
