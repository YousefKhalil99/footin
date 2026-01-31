<!--
  LoadingSpinner Component
  
  Futuristic animated loading indicator with glowing rings.
  
  Props:
  - message: Optional loading message to display
  - size: 'sm' | 'md' | 'lg' (default: 'md')
-->
<script lang="ts">
  interface Props {
    message?: string;
    size?: 'sm' | 'md' | 'lg';
  }

  let { message, size = 'md' }: Props = $props();
</script>

<div class="loading-container size-{size}">
  <div class="spinner-wrapper">
    <div class="ring ring-outer"></div>
    <div class="ring ring-middle"></div>
    <div class="ring ring-inner"></div>
    <div class="core"></div>
  </div>
  
  {#if message}
    <p class="loading-message">{message}</p>
  {/if}
</div>

<style>
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 24px;
    padding: 32px;
  }

  .spinner-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Size variants */
  .size-sm .spinner-wrapper {
    width: 48px;
    height: 48px;
  }

  .size-md .spinner-wrapper {
    width: 80px;
    height: 80px;
  }

  .size-lg .spinner-wrapper {
    width: 120px;
    height: 120px;
  }

  .ring {
    position: absolute;
    border-radius: 50%;
    border: 2px solid transparent;
  }

  .ring-outer {
    width: 100%;
    height: 100%;
    border-top-color: var(--accent-cyan);
    border-right-color: var(--accent-cyan);
    animation: spin 1.5s linear infinite;
    filter: drop-shadow(0 0 8px var(--accent-cyan));
  }

  .ring-middle {
    width: 70%;
    height: 70%;
    border-bottom-color: var(--accent-purple);
    border-left-color: var(--accent-purple);
    animation: spin 1s linear infinite reverse;
    filter: drop-shadow(0 0 6px var(--accent-purple));
  }

  .ring-inner {
    width: 40%;
    height: 40%;
    border-top-color: var(--accent-lime);
    animation: spin 0.8s linear infinite;
    filter: drop-shadow(0 0 4px var(--accent-lime));
  }

  .core {
    width: 15%;
    height: 15%;
    background: var(--accent-cyan);
    border-radius: 50%;
    box-shadow: 0 0 20px var(--accent-cyan);
    animation: pulse 1.5s ease-in-out infinite;
  }

  .loading-message {
    margin: 0;
    font-size: 0.9375rem;
    color: var(--text-secondary);
    text-align: center;
    animation: fade-pulse 2s ease-in-out infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.2);
    }
  }

  @keyframes fade-pulse {
    0%, 100% {
      opacity: 0.7;
    }
    50% {
      opacity: 1;
    }
  }
</style>
