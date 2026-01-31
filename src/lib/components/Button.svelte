<!--
  Button Component
  
  A styled button with primary/secondary variants and loading state.
  Features neon glow effects on hover and proper disabled styling.
  
  Props:
  - variant: 'primary' | 'secondary' (default: 'primary')
  - disabled: Whether the button is disabled
  - loading: Whether to show loading spinner
  - type: HTML button type
  - fullWidth: Whether to span full width
-->
<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary';
    disabled?: boolean;
    loading?: boolean;
    type?: 'button' | 'submit' | 'reset';
    fullWidth?: boolean;
    onclick?: () => void;
    children: Snippet;
  }

  let { 
    variant = 'primary',
    disabled = false,
    loading = false,
    type = 'button',
    fullWidth = false,
    onclick,
    children
  }: Props = $props();

  const isDisabled = $derived(disabled || loading);
</script>

<button
  {type}
  class="btn btn-{variant}"
  class:full-width={fullWidth}
  class:loading
  disabled={isDisabled}
  {onclick}
>
  {#if loading}
    <span class="spinner"></span>
  {/if}
  <span class="btn-content" class:hidden={loading}>
    {@render children()}
  </span>
</button>

<style>
  .btn {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    font-size: 0.9375rem;
    font-weight: 600;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: 
      background var(--transition-smooth),
      border-color var(--transition-smooth),
      box-shadow var(--transition-smooth),
      transform var(--transition-fast);
    outline: none;
    min-height: 48px;
  }

  .btn:focus-visible {
    box-shadow: 0 0 0 2px var(--bg-dark), 0 0 0 4px var(--accent-cyan);
  }

  .btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Primary variant - filled with glow */
  .btn-primary {
    background: linear-gradient(135deg, var(--accent-cyan), #00c8d4);
    border: 1px solid var(--accent-cyan);
    color: var(--bg-dark);
    box-shadow: var(--glow-subtle);
  }

  .btn-primary:hover:not(:disabled) {
    box-shadow: var(--glow-cyan);
    background: linear-gradient(135deg, #00d4ff, var(--accent-cyan));
  }

  /* Secondary variant - outlined */
  .btn-secondary {
    background: transparent;
    border: 1px solid var(--border-glow);
    color: var(--accent-cyan);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--accent-cyan-dim);
    border-color: var(--accent-cyan);
    box-shadow: var(--glow-subtle);
  }

  .full-width {
    width: 100%;
  }

  .btn-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-content.hidden {
    visibility: hidden;
  }

  /* Loading spinner */
  .spinner {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
