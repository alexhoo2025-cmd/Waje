#!/usr/bin/env node

import crypto from "node:crypto";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_CONFIG = path.join(ROOT, "config", "play_reviews.json");
const execFileAsync = promisify(execFile);

function parseArgs(argv) {
  const args = { date: null, mode: "full", maxReviews: null, minNewReviews: 0, backfillUnseen: false, headed: false, config: DEFAULT_CONFIG };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === "--date") args.date = argv[++i];
    else if (value === "--mode") args.mode = argv[++i];
    else if (value === "--max-reviews") args.maxReviews = Number(argv[++i]);
    else if (value === "--min-new-reviews") args.minNewReviews = Number(argv[++i]);
    else if (value === "--backfill-unseen") args.backfillUnseen = true;
    else if (value === "--headed") args.headed = true;
    else if (value === "--config") args.config = path.resolve(argv[++i]);
    else if (value === "--help") {
      console.log("Usage: node scripts/collect_play_reviews.mjs [--date YYYY-MM-DD] [--mode full|incremental] [--max-reviews N] [--min-new-reviews N] [--backfill-unseen] [--headed]");
      process.exit(0);
    }
  }
  if (!args.date) {
    args.date = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Hong_Kong", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(args.date)) throw new Error(`Invalid --date: ${args.date}`);
  if (!["full", "incremental"].includes(args.mode)) throw new Error(`Invalid --mode: ${args.mode}`);
  if (!Number.isFinite(args.minNewReviews) || args.minNewReviews < 0) throw new Error(`Invalid --min-new-reviews: ${args.minNewReviews}`);
  return args;
}

function sha256(value) {
  return crypto.createHash("sha256").update(String(value), "utf8").digest("hex");
}

function cleanText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function parseDateText(value) {
  const match = cleanText(value).match(/\b\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4}\b/);
  return match ? match[0] : null;
}

function uniqueBy(values) {
  return [...new Set(values.map(cleanText).filter(Boolean))];
}

async function ensureDir(directory) {
  await fs.mkdir(directory, { recursive: true });
}

async function writeJson(filePath, payload) {
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function loadSeenIndex() {
  const python = process.env.PYTHON || "python3";
  const helper = path.join(ROOT, "scripts", "play_review_index.py");
  try {
    const { stdout } = await execFileAsync(python, [helper, "export"], { cwd: ROOT, maxBuffer: 20 * 1024 * 1024 });
    const parsed = JSON.parse(stdout.trim() || "{}");
    return new Map(Object.entries(parsed));
  } catch (error) {
    throw new Error(`review index unavailable: ${error?.message || error}`);
  }
}

async function selectNewest(page) {
  if (await page.getByRole("button", { name: "Newest", exact: true }).count() === 1) return;
  const relevant = page.getByRole("button", { name: "Most relevant", exact: true });
  if (await relevant.count() !== 1) throw new Error("Sort control not found");
  await relevant.click();
  const visibleMenu = page.locator('[role="menu"]:visible');
  await visibleMenu.waitFor({ state: "visible", timeout: 5000 });
  if (await visibleMenu.count() !== 1) throw new Error("Sort menu not visible");
  const newest = visibleMenu.getByRole("menuitemradio", { name: "Newest", exact: true });
  if (await newest.count() !== 1) throw new Error("Newest sort option not found");
  await newest.click();
  await page.waitForTimeout(500);
}

async function selectPhone(page) {
  const phone = page.getByRole("button", { name: "Phone", exact: true });
  if (await phone.count() !== 1) return;
  const pressed = await phone.getAttribute("aria-pressed");
  if (pressed !== "true") {
    await phone.click();
    await page.waitForTimeout(500);
  }
}

async function findDialog(page, appName) {
  const dialogs = page.locator('[role="dialog"]');
  if (await dialogs.count() === 1) return dialogs;
  throw new Error("Ratings and reviews dialog not found");
}

async function extractState(page) {
  return page.evaluate(() => {
    const dialog = document.querySelector('[role="dialog"]');
    if (!dialog) return { error: "dialog_not_found" };
    const candidates = [...dialog.querySelectorAll("*")].filter((element) => {
      const style = getComputedStyle(element);
      return element.clientHeight > 0 && element.scrollHeight > element.clientHeight + 20 && ["auto", "scroll"].includes(style.overflowY);
    });
    const scroller = candidates.find((element) => element.querySelectorAll(".RHo1pe").length > 0)
      || candidates.find((element) => /Ratings and reviews/i.test(element.textContent || ""));
    if (!scroller) return { error: "review_scroller_not_found" };
    const collapse = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
    const isDate = (value) => /\b\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4}\b/.test(collapse(value));
    const uniqueTexts = (values) => [...new Set(values.map(collapse).filter(Boolean))];

    const getCards = () => {
      const known = [...scroller.querySelectorAll(".RHo1pe")];
      if (known.length) return known;
      return [...scroller.querySelectorAll("header")]
        .map((header) => header.parentElement)
        .filter((element) => element && element.textContent && [...element.querySelectorAll("[aria-label], [alt]")].some((node) => /rated .*star/i.test(`${node.getAttribute("aria-label") || ""} ${node.getAttribute("alt") || ""}`)));
    };

    const datePattern = /\b\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4}\b/g;
    const extractRating = (card) => {
      const signals = [...card.querySelectorAll("[aria-label], [alt], [title]")]
        .map((node) => `${node.getAttribute("aria-label") || ""} ${node.getAttribute("alt") || ""} ${node.getAttribute("title") || ""}`)
        .join(" ");
      const match = signals.match(/rated\s+(\d)\s+stars?/i) || signals.match(/(\d)\s+stars?/i);
      return match ? Number(match[1]) : null;
    };
    const extractCard = (card) => {
      const header = card.querySelector("header");
      const author = collapse(card.querySelector(".gSGphe")?.textContent || "");
      const headerText = collapse(header?.textContent || "");
      const dates = [...headerText.matchAll(datePattern)].map((match) => match[0]);
      const reviewText = collapse(card.querySelector(".h3YV2d")?.textContent || "");
      const helpfulMatch = collapse(card.textContent || "").match(/([\d,]+)\s+people? found this review helpful/i);
      const reply = card.querySelector(".ocpBU");
      const replyText = collapse(reply?.textContent || "");
      const replyDates = [...replyText.matchAll(datePattern)].map((match) => match[0]);
      const replyParts = uniqueTexts(reply ? [...reply.children].map((child) => child.textContent || "") : []);
      const developerName = collapse(reply?.querySelector(".I6j64d")?.textContent || replyParts.find((part) => !isDate(part) && part.length < 100) || "");
      const developerReplyDate = collapse(reply?.querySelector(".I9Jtec")?.textContent || replyDates[0] || "") || null;
      const replyBody = collapse(reply?.querySelector(".ras4vb")?.textContent || replyParts.filter((part) => part !== developerName && !isDate(part)).sort((a, b) => b.length - a.length)[0] || "");
      const reviewDate = collapse(card.querySelector(".bp9Aid")?.textContent || dates[0] || "") || null;
      return {
        review_id: header?.getAttribute("data-review-id") || card.getAttribute("data-review-id") || card.querySelector("[data-review-id]")?.getAttribute("data-review-id") || null,
        author_display_name: author || null,
        rating: extractRating(card),
        review_date_display: reviewDate,
        review_text: reviewText || null,
        helpful_count: helpfulMatch ? Number(helpfulMatch[1].replace(/,/g, "")) : null,
        developer_name: developerName || null,
        developer_reply_date_display: developerReplyDate,
        developer_reply_text: replyBody || null,
        identity_raw: [author, reviewDate, reviewText.slice(0, 120)].join("|"),
        content_raw: [author, reviewDate, reviewText, developerName, developerReplyDate, replyBody].join("|")
      };
    };
    const cards = getCards().map(extractCard).filter((card) => card.review_text || card.developer_reply_text);
    return {
      scroll_top: scroller.scrollTop,
      scroll_height: scroller.scrollHeight,
      client_height: scroller.clientHeight,
      loading: /loading[.…]*/i.test(collapse(scroller.textContent || "")),
      card_count: cards.length,
      cards
    };
  });
}

async function scrollReviewList(page, delta) {
  return page.evaluate((scrollDelta) => {
    const dialog = document.querySelector('[role="dialog"]');
    if (!dialog) return false;
    const candidates = [...dialog.querySelectorAll("*")].filter((element) => {
      const style = getComputedStyle(element);
      return element.clientHeight > 0 && element.scrollHeight > element.clientHeight + 20 && ["auto", "scroll"].includes(style.overflowY);
    });
    const scroller = candidates.find((element) => element.querySelectorAll(".RHo1pe").length > 0)
      || candidates.find((element) => /Ratings and reviews/i.test(element.textContent || ""));
    if (!scroller) return false;
    scroller.scrollTop = Math.min(scroller.scrollTop + scrollDelta, scroller.scrollHeight);
    return true;
  }, delta);
}

function normalizeRecord(raw, config, capturedAt, seenIndex = new Map()) {
  const author = cleanText(raw.author_display_name);
  const reviewText = cleanText(raw.review_text);
  const developerReply = cleanText(raw.developer_reply_text);
  const identityKey = raw.identity_key || sha256([config.package_name, raw.identity_raw || ""].join("|"));
  const contentHash = raw.content_hash || sha256(raw.content_raw || [author, raw.review_date_display, reviewText, raw.developer_name, raw.developer_reply_date_display, developerReply].join("|"));
  const reviewKey = raw.review_id || sha256([config.package_name, identityKey].join("|"));
  const previousHash = seenIndex.get(reviewKey);
  const recordState = previousHash === undefined ? "new" : previousHash === contentHash ? "existing" : "updated";
  return {
    schema_version: 1,
    review_key: reviewKey,
    review_id: raw.review_id,
    identity_key: identityKey,
    entity_id: config.entity_id,
    package_name: config.package_name,
    author_hash: sha256(author),
    rating: raw.rating,
    review_date_display: raw.review_date_display,
    review_text: reviewText || null,
    helpful_count: raw.helpful_count,
    developer_name: raw.developer_name || null,
    developer_reply_date_display: raw.developer_reply_date_display,
    developer_reply_text: developerReply || null,
    has_developer_reply: Boolean(developerReply),
    content_hash: contentHash,
    source_url: config.url,
    captured_at: capturedAt,
    source_type: "google_play_public_reviews",
    record_state: recordState,
    collection_run_id: null,
    is_backfill: false
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = JSON.parse(await fs.readFile(args.config, "utf8"));
  if (!config.enabled) {
    console.log("Google Play review collection disabled by config");
    return;
  }
  const targetNewReviews = args.minNewReviews || (args.mode === "incremental" && args.backfillUnseen ? Number(config.min_new_reviews || 200) : 0);
  const maxReviews = args.maxReviews ?? (targetNewReviews > 0 ? 0 : (args.mode === "incremental" ? Number(config.incremental_max_reviews || 200) : Number(config.max_reviews || 0)));
  const capturedAt = new Date().toISOString();
  const runId = capturedAt.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
  const runDir = path.join(ROOT, "data", "raw", "play_reviews", args.date, runId);
  await ensureDir(runDir);
  const seenIndex = await loadSeenIndex();
  const manifest = {
    schema_version: 1,
    run_id: runId,
    date: args.date,
    mode: args.mode,
    target_new_count: targetNewReviews,
    new_count: 0,
    updated_count: 0,
    already_seen_count: 0,
    shortfall: 0,
    backfill_unseen: args.backfillUnseen,
    filter: { locale: config.locale, market: config.market, device: config.device, sort: config.sort },
    status: "running",
    source_id: `${config.entity_id}_play_reviews`,
    package_name: config.package_name,
    url: config.url,
    fetched_at: capturedAt,
    stop_reason: null,
    errors: [],
    card_count_seen: 0,
    unique_review_count: 0,
    raw_path: path.relative(ROOT, runDir)
  };
  let browser;
  let page;
  try {
    browser = await chromium.launch({ headless: args.headed ? false : Boolean(config.headless), args: ["--disable-blink-features=AutomationControlled"] });
    const context = await browser.newContext({ locale: config.locale, userAgent: config.user_agent, viewport: { width: 1280, height: 900 } });
    page = await context.newPage();
    await page.goto(config.url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(1500);
    const seeAll = page.getByRole("button", { name: "See all reviews", exact: true });
    if (await seeAll.count() !== 1) throw new Error("See all reviews button not found");
    await seeAll.click();
    await page.locator('[role="dialog"]').waitFor({ state: "visible", timeout: 15000 });
    await findDialog(page, config.app_name);
    await selectPhone(page);
    await selectNewest(page);
    const records = new Map();
    let stableBottomChecks = 0;
    let previousHeight = 0;
    let previousCount = 0;
    let stopReason = "max_scroll_steps";
    for (let step = 0; step < Number(config.max_scroll_steps || 2500); step += 1) {
      const state = await extractState(page);
      if (state.error) throw new Error(state.error);
      for (const raw of state.cards) {
        const normalized = normalizeRecord(raw, config, capturedAt, seenIndex);
        normalized.collection_run_id = runId;
        normalized.is_backfill = Boolean(args.backfillUnseen && normalized.record_state === "new");
        records.set(normalized.review_key, normalized);
      }
      manifest.card_count_seen = Math.max(manifest.card_count_seen, state.card_count);
      manifest.unique_review_count = records.size;
      const newCount = [...records.values()].filter((row) => row.record_state === "new").length;
      if (targetNewReviews > 0 && newCount >= targetNewReviews) {
        stopReason = "target_new_reviews";
        break;
      }
      if (maxReviews > 0 && records.size >= maxReviews) {
        stopReason = "max_reviews";
        break;
      }
      const atBottom = state.scroll_top + state.client_height >= state.scroll_height - 32;
      const noGrowth = state.scroll_height === previousHeight && state.card_count === previousCount;
      if (atBottom && noGrowth && !state.loading) stableBottomChecks += 1;
      else if (!atBottom || !noGrowth) stableBottomChecks = 0;
      if (stableBottomChecks >= Number(config.bottom_stable_checks || 3)) {
        stopReason = "bottom_stable";
        break;
      }
      previousHeight = state.scroll_height;
      previousCount = state.card_count;
      if (!(await scrollReviewList(page, Number(config.scroll_delta_px || 640)))) throw new Error("Could not scroll review list");
      await page.waitForTimeout(Number(config.settle_ms || 750));
    }
    const finalState = await extractState(page);
    for (const raw of finalState.cards) {
      const normalized = normalizeRecord(raw, config, capturedAt, seenIndex);
      normalized.collection_run_id = runId;
      normalized.is_backfill = Boolean(args.backfillUnseen && normalized.record_state === "new");
      records.set(normalized.review_key, normalized);
    }
    const allOutput = [...records.values()];
    const output = maxReviews > 0 ? allOutput.slice(0, maxReviews) : allOutput;
    const newCount = output.filter((row) => row.record_state === "new").length;
    const updatedCount = output.filter((row) => row.record_state === "updated").length;
    const alreadySeenCount = output.filter((row) => row.record_state !== "new").length;
    manifest.new_count = newCount;
    manifest.updated_count = updatedCount;
    manifest.already_seen_count = alreadySeenCount;
    manifest.shortfall = Math.max(0, targetNewReviews - newCount);
    if (targetNewReviews > 0 && newCount < targetNewReviews) stopReason = "shortfall";
    await fs.writeFile(path.join(runDir, "reviews-raw.jsonl"), `${output.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");
    await fs.writeFile(path.join(runDir, "page.html"), await page.content(), "utf8");
    const visibleReviewSummaries = await page.locator("body").innerText().then((text) => text.match(/\d+(?:\.\d+)?[kK]? reviews/g)?.slice(0, 4) || []).catch(() => []);
    const metadataPath = path.join(runDir, "page-metadata.json");
    await writeJson(metadataPath, {
      title: await page.title(),
      final_url: page.url(),
      visible_review_summaries: visibleReviewSummaries,
      final_state: finalState
    });
    manifest.status = manifest.shortfall > 0 ? "shortfall" : "ok";
    manifest.stop_reason = stopReason;
    manifest.unique_review_count = output.length;
    manifest.raw_file = path.relative(ROOT, path.join(runDir, "reviews-raw.jsonl"));
    manifest.page_file = path.relative(ROOT, path.join(runDir, "page.html"));
    manifest.metadata_file = path.relative(ROOT, metadataPath);
    manifest.visible_review_summaries = visibleReviewSummaries;
    await context.close();
  } catch (error) {
    manifest.status = /captcha|sign.?in|login|blocked/i.test(String(error)) ? "blocked" : "error";
    manifest.stop_reason = "error";
    manifest.errors.push(`${error?.name || "Error"}: ${error?.message || error}`);
    if (page) {
      try {
        await fs.writeFile(path.join(runDir, "debug.html"), await page.content(), "utf8");
      } catch {
        // Keep the manifest authoritative even if a failed page cannot be serialized.
      }
    }
  } finally {
    if (browser) await browser.close();
    manifest.finished_at = new Date().toISOString();
    await writeJson(path.join(runDir, "manifest.json"), manifest);
    const latestManifest = path.join(ROOT, "data", "raw", "play_reviews", args.date, `manifest-${runId}.json`);
    await writeJson(latestManifest, manifest);
    console.log(JSON.stringify({ status: manifest.status, stop_reason: manifest.stop_reason, unique_review_count: manifest.unique_review_count, manifest: path.relative(ROOT, latestManifest) }, null, 2));
    if (manifest.status !== "ok") process.exitCode = 2;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
