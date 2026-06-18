import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { loops, site } from "./loop-data.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const renderer = path.join(root, "scripts", "render-social-images.py");
const python = process.env.PYTHON ?? "python3";
const payload = JSON.stringify({
  site,
  loops: loops.map(({ number, slug, title, categoryLabel, author }) => ({
    number,
    slug,
    title,
    categoryLabel,
    author,
  })),
});

const result = spawnSync(python, [renderer], {
  cwd: root,
  input: payload,
  encoding: "utf8",
});

if (result.stdout) {
  process.stdout.write(result.stdout);
}

if (result.status !== 0) {
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }

  process.exit(result.status ?? 1);
}

const homepagePath = path.join(root, "site", "index.html");
const homepage = await readFile(homepagePath, "utf8");
const escapedBaseUrl = site.baseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const homepageImagePattern = new RegExp(
  `${escapedBaseUrl}assets/social/loop-library-[a-zA-Z0-9.-]+\\.jpg`,
  "g",
);
const homepageImageMatches = homepage.match(homepageImagePattern) ?? [];
const homepageImageUrl = `${site.baseUrl}assets/social/loop-library-${site.socialImageVersion}.jpg`;

if (homepageImageMatches.length !== 4) {
  throw new Error(
    `Expected four homepage social-image references; found ${homepageImageMatches.length}.`,
  );
}

const updatedHomepage = homepage.replaceAll(homepageImagePattern, homepageImageUrl);
if (updatedHomepage !== homepage) {
  await writeFile(homepagePath, updatedHomepage);
  console.log(`Updated homepage social metadata to ${homepageImageUrl}.`);
}
