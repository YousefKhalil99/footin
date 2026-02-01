import { betterAuth } from "better-auth";
import { Pool } from "@neondatabase/serverless";
import {
	DATABASE_URL,
	BETTER_AUTH_SECRET,
	GOOGLE_CLIENT_ID,
	GOOGLE_CLIENT_SECRET,
	GITHUB_CLIENT_ID,
	GITHUB_CLIENT_SECRET
} from "$env/static/private";
import { env } from "$env/dynamic/private";

let auth: ReturnType<typeof betterAuth> | null = null;

function initAuth() {
	if (auth) return auth;

	if (!DATABASE_URL) {
		throw new Error("DATABASE_URL environment variable is not set");
	}

	if (!BETTER_AUTH_SECRET) {
		throw new Error("BETTER_AUTH_SECRET environment variable is not set");
	}

	const pool = new Pool({ connectionString: DATABASE_URL });

	auth = betterAuth({
		database: {
			provider: "postgresql",
			pool,
			type: "neon-serverless"
		},
		secret: BETTER_AUTH_SECRET,
		baseURL: env.PUBLIC_URL || "http://localhost:5173",
		emailAndPassword: {
			enabled: true
		},
		socialProviders: {
			google: {
				clientId: GOOGLE_CLIENT_ID || "",
				clientSecret: GOOGLE_CLIENT_SECRET || ""
			},
			github: {
				clientId: GITHUB_CLIENT_ID || "",
				clientSecret: GITHUB_CLIENT_SECRET || ""
			}
		}
	});

	return auth;
}

export { initAuth };
export const getAuth = () => initAuth();
