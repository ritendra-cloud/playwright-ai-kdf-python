# OrangeHRM Login Test Plan

## Overview

This suite covers the OrangeHRM demo site's login form: successful authentication, invalid credentials, and missing required values. It excludes authenticated HR features, password recovery, account locking, and performance/security testing. The generator must inspect the live application to record its current locators and confirm the exact dashboard and error-message text.

## Suite: OrangeHRM Authentication

### Seed

- `test_cases/seed/seed.csv`

## Scenarios

#### 1. Administrator signs in with valid credentials
**Test ID:** TC002  **Tags:** smoke;external
**Steps:**
1. Open the OrangeHRM login page from the seed state.
2. Enter the configured valid test username in the Username field.
3. Enter the configured valid test password in the Password field.
4. Select Login.
**Expected:**
- The user is taken to the authenticated dashboard.
- A dashboard heading or other authenticated-page landmark is visible.
- The URL indicates the dashboard route.

#### 2. User cannot sign in with an invalid password
**Test ID:** TC003  **Tags:** regression;external
**Steps:**
1. Open the OrangeHRM login page from the seed state.
2. Enter a configured valid test username in the Username field.
3. Enter an intentionally invalid password in the Password field.
4. Select Login.
**Expected:**
- The login page remains displayed.
- An invalid-credentials error message is visible.
- The password value is not exposed in the test output.

#### 3. Username is required
**Test ID:** TC004  **Tags:** regression;external
**Steps:**
1. Open the OrangeHRM login page from the seed state.
2. Leave the Username field empty.
3. Enter any non-empty value in the Password field.
4. Select Login.
**Expected:**
- A required-field validation message is shown for Username.
- The user remains on the login page.

#### 4. Password is required
**Test ID:** TC005  **Tags:** regression;external
**Steps:**
1. Open the OrangeHRM login page from the seed state.
2. Enter any non-empty value in the Username field.
3. Leave the Password field empty.
4. Select Login.
**Expected:**
- A required-field validation message is shown for Password.
- The user remains on the login page.

#### 5. Both credentials are required
**Test ID:** TC006  **Tags:** regression;external
**Steps:**
1. Open the OrangeHRM login page from the seed state.
2. Leave the Username and Password fields empty.
3. Select Login.
**Expected:**
- Required-field validation messages are shown for both Username and Password.
- The user remains on the login page.
