/**
 * Workflow Store
 * 
 * Manages the multi-phase workflow state for the Job Outbound Automation Suite.
 * Tracks current phase, user inputs, discovered jobs, selections, and contacts.
 */

import { writable, derived, get } from 'svelte/store';
import type { Job, Contact } from './mockData';

// ============================================
// WORKFLOW PHASES
// ============================================
export const PHASES = {
  TARGETING: 1,
  PROCESSING: 2,
  DISCOVERY: 3,
  SELECTION: 4,
  EXTRACTION: 5,
  OUTREACH: 6
} as const;

export type PhaseNumber = typeof PHASES[keyof typeof PHASES];

export const PHASE_LABELS: Record<PhaseNumber, string> = {
  1: 'Targeting',
  2: 'Processing',
  3: 'Discovery',
  4: 'Selection',
  5: 'Extraction',
  6: 'Outreach'
};

// ============================================
// STORES
// ============================================

/** Current workflow phase (1-6) */
export const currentPhase = writable<PhaseNumber>(PHASES.TARGETING);

/** Target companies entered by user (max 5) */
export const targetCompanies = writable<string[]>([]);

/** Target roles entered by user (max 5) */
export const targetRoles = writable<string[]>([]);

/** Jobs discovered during the processing phase */
export const discoveredJobs = writable<Job[]>([]);

/** Set of job IDs that user has selected */
export const selectedJobIds = writable<Set<string>>(new Set());

/** Map of job ID to array of contacts (3 per job) */
export const contactsByJob = writable<Map<string, Contact[]>>(new Map());

/** Set of contact IDs that user has selected for sending */
export const selectedContactIds = writable<Set<string>>(new Set());

// ============================================
// DERIVED STORES
// ============================================

/** Whether user can proceed to search (has at least 1 company and 1 role) */
export const canSearch = derived(
  [targetCompanies, targetRoles],
  ([$companies, $roles]) => $companies.length > 0 && $roles.length > 0
);

/** Whether user can proceed to extraction (has at least 1 job selected) */
export const canExtract = derived(
  selectedJobIds,
  ($selectedIds) => $selectedIds.size > 0
);

/** Array of selected job objects */
export const selectedJobs = derived(
  [discoveredJobs, selectedJobIds],
  ([$jobs, $selectedIds]) => $jobs.filter(job => $selectedIds.has(job.id))
);

/** Selected contacts ready for sending */
export const selectedContacts = derived(
  [contactsByJob, selectedContactIds],
  ([$contactsMap, $selectedIds]) => {
    const allContacts: Contact[] = [];
    $contactsMap.forEach(contacts => {
      contacts.forEach(contact => {
        if ($selectedIds.has(contact.id)) {
          allContacts.push(contact);
        }
      });
    });
    return allContacts;
  }
);

// ============================================
// ACTIONS
// ============================================

/**
 * Advance to the next workflow phase
 */
export function nextPhase(): void {
  currentPhase.update(phase => {
    if (phase < PHASES.OUTREACH) {
      return (phase + 1) as PhaseNumber;
    }
    return phase;
  });
}

/**
 * Go back to the previous workflow phase
 */
export function prevPhase(): void {
  currentPhase.update(phase => {
    if (phase > PHASES.TARGETING) {
      return (phase - 1) as PhaseNumber;
    }
    return phase;
  });
}

/**
 * Jump to a specific phase
 */
export function goToPhase(phase: PhaseNumber): void {
  currentPhase.set(phase);
}

/**
 * Toggle job selection
 */
export function toggleJobSelection(jobId: string): void {
  selectedJobIds.update(ids => {
    const newIds = new Set(ids);
    if (newIds.has(jobId)) {
      newIds.delete(jobId);
    } else {
      newIds.add(jobId);
    }
    return newIds;
  });
}

/**
 * Toggle contact selection
 */
export function toggleContactSelection(contactId: string): void {
  selectedContactIds.update(ids => {
    const newIds = new Set(ids);
    if (newIds.has(contactId)) {
      newIds.delete(contactId);
    } else {
      newIds.add(contactId);
    }
    return newIds;
  });
}

/**
 * Reset all workflow state to initial values
 */
export function resetWorkflow(): void {
  currentPhase.set(PHASES.TARGETING);
  targetCompanies.set([]);
  targetRoles.set([]);
  discoveredJobs.set([]);
  selectedJobIds.set(new Set());
  contactsByJob.set(new Map());
  selectedContactIds.set(new Set());
}

/**
 * Get current phase value (non-reactive)
 */
export function getCurrentPhase(): PhaseNumber {
  return get(currentPhase);
}
