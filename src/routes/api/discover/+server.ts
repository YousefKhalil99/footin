import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { auth } from "$lib/auth";
import { pool } from "$lib/db";
import { env } from "$env/dynamic/private";
import { ApifyClient } from "apify-client";

type ApifyInput = {
	enrichCompanyData?: boolean;
	keyword: string[];
	location?: string;
	publishedAt?: string;
	saveOnlyUniqueItems?: boolean;
	startUrls?: Array<{ url: string }>;
	maxItems?: number;
};

type ApifyItem = {
	jobId?: string;
	jobTitle?: string;
	location?: string;
	salaryInfo?: string;
	postedTime?: string;
	publishedAt?: string;
	searchString?: string;
	jobUrl?: string;
	companyName?: string;
	companyUrl?: string;
	companyLogo?: string;
	jobDescription?: string;
	applicationsCount?: number;
	contractType?: string;
	experienceLevel?: string;
	workType?: string;
	sector?: string;
	posterFullName?: string;
	posterProfileUrl?: string;
	companyId?: string;
	applyUrl?: string;
	applyType?: string;
	[key: string]: unknown;
};

type SessionResult = { data?: any } | any;

// Actor ID for the LinkedIn job scraper
const LINKEDIN_SCRAPER_ACTOR_ID = "2rJKkhh7vjpX7pvjg";

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

async function upsertJobs(userId: string, items: ApifyItem[], searchParams: ApifyInput) {
	if (!items.length) {
		return { count: 0, jobs: [] as any[] };
	}

	// Deduplicate items by job_url to avoid "ON CONFLICT cannot affect row a second time" error
	const seenUrls = new Set<string>();
	const uniqueItems = items.filter(item => {
		const url = item.jobUrl;
		if (!url || seenUrls.has(url)) {
			return false;
		}
		seenUrls.add(url);
		return true;
	});

	if (!uniqueItems.length) {
		return { count: 0, jobs: [] as any[] };
	}

	const fields = [
		"user_id",
		"source",
		"job_id",
		"job_title",
		"location",
		"salary_info",
		"posted_time",
		"published_at",
		"search_string",
		"job_url",
		"company_name",
		"company_url",
		"company_logo",
		"job_description",
		"applications_count",
		"contract_type",
		"experience_level",
		"work_type",
		"sector",
		"poster_full_name",
		"poster_profile_url",
		"company_id",
		"apply_url",
		"apply_type",
		"raw",
		"search_params"
	];

	const values: unknown[] = [];
	const placeholders: string[] = [];

	uniqueItems.forEach((item) => {
		// Helper to convert empty strings to null
		const toNullableString = (val: unknown): string | null => {
			if (val === null || val === undefined || val === "") return null;
			return String(val);
		};

		// Helper to convert to integer or null
		const toNullableInt = (val: unknown): number | null => {
			if (val === null || val === undefined || val === "") return null;
			const num = Number(val);
			return isNaN(num) ? null : Math.floor(num);
		};

		const row = [
			userId,
			"apify-linkedin",
			toNullableString(item.jobId),
			item.jobTitle || "Unknown role",
			toNullableString(item.location),
			toNullableString(item.salaryInfo),
			toNullableString(item.postedTime),
			toNullableString(item.publishedAt),
			toNullableString(item.searchString),
			toNullableString(item.jobUrl),
			toNullableString(item.companyName),
			toNullableString(item.companyUrl),
			toNullableString(item.companyLogo),
			toNullableString(item.jobDescription),
			toNullableInt(item.applicationsCount),
			toNullableString(item.contractType),
			toNullableString(item.experienceLevel),
			toNullableString(item.workType),
			toNullableString(item.sector),
			toNullableString(item.posterFullName),
			toNullableString(item.posterProfileUrl),
			toNullableString(item.companyId),
			toNullableString(item.applyUrl),
			toNullableString(item.applyType),
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
		ON CONFLICT (user_id, source, job_url)
		DO UPDATE SET
			job_id = EXCLUDED.job_id,
			job_title = EXCLUDED.job_title,
			location = EXCLUDED.location,
			salary_info = EXCLUDED.salary_info,
			posted_time = EXCLUDED.posted_time,
			published_at = EXCLUDED.published_at,
			search_string = EXCLUDED.search_string,
			company_name = EXCLUDED.company_name,
			company_url = EXCLUDED.company_url,
			company_logo = EXCLUDED.company_logo,
			job_description = EXCLUDED.job_description,
			applications_count = EXCLUDED.applications_count,
			contract_type = EXCLUDED.contract_type,
			experience_level = EXCLUDED.experience_level,
			work_type = EXCLUDED.work_type,
			sector = EXCLUDED.sector,
			poster_full_name = EXCLUDED.poster_full_name,
			poster_profile_url = EXCLUDED.poster_profile_url,
			company_id = EXCLUDED.company_id,
			apply_url = EXCLUDED.apply_url,
			apply_type = EXCLUDED.apply_type,
			raw = EXCLUDED.raw,
			search_params = EXCLUDED.search_params,
			updated_at = NOW()
		RETURNING id, job_title as title, company_name, location, job_url, apply_url, published_at, job_description as description
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

	const apifyInput: ApifyInput = {
		startUrls,
		keyword: keywords,
		location: body.location,
		publishedAt: body.publishedAt,
		saveOnlyUniqueItems: body.saveOnlyUniqueItems ?? false,
		enrichCompanyData: body.enrichCompanyData ?? false,
		maxItems: 150 // Apify minimum
	};

	try {
		// Initialize the ApifyClient
		const client = new ApifyClient({ token: apifyToken });

		// Run the Actor and wait for it to finish
		const run = await client.actor(LINKEDIN_SCRAPER_ACTOR_ID).call(apifyInput);

		// Fetch results from the run's dataset
		const { items } = await client.dataset(run.defaultDatasetId).listItems();

		if (!Array.isArray(items)) {
			return json({ error: "Unexpected Apify response" }, { status: 502 });
		}

		const upserted = await upsertJobs(userId, items as ApifyItem[], apifyInput);

		return json({
			inserted: upserted.count,
			jobs: upserted.jobs
		});
	} catch (error) {
		console.error("Apify error:", error);
		return json(
			{ error: "Apify request failed", details: error instanceof Error ? error.message : String(error) },
			{ status: 502 }
		);
	}
};
