import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { auth } from "$lib/auth";
import { pool } from "$lib/db";
import { env } from "$env/dynamic/private";

type ApifyInput = {
	enrichCompanyData?: boolean;
	keyword: string[];
	location?: string;
	publishedAt?: string;
	saveOnlyUniqueItems?: boolean;
	startUrls?: Array<{ url: string }>;
};

type ApifyItem = Record<string, unknown>;

type SessionResult = { data?: any } | any;

const APIFY_ENDPOINT =
	env.APIFY_LINKEDIN_ENDPOINT ||
	"https://api.apify.com/v2/acts/cheap_scraper~linkedin-job-scraper/run-sync-get-dataset-items";

function normalizeSession(result: SessionResult) {
	if (result && typeof result === "object" && "data" in result) {
		return result.data;
	}
	return result;
}

function buildLinkedInSearchUrl(keyword: string, location?: string, publishedAt?: string) {
	const params = new URLSearchParams();
	if (keyword) params.set("keywords", keyword);
	if (publishedAt) params.set("f_TPR", publishedAt);
	if (location) params.set("location", location);

	const query = params.toString();
	return `https://www.linkedin.com/jobs/search/?${query}`;
}

function extractString(value: unknown): string | undefined {
	if (typeof value === "string" && value.trim()) return value;
	return undefined;
}

function mapApifyItem(item: ApifyItem, index: number) {
	const title =
		extractString(item.title) ||
		extractString(item.jobTitle) ||
		extractString(item.positionName) ||
		extractString(item.name) ||
		"Unknown role";

	const companyName =
		extractString(item.companyName) ||
		extractString(item.company) ||
		(extractString((item as any)?.company?.name) ?? undefined);

	const jobUrl =
		extractString(item.jobUrl) ||
		extractString(item.url) ||
		extractString(item.link);

	const applyUrl =
		extractString(item.applyUrl) ||
		extractString(item.applyLink) ||
		extractString(item.jobApplyUrl);

	const location =
		extractString(item.location) ||
		extractString(item.jobLocation) ||
		extractString(item.locationName);

	const publishedAt =
		extractString(item.publishedAt) ||
		extractString(item.postedAt) ||
		extractString(item.listedAt);

	const description =
		extractString(item.description) ||
		extractString(item.jobDescription) ||
		extractString(item.descriptionText);

	const sourceJobId =
		extractString(item.jobId) ||
		extractString(item.id) ||
		extractString(item.job_id);

	const sourceJobKey =
		sourceJobId ||
		jobUrl ||
		`${title}|${companyName ?? ""}|${location ?? ""}|${publishedAt ?? ""}|${index}`;

	return {
		title,
		companyName,
		jobUrl,
		applyUrl,
		location,
		publishedAt,
		description,
		sourceJobId,
		sourceJobKey
	};
}

async function upsertJobs(userId: string, items: ApifyItem[], searchParams: ApifyInput) {
	if (!items.length) {
		return { count: 0, jobs: [] as any[] };
	}

	const fields = [
		"user_id",
		"source",
		"source_job_key",
		"source_job_id",
		"title",
		"company_name",
		"location",
		"job_url",
		"apply_url",
		"published_at",
		"description",
		"raw",
		"search_params"
	];

	const values: unknown[] = [];
	const placeholders: string[] = [];

	items.forEach((item, index) => {
		const mapped = mapApifyItem(item, index);
		const row = [
			userId,
			"apify-linkedin",
			mapped.sourceJobKey,
			mapped.sourceJobId ?? null,
			mapped.title,
			mapped.companyName ?? null,
			mapped.location ?? null,
			mapped.jobUrl ?? null,
			mapped.applyUrl ?? null,
			mapped.publishedAt ?? null,
			mapped.description ?? null,
			JSON.stringify(item),
			JSON.stringify(searchParams)
		];

		const baseIndex = values.length;
		const rowPlaceholders = row.map((_, idx) => `$${baseIndex + idx + 1}`).join(", ");
		placeholders.push(`(${rowPlaceholders})`);
		values.push(...row);
	});

	const query = `
		INSERT INTO public.jobs (${fields.join(", ")})
		VALUES ${placeholders.join(", ")}
		ON CONFLICT (user_id, source, source_job_key)
		DO UPDATE SET
			source_job_id = EXCLUDED.source_job_id,
			title = EXCLUDED.title,
			company_name = EXCLUDED.company_name,
			location = EXCLUDED.location,
			job_url = EXCLUDED.job_url,
			apply_url = EXCLUDED.apply_url,
			published_at = EXCLUDED.published_at,
			description = EXCLUDED.description,
			raw = EXCLUDED.raw,
			search_params = EXCLUDED.search_params,
			updated_at = NOW()
		RETURNING id, title, company_name, location, job_url, apply_url, published_at
	`;

	const client = await pool.connect();
	try {
		const result = await client.query(query, values);
		return { count: result.rowCount ?? 0, jobs: result.rows };
	} finally {
		client.release();
	}
}

export const POST: RequestHandler = async ({ request }) => {
	const apifyToken = env.APIFY_API_TOKEN;
	if (!apifyToken) {
		return json({ error: "APIFY_API_TOKEN is not configured" }, { status: 500 });
	}

	const sessionResult = await auth.api.getSession({ headers: request.headers });
	const session = normalizeSession(sessionResult);
	const userId = session?.user?.id;

	if (!userId) {
		return json({ error: "Unauthorized" }, { status: 401 });
	}

	let body: ApifyInput;
	try {
		body = (await request.json()) as ApifyInput;
	} catch {
		return json({ error: "Invalid JSON body" }, { status: 400 });
	}

	const keywords = Array.isArray(body?.keyword)
		? body.keyword.filter((value) => typeof value === "string" && value.trim())
		: [];

	if (!keywords.length) {
		return json({ error: "keyword is required" }, { status: 400 });
	}

	const startUrls =
		Array.isArray(body.startUrls) && body.startUrls.length
			? body.startUrls
			: [{ url: buildLinkedInSearchUrl(keywords[0], body.location, body.publishedAt) }];

	const apifyPayload: ApifyInput = {
		enrichCompanyData: body.enrichCompanyData ?? false,
		keyword: keywords,
		location: body.location,
		publishedAt: body.publishedAt,
		saveOnlyUniqueItems: body.saveOnlyUniqueItems ?? false,
		startUrls
	};

	const apifyUrl = new URL(APIFY_ENDPOINT);
	apifyUrl.searchParams.set("token", apifyToken);

	const apifyResponse = await fetch(apifyUrl.toString(), {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(apifyPayload)
	});

	if (!apifyResponse.ok) {
		const details = await apifyResponse.text();
		return json(
			{ error: "Apify request failed", details },
			{ status: 502 }
		);
	}

	const apifyItems = (await apifyResponse.json()) as ApifyItem[];

	if (!Array.isArray(apifyItems)) {
		return json({ error: "Unexpected Apify response" }, { status: 502 });
	}

	const upserted = await upsertJobs(userId, apifyItems, apifyPayload);

	return json({
		inserted: upserted.count,
		jobs: upserted.jobs
	});
};
