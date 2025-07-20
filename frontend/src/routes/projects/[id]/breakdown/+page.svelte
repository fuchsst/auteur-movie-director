<!--
Project Breakdown Page
STORY-086: Professional Script Breakdown Interface

Main page component for the script breakdown interface that provides
a comprehensive view of production elements and scene-by-scene analysis.
-->

<script lang="ts">
  import { page } from '$app/stores';
  import BreakdownView from '$lib/breakdown/BreakdownView.svelte';
  import { projectStore } from '$lib/stores/projectStore';

  $: projectId = $page.params.id;
  $: currentProject = $projectStore.projects.find(p => p.id === projectId);
</script>

<svelte:head>
  <title>{currentProject?.name || 'Project'} - Script Breakdown</title>
  <meta name="description" content="Professional script breakdown interface for production planning" />
</svelte:head>

<div class="page-container">
  <BreakdownView {projectId} />
</div>

<style>
  .page-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
</style>