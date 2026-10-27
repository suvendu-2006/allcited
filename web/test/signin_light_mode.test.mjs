import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

test('Clerk Sign In Modal Light Mode Parity & Clean Google Button', () => {
  const possiblePaths = [
    path.resolve(process.cwd(), 'src/app/globals.css'),
    path.resolve(process.cwd(), 'web/src/app/globals.css'),
    path.resolve(new URL('.', import.meta.url).pathname, '../src/app/globals.css'),
  ];
  const globalsPath = possiblePaths.find((p) => fs.existsSync(p));
  assert.ok(globalsPath, 'globals.css path found');
  const globals = fs.readFileSync(globalsPath, 'utf-8');

  // 1. Header title must be dark & visible in light mode (both color and -webkit-text-fill-color)
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root) [class*="headerTitle"]'),
    'Light mode header title selector exists'
  );
  assert.ok(
    globals.includes('-webkit-text-fill-color: var(--ink-primary) !important'),
    'Header title enforces ink-primary text fill'
  );

  // 2. Google / social buttons must have neutral borders and zero orange highlights/rectangles in light mode
  assert.ok(
    globals.includes('button[class*="socialButtonsBlockButton__google"]') ||
    globals.includes('[class*="socialButtonsBlockButton__google"]'),
    'Google button explicitly targeted in light mode'
  );
  assert.ok(
    globals.includes('border: 1px solid rgba(26, 25, 24, 0.15) !important;') ||
    globals.includes('border: 1px solid var(--border) !important;'),
    'Neutral 1px border enforced on social buttons in light mode'
  );
  assert.ok(
    globals.includes('box-shadow: none !important;'),
    'Orange box shadow glow removed in light mode'
  );

  // 2b. Button text and inner spans must strip borders so no rectangle wraps the text
  assert.ok(
    globals.includes(':root:not(.dark) [class*="socialButtonsBlockButtonText"]'),
    'Social button text span explicitly stripped of borders'
  );

  // 3. GitHub and monochrome social icons must be visible in light mode (filter: none)
  assert.ok(
    globals.includes(':root:not(.dark) img[alt*="GitHub" i]') ||
    globals.includes(':root:not(.dark) img[src*="github" i]'),
    'GitHub img targeted in light mode'
  );
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) [class*="socialButtonsIconButton"] :is(img, svg)'),
    'Social button icon img/svg targeted in light mode'
  );

  // 5. Email identity preview text & edit icon must be visible in light mode (ink-primary & accent-primary)
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) [class*="identityPreviewText"]') ||
    globals.includes(':root:not(.dark) [class*="identityPreviewText"]'),
    'Identity preview text selector exists in light mode'
  );
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) [class*="identityPreviewEditButton"]') ||
    globals.includes(':root:not(.dark) [class*="identityPreviewEditButton"]'),
    'Identity preview edit pencil button selector exists in light mode'
  );

  // 6. OTP verification code: outer container must NEVER have a border (prevents giant single-box defect)
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) :is(.cl-otpCodeField, .cl-otpCodeFieldInputs, div[class*="otpCodeFieldInputs"], div[class*="otpCodeField"])') ||
    globals.includes(':is(.cl-otpCodeField, .cl-otpCodeFieldInputs'),
    'OTP container reset exists to prevent outer box border'
  );

  // 6b. OTP individual inputs (6 separate rounded boxes) must have crisp visible borders and ink-primary text
  assert.ok(
    globals.includes('input.cl-otpCodeFieldInput') ||
    globals.includes('input[class*="otpCodeFieldInput"]') ||
    globals.includes('[data-testid="otp-input-segment"]'),
    'OTP individual input element selector exists in light mode'
  );
  assert.ok(
    globals.includes('border: 1.5px solid rgba(26, 25, 24, 0.22) !important;') ||
    globals.includes('border: 1.5px solid rgba(26, 25, 24, 0.25) !important;'),
    'OTP code inputs enforce visible 1.5px neutral border in light mode'
  );
  assert.ok(
    globals.includes('width: 44px !important;'),
    'OTP individual segmented box width enforced'
  );
  assert.ok(
    globals.includes('input[data-input-otp]') &&
    globals.includes('-webkit-text-fill-color: transparent !important;'),
    'Master hidden input has transparent text fill to prevent character superposition in boxes'
  );

  // 7. Resend code link & alternative methods must have proper contrast and transparent background
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) [class*="formResendCodeLink"]') ||
    globals.includes(':root:not(.dark) [class*="formResendCodeLink"]'),
    'Resend code link selector exists in light mode'
  );
  assert.ok(
    globals.includes(':root:not(.dark) :is(.cl-signIn-root, .cl-signUp-root, .cl-modalContent) :is([class*="footerAction"], [class*="footerActionLink"], [class*="alternativeMethods"]'),
    'Alternative methods and footerAction are transparent without beige background boxes'
  );
});
