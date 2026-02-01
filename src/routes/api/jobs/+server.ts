import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { auth } from "$lib/auth";
import { pool } from "$lib/db";

type SessionResult = { data?: any } | any;

function normalizeSession(result: SessionResult) {
	if (result && typeof result === "object" && "data" in result) {
		return result.data;
	}
	return result;
}

// GET /api/jobs - Fetch existing jobs from database
export const GET: RequestHandler = async ({ request, url }) => {
	const sessionResult = await auth.api.getSession({ headers: request.headers });
	const session = normalizeSession(sessionResult);
	const userId = session?.user?.id;

	if (!userId) {
		return json({ error: "Unauthorized" }, { status: 401 });
	}

	// Optional filters from query params
	const keywords = url.searchParams.getAll("keyword");
	const location = url.searchParams.get("location");

	const client = await pool.connect();
	try {
		let query = `
			SELECT
				id,
				job_title as title,
				company_name,
				location,
				job_url,
				apply_url,
				published_at,
				job_description as description,
				salary_info,
				contract_type,
				experience_level,
				work_type,
				company_logo,
				created_at
			FROM public.jobs
			WHERE user_id = $1
		`;
		const params: unknown[] = [userId];
		let paramIndex = 2;

		// Filter by keywords if provided (search in job_title)
		if (keywords.length > 0) {
			const keywordConditions = keywords.map((_, i) => `job_title ILIKE $${paramIndex + i}`);
			query += ` AND (${keywordConditions.join(" OR ")})`;
			keywords.forEach(k => params.push(`%${k}%`));
			paramIndex += keywords.length;
		}

		// Filter by location if provided
		if (location) {
			query += ` AND location ILIKE $${paramIndex}`;
			params.push(`%${location}%`);
		}

		query += ` ORDER BY created_at DESC LIMIT 200`;

		const result = await client.query(query, params);

		return json({
			jobs: result.rows,
			count: result.rowCount
		});
	} finally {
		client.release();
	}
};
