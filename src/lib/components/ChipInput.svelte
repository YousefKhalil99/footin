<!--
  ChipInput Component
  
  A tag/chip input that allows users to add items by pressing Enter.
  Chips can be removed by clicking the X button.
  Enforces a maximum number of chips and provides visual feedback.
  
  Props:
  - label: Input label text
  - placeholder: Input placeholder text
  - maxChips: Maximum number of chips allowed (default: 5)
  - chips: Bindable array of chip values
-->
<script lang="ts">
  import { fly, scale } from 'svelte/transition';
  import { flip } from 'svelte/animate';

  interface Props {
    label: string;
    placeholder?: string;
    maxChips?: number;
    chips: string[];
  }

  let { 
    label, 
    placeholder = 'Type and press Enter...', 
    maxChips = 5,
    chips = $bindable([])
  }: Props = $props();

  let inputValue = $state('');
  let inputElement: HTMLInputElement;
  let isFocused = $state(false);

  // Computed: whether we've reached the max limit
  const isMaxReached = $derived(chips.length >= maxChips);

  /**
   * Adds a chip if value is valid and limit not reached
   */
  function addChip(): void {
    const value = inputValue.trim();
    
    // Validate: non-empty, not duplicate, under limit
    if (value && !chips.includes(value) && chips.length < maxChips) {
      chips = [...chips, value];
      inputValue = '';
    } else if (chips.includes(value)) {
      // Clear input if duplicate
      inputValue = '';
    }
  }

  /**
   * Removes a chip by index
   */
  function removeChip(index: number): void {
    chips = chips.filter((_, i) => i !== index);
  }

  /**
   * Handle keydown events on the input
   */
  function handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      event.preventDefault();
      addChip();
    } else if (event.key === 'Backspace' && inputValue === '' && chips.length > 0) {
      // Remove last chip if backspace pressed on empty input
      removeChip(chips.length - 1);
    }
  }
</script>

<div class="chip-input-container">
  <label class="chip-label">
    {label}
    <span class="chip-count" class:at-limit={isMaxReached}>
      {chips.length}/{maxChips}
    </span>
  </label>
  
  <div 
    class="chip-input-wrapper"
    class:focused={isFocused}
    class:has-chips={chips.length > 0}
  >
    <!-- Existing chips -->
    <div class="chips-container">
      {#each chips as chip, index (chip)}
        <span 
          class="chip"
          animate:flip={{ duration: 200 }}
          in:scale={{ duration: 200, start: 0.8 }}
          out:fly={{ x: -20, duration: 150 }}
        >
          <span class="chip-text">{chip}</span>
          <button 
            type="button"
            class="chip-remove"
            onclick={() => removeChip(index)}
            aria-label="Remove {chip}"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </span>
      {/each}
    </div>
    
    <!-- Input field -->
    {#if !isMaxReached}
      <input
        bind:this={inputElement}
        bind:value={inputValue}
        type="text"
        {placeholder}
        class="chip-input"
        onkeydown={handleKeydown}
        onfocus={() => isFocused = true}
        onblur={() => isFocused = false}
      />
    {:else}
      <span class="max-reached-text">Maximum reached</span>
    {/if}
  </div>
</div>

<style>
  .chip-input-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .chip-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .chip-count {
    font-size: 0.75rem;
    font-weight: 400;
    color: var(--text-muted);
    transition: color var(--transition-fast);
  }

  .chip-count.at-limit {
    color: var(--accent-cyan);
  }

  .chip-input-wrapper {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    min-height: 56px;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    transition: 
      border-color var(--transition-smooth),
      box-shadow var(--transition-smooth);
  }

  .chip-input-wrapper:hover {
    border-color: rgba(255, 255, 255, 0.15);
  }

  .chip-input-wrapper.focused {
    border-color: var(--accent-cyan);
    box-shadow: var(--glow-subtle);
  }

  .chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: linear-gradient(135deg, var(--accent-cyan-dim), var(--accent-purple-dim));
    border: 1px solid var(--accent-cyan-dim);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    color: var(--text-primary);
    transition: 
      background var(--transition-fast),
      border-color var(--transition-fast);
  }

  .chip:hover {
    border-color: var(--accent-cyan);
  }

  .chip-text {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chip-remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    padding: 0;
    background: transparent;
    border-radius: 50%;
    color: var(--text-secondary);
    transition: 
      color var(--transition-fast),
      background var(--transition-fast);
    cursor: pointer;
  }

  .chip-remove:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }

  .chip-input {
    flex: 1;
    min-width: 120px;
    padding: 4px 0;
    font-size: 0.9375rem;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
  }

  .chip-input::placeholder {
    color: var(--text-muted);
  }

  .max-reached-text {
    font-size: 0.875rem;
    color: var(--text-muted);
    font-style: italic;
  }
</style>
