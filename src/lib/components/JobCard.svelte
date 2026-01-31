<!--
  JobCard Component
  
  Displays a job listing with company, role, summarized JD, and selection checkbox.
  Features border-glow on hover and entry animations.
  
  Props:
  - job: Job object with id, company, role, summarizedJD, etc.
  - selected: Whether this job is currently selected
  - onToggle: Callback when selection is toggled
-->
<script lang="ts">
  import type { Job } from '$lib/stores/mockData';

  interface Props {
    job: Job;
    selected: boolean;
    onToggle: () => void;
  }

  let { job, selected, onToggle }: Props = $props();
</script>

<article 
  class="job-card"
  class:selected
  role="listitem"
>
  <div class="card-header">
    <div class="company-info">
      <div class="company-logo">
        {job.company.charAt(0)}
      </div>
      <div class="company-details">
        <h3 class="company-name">{job.company}</h3>
        <span class="location">{job.location}</span>
      </div>
    </div>
    
    <label class="checkbox-wrapper">
      <input 
        type="checkbox" 
        checked={selected}
        onchange={onToggle}
        class="sr-only"
      />
      <span class="custom-checkbox" class:checked={selected}>
        {#if selected}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
        {/if}
      </span>
    </label>
  </div>
  
  <div class="card-body">
    <h4 class="role-title">{job.role}</h4>
    
    <div class="meta-row">
      <span class="badge">{job.type}</span>
      {#if job.salary}
        <span class="salary">{job.salary}</span>
      {/if}
      <span class="posted">{job.postedDate}</span>
    </div>
    
    <p class="jd-summary">{job.summarizedJD}</p>
  </div>
</article>

<style>
  .job-card {
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
      box-shadow var(--transition-smooth),
      transform var(--transition-fast);
    cursor: pointer;
  }

  .job-card:hover {
    border-color: var(--border-glow);
    box-shadow: var(--glow-subtle);
    transform: translateY(-2px);
  }

  .job-card.selected {
    border-color: var(--accent-cyan);
    box-shadow: var(--glow-cyan);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }

  .company-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .company-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, var(--accent-cyan-dim), var(--accent-purple-dim));
    border-radius: var(--radius-md);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent-cyan);
  }

  .company-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .company-name {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .location {
    font-size: 0.8125rem;
    color: var(--text-muted);
  }

  /* Custom checkbox */
  .checkbox-wrapper {
    cursor: pointer;
  }

  .custom-checkbox {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 2px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    background: var(--bg-surface);
    transition: 
      background var(--transition-fast),
      border-color var(--transition-fast),
      box-shadow var(--transition-fast);
  }

  .custom-checkbox:hover {
    border-color: var(--accent-cyan);
  }

  .custom-checkbox.checked {
    background: var(--accent-cyan);
    border-color: var(--accent-cyan);
    box-shadow: 0 0 10px var(--accent-cyan-dim);
  }

  .custom-checkbox svg {
    width: 14px;
    height: 14px;
    color: var(--bg-dark);
  }

  .card-body {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .role-title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--accent-cyan);
  }

  .meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }

  .badge {
    padding: 4px 10px;
    background: var(--bg-elevated);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .salary {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--accent-lime);
  }

  .posted {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-left: auto;
  }

  .jd-summary {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
