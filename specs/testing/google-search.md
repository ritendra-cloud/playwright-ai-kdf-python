# Google Search Test Plan

> Sample plan in the format the **playwright-test-planner** agent produces. The generator agent turned
> scenario 1 into `test_cases/google_search.csv` (TC001).

## Overview

Covers a basic Google web search: open the home page, search for a text, and verify the results page before the
browser is closed. Out of scope: image/news tabs, ads, personalisation, sign-in.

## Suite: Google Search

### Seed
- `test_cases/seed/seed.csv`

## Scenarios

#### 1. Search for a text and verify the results
**Test ID:** TC001  **Tags:** smoke, external
**Steps:**
1. Open Chrome and go to https://www.google.com
2. If a cookie-consent pop-up appears, accept it
3. Type the search text (default "Playwright Python", overridable with the `SEARCH_TEXT` environment variable) into the search box
4. Press Enter
5. Close the browser at the end of the test

**Expected:**
- The search box is visible on the home page
- The URL contains `/search`
- The page title contains the search text
- At least three result headings are listed
- The results area mentions the search text
- The browser is closed when the test ends

#### 2. Empty search stays on the home page (not yet generated)
**Test ID:** TC002  **Tags:** regression, external
**Steps:**
1. Open https://www.google.com
2. With the search box empty, press Enter

**Expected:**
- The search box is still visible
- The URL does not contain `/search`
