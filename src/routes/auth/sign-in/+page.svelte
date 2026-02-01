<!--
  Sign In Page
  
  Form-based authentication for existing users.
-->
<script lang="ts">
    import { signIn } from "$lib/auth-client";
    import { Button } from "$lib/components";
    import { goto } from "$app/navigation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let email = $state("");
    let password = $state("");
    let showPassword = $state(false);
    let isLoading = $state(false);
    let error = $state("");

    async function handleSignIn() {
        error = "";
        isLoading = true;

        try {
            const result = await signIn.email({
                email,
                password,
            });

            if (result.error) {
                error = result.error.message || "Sign in failed";
                return;
            }

            // Redirect to home page on success
            await goto("/");
        } catch (e) {
            error = "An error occurred during sign in. Please try again.";
            console.error("Sign in error:", e);
        } finally {
            isLoading = false;
        }
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === "Enter" && !isLoading) {
            handleSignIn();
        }
    }
</script>

<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h1>Sign In</h1>
            <p>Welcome back to FootIn</p>
        </div>

        {#if error}
            <div class="error-message">
                {error}
            </div>
        {/if}

        <form onsubmit={(e) => { e.preventDefault(); handleSignIn(); }} class="auth-form">
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
                <div class="password-field">
                    <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="••••••••"
                        bind:value={password}
                        disabled={isLoading}
                        onkeydown={handleKeyDown}
                        required
                    />
                    <button
                        type="button"
                        class="password-toggle"
                        onclick={() => showPassword = !showPassword}
                        aria-label="Toggle password visibility"
                    >
                        {#if showPassword}
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                                <line x1="1" y1="1" x2="23" y2="23"/>
                            </svg>
                        {:else}
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                        {/if}
                    </button>
                </div>
            </div>

            <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={isLoading}
                disabled={!email || !password || isLoading}
            >
                Sign In
            </Button>
        </form>

        <div class="auth-footer">
            <p>
                Don't have an account?
                <a href="/auth/sign-up">Sign up</a>
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

    .password-field {
        position: relative;
        display: flex;
        align-items: center;
    }

    .password-field input {
        padding-right: 2.75rem;
        flex: 1;
    }

    .password-toggle {
        position: absolute;
        right: 0.75rem;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem;
        border-radius: var(--radius-sm);
        transition: all var(--transition-fast);
    }

    .password-toggle:hover {
        color: var(--text-primary);
        background: var(--bg-elevated);
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
