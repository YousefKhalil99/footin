import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { auth } from "$lib/auth";
import { pool } from "$lib/db";
import { env } from "$env/dynamic/private";

/**
 * Job data returned from the Modal agent's Browserbase scraper.
 * These are the fields we receive after the agent visits company career pages.
 */
type JobItem = {
	id?: string;
	company?: string;
	role?: string;
	location?: string;
	type?: string;
	summarizedJD?: string;
	postedDate?: string;
	url?: string;
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

/**
 * Insert or update jobs in the database from Modal agent results.
 * 
 * The Modal agent's Browserbase scraper returns simplified job data,
 * so we map it to our database schema here.
 */
async function upsertJobs(userId: string, items: JobItem[], searchKeywords: string[]) {
	if (!items.length) {
		return { count: 0, jobs: [] as any[] };
	}

	// Deduplicate items by URL to avoid conflicts
	const seenUrls = new Set<string>();
	const uniqueItems = items.filter(item => {
		const url = item.url;
		if (!url || seenUrls.has(url)) {
			return false;
		}
		seenUrls.add(url);
		return true;
	});

	if (!uniqueItems.length) {
		return { count: 0, jobs: [] as any[] };
	}

	// Simplified fields for Browserbase job data
	const fields = [
		"user_id",
		"source",
		"job_id",
		"job_title",
		"location",
		"job_url",
		"company_name",
		"job_description",
		"contract_type",
		"posted_time",
		"apply_url",
		"raw",
		"search_params"
	];

	const values: unknown[] = [];
	const placeholders: string[] = [];

	// Helper to convert empty strings to null
	const toNullableString = (val: unknown): string | null => {
		if (val === null || val === undefined || val === "") return null;
		return String(val);
	};

	uniqueItems.forEach((item) => {
		const row = [
			userId,
			"browserbase-careers",  // Updated source
			toNullableString(item.id),
			item.role || "Unknown role",
			toNullableString(item.location),
			toNullableString(item.url),
			toNullableString(item.company),
			toNullableString(item.summarizedJD),
			toNullableString(item.type),
			toNullableString(item.postedDate),
			toNullableString(item.url),  // apply_url same as url
			JSON.stringify(item),
			JSON.stringify({ keywords: searchKeywords })
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
			company_name = EXCLUDED.company_name,
			job_description = EXCLUDED.job_description,
			contract_type = EXCLUDED.contract_type,
			posted_time = EXCLUDED.posted_time,
			apply_url = EXCLUDED.apply_url,
			raw = EXCLUDED.raw,
			search_params = EXCLUDED.search_params,
			updated_at = NOW()
		RETURNING id, job_title as title, company_name, location, job_url, apply_url, job_description as description
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
	const modalUrl = env.MODAL_AGENT_URL;

	if (!modalUrl) {
		return json({ error: "MODAL_AGENT_URL is not configured" }, { status: 500 });
	}

	// DEMO MODE: Bypass auth
	const userId = "00000000-0000-0000-0000-000000000000"; // Static Demo User ID


	let body: any;
	try {
		body = await request.json();
	} catch {
		return json({ error: "Invalid JSON body" }, { status: 400 });
	}

	const companies = Array.isArray(body?.companies) ? body.companies : [];
	const roles = Array.isArray(body?.roles) ? body.roles : [];

	// Legacy support: if only keyword provided, treat as search terms
	if (!companies.length && !roles.length && body?.keyword) {
		// Just pass keywords as roles for now if no structure
		const keywords = Array.isArray(body.keyword) ? body.keyword : [];
		roles.push(...keywords);
	}

	if (!companies.length) {
		return json({ error: "At least one target company is required" }, { status: 400 });
	}

	try {
		// Call Modal agent for discovery
		const response = await fetch(`${modalUrl}/discover`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				companies: companies,
				roles: roles.length ? roles : ["Open Role"], // Default if no role specified
				max_results: 20
			})
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error(`Modal Agent error: ${response.status}`, errorText);
			throw new Error(`Agent failed: ${response.statusText}`);
		}

		const items = await response.json();

		// Use roles as keywords for storage
		const searchKeywords = roles.length ? roles : ["Open Role"];

		const upserted = await upsertJobs(userId, items as JobItem[], searchKeywords);

		return json({
			inserted: upserted.count,
			jobs: upserted.jobs
		});
	} catch (error) {
		console.error("Agent error:", error);
		return json(
			{ error: "Agent request failed", details: error instanceof Error ? error.message : String(error) },
			{ status: 502 }
		);
	}
};
