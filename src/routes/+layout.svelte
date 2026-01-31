<!--
  Main Application Layout
  
  Sets up the root layout with dark theme, fonts, and SEO meta tags.
-->
<script lang="ts">
	import "./layout.css";
	import favicon from "$lib/assets/favicon.svg";

	let { children } = $props();
</script>

<svelte:head>
	<title>FootIn — Job Outbound Automation Suite</title>
	<meta
		name="description"
		content="AI-powered job hunting automation. Find jobs, identify hiring managers, and send personalized outreach at scale."
	/>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}
