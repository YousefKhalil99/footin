import pg from "pg";
import "dotenv/config";

const { Pool } = pg;

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
	console.error("DATABASE_URL environment variable is not set");
	process.exit(1);
}

const pool = new Pool({
	connectionString: DATABASE_URL,
	max: 5,
	idleTimeoutMillis: 30000,
	connectionTimeoutMillis: 2000
});

async function initDatabase() {
	console.log("Initializing database schema for Better Auth in neon_auth schema...\n");

	const client = await pool.connect();

	try {
		// Ensure pgcrypto extension for UUID generation
		await client.query('CREATE EXTENSION IF NOT EXISTS "pgcrypto"');
		console.log("✓ Ensured pgcrypto extension");

		// Create neon_auth schema if it doesn't exist
		await client.query("CREATE SCHEMA IF NOT EXISTS neon_auth");
		console.log("✓ Created 'neon_auth' schema");

		// Drop existing tables in neon_auth schema to recreate with correct schema
		await client.query('DROP TABLE IF EXISTS neon_auth."verification" CASCADE');
		await client.query('DROP TABLE IF EXISTS neon_auth."account" CASCADE');
		await client.query('DROP TABLE IF EXISTS neon_auth."session" CASCADE');
		await client.query('DROP TABLE IF EXISTS neon_auth."user" CASCADE');
		console.log("✓ Dropped existing tables in neon_auth schema");

		// Create user table in neon_auth schema (Better Auth uses camelCase)
		await client.query(`
			CREATE TABLE neon_auth."user" (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				email TEXT NOT NULL UNIQUE,
				"emailVerified" BOOLEAN NOT NULL DEFAULT FALSE,
				image TEXT,
				"createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
				"updatedAt" TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`);
		console.log("✓ Created 'neon_auth.user' table");

		// Create session table in neon_auth schema
		await client.query(`
			CREATE TABLE neon_auth."session" (
				id TEXT PRIMARY KEY,
				"userId" TEXT NOT NULL REFERENCES neon_auth."user"(id) ON DELETE CASCADE,
				token TEXT NOT NULL UNIQUE,
				"expiresAt" TIMESTAMP NOT NULL,
				"ipAddress" TEXT,
				"userAgent" TEXT,
				"createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
				"updatedAt" TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`);
		console.log("✓ Created 'neon_auth.session' table");

		// Create account table in neon_auth schema (for OAuth providers and email/password)
		await client.query(`
			CREATE TABLE neon_auth."account" (
				id TEXT PRIMARY KEY,
				"userId" TEXT NOT NULL REFERENCES neon_auth."user"(id) ON DELETE CASCADE,
				"accountId" TEXT NOT NULL,
				"providerId" TEXT NOT NULL,
				"accessToken" TEXT,
				"refreshToken" TEXT,
				"accessTokenExpiresAt" TIMESTAMP,
				"refreshTokenExpiresAt" TIMESTAMP,
				scope TEXT,
				"idToken" TEXT,
				password TEXT,
				"createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
				"updatedAt" TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`);
		console.log("✓ Created 'neon_auth.account' table");

		// Create verification table in neon_auth schema
		await client.query(`
			CREATE TABLE neon_auth."verification" (
				id TEXT PRIMARY KEY,
				identifier TEXT NOT NULL,
				value TEXT NOT NULL,
				"expiresAt" TIMESTAMP NOT NULL,
				"createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
				"updatedAt" TIMESTAMP NOT NULL DEFAULT NOW()
			)
		`);
		console.log("✓ Created 'neon_auth.verification' table");

		// Create application tables in public schema
		await client.query(`
			CREATE TABLE IF NOT EXISTS public.jobs (
				id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
				user_id TEXT NOT NULL REFERENCES neon_auth."user"(id) ON DELETE CASCADE,
				source TEXT NOT NULL,
				source_job_key TEXT NOT NULL,
				source_job_id TEXT,
				title TEXT NOT NULL,
				company_name TEXT,
				location TEXT,
				job_url TEXT,
				apply_url TEXT,
				published_at TIMESTAMPTZ,
				description TEXT,
				raw JSONB NOT NULL,
				search_params JSONB NOT NULL,
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				CONSTRAINT jobs_user_source_key_unique UNIQUE (user_id, source, source_job_key)
			)
		`);
		console.log("✓ Created 'public.jobs' table");

		await client.query(
			"CREATE INDEX IF NOT EXISTS jobs_user_id_idx ON public.jobs (user_id)"
		);
		await client.query(
			"CREATE INDEX IF NOT EXISTS jobs_published_at_idx ON public.jobs (published_at)"
		);
		console.log("✓ Created jobs indexes");

		console.log("\n✅ Database schema initialized successfully in neon_auth schema!");
	} catch (error) {
		console.error("Failed to initialize database:", error);
		process.exit(1);
	} finally {
		client.release();
		await pool.end();
	}
}

initDatabase();
