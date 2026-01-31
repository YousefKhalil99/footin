/**
 * Mock Data Generators
 * 
 * Provides simulated job listings, contacts, and AI-generated email drafts
 * for demonstration purposes. Structured to easily swap for real API calls.
 */

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface Job {
    id: string;
    company: string;
    role: string;
    location: string;
    type: string; // "Full-time", "Contract", etc.
    summarizedJD: string;
    postedDate: string;
    salary?: string;
}

export interface Contact {
    id: string;
    jobId: string;
    name: string;
    title: string;
    source: 'Hiring Manager' | 'Team Lead' | 'Peer';
    linkedInActivity: string;
    draftedEmail: string;
    emailSubject: string;
}

// ============================================
// MOCK DATA POOLS
// ============================================

const LOCATIONS = [
    'San Francisco, CA',
    'New York, NY',
    'Seattle, WA',
    'Austin, TX',
    'Remote',
    'Boston, MA',
    'Los Angeles, CA',
    'Denver, CO'
];

const JOB_TYPES = ['Full-time', 'Contract', 'Full-time • Remote', 'Hybrid'];

const SALARY_RANGES = [
    '$120K - $180K',
    '$150K - $220K',
    '$180K - $250K',
    '$200K - $300K',
    '$140K - $190K'
];

const JD_TEMPLATES = [
    (company: string, role: string) =>
        `Join ${company}'s innovative team as a ${role}. You'll work on cutting-edge projects, collaborate with world-class engineers, and have direct impact on products used by millions.`,
    (company: string, role: string) =>
        `${company} is seeking a ${role} to help scale our platform. This role involves designing robust systems, mentoring junior engineers, and driving technical excellence.`,
    (company: string, role: string) =>
        `As a ${role} at ${company}, you'll lead key initiatives, partner with cross-functional teams, and build solutions that define the future of our industry.`,
    (company: string, role: string) =>
        `${company} is hiring a ${role} to join our fast-growing team. You'll own end-to-end delivery, work with modern tech stacks, and shape our engineering culture.`
];

const FIRST_NAMES = ['Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'Chris', 'Amanda', 'Ryan', 'Rachel', 'Kevin'];
const LAST_NAMES = ['Chen', 'Johnson', 'Williams', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Anderson', 'Taylor'];

const TITLES = {
    'Hiring Manager': ['Engineering Manager', 'Senior Engineering Manager', 'Director of Engineering', 'VP of Engineering'],
    'Team Lead': ['Tech Lead', 'Staff Engineer', 'Principal Engineer', 'Senior Staff Engineer'],
    'Peer': ['Senior Software Engineer', 'Software Engineer II', 'Senior Developer', 'Platform Engineer']
};

const LINKEDIN_ACTIVITIES = [
    'Recently shared an article about AI/ML best practices',
    'Commented on a post about remote work culture',
    'Celebrated 5 years at the company last month',
    'Posted about their team\'s latest product launch',
    'Shared insights on building diverse engineering teams',
    'Attended a conference on distributed systems',
    'Wrote about their career journey in tech',
    'Mentioned they\'re building out the team',
    'Recently promoted to their current role',
    'Shared a podcast about engineering leadership'
];

// ============================================
// HELPER FUNCTIONS
// ============================================

function generateId(): string {
    return Math.random().toString(36).substring(2, 11);
}

function randomFrom<T>(array: T[]): T {
    return array[Math.floor(Math.random() * array.length)];
}

function generateDaysAgo(): string {
    const days = Math.floor(Math.random() * 14) + 1;
    return days === 1 ? '1 day ago' : `${days} days ago`;
}

// ============================================
// MOCK GENERATORS
// ============================================

/**
 * Generates mock job listings based on target companies and roles.
 * Simulates what a job scraper would return.
 * 
 * @param companies - Array of target company names
 * @param roles - Array of target role names
 * @returns Array of Job objects
 */
export function generateMockJobs(companies: string[], roles: string[]): Job[] {
    const jobs: Job[] = [];

    // Generate 1-3 jobs per company-role combination
    companies.forEach(company => {
        roles.forEach(role => {
            const numJobs = Math.floor(Math.random() * 2) + 1; // 1-2 jobs per combo

            for (let i = 0; i < numJobs; i++) {
                jobs.push({
                    id: generateId(),
                    company,
                    role: i === 0 ? role : `Senior ${role}`, // Variation
                    location: randomFrom(LOCATIONS),
                    type: randomFrom(JOB_TYPES),
                    summarizedJD: randomFrom(JD_TEMPLATES)(company, role),
                    postedDate: generateDaysAgo(),
                    salary: Math.random() > 0.3 ? randomFrom(SALARY_RANGES) : undefined
                });
            }
        });
    });

    // Shuffle and limit to reasonable number
    return jobs.sort(() => Math.random() - 0.5).slice(0, 12);
}

/**
 * Generates mock contacts for a job listing.
 * Simulates LinkedIn search + enrichment results.
 * 
 * @param job - The job to generate contacts for
 * @returns Array of 3 Contact objects
 */
export function generateMockContacts(job: Job): Contact[] {
    const sources: Array<'Hiring Manager' | 'Team Lead' | 'Peer'> = ['Hiring Manager', 'Team Lead', 'Peer'];

    return sources.map(source => {
        const firstName = randomFrom(FIRST_NAMES);
        const lastName = randomFrom(LAST_NAMES);
        const name = `${firstName} ${lastName}`;
        const title = randomFrom(TITLES[source]);
        const linkedInActivity = randomFrom(LINKEDIN_ACTIVITIES);

        // Generate personalized email based on LinkedIn activity
        const { subject, body } = generatePersonalizedEmail(
            name,
            firstName,
            title,
            job.company,
            job.role,
            linkedInActivity
        );

        return {
            id: generateId(),
            jobId: job.id,
            name,
            title,
            source,
            linkedInActivity,
            emailSubject: subject,
            draftedEmail: body
        };
    });
}

/**
 * Generates a personalized email draft based on contact info and LinkedIn activity.
 * Simulates what an LLM would produce.
 */
function generatePersonalizedEmail(
    fullName: string,
    firstName: string,
    title: string,
    company: string,
    role: string,
    linkedInActivity: string
): { subject: string; body: string } {
    // Extract personalization hook from LinkedIn activity
    let hook = '';
    if (linkedInActivity.includes('AI/ML')) {
        hook = `I noticed your recent post about AI/ML best practices — it really resonated with my own experience building ML pipelines.`;
    } else if (linkedInActivity.includes('remote work')) {
        hook = `Your thoughts on remote work culture caught my attention — I've been passionate about building effective distributed teams.`;
    } else if (linkedInActivity.includes('5 years')) {
        hook = `Congratulations on your 5-year milestone at ${company}! That kind of tenure speaks to the incredible culture you've helped build.`;
    } else if (linkedInActivity.includes('product launch')) {
        hook = `I saw your team's recent product launch — impressive work. The technical challenges you must have solved are exactly the kind I thrive on.`;
    } else if (linkedInActivity.includes('diverse')) {
        hook = `Your insights on building diverse engineering teams aligned with my own values about inclusive workplaces.`;
    } else if (linkedInActivity.includes('conference')) {
        hook = `I noticed you attended a distributed systems conference recently — I'd love to hear your takeaways sometime.`;
    } else if (linkedInActivity.includes('promoted')) {
        hook = `Congratulations on your recent promotion! It's clear you're making a strong impact at ${company}.`;
    } else if (linkedInActivity.includes('building out')) {
        hook = `I saw you're growing the team — exciting times! I'd love to be part of that growth story.`;
    } else {
        hook = `I've been following ${company}'s journey and the innovative work your team is doing.`;
    }

    const subject = `${role} opportunity at ${company} — Quick intro`;

    const body = `Hi ${firstName},

${hook}

I'm reaching out because I saw the ${role} position at ${company} and believe my background could be a strong fit. I've spent the last several years building scalable systems and leading technical initiatives that drove measurable business impact.

I'd love to learn more about what your team is working on and share how I might contribute. Would you be open to a brief 15-minute chat next week?

Looking forward to connecting!

Best regards`;

    return { subject, body };
}

/**
 * Simulates processing delay for job discovery.
 * Returns a promise that resolves after 2-3 seconds.
 */
export function simulateJobSearch(): Promise<void> {
    const delay = 2000 + Math.random() * 1000;
    return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * Simulates AI extraction delay.
 * Returns a promise that resolves after 1-2 seconds.
 */
export function simulateAIExtraction(): Promise<void> {
    const delay = 1500 + Math.random() * 1000;
    return new Promise(resolve => setTimeout(resolve, delay));
}
