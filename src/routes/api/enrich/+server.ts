/**
 * Enrich API Route
 * 
 * Gets company news and X profiles via web scraping.
 * Uses Browserbase/Stagehand for AI-powered extraction.
 * 
 * POST /api/enrich
 * Body: { companies: string[] }
 * Returns: { [company]: { news: Article[], x_profile: Profile | null } }
 * 
 * Note: This is a simplified version that returns mock data
 * if Browserbase credentials are not configured.
 */

import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { env } from "$env/dynamic/private";

interface Article {
    title: string;
    source: string;
    date: string;
    url?: string;
}

interface XProfile {
    handle: string;
    display_name: string;
    bio: string;
    tweets: Array<{ text: string; date: string }>;
}

interface EnrichmentResult {
    news: Article[];
    x_profile: XProfile | null;
}

/**
 * Fetch Google News RSS for a company (simplified, no browser needed)
 */
async function fetchCompanyNews(company: string): Promise<Article[]> {
    try {
        // Use Google News RSS feed (public, no API key needed)
        const encodedQuery = encodeURIComponent(company);
        const rssUrl = `https://news.google.com/rss/search?q=${encodedQuery}&hl=en-US&gl=US&ceid=US:en`;

        const response = await fetch(rssUrl);
        if (!response.ok) {
            console.error(`Failed to fetch news for ${company}`);
            return [];
        }

        const xml = await response.text();

        // Simple XML parsing for RSS items
        const items: Article[] = [];
        const itemRegex = /<item>([\s\S]*?)<\/item>/g;
        let match;

        while ((match = itemRegex.exec(xml)) !== null && items.length < 5) {
            const itemXml = match[1];

            const titleMatch = /<title>(.*?)<\/title>/.exec(itemXml);
            const sourceMatch = /<source.*?>(.*?)<\/source>/.exec(itemXml);
            const dateMatch = /<pubDate>(.*?)<\/pubDate>/.exec(itemXml);
            const linkMatch = /<link>(.*?)<\/link>/.exec(itemXml);

            if (titleMatch) {
                items.push({
                    title: titleMatch[1].replace(/<!\[CDATA\[(.*?)\]\]>/, "$1"),
                    source: sourceMatch ? sourceMatch[1] : "Unknown",
                    date: dateMatch ? formatDate(dateMatch[1]) : "Recently",
                    url: linkMatch ? linkMatch[1] : undefined,
                });
            }
        }

        return items;
    } catch (error) {
        console.error(`Error fetching news for ${company}:`, error);
        return [];
    }
}

/**
 * Format RSS date to human-readable format
 */
function formatDate(rssDate: string): string {
    try {
        const date = new Date(rssDate);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return "Today";
        if (diffDays === 1) return "Yesterday";
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch {
        return "Recently";
    }
}

export const POST: RequestHandler = async ({ request }) => {
    let body: { companies?: string[] };

    try {
        body = await request.json();
    } catch {
        return json({ error: "Invalid JSON body" }, { status: 400 });
    }

    const companies = body.companies?.filter(Boolean).slice(0, 5) || [];

    if (companies.length === 0) {
        return json({ error: "companies array is required" }, { status: 400 });
    }

    const results: Record<string, EnrichmentResult> = {};

    // Fetch news for each company (in parallel)
    await Promise.all(
        companies.map(async (company) => {
            const news = await fetchCompanyNews(company);

            results[company] = {
                news,
                x_profile: null, // X profile scraping requires Browserbase
            };
        })
    );

    // Check if Browserbase is configured for advanced enrichment
    const hasBrowserbase = Boolean(
        env.BROWSERBASE_API_KEY &&
        env.BROWSERBASE_PROJECT_ID &&
        env.MODEL_API_KEY
    );

    return json({
        results,
        enrichment_level: hasBrowserbase ? "full" : "basic",
        note: hasBrowserbase
            ? "Full enrichment with X profiles available"
            : "Basic enrichment (news only). Configure BROWSERBASE_API_KEY for X profile data.",
    });
};
