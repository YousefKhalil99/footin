<!--
  ContactCard Component
  
  Displays a contact with name, title, source, LinkedIn activity insight,
  drafted email, and action buttons (select, send).
  
  Props:
  - contact: Contact object with id, name, title, draftedEmail, etc.
  - selected: Whether this contact is selected for sending
  - onToggleSelect: Callback when selection is toggled
  - onSend: Callback when send button is clicked
-->
<script lang="ts">
  import { slide } from 'svelte/transition';
  import type { Contact } from '$lib/stores/mockData';
  import Button from './Button.svelte';

  interface Props {
    contact: Contact;
    selected: boolean;
    onToggleSelect: () => void;
    onSend: () => void;
  }

  let { contact, selected, onToggleSelect, onSend }: Props = $props();

  let isExpanded = $state(false);
  let emailContent = $state(contact.draftedEmail);

  const sourceColors: Record<string, string> = {
    'Hiring Manager': 'var(--accent-cyan)',
    'Team Lead': 'var(--accent-purple)',
    'Peer': 'var(--accent-lime)'
  };
</script>

<article class="contact-card" class:selected>
  <div class="card-header">
    <div class="contact-info">
      <div 
        class="avatar"
        style="--source-color: {sourceColors[contact.source]}"
      >
        {contact.name.split(' ').map(n => n[0]).join('')}
      </div>
      <div class="contact-details">
        <h4 class="contact-name">{contact.name}</h4>
        <span class="contact-title">{contact.title}</span>
        <span 
          class="contact-source"
          style="color: {sourceColors[contact.source]}"
        >
          {contact.source}
        </span>
      </div>
    </div>
    
    <label class="toggle-wrapper">
      <input 
        type="checkbox" 
        checked={selected}
        onchange={onToggleSelect}
        class="sr-only"
      />
      <span class="toggle-track" class:active={selected}>
        <span class="toggle-thumb"></span>
      </span>
    </label>
  </div>
  
  <div class="insight-row">
    <span class="insight-icon">💡</span>
    <p class="insight-text">{contact.linkedInActivity}</p>
  </div>
  
  <button 
    class="email-toggle"
    onclick={() => isExpanded = !isExpanded}
  >
    <span class="email-subject">{contact.emailSubject}</span>
    <svg 
      class="chevron" 
      class:rotated={isExpanded}
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      stroke-width="2"
    >
      <path d="M6 9l6 6 6-6"/>
    </svg>
  </button>
  
  {#if isExpanded}
    <div class="email-section" transition:slide={{ duration: 200 }}>
      <textarea 
        bind:value={emailContent}
        class="email-textarea"
        rows="10"
      ></textarea>
    </div>
  {/if}
  
  <div class="card-actions">
    <Button variant="secondary" onclick={() => isExpanded = !isExpanded}>
      {isExpanded ? 'Collapse' : 'Preview Email'}
    </Button>
    <Button variant="primary" onclick={onSend} disabled={!selected}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
      </svg>
      Send
    </Button>
  </div>
</article>

<style>
  .contact-card {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 20px;
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    transition: 
      border-color var(--transition-smooth),
      box-shadow var(--transition-smooth);
  }

  .contact-card.selected {
    border-color: var(--accent-cyan-dim);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }

  .contact-info {
    display: flex;
    gap: 14px;
  }

  .avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: var(--bg-elevated);
    border: 2px solid var(--source-color);
    border-radius: 50%;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--source-color);
    box-shadow: 0 0 12px color-mix(in srgb, var(--source-color) 30%, transparent);
  }

  .contact-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .contact-name {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .contact-title {
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }

  .contact-source {
    font-size: 0.75rem;
    font-weight: 500;
  }

  /* Toggle switch */
  .toggle-wrapper {
    cursor: pointer;
  }

  .toggle-track {
    display: flex;
    align-items: center;
    width: 44px;
    height: 24px;
    padding: 2px;
    background: var(--bg-elevated);
    border-radius: 12px;
    transition: background var(--transition-smooth);
  }

  .toggle-track.active {
    background: var(--accent-cyan);
  }

  .toggle-thumb {
    width: 20px;
    height: 20px;
    background: var(--text-primary);
    border-radius: 50%;
    transition: transform var(--transition-smooth);
  }

  .toggle-track.active .toggle-thumb {
    transform: translateX(20px);
  }

  .insight-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px;
    background: var(--bg-surface);
    border-radius: var(--radius-md);
  }

  .insight-icon {
    font-size: 1rem;
    flex-shrink: 0;
  }

  .insight-text {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .email-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: border-color var(--transition-fast);
  }

  .email-toggle:hover {
    border-color: var(--accent-cyan-dim);
  }

  .email-subject {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .chevron {
    width: 18px;
    height: 18px;
    color: var(--text-muted);
    transition: transform var(--transition-smooth);
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .email-section {
    overflow: hidden;
  }

  .email-textarea {
    width: 100%;
    padding: 14px;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    font-family: inherit;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--text-primary);
    resize: vertical;
    transition: border-color var(--transition-fast);
  }

  .email-textarea:focus {
    outline: none;
    border-color: var(--accent-cyan);
  }

  .card-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    padding-top: 8px;
    border-top: 1px solid var(--border-subtle);
  }
</style>
