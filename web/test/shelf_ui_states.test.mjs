import { test, describe } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webSrc = path.resolve(__dirname, "../src");

describe("Frontend Shelf UI States & Components Verification (§4)", () => {
  const libraryPagePath = path.join(webSrc, "app/library/page.tsx");
  const libraryGridPath = path.join(webSrc, "components/LibraryGrid.tsx");
  const libraryDocCardPath = path.join(webSrc, "components/LibraryDocCard.tsx");
  const navbarPath = path.join(webSrc, "components/Navbar.tsx");

  test("Library page mounts Navbar, Footer, and LibraryGrid with proper routes", () => {
    const content = fs.readFileSync(libraryPagePath, "utf-8");
    assert.match(content, /<Navbar \/>/);
    assert.match(content, /<Footer \/>/);
    assert.match(content, /<LibraryGrid/);
    assert.match(content, /Your shelf/);
    assert.match(content, /Keep your documents here\. Ask questions across all of them, anytime\. Private to your account\./);
    assert.match(content, /router\.push\(`\/\?session_id=\${doc\.id}&filename=\${encodeURIComponent\(doc\.filename\)}`\)/);
    assert.match(content, /router\.push\(`\/\?shelf_query=\${encodeURIComponent\(query\)}`\)/);
  });

  test("State 1: Degraded state renders amber alert banner with exact copy", () => {
    const content = fs.readFileSync(libraryGridPath, "utf-8");
    assert.match(content, /isDegraded/);
    assert.match(content, /AlertTriangle/);
    assert.match(content, /border-amber-300/);
    assert.match(content, /bg-amber-50\/50/);
    assert.match(content, /The shelf is briefly unreachable\. Chat still works fine\. We(?:'|&apos;)re on it\./);
  });

  test("State 2: Loading state renders skeleton placeholder cards", () => {
    const content = fs.readFileSync(libraryGridPath, "utf-8");
    assert.match(content, /(!isLoaded || loading)/);
    assert.match(content, /<Skeleton className="h-32" \/>/);
  });

  test("State 3: Signed out state renders sign-in and guest continue actions", () => {
    const content = fs.readFileSync(libraryGridPath, "utf-8");
    assert.match(content, /!isSignedIn/);
    assert.match(content, /SignInButton/);
    assert.match(content, /Sign in to start your shelf/);
    assert.match(content, /Continue as guest/);
    assert.match(content, /href="\/\?workspace=true"/);
    assert.match(content, /Continue as guest to ask right away — or sign in to keep documents between visits\./);
  });

  test("State 4: Signed in with documents renders search composer and LibraryDocCard components", () => {
    const content = fs.readFileSync(libraryGridPath, "utf-8");
    assert.match(content, /Ask across everything on your shelf…/);
    assert.match(content, /Search shelf/);
    assert.match(content, /<LibraryDocCard/);
    assert.match(content, /No documents saved to your shelf yet/);
    assert.match(content, /docs\.map\(\(doc\) => \(/);
  });

  test("LibraryDocCard provides document chunk count, remove action, and 'Ask about this'", () => {
    const content = fs.readFileSync(libraryDocCardPath, "utf-8");
    assert.match(content, /doc\.chunk_count/);
    assert.match(content, /Trash2/);
    assert.match(content, /Ask about this/);
    assert.match(content, /onAsk\(doc\)/);
    assert.match(content, /onRemove\(doc\)/);
  });

  test("Navbar links to Shelf route (/library) across desktop and mobile menus", () => {
    const content = fs.readFileSync(navbarPath, "utf-8");
    const desktopLink = /<Link\s+href="\/library"[^>]*>[\s\S]*?Shelf[\s\S]*?<\/Link>/g;
    const matches = content.match(desktopLink);
    assert.ok(matches && matches.length >= 2, "Expected at least 2 '/library' navigation links (desktop + mobile)");
  });
});
