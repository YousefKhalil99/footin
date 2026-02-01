import pg from "pg";
import { env } from "$env/dynamic/private";

const { Pool } = pg;

const DATABASE_URL = env.DATABASE_URL;

if (!DATABASE_URL) {
	throw new Error("DATABASE_URL environment variable is not set");
}

// Use unpooled connection for Neon to support search_path option
const unpooledUrl = DATABASE_URL.replace("-pooler.", ".");
const connectionString = `${unpooledUrl}${unpooledUrl.includes("?") ? "&" : "?"}options=-c%20search_path%3Dpublic`;

export const pool = new Pool({
	connectionString,
	max: 20,
	idleTimeoutMillis: 30000,
	connectionTimeoutMillis: 2000
});

pool.on("error", (err) => {
	console.error("Unexpected error on idle client", err);
});
