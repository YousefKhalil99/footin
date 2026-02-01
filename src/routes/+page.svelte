<!--
  Main Page - Job Outbound Automation Suite
  
  Multi-phase workflow for job discovery, selection, and outreach.
  Phases:
    1. Targeting - Enter target companies and roles
    2. Processing - Simulated job scraping
    3. Discovery - View found jobs
    4. Selection - Select jobs to pursue
    5. Extraction - AI extracts contacts
    6. Outreach - Review and send personalized emails
-->
<script lang="ts">
    import { fly, fade, scale } from "svelte/transition";
    import {
        Button,
        ChipInput,
        ProgressStepper,
        LoadingSpinner,
        JobCard,
        ContactCard,
    } from "$lib/components";
    import { signOut, authClient } from "$lib/auth-client";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { env } from "$env/dynamic/public";
    import {
        currentPhase,
        targetCompanies,
        targetRoles,
        discoveredJobs,
        selectedJobIds,
        contactsByJob,
        selectedContactIds,
        canExtract,
        selectedJobs,
        nextPhase,
        goToPhase,
        toggleJobSelection,
        toggleContactSelection,
        resetWorkflow,
        PHASES,
    } from "$lib/stores/workflow";
    import {
        generateMockJobs,
        generateMockContacts,
        simulateJobSearch,
        simulateAIExtraction,
        type Job,
        type Contact,
    } from "$lib/stores/mockData";

    // Local state for bound chip inputs
    let companies = $state<string[]>([]);
    let roles = $state<string[]>([]);
    const canSearchLocal = $derived(companies.length > 0 && roles.length > 0);

    // Check if we should use mock data (default to true for development)
    const useMockData = env.PUBLIC_USE_MOCK_DATA !== "false";

    // Auth state
    let session = $state<any>(null);
    let isAuthLoading = $state(true);

    // Fetch session on mount
    onMount(async () => {
        try {
            const { data } = await authClient.getSession();
            session = data;
        } catch (error) {
            console.error("Failed to get session:", error);
        } finally {
            isAuthLoading = false;
        }
    });

    // Sign in handler - navigate to sign in page
    async function handleSignIn(): Promise<void> {
        await goto("/auth/sign-in");
    }

    // Sign up handler - navigate to sign up page
    async function handleSignUp(): Promise<void> {
        await goto("/auth/sign-up");
    }

    // Sign out handler
    async function handleSignOut(): Promise<void> {
        try {
            await signOut();
            session = null;
        } catch (error) {
            console.error("Sign out error:", error);
        }
    }

    // Sync to stores when values change
    $effect(() => {
        targetCompanies.set(companies);
    });

    $effect(() => {
        targetRoles.set(roles);
    });

    // Track if we're showing cached results
    let showingCachedResults = $state(false);

    /**
     * Transform API job data to Job format
     */
    function transformJobData(job: any): Job {
        return {
            id: job.id,
            company: job.company_name || "Unknown",
            role: job.title,
            location: job.location || "Not specified",
            type: "Full-time",
            summarizedJD: job.description || "No description available",
            postedDate: job.published_at || "Recently",
            salary: job.salary_info || undefined,
        };
    }

    /**
     * Handle search button click - check for cached jobs first
     */
    async function handleSearch(): Promise<void> {
        if (!canSearchLocal) return;

        // Sync current inputs to stores
        targetCompanies.set(companies);
        targetRoles.set(roles);

        // Move to processing phase
        goToPhase(PHASES.PROCESSING);

        let jobs: Job[] = [];

        try {
            if (useMockData) {
                // Simulate job search delay
                await simulateJobSearch();
                // Generate mock jobs based on inputs
                jobs = generateMockJobs(companies, roles);
                showingCachedResults = false;
            } else {
                // First, check for existing jobs in the database
                const params = new URLSearchParams();
                roles.forEach((role) => params.append("keyword", role));

                const cachedResponse = await fetch(
                    `/api/jobs?${params.toString()}`,
                );
                const cachedData = await cachedResponse.json();

                if (
                    cachedResponse.ok &&
                    cachedData.jobs &&
                    cachedData.jobs.length > 0
                ) {
                    // We have cached results, use them
                    jobs = cachedData.jobs.map(transformJobData);
                    showingCachedResults = true;
                } else {
                    // No cached results, run fresh search
                    await runFreshSearch();
                    return;
                }
            }

            discoveredJobs.set(jobs);

            // Move to discovery phase
            goToPhase(PHASES.DISCOVERY);
        } catch (error) {
            console.error("Search failed:", error);
            alert(
                `Search failed: ${error instanceof Error ? error.message : "Unknown error"}`,
            );
            goToPhase(PHASES.TARGETING);
        }
    }

    /**
     * Run a fresh search from Apify (scrape new jobs)
     */
    async function runFreshSearch(): Promise<void> {
        // Move to processing phase
        goToPhase(PHASES.PROCESSING);
        showingCachedResults = false;

        try {
            const response = await fetch("/api/discover", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    keyword: roles.length > 0 ? roles : $targetRoles,
                    location: "Remote", // TODO: make this configurable
                    publishedAt: "r86400", // Last 24 hours
                }),
            });
            const data = await response.json();
            if (!response.ok || data.error) {
                console.error("API error:", data.error || response.statusText);
                throw new Error(data.error || "Failed to fetch jobs");
            }

            // Transform API response to Job format
            const jobs = (data.jobs || []).map(transformJobData);

            discoveredJobs.set(jobs);

            // Move to discovery phase
            goToPhase(PHASES.DISCOVERY);
        } catch (error) {
            console.error("Fresh search failed:", error);
            alert(
                `Search failed: ${error instanceof Error ? error.message : "Unknown error"}`,
            );
            goToPhase(PHASES.TARGETING);
        }
    }

    /**
     * Handle continue after job selection
     */
    async function handleContinueToExtraction(): Promise<void> {
        if (!$canExtract) return;

        // Move to extraction phase
        goToPhase(PHASES.EXTRACTION);

        const contactsMap = new Map<string, Contact[]>();

        if (useMockData) {
            // Simulate AI extraction delay
            await simulateAIExtraction();

            // Generate contacts for each selected job
            $selectedJobs.forEach((job) => {
                const contacts = generateMockContacts(job);
                contactsMap.set(job.id, contacts);

                // Auto-select all contacts by default
                contacts.forEach((c) => {
                    selectedContactIds.update((ids) => {
                        const newIds = new Set(ids);
                        newIds.add(c.id);
                        return newIds;
                    });
                });
            });
        } else {
<<<<<<< Updated upstream
            // Use Hunter.io API for contact extraction
=======
            // Use Hunter.io API for contact extraction via Modal agent
>>>>>>> Stashed changes
            try {
                // Get unique company names from selected jobs
                const companyNames = [
                    ...new Set($selectedJobs.map((job) => job.company)),
                ];

                const response = await fetch("/api/find-people", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        companies: companyNames,
                        departments: ["it", "management", "sales"],
                    }),
                });

                if (!response.ok) {
<<<<<<< Updated upstream
                    throw new Error("Failed to fetch contacts");
=======
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(
                        errorData.error || "Failed to fetch contacts",
                    );
>>>>>>> Stashed changes
                }

                const contactsByCompany = await response.json();

                // Map contacts back to jobs
                $selectedJobs.forEach((job) => {
                    const companyContacts =
                        contactsByCompany[job.company] || [];

                    // Transform Hunter contacts to our Contact format
                    const contacts: Contact[] = companyContacts.map(
                        (c: any, index: number) => {
                            const source:
                                | "Hiring Manager"
                                | "Team Lead"
                                | "Peer" =
                                c.seniority === "executive"
                                    ? "Hiring Manager"
                                    : c.seniority === "senior"
                                      ? "Team Lead"
                                      : "Peer";

                            // Generate personalized email
                            const firstName = c.name?.split(" ")[0] || "there";
                            const emailSubject = `${job.role} opportunity at ${job.company} — Quick intro`;
                            const draftedEmail = `Hi ${firstName},

I came across the ${job.role} position at ${job.company} and believe my background could be a strong fit.

I noticed your work as ${c.title || "a leader"} at ${job.company} and would love to learn more about what your team is working on.

Would you be open to a brief 15-minute chat next week?

Best regards`;

                            return {
                                id: `${job.id}-${index}`,
                                jobId: job.id,
                                name: c.name || "Unknown",
                                title: c.title || c.seniority || "Team Member",
                                source,
                                linkedInActivity: c.linkedin_url
                                    ? "LinkedIn profile available"
                                    : "No recent activity found",
                                emailSubject,
                                draftedEmail,
                            };
                        },
                    );

                    if (contacts.length > 0) {
                        contactsMap.set(job.id, contacts);

                        // Auto-select all contacts
                        contacts.forEach((c) => {
                            selectedContactIds.update((ids) => {
                                const newIds = new Set(ids);
                                newIds.add(c.id);
                                return newIds;
                            });
                        });
                    }
                });
            } catch (error) {
                console.error("Contact extraction failed:", error);
                // Fall back to mock data on error
<<<<<<< Updated upstream
=======
                alert(
                    `Contact extraction encountered an error: ${error instanceof Error ? error.message : "Unknown error"}. Using mock data instead.`,
                );
>>>>>>> Stashed changes
                $selectedJobs.forEach((job) => {
                    const contacts = generateMockContacts(job);
                    contactsMap.set(job.id, contacts);
                    contacts.forEach((c) => {
                        selectedContactIds.update((ids) => {
                            const newIds = new Set(ids);
                            newIds.add(c.id);
                            return newIds;
                        });
                    });
                });
            }
        }

        contactsByJob.set(contactsMap);

        // Move to outreach phase
        goToPhase(PHASES.OUTREACH);
    }

    /**
     * Handle sending an email (simulated)
     */
    function handleSendEmail(contact: Contact): void {
        // In a real app, this would call an API
        alert(
            `Email sent to ${contact.name}!\n\nSubject: ${contact.emailSubject}`,
        );
    }

    /**
     * Reset and start over
     */
    function handleStartOver(): void {
        companies = [];
        roles = [];
        resetWorkflow();
    }
</script>

<div class="app-container">
    <header class="app-header">
        <div class="logo">
            <span class="logo-icon">🚀</span>
            <span class="logo-text">Foot<span class="accent">In</span></span>
        </div>
        <p class="tagline">AI-Powered Job Outreach Automation</p>
        <div class="header-actions">
            {#if isAuthLoading}
                <span class="user-info">Loading...</span>
            {:else if session?.user}
                <span class="user-info"
                    >Welcome, {session.user.name || session.user.email}</span
                >
                <Button variant="secondary" onclick={handleSignOut}>
                    Sign Out
                </Button>
            {:else}
                <Button
                    variant="secondary"
                    onclick={handleSignIn}
                    disabled={isAuthLoading}
                >
                    Sign In
                </Button>
                <Button
                    variant="primary"
                    onclick={handleSignUp}
                    disabled={isAuthLoading}
                >
                    Sign Up
                </Button>
            {/if}
        </div>
    </header>

    <ProgressStepper currentPhase={$currentPhase} />

    <main class="main-content">
        <!-- PHASE 1: TARGETING -->
        {#if $currentPhase === PHASES.TARGETING}
            <section
                class="phase-container"
                in:fly={{ y: 30, duration: 400, delay: 100 }}
            >
                <div class="phase-header">
                    <h1 class="phase-title">Target Your Search</h1>
                    <p class="phase-description">
                        Enter up to 5 companies and 5 roles you're interested
                        in. We'll find matching opportunities and relevant
                        contacts.
                    </p>
                </div>

                <div class="targeting-form">
                    <ChipInput
                        label="Target Companies"
                        placeholder="e.g., Google, Anthropic, Stripe..."
                        maxChips={5}
                        bind:chips={companies}
                    />

                    <ChipInput
                        label="Target Roles"
                        placeholder="e.g., Software Engineer, Product Manager..."
                        maxChips={5}
                        bind:chips={roles}
                    />

                    <div class="form-actions">
                        <Button
                            variant="primary"
                            disabled={!canSearchLocal}
                            onclick={handleSearch}
                        >
                            <svg
                                width="18"
                                height="18"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                            Search Jobs
                        </Button>
                    </div>
                </div>
            </section>
        {/if}

        <!-- PHASE 2: PROCESSING -->
        {#if $currentPhase === PHASES.PROCESSING}
            <section
                class="phase-container centered"
                in:fade={{ duration: 300 }}
            >
                <LoadingSpinner
                    size="lg"
                    message="Searching job boards and career pages..."
                />
                <p class="processing-detail">
                    Scanning opportunities at {$targetCompanies.join(", ")}
                </p>
            </section>
        {/if}

        <!-- PHASE 3 & 4: DISCOVERY & SELECTION -->
        {#if $currentPhase === PHASES.DISCOVERY || $currentPhase === PHASES.SELECTION}
            <section
                class="phase-container"
                in:fly={{ y: 30, duration: 400, delay: 100 }}
            >
                <div class="phase-header">
                    <h1 class="phase-title">
                        {$currentPhase === PHASES.DISCOVERY
                            ? "Jobs Found"
                            : "Select Jobs to Pursue"}
                    </h1>
                    <p class="phase-description">
                        {#if $currentPhase === PHASES.DISCOVERY}
                            {#if showingCachedResults}
                                Showing {$discoveredJobs.length} saved jobs from
                                previous searches.
                            {:else}
                                We found {$discoveredJobs.length} matching opportunities.
                            {/if}
                            Review and select the ones you'd like to pursue.
                        {:else}
                            You've selected {$selectedJobIds.size} job(s). Ready
                            to find contacts?
                        {/if}
                    </p>
                    {#if showingCachedResults && !useMockData}
                        <Button variant="secondary" onclick={runFreshSearch}>
                            <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <path
                                    d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"
                                />
                            </svg>
                            Run Fresh Search
                        </Button>
                    {/if}
                </div>

                <div class="jobs-grid">
                    {#each $discoveredJobs as job, index (job.id)}
                        <div
                            in:fly={{ y: 20, duration: 300, delay: index * 50 }}
                        >
                            <JobCard
                                {job}
                                selected={$selectedJobIds.has(job.id)}
                                onToggle={() => {
                                    toggleJobSelection(job.id);
                                    // Auto-advance to selection phase when first job selected
                                    if ($currentPhase === PHASES.DISCOVERY) {
                                        goToPhase(PHASES.SELECTION);
                                    }
                                }}
                            />
                        </div>
                    {/each}
                </div>

                {#if $selectedJobIds.size > 0}
                    <div class="phase-actions" in:scale={{ duration: 200 }}>
                        <Button
                            variant="secondary"
                            onclick={() => goToPhase(PHASES.TARGETING)}
                        >
                            ← Back to Search
                        </Button>
                        <Button
                            variant="primary"
                            onclick={handleContinueToExtraction}
                        >
                            Find Contacts for {$selectedJobIds.size} Job(s)
                            <svg
                                width="18"
                                height="18"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <path d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                        </Button>
                    </div>
                {/if}
            </section>
        {/if}

        <!-- PHASE 5: EXTRACTION -->
        {#if $currentPhase === PHASES.EXTRACTION}
            <section
                class="phase-container centered"
                in:fade={{ duration: 300 }}
            >
                <LoadingSpinner
                    size="lg"
                    message="AI is extracting key details and finding contacts..."
                />
                <p class="processing-detail">
                    Researching hiring managers and team members for your
                    selected roles
                </p>
            </section>
        {/if}

        <!-- PHASE 6: OUTREACH -->
        {#if $currentPhase === PHASES.OUTREACH}
            <section
                class="phase-container"
                in:fly={{ y: 30, duration: 400, delay: 100 }}
            >
                <div class="phase-header">
                    <h1 class="phase-title">Review & Send Outreach</h1>
                    <p class="phase-description">
                        We found contacts for your selected jobs. Review the
                        AI-drafted emails and send when ready.
                    </p>
                </div>

                <div class="outreach-container">
                    {#each $selectedJobs as job, jobIndex (job.id)}
                        {@const contacts = $contactsByJob.get(job.id) || []}

                        <div
                            class="job-outreach-section"
                            in:fly={{
                                y: 20,
                                duration: 300,
                                delay: jobIndex * 100,
                            }}
                        >
                            <div class="job-outreach-header">
                                <span class="job-company">{job.company}</span>
                                <h3 class="job-role">{job.role}</h3>
                            </div>

                            <div class="contacts-grid">
                                {#each contacts as contact, contactIndex (contact.id)}
                                    <div
                                        in:fly={{
                                            x: -20,
                                            duration: 250,
                                            delay: contactIndex * 75,
                                        }}
                                    >
                                        <ContactCard
                                            {contact}
                                            selected={$selectedContactIds.has(
                                                contact.id,
                                            )}
                                            onToggleSelect={() =>
                                                toggleContactSelection(
                                                    contact.id,
                                                )}
                                            onSend={() =>
                                                handleSendEmail(contact)}
                                        />
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>

                <div class="phase-actions">
                    <Button
                        variant="secondary"
                        onclick={() => goToPhase(PHASES.SELECTION)}
                    >
                        ← Back to Selection
                    </Button>
                    <Button variant="secondary" onclick={handleStartOver}>
                        Start New Search
                    </Button>
                    <Button
                        variant="primary"
                        disabled={$selectedContactIds.size === 0}
                        onclick={() =>
                            alert(
                                `Sending ${$selectedContactIds.size} emails...`,
                            )}
                    >
                        <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                        >
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                        </svg>
                        Send All Selected ({$selectedContactIds.size})
                    </Button>
                </div>
            </section>
        {/if}
    </main>

    <footer class="app-footer">
        <p>Built with AI for the modern job seeker</p>
    </footer>
</div>

<style>
    .app-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
    }

    .app-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 24px 0 16px;
        position: relative;
    }

    .header-actions {
        position: absolute;
        top: 24px;
        right: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .user-info {
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    .logo {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .logo-icon {
        font-size: 2rem;
    }

    .logo-text {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .logo-text .accent {
        color: var(--accent-cyan);
    }

    .tagline {
        margin: 0;
        font-size: 0.9375rem;
        color: var(--text-muted);
    }

    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 32px 0;
    }

    .phase-container {
        display: flex;
        flex-direction: column;
        gap: 32px;
    }

    .phase-container.centered {
        align-items: center;
        justify-content: center;
        min-height: 400px;
    }

    .phase-header {
        text-align: center;
        max-width: 600px;
        margin: 0 auto;
    }

    .phase-title {
        margin: 0 0 12px;
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(
            135deg,
            var(--text-primary),
            var(--accent-cyan)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .phase-description {
        margin: 0;
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }

    .targeting-form {
        display: flex;
        flex-direction: column;
        gap: 24px;
        max-width: 600px;
        margin: 0 auto;
        width: 100%;
    }

    .form-actions {
        display: flex;
        justify-content: center;
        padding-top: 16px;
    }

    .processing-detail {
        margin: 0;
        font-size: 0.875rem;
        color: var(--text-muted);
        text-align: center;
    }

    .jobs-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 20px;
    }

    .phase-actions {
        display: flex;
        justify-content: center;
        gap: 16px;
        padding-top: 24px;
        flex-wrap: wrap;
    }

    .outreach-container {
        display: flex;
        flex-direction: column;
        gap: 40px;
    }

    .job-outreach-section {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .job-outreach-header {
        padding: 16px 20px;
        background: var(--bg-surface);
        border-left: 3px solid var(--accent-cyan);
        border-radius: var(--radius-md);
    }

    .job-company {
        font-size: 0.8125rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .job-role {
        margin: 4px 0 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .contacts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 20px;
    }

    .app-footer {
        padding: 24px 0;
        text-align: center;
    }

    .app-footer p {
        margin: 0;
        font-size: 0.8125rem;
        color: var(--text-muted);
    }

    /* Responsive */
    @media (max-width: 768px) {
        .app-container {
            padding: 16px;
        }

        .phase-title {
            font-size: 1.5rem;
        }

        .jobs-grid,
        .contacts-grid {
            grid-template-columns: 1fr;
        }

        .phase-actions {
            flex-direction: column;
            align-items: stretch;
        }
    }
</style>
