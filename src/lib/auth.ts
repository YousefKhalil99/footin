import { betterAuth } from "better-auth";
import pg from "pg";
import {
	DATABASE_URL,
	BETTER_AUTH_SECRET,
	GOOGLE_CLIENT_ID,
	GOOGLE_CLIENT_SECRET,
	GITHUB_CLIENT_ID,
	GITHUB_CLIENT_SECRET
} from "$env/static/private";
import { env } from "$env/dynamic/private";

const { Pool } = pg;

if (!DATABASE_URL) {
	throw new Error("DATABASE_URL environment variable is not set");
}

if (!BETTER_AUTH_SECRET) {
	throw new Error("BETTER_AUTH_SECRET environment variable is not set");
}

// Use unpooled connection for Neon to support search_path option
// Replace -pooler hostname with direct connection
const unpooledUrl = DATABASE_URL.replace("-pooler.", ".");
const connectionString = `${unpooledUrl}${unpooledUrl.includes("?") ? "&" : "?"}options=-c%20search_path%3Dneon_auth%2Cpublic`;

// Create pool with proper error handling
const pool = new Pool({
	connectionString,
	max: 20,
	idleTimeoutMillis: 30000,
	connectionTimeoutMillis: 2000
});

// Handle pool errors
pool.on("error", (err) => {
	console.error("Unexpected error on idle client", err);
});

// Initialize neon_auth schema
async function initializeSchema() {
	try {
		const client = await pool.connect();
		// Create schema if it doesn't exist
		await client.query("CREATE SCHEMA IF NOT EXISTS neon_auth");
		client.release();
		console.log("Database connection successful, schema neon_auth ready");
	} catch (err) {
		console.error("Database connection failed:", err);
		throw err;
	}
}

// Initialize schema before exporting auth
await initializeSchema();

export const auth = betterAuth({
	basePath: "/api/auth",
	database: pool,
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

export const getAuth = () => auth;
