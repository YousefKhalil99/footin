<!--
  ProgressStepper Component
  
  Horizontal workflow indicator showing all phases of the automation suite.
  Active phase has glow effect, completed phases show checkmark.
  
  Props:
  - currentPhase: Current active phase number (1-6)
-->
<script lang="ts">
  import { PHASE_LABELS, type PhaseNumber } from '$lib/stores/workflow';

  interface Props {
    currentPhase: PhaseNumber;
  }

  let { currentPhase }: Props = $props();

  const phases: PhaseNumber[] = [1, 2, 3, 4, 5, 6];

  // Icons for each phase
  const phaseIcons: Record<PhaseNumber, string> = {
    1: '🎯', // Targeting
    2: '⚡', // Processing
    3: '🔍', // Discovery
    4: '✅', // Selection
    5: '🤖', // Extraction
    6: '📧'  // Outreach
  };
</script>

<nav class="stepper" aria-label="Workflow progress">
  <ol class="stepper-list">
    {#each phases as phase}
      {@const isActive = phase === currentPhase}
      {@const isCompleted = phase < currentPhase}
      {@const isPending = phase > currentPhase}
      
      <li 
        class="step"
        class:active={isActive}
        class:completed={isCompleted}
        class:pending={isPending}
        aria-current={isActive ? 'step' : undefined}
      >
        <div class="step-indicator">
          {#if isCompleted}
            <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          {:else}
            <span class="step-icon">{phaseIcons[phase]}</span>
          {/if}
        </div>
        <span class="step-label">{PHASE_LABELS[phase]}</span>
        
        {#if phase < 6}
          <div class="step-connector" class:filled={isCompleted}></div>
        {/if}
      </li>
    {/each}
  </ol>
</nav>

<style>
  .stepper {
    width: 100%;
    padding: 16px 0;
    overflow-x: auto;
  }

  .stepper-list {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    list-style: none;
    margin: 0;
    padding: 0;
    min-width: 600px;
  }

  .step {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    gap: 8px;
  }

  .step-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--bg-elevated);
    border: 2px solid var(--border-subtle);
    transition: 
      background var(--transition-smooth),
      border-color var(--transition-smooth),
      box-shadow var(--transition-smooth);
    z-index: 1;
  }

  .step.active .step-indicator {
    background: var(--accent-cyan-dim);
    border-color: var(--accent-cyan);
    box-shadow: var(--glow-cyan);
    animation: pulse-glow 2s ease-in-out infinite;
  }

  .step.completed .step-indicator {
    background: var(--accent-cyan);
    border-color: var(--accent-cyan);
  }

  .step.pending .step-indicator {
    opacity: 0.5;
  }

  .step-icon {
    font-size: 1.25rem;
  }

  .check-icon {
    width: 20px;
    height: 20px;
    color: var(--bg-dark);
  }

  .step-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-align: center;
    transition: color var(--transition-fast);
  }

  .step.active .step-label {
    color: var(--accent-cyan);
    font-weight: 600;
  }

  .step.completed .step-label {
    color: var(--text-primary);
  }

  .step.pending .step-label {
    color: var(--text-muted);
  }

  /* Connector line between steps */
  .step-connector {
    position: absolute;
    top: 24px;
    left: calc(50% + 24px);
    width: calc(100% - 48px);
    height: 2px;
    background: var(--border-subtle);
    transition: background var(--transition-smooth);
  }

  .step-connector.filled {
    background: var(--accent-cyan);
  }

  /* Responsive: hide labels on small screens */
  @media (max-width: 768px) {
    .stepper-list {
      min-width: 400px;
    }

    .step-indicator {
      width: 40px;
      height: 40px;
    }

    .step-icon {
      font-size: 1rem;
    }

    .step-label {
      font-size: 0.625rem;
    }

    .step-connector {
      top: 20px;
      left: calc(50% + 20px);
      width: calc(100% - 40px);
    }
  }

  @keyframes pulse-glow {
    0%, 100% {
      box-shadow: var(--glow-cyan);
    }
    50% {
      box-shadow: 0 0 30px rgba(0, 243, 255, 0.6), 0 0 60px rgba(0, 243, 255, 0.3);
    }
  }
</style>
