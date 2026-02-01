/**
 * Find People API Route
 * 
 * Searches for contacts at companies via Hunter.io API.
 * Returns 2-3 contacts per company with email addresses.
 * 
 * POST /api/find-people
 * Body: { companies: string[], departments?: string[] }
 * Returns: { [company]: Contact[] }
 */

import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { env } from "$env/dynamic/private";

// Hunter.io API base URL
const HUNTER_BASE_URL = "https://api.hunter.io/v2";

/**
 * Convert company name to domain.
 * Uses known mappings or defaults to lowercase + .com
 */
function companyToDomain(company: string): string {
    const knownDomains: Record<string, string> = {
        google: "google.com",
        meta: "meta.com",
        facebook: "meta.com",
        openai: "openai.com",
        anthropic: "anthropic.com",
        microsoft: "microsoft.com",
        apple: "apple.com",
        amazon: "amazon.com",
        netflix: "netflix.com",
        stripe: "stripe.com",
        airbnb: "airbnb.com",
        uber: "uber.com",
        lyft: "lyft.com",
        salesforce: "salesforce.com",
        shopify: "shopify.com",
    };

    let companyLower = company.toLowerCase().trim();

    if (knownDomains[companyLower]) {
        return knownDomains[companyLower];
    }

    // Remove common suffixes
    for (const suffix of [" inc", " corp", " llc", " ltd", ", inc", ", corp"]) {
        if (companyLower.endsWith(suffix)) {
            companyLower = companyLower.slice(0, -suffix.length);
        }
    }

    return `${companyLower.replace(/\s+/g, "")}.com`;
}

interface HunterEmail {
    first_name?: string;
    last_name?: string;
    value?: string;
    position?: string;
    seniority?: string;
    department?: string;
    linkedin?: string;
    confidence?: number;
}

interface Contact {
    name: string;
    email: string | null;
    title: string | null;
    seniority: string | null;
    department: string | null;
    linkedin_url: string | null;
    confidence: number | null;
    company: string;
}

/**
 * Search Hunter.io for contacts at a domain.
 */
async function searchHunter(
    apiKey: string,
    domain: string,
    department?: string,
    seniority?: string
): Promise<Contact[]> {
    const params = new URLSearchParams({
        domain,
        api_key: apiKey,
        type: "personal",
        limit: "5",
    });

    if (department) params.set("department", department);
    if (seniority) params.set("seniority", seniority);

    try {
        const response = await fetch(`${HUNTER_BASE_URL}/domain-search?${params}`);

        if (!response.ok) {
            console.error(`Hunter API error: ${response.status}`);
            return [];
        }

        const data = await response.json();
        const emails: HunterEmail[] = data?.data?.emails || [];

        return emails.map((e) => ({
            name: `${e.first_name || ""} ${e.last_name || ""}`.trim(),
            email: e.value || null,
            title: e.position || null,
            seniority: e.seniority || null,
            department: e.department || null,
            linkedin_url: e.linkedin || null,
            confidence: e.confidence || null,
            company: domain.replace(".com", "").replace(".", " "),
        }));
    } catch (error) {
        console.error(`Hunter search error for ${domain}:`, error);
        return [];
    }
}

/**
 * Pick best 2-3 contacts: prefer executives + seniors.
 */
function pickBestContacts(contacts: Contact[]): Contact[] {
    if (contacts.length === 0) return [];

    const executives = contacts.filter((c) => c.seniority === "executive");
    const seniors = contacts.filter((c) => c.seniority === "senior");
    const others = contacts.filter(
        (c) => c.seniority !== "executive" && c.seniority !== "senior"
    );

    const selected: Contact[] = [];

    // Add up to 2 executives
    selected.push(...executives.slice(0, 2));

    // Add 1 senior
    if (seniors.length > 0) {
        selected.push(seniors[0]);
    }

    // Fill to at least 2
    if (selected.length < 2) {
        const remaining = [...seniors.slice(1), ...others];
        selected.push(...remaining.slice(0, 2 - selected.length));
    }

    return selected.slice(0, 3);
}

export const POST: RequestHandler = async ({ request }) => {
    const apiKey = env.HUNTER_API_KEY;

    if (!apiKey) {
        return json(
            { error: "HUNTER_API_KEY is not configured" },
            { status: 500 }
        );
    }

    let body: { companies?: string[]; departments?: string[] };

    try {
        body = await request.json();
    } catch {
        return json({ error: "Invalid JSON body" }, { status: 400 });
    }

    const companies = body.companies?.filter(Boolean).slice(0, 5) || [];

    if (companies.length === 0) {
        return json({ error: "companies array is required" }, { status: 400 });
    }

    const departments = body.departments?.filter(Boolean) || ["it", "management", "sales"];
    const results: Record<string, Contact[]> = {};

    for (const company of companies) {
        const domain = companyToDomain(company);
        const allContacts: Contact[] = [];

        // Search for executives and seniors across departments
        for (const seniority of ["executive", "senior"]) {
            for (const dept of departments.slice(0, 3)) {
                const contacts = await searchHunter(apiKey, domain, dept, seniority);
                allContacts.push(...contacts);
            }
        }

        // Deduplicate by email
        const seen = new Set<string>();
        const unique = allContacts.filter((c) => {
            if (!c.email || seen.has(c.email)) return false;
            seen.add(c.email);
            c.company = company; // Use original company name
            return true;
        });

        results[company] = pickBestContacts(unique);
    }

    return json(results);
};
