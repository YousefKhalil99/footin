<!--
  Sign Up Page
  
  Form-based registration for new users.
-->
<script lang="ts">
    import { signUp } from "$lib/auth-client";
    import { Button } from "$lib/components";
    import { goto } from "$app/navigation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let name = $state("");
    let email = $state("");
    let password = $state("");
    let confirmPassword = $state("");
    let isLoading = $state(false);
    let error = $state("");

    async function handleSignUp() {
        error = "";

        // Validate passwords match
        if (password !== confirmPassword) {
            error = "Passwords do not match";
            return;
        }

        // Validate password length
        if (password.length < 8) {
            error = "Password must be at least 8 characters";
            return;
        }

        isLoading = true;

        try {
            const result = await signUp.email({
                email,
                password,
                name,
            });

            if (result.error) {
                error = result.error.message || "Sign up failed";
                return;
            }

            // Redirect to home page on success
            await goto("/");
        } catch (e) {
            error = "An error occurred during sign up. Please try again.";
            console.error("Sign up error:", e);
        } finally {
            isLoading = false;
        }
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === "Enter" && !isLoading) {
            handleSignUp();
        }
    }
</script>

<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h1>Create Account</h1>
            <p>Join FootIn and start your job search</p>
        </div>

        {#if error}
            <div class="error-message">
                {error}
            </div>
        {/if}

        <form onsubmit={(e) => { e.preventDefault(); handleSignUp(); }} class="auth-form">
            <div class="form-group">
                <label for="name">Full Name</label>
                <input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    bind:value={name}
                    disabled={isLoading}
                    required
                />
            </div>

            <div class="form-group">
                <label for="email">Email</label>
                <input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    bind:value={email}
                    disabled={isLoading}
                    required
                />
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    bind:value={password}
                    disabled={isLoading}
                    required
                />
                <span class="password-hint">At least 8 characters</span>
            </div>

            <div class="form-group">
                <label for="confirmPassword">Confirm Password</label>
                <input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    bind:value={confirmPassword}
                    disabled={isLoading}
                    onkeydown={handleKeyDown}
                    required
                />
            </div>

            <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={isLoading}
                disabled={!name || !email || !password || !confirmPassword || isLoading}
            >
                Create Account
            </Button>
        </form>

        <div class="auth-footer">
            <p>
                Already have an account?
                <a href="/auth/sign-in">Sign in</a>
            </p>
            <p>
                <a href="/">Back to home</a>
            </p>
        </div>
    </div>
</div>

<style>
    .auth-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 24px;
        background: var(--bg-dark);
    }

    .auth-card {
        width: 100%;
        max-width: 400px;
        padding: 32px;
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .auth-header {
        margin-bottom: 32px;
        text-align: center;
    }

    .auth-header h1 {
        margin: 0 0 8px;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .auth-header p {
        margin: 0;
        font-size: 0.9375rem;
        color: var(--text-muted);
    }

    .error-message {
        margin-bottom: 20px;
        padding: 12px 16px;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: var(--radius-md);
        color: #ef4444;
        font-size: 0.875rem;
    }

    .auth-form {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-bottom: 24px;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .form-group label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .form-group input {
        padding: 12px 16px;
        font-size: 0.9375rem;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        transition: all var(--transition-smooth);
    }

    .form-group input:focus {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 0 2px rgba(0, 243, 255, 0.2);
    }

    .form-group input:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .form-group input::placeholder {
        color: var(--text-muted);
    }

    .password-hint {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .auth-footer {
        text-align: center;
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .auth-footer a {
        color: var(--accent-cyan);
        text-decoration: none;
        transition: color var(--transition-fast);
    }

    .auth-footer a:hover {
        color: var(--text-primary);
    }
</style>
