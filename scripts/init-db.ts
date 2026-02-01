import { neon } from "@neondatabase/serverless";
import "dotenv/config";

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
	console.error("DATABASE_URL environment variable is not set");
	process.exit(1);
}

const sql = neon(DATABASE_URL);

async function initDatabase() {
	console.log("Initializing database schema for Better Auth...\n");

	try {
		// Create user table
		await sql`
			CREATE TABLE IF NOT EXISTS "user" (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				email TEXT NOT NULL UNIQUE,
				email_verified BOOLEAN NOT NULL DEFAULT FALSE,
				image TEXT,
				created_at TIMESTAMP NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`;
		console.log("✓ Created 'user' table");

		// Create session table
		await sql`
			CREATE TABLE IF NOT EXISTS "session" (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
				token TEXT NOT NULL UNIQUE,
				expires_at TIMESTAMP NOT NULL,
				ip_address TEXT,
				user_agent TEXT,
				created_at TIMESTAMP NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`;
		console.log("✓ Created 'session' table");

		// Create account table (for OAuth providers)
		await sql`
			CREATE TABLE IF NOT EXISTS "account" (
				id TEXT PRIMARY KEY,
				user_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
				account_id TEXT NOT NULL,
				provider_id TEXT NOT NULL,
				access_token TEXT,
				refresh_token TEXT,
				access_token_expires_at TIMESTAMP,
				refresh_token_expires_at TIMESTAMP,
				scope TEXT,
				id_token TEXT,
				password TEXT,
				created_at TIMESTAMP NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`;
		console.log("✓ Created 'account' table");

		// Create verification table
		await sql`
			CREATE TABLE IF NOT EXISTS "verification" (
				id TEXT PRIMARY KEY,
				identifier TEXT NOT NULL,
				value TEXT NOT NULL,
				expires_at TIMESTAMP NOT NULL,
				created_at TIMESTAMP NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`;
		console.log("✓ Created 'verification' table");

		console.log("\n✅ Database schema initialized successfully!");
	} catch (error) {
		console.error("Failed to initialize database:", error);
		process.exit(1);
	}
}

initDatabase();
