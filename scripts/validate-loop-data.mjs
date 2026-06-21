function fail(message) {
  throw new Error(message);
}

function requireCondition(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function requireText(value, label) {
  requireCondition(typeof value === "string", `${label} must be a string.`);
  requireCondition(value.trim().length > 0, `${label} must not be empty.`);
}

function requireIsoDate(value, label) {
  requireText(value, label);
  requireCondition(
    /^\d{4}-\d{2}-\d{2}$/.test(value),
    `${label} must use YYYY-MM-DD.`,
  );

  const parsed = new Date(`${value}T00:00:00Z`);
  requireCondition(
    !Number.isNaN(parsed.getTime()) &&
      parsed.toISOString().slice(0, 10) === value,
    `${label} must be a valid calendar date.`,
  );
}

function requireUniqueText(loops, field) {
  const ownerByValue = new Map();

  for (const loop of loops) {
    const normalized = loop[field].trim().toLowerCase();
    const owner = ownerByValue.get(normalized);

    requireCondition(
      owner === undefined,
      `${loop.slug}.${field} duplicates ${owner}.${field}.`,
    );
    ownerByValue.set(normalized, loop.slug);
  }
}

export function validateLoopData(loops) {
  requireCondition(Array.isArray(loops), "Loop catalog must be an array.");
  requireCondition(loops.length > 0, "Loop catalog must not be empty.");

  const requiredTextFields = [
    "slug",
    "title",
    "summary",
    "seoTitle",
    "description",
    "categoryLabel",
    "author",
    "prompt",
    "verifyTitle",
    "verifyDetail",
    "useWhen",
    "why",
    "note",
  ];

  loops.forEach((loop, index) => {
    requireCondition(
      loop !== null && typeof loop === "object" && !Array.isArray(loop),
      `Loop ${index + 1} must be an object.`,
    );

    const label =
      typeof loop.slug === "string" && loop.slug.trim()
        ? loop.slug
        : `loop ${index + 1}`;

    requireText(loop.number, `${label}.number`);
    for (const field of requiredTextFields) {
      requireText(loop[field], `${label}.${field}`);
    }

    requireCondition(
      loop.number === String(index + 1).padStart(3, "0"),
      `${label}.number must match catalog order.`,
    );
    requireCondition(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(loop.slug),
      `${label}.slug must use lowercase kebab-case.`,
    );

    requireIsoDate(loop.published, `${label}.published`);
    requireIsoDate(loop.modified, `${label}.modified`);
    requireCondition(
      loop.modified >= loop.published,
      `${label}.modified must be on or after published.`,
    );

    requireCondition(
      Array.isArray(loop.steps),
      `${label}.steps must be an array.`,
    );
    requireCondition(
      loop.steps.length >= 3,
      `${label}.steps must include at least three steps.`,
    );
    loop.steps.forEach((step, stepIndex) =>
      requireText(step, `${label}.steps[${stepIndex}]`),
    );

    requireCondition(
      Array.isArray(loop.keywords),
      `${label}.keywords must be an array.`,
    );
    requireCondition(
      loop.keywords.length >= 3,
      `${label}.keywords must include at least three terms.`,
    );
    loop.keywords.forEach((keyword, keywordIndex) =>
      requireText(keyword, `${label}.keywords[${keywordIndex}]`),
    );
    requireCondition(
      new Set(loop.keywords.map((keyword) => keyword.trim().toLowerCase()))
        .size === loop.keywords.length,
      `${label}.keywords must be unique.`,
    );

    requireCondition(
      Array.isArray(loop.related),
      `${label}.related must be an array.`,
    );
    requireCondition(
      loop.related.length >= 1,
      `${label}.related must include at least one loop.`,
    );
    loop.related.forEach((slug, relatedIndex) =>
      requireText(slug, `${label}.related[${relatedIndex}]`),
    );
    requireCondition(
      new Set(loop.related).size === loop.related.length,
      `${label}.related must not contain duplicates.`,
    );
    requireCondition(
      !loop.related.includes(loop.slug),
      `${label}.related must not link to itself.`,
    );

    if (Object.hasOwn(loop, "sourceUrl")) {
      requireText(loop.sourceUrl, `${label}.sourceUrl`);

      let sourceUrl;
      try {
        sourceUrl = new URL(loop.sourceUrl);
      } catch {
        fail(`${label}.sourceUrl must be a valid HTTP URL.`);
      }

      requireCondition(
        sourceUrl.protocol === "http:" || sourceUrl.protocol === "https:",
        `${label}.sourceUrl must be a valid HTTP URL.`,
      );
    }

    if (Object.hasOwn(loop, "contributorPlaybook")) {
      const playbook = loop.contributorPlaybook;
      requireCondition(
        playbook !== null &&
          typeof playbook === "object" &&
          !Array.isArray(playbook),
        `${label}.contributorPlaybook must be an object.`,
      );

      for (const field of [
        "whenNotToUse",
        "expectedOutputs",
        "implementationGuidance",
        "reviewerHandoff",
      ]) {
        requireCondition(
          Array.isArray(playbook[field]) && playbook[field].length > 0,
          `${label}.contributorPlaybook.${field} must be a non-empty array.`,
        );
        playbook[field].forEach((item, itemIndex) =>
          requireText(
            item,
            `${label}.contributorPlaybook.${field}[${itemIndex}]`,
          ),
        );
      }
    }
  });

  for (const field of ["slug", "title", "seoTitle", "description", "prompt"]) {
    requireUniqueText(loops, field);
  }

  const slugs = new Set(loops.map((loop) => loop.slug));
  for (const loop of loops) {
    for (const relatedSlug of loop.related) {
      requireCondition(
        slugs.has(relatedSlug),
        `${loop.slug} references unknown related loop: ${relatedSlug}`,
      );
    }
  }
}
