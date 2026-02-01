# Authentication Setup with Neon.tech

## Current Status ✅

Your project is already configured with:
- **Database**: Neon.tech PostgreSQL serverless
- **Auth Framework**: Better Auth v1.4.18
- **Connection Pool**: @neondatabase/serverless

## Connection Details

Your `.env` file already has:
```
DATABASE_URL=postgresql://neondb_owner:npg_Z7TQuPE9UkAy@ep-fragrant-glitter-ak9yulp8-pooler.c-3.us-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
```

## Setup Steps

### 1. Initialize Database Schema

The project includes a database initialization script to set up all required Better Auth tables:

```bash
npm run db:init
```

This creates:
- `user` - User accounts
- `session` - Session management
- `account` - OAuth provider links
- `verification` - Email verification tokens

### 2. Configure OAuth Providers (Optional)

Update your `.env` file with OAuth credentials:

**Google OAuth:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URIs: `http://localhost:5173/api/auth/callback/google` and your production URL
6. Copy Client ID and Secret to `.env`:

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

**GitHub OAuth:**
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:5173/api/auth/callback/github` and production URL
4. Copy Client ID and Secret to `.env`:

```env
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### 3. Generate BETTER_AUTH_SECRET

Replace the placeholder secret with a secure random value:

```bash
# Generate a secure secret
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Update `.env`:
```env
BETTER_AUTH_SECRET=your-generated-secret-here
```

### 4. Test Authentication

Start your development server:
```bash
npm run dev
```

Then test auth endpoints:
```bash
# Test basic auth
curl http://localhost:5173/api/auth/sign-up \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'
```

## Authentication Flow

1. **Frontend** (`src/lib/auth-client.ts`): Client-side auth utilities
   - `signUp()` - Create new account
   - `signIn()` - Login
   - `signOut()` - Logout
   - `useSession()` - Get current session

2. **Backend** (`src/lib/auth.ts`): Server-side auth handler
   - Manages database operations
   - Handles OAuth flows
   - Session management

3. **API Routes** (`src/routes/api/auth/[...all]/+server.ts`): Auth endpoints
   - Handles GET/POST requests
   - Routes to Better Auth handler

## Verification Checklist

- [ ] Database URL is configured in `.env`
- [ ] Run `npm run db:init` to create tables
- [ ] OAuth credentials configured (optional for local testing)
- [ ] `BETTER_AUTH_SECRET` is a secure value
- [ ] Dev server runs without errors: `npm run dev`
- [ ] Auth API endpoints accessible at `http://localhost:5173/api/auth/*`

## Troubleshooting

**"database connection failed"**
- Verify `DATABASE_URL` is correct
- Check Neon.tech dashboard that database is running
- Ensure network access is allowed

**"tables don't exist"**
- Run `npm run db:init` to create schema

**"oauth authentication fails"**
- Verify OAuth credentials in `.env`
- Check redirect URLs match exactly
- Ensure `BETTER_AUTH_SECRET` is set

## API Endpoints

All auth endpoints are available at `/api/auth/*`:

- `POST /api/auth/sign-up` - Register new user
- `POST /api/auth/sign-in` - Login
- `POST /api/auth/sign-out` - Logout
- `GET /api/auth/session` - Get current session
- `POST /api/auth/callback/google` - Google OAuth callback
- `POST /api/auth/callback/github` - GitHub OAuth callback
