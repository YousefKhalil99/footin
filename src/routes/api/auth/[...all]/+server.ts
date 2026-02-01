import { getAuth } from "$lib/auth";
import type { RequestHandler } from "./$types";

export const GET: RequestHandler = async ({ request }) => {
	const auth = getAuth();
	return auth.handler(request);
};

export const POST: RequestHandler = async ({ request }) => {
	const auth = getAuth();
	return auth.handler(request);
};
