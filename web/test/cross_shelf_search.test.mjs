import { test, describe } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webSrc = path.resolve(__dirname, "../src");

describe("Cross-Shelf Search & Multi-Document Synthesis Contract (§8)", () => {
  const libraryGridPath = path.join(webSrc, "components/LibraryGrid.tsx");
  const libraryPagePath = path.join(webSrc, "app/library/page.tsx");
  const homePagePath = path.join(webSrc, "app/page.tsx");
  const chatPath = path.join(webSrc, "components/Chat.tsx");

  test("1. LibraryGrid provides cross-shelf search composer form and submission handler", () => {
    const content = fs.readFileSync(libraryGridPath, "utf-8");

    // Interface defines onAskAcrossShelf callback
    assert.match(
      content,
      /onAskAcrossShelf\?:\s*\(query:\s*string\)\s*=>\s*void/,
      "LibraryGridProps must define onAskAcrossShelf"
    );

    // Search composer input with exact placeholder
    assert.match(
      content,
      /placeholder="Ask across everything on your shelf…"|placeholder='Ask across everything on your shelf…'/,
      "Input must have exact shelf search placeholder"
    );

    // Form onSubmit calls onAskAcrossShelf when trimmed query is non-empty
    assert.match(
      content,
      /if\s*\(\s*shelfQuery\.trim\(\)\s*\)\s*onAskAcrossShelf\?\.(\(shelfQuery\))/,
      "Form submission must invoke onAskAcrossShelf with shelfQuery"
    );

    // Submit button is disabled when empty
    assert.match(
      content,
      /disabled=\{\s*!shelfQuery\.trim\(\)\s*\}/,
      "Submit button must be disabled when shelfQuery is empty"
    );

    // Search button copy
    assert.match(
      content,
      /Search shelf/,
      "Button label must indicate 'Search shelf'"
    );
  });

  test("2. Library page wires onAskAcrossShelf to router.push with /?shelf_query=...", () => {
    const content = fs.readFileSync(libraryPagePath, "utf-8");

    assert.match(
      content,
      /onAskAcrossShelf=\{\s*\(query\)\s*=>\s*\{[\s\S]*?router\.push\(`\/\?shelf_query=\$\{encodeURIComponent\(query\)\}`\);?[\s\S]*?\}\}/,
      "Library page must route onAskAcrossShelf to /?shelf_query=${encodeURIComponent(query)}"
    );
  });

  test("3. Home page (page.tsx) parses shelf_query URL param and activates isShelfMode", () => {
    const content = fs.readFileSync(homePagePath, "utf-8");

    // State definitions
    assert.match(content, /const\s*\[isShelfMode,\s*setIsShelfMode\]\s*=\s*useState<boolean>\(false\);/);
    assert.match(content, /const\s*\[initialShelfQuery,\s*setInitialShelfQuery\]\s*=\s*useState<string\s*\|\s*null>\(null\);/);

    // syncFromUrl parses shelf_query
    assert.match(content, /const\s+urlShelfQuery\s*=\s*params\.get\("shelf_query"\);/);
    assert.match(content, /if\s*\(\s*urlShelfQuery\s*\)\s*\{[\s\S]*?setIsShelfMode\(true\);[\s\S]*?setDocumentName\("Your shelf \(all documents\)"\);[\s\S]*?setInWorkspace\(true\);[\s\S]*?setInitialShelfQuery\(decodeURIComponent\(urlShelfQuery\)\);[\s\S]*?\}/);

    // Clearing shelf_query when navigating back or home
    assert.match(content, /url\.searchParams\.delete\("shelf_query"\);/);
    assert.match(content, /setIsShelfMode\(false\);/);
    assert.match(content, /setInitialShelfQuery\(null\);/);

    // Save to shelf button suppressed when isShelfMode is active
    assert.match(content, /sessionId\s*&&\s*!isShelfMode/);

    // Chat invocation passes shelf props
    assert.match(content, /isShelfMode=\{isShelfMode\}/);
    assert.match(content, /initialShelfQuery=\{initialShelfQuery\}/);
    assert.match(content, /onClearInitialShelfQuery=\{\(\)\s*=>\s*setInitialShelfQuery\(null\)\}/);
  });

  test("4. Chat component implements auto-dispatch for initialShelfQuery and shelf-mode POST /v1/library/query", () => {
    const content = fs.readFileSync(chatPath, "utf-8");

    // ChatProps accepts shelf mode props
    assert.match(content, /isShelfMode\?:\s*boolean;/);
    assert.match(content, /initialShelfQuery\?:\s*string\s*\|\s*null;/);
    assert.match(content, /onClearInitialShelfQuery\?:\s*\(\)\s*=>\s*void;/);

    // useEffect auto-dispatches initialShelfQuery
    assert.match(
      content,
      /if\s*\(\s*initialShelfQuery\s*&&\s*initialShelfQuery\.trim\(\)\s*\)\s*\{[\s\S]*?handleSend\(initialShelfQuery\.trim\(\)\);[\s\S]*?onClearInitialShelfQuery\?\.\(\);[\s\S]*?\}/
    );

    // handleSend handles isShelfMode
    assert.match(content, /if\s*\(\s*isShelfMode\s*\)\s*\{/);
    assert.match(content, /searching across your shelf…/);

    // Calls /v1/library/query endpoint
    assert.match(
      content,
      /\/v1\/library\/query/,
      "Chat must dispatch POST to /v1/library/query in shelf mode"
    );

    // Transmits query and top_k parameters
    assert.match(content, /query:\s*queryText/);
    assert.match(content, /top_k:\s*5/);

    // Handles response data: answer and citations
    assert.match(content, /const\s+answer\s*=\s*data\.answer/);
    assert.match(content, /const\s+citations:\s*Citation\[\]\s*=\s*data\.citations/);

    // Header badge displays 'multi-document synthesis'
    assert.match(content, /isShelfMode\s*\?\s*"multi-document synthesis"\s*:\s*"grounded Q&A session"/);

    // Composer placeholder in shelf mode
    assert.match(content, /isShelfMode\s*\?\s*"Ask across everything on your shelf…"(\s*:\s*undefined)?/);

    // Composer disabled check permits shelf mode without sessionId
    assert.match(content, /disabled=\{\(!sessionId\s*&&\s*!isShelfMode\)/);
  });
});
