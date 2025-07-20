<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	import type { 
		TableReadSession, 
		CreativeBible, 
		TableReadFormData,
		StoryCircleBeat,
		CharacterAnalysis,
		SceneAnalysis
	} from '$lib/types/table-read';
	import { tableReadStore } from '$lib/stores/table-read-store';

	export let projectId: string;

	// State
	let loading = false;
	let error: string | null = null;
	let currentSession: TableReadSession | null = null;
	let currentBible: CreativeBible | null = null;
	let sessions: TableReadSession[] = [];
	let activeTab = 'create';
	let selectedBeat: StoryCircleBeat | null = null;
	let selectedCharacter: CharacterAnalysis | null = null;
	let selectedScene: SceneAnalysis | null = null;

	// Form data
	let formData: TableReadFormData = {
		script_content: '',
		analysis_depth: 'comprehensive',
		focus_areas: ['characters', 'structure', 'themes'],
		include_audio: false,
		generate_bible: true
	};

	// UI state
	let showCharacterModal = false;
	let showSceneModal = false;
	let showStoryCircleModal = false;
	let showExportModal = false;
	let exportFormat = 'pdf';
	let includeAudio = false;

	onMount(async () => {
		await loadSessions();
	});

	async function loadSessions() {
		try {
			loading = true;
			sessions = await tableReadStore.loadSessions(projectId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load sessions';
		} finally {
			loading = false;
		}
	}

	async function createTableRead() {
		if (!formData.script_content.trim()) {
			error = 'Please provide script content';
			return;
		}

		try {
			loading = true;
			error = null;

			const request = {
				project_id: projectId,
				...formData,
				character_voices: {}
			};

			const session = await tableReadStore.createSession(request);
			currentSession = session;
			activeTab = 'sessions';

			// Refresh sessions list
			sessions = await tableReadStore.loadSessions(projectId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create session';
		} finally {
			loading = false;
		}
	}

	async function loadBible(bibleId: string) {
		try {
			loading = true;
			const bible = await tableReadStore.loadBible(bibleId);
			currentBible = bible;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load bible';
		} finally {
			loading = false;
		}
	}

	async function refreshSession(sessionId: string) {
		try {
			await tableReadStore.refreshSession(sessionId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to refresh session';
		}
	}

	function selectCharacter(character: CharacterAnalysis) {
		selectedCharacter = character;
		showCharacterModal = true;
	}

	function selectScene(scene: SceneAnalysis) {
		selectedScene = scene;
		showSceneModal = true;
	}

	function formatBeatDescription(beat: StoryCircleBeat): string {
		const descriptions = {
			'you': 'Character in their comfort zone',
			'need': 'Character wants something',
			'go': 'Character enters unfamiliar situation',
			'search': 'Character adapts and learns',
			'find': 'Character gets what they wanted',
			'take': 'Character pays the price',
			'return': 'Character returns to familiar situation',
			'change': 'Character has fundamentally changed'
		};
		return descriptions[beat] || beat;
	}

	function getBeatColor(beat: StoryCircleBeat): string {
		const colors = {
			'you': 'bg-blue-100 text-blue-800',
			'need': 'bg-purple-100 text-purple-800',
			'go': 'bg-red-100 text-red-800',
			'search': 'bg-yellow-100 text-yellow-800',
			'find': 'bg-green-100 text-green-800',
			'take': 'bg-orange-100 text-orange-800',
			'return': 'bg-indigo-100 text-indigo-800',
			'change': 'bg-pink-100 text-pink-800'
		};
		return colors[beat] || 'bg-gray-100 text-gray-800';
	}

	function getStatusColor(status: string): string {
		const colors = {
			'processing': 'text-blue-600 bg-blue-50',
			'completed': 'text-green-600 bg-green-50',
			'error': 'text-red-600 bg-red-50'
		};
		return colors[status] || 'text-gray-600 bg-gray-50';
	}

	async function exportBible(bibleId: string) {
		try {
			await tableReadStore.exportBible(bibleId, exportFormat, includeAudio);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Export failed';
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleString();
	}

	$: if (currentSession?.status === 'completed' && currentSession.results) {
		currentBible = currentSession.results;
	}
</script>

<div class="table-read-view bg-gray-50 min-h-screen">
	<!-- Header -->
	<div class="bg-white shadow-sm border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="py-4">
				<h1 class="text-3xl font-bold text-gray-900">Digital Table Read</h1>
				<p class="text-gray-600 mt-1">AI-powered script analysis using Dan Harmon's Story Circle</p>
			</div>
		</div>
	</div>

	<!-- Navigation Tabs -->
	<div class="bg-white border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<nav class="flex space-x-8">
				{#each [
					{ id: 'create', label: 'Create Analysis' },
					{ id: 'sessions', label: 'Sessions' },
					{ id: 'results', label: 'Results' }
				] as tab}
					<button
						class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === tab.id 
							? 'border-blue-500 text-blue-600' 
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
						on:click={() => activeTab = tab.id}
					>
						{tab.label}
					</button>
				{/each}
			</nav>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error Display -->
		{#if error}
			<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
				<div class="flex">
					<div class="text-red-700">{error}</div>
					<button
						class="ml-auto text-red-600 hover:text-red-800"
						on:click={() => error = null}
					>×</button
				>
				</div>
			</div>
		{/if}

		<!-- Loading -->
		{#if loading}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			</div>
		{/if}

		<!-- Create Analysis Tab -->
		{#if activeTab === 'create'}
			<div class="bg-white rounded-lg shadow p-6" transition:fade>
				<h2 class="text-2xl font-bold text-gray-900 mb-6">Create New Analysis</h2>

				<form on:submit|preventDefault={createTableRead} class="space-y-6">
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-2">Script Content</label>
						<textarea
							bind:value={formData.script_content}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							rows={12}
							placeholder="Paste your script here..."
							required
						></textarea>
						<p class="text-sm text-gray-500 mt-1">Include scene headings, character names, and dialogue</p>
					</div>

					<div class="grid grid-cols-2 gap-6">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Analysis Depth</label>
							<select
								bind:value={formData.analysis_depth}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							>
								<option value="basic">Basic - Quick overview</option>
								<option value="comprehensive">Comprehensive - Detailed analysis</option>
								<option value="deep">Deep - In-depth exploration</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Focus Areas</label>
							<div class="space-y-2">
								{#each [
									{ value: 'characters', label: 'Character Analysis' },
									{ value: 'structure', label: 'Story Structure' },
									{ value: 'themes', label: 'Themes & Motifs' },
									{ value: 'dialogue', label: 'Dialogue Patterns' },
									{ value: 'visual', label: 'Visual Style' }
								] as area}
									<label class="flex items-center">
										<input
											type="checkbox"
											bind:group={formData.focus_areas}
											value={area.value}
											class="mr-2"
										/>
										{area.label}
									</label>
								{/each}
							</div>
						</div>
					</div>

					<div class="flex justify-end">
						<button
							type="submit"
							class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
							disabled={loading}
						>
							{loading ? 'Creating Analysis...' : 'Start Analysis'}
						</button>
					</div>
				</form>
			</div>
		{/if}

		<!-- Sessions Tab -->
		{#if activeTab === 'sessions'}
			<div class="space-y-4" transition:fade>
				<div class="flex justify-between items-center mb-4">
					<h2 class="text-2xl font-bold text-gray-900">Analysis Sessions</h2>
					<button
						class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
						on:click={loadSessions}
					>
						Refresh
					</button>
				</div>

				{#if sessions.length === 0}
					<div class="bg-white rounded-lg shadow p-8 text-center">
						<p class="text-gray-500">No analysis sessions found. Create your first analysis!</p>
					</div>
				{:else}
					<div class="grid gap-4">
						{#each sessions as session}
							<div class="bg-white rounded-lg shadow p-6" transition:slide>
								<div class="flex justify-between items-start mb-4">
									<div>
										<h3 class="text-lg font-semibold text-gray-900">Session {session.session_id.slice(0, 8)}...</h3>
										<p class="text-sm text-gray-500">{formatDate(session.started_at)}</p>
									</div>
									<span class={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
										{session.status}
									</span>
								</div>

								{#if session.status === 'processing'}
									<div class="mb-4">
										<div class="flex justify-between text-sm text-gray-600 mb-1">
											<span>{session.current_analysis}</span>
											<span>{Math.round(session.progress * 100)}%</span>
										</div>
										<div class="w-full bg-gray-200 rounded-full h-2">
											<div
												class="bg-blue-600 h-2 rounded-full transition-all duration-300"
												style="width: {session.progress * 100}%"
											></div>
										</div>
									</div>
									<button
										class="text-blue-600 hover:text-blue-800 text-sm"
										on:click={() => refreshSession(session.session_id)}
									>
										Refresh Status
									</button>
								{:else if session.status === 'completed' && session.results}
									<div class="flex space-x-2">
										<button
											class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
											on:click={() => loadBible(session.bible_id)}
										>
											View Bible
										</button>
										<button
											class="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
											on:click={() => {
												exportFormat = 'pdf';
												showExportModal = true;
											}}
										>
											Export
										</button>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}

		<!-- Results Tab -->
		{#if activeTab === 'results' && currentBible}
			<div class="space-y-6" transition:fade>
				<!-- Bible Header -->
				<div class="bg-white rounded-lg shadow p-6">
					<h2 class="text-2xl font-bold text-gray-900 mb-2">{currentBible.title}</h2>
					<p class="text-gray-600 mb-4">{currentBible.logline}</p>
					<div class="grid grid-cols-4 gap-4 text-sm">
						<div class="bg-gray-50 p-3 rounded">
							<span class="font-semibold">Characters:</span> {Object.keys(currentBible.character_bios).length}
						</div>
						<div class="bg-gray-50 p-3 rounded">
							<span class="font-semibold">Scenes:</span> {currentBible.scene_analyses.length}
						</div>
						<div class="bg-gray-50 p-3 rounded">
							<span class="font-semibold">Genre:</span> {currentBible.genre_analysis}
						</div>
						<div class="bg-gray-50 p-3 rounded">
							<span class="font-semibold">Tone:</span> {currentBible.tone_description}
						</div>
					</div>
				</div>

				<!-- Story Circle Visualization -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex justify-between items-center mb-4">
						<h3 class="text-lg font-semibold">Story Circle Analysis</h3>
						<button
							class="text-blue-600 hover:text-blue-800 text-sm"
							on:click={() => showStoryCircleModal = true}
						>
							View Full Circle
						</button>
					</div>
					<div class="grid grid-cols-4 gap-4">
						{#each Object.entries(currentBible.story_circle.beats) as [beat, scenes]}
							<div
								class="border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
								on:click={() => selectedBeat = beat as StoryCircleBeat}
							>
								<div class={`text-xs font-medium px-2 py-1 rounded mb-2 ${getBeatColor(beat as StoryCircleBeat)}`}>
									{beat.toUpperCase()}
								</div>
								<p class="text-sm text-gray-600">{formatBeatDescription(beat as StoryCircleBeat)}</p>
								<p class="text-xs text-gray-500 mt-1">{scenes.length} scenes</p>
							</div>
						{/each}
					</div>
				</div>

				<!-- Characters Grid -->
				<div class="bg-white rounded-lg shadow p-6">
					<h3 class="text-lg font-semibold mb-4">Character Analysis</h3>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{#each Object.entries(currentBible.character_bios) as [name, character]}
							<div
								class="border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
								on:click={() => selectCharacter(character)}
							>
								<h4 class="font-semibold text-gray-900">{name}</h4>
								<p class="text-sm text-gray-600">{character.archetype}</p>
								<p class="text-xs text-gray-500 mt-1">{character.character_arc}</p>
							</div>
						{/each}
					</div>
				</div>

				<!-- Scenes List -->
				<div class="bg-white rounded-lg shadow p-6">
					<h3 class="text-lg font-semibold mb-4">Scene Analysis</h3>
					<div class="space-y-4">
						{#each currentBible.scene_analyses as scene}
							<div
								class="border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
								on:click={() => selectScene(scene)}
							>
								<div class="flex justify-between items-start">
									<div>
										<h4 class="font-semibold">{scene.scene_heading}</h4>
										<p class="text-sm text-gray-600">{scene.synopsis}</p>
									</div>
									<div class={`text-xs px-2 py-1 rounded ${getBeatColor(scene.story_circle_beat)}`}>
										{scene.story_circle_beat.toUpperCase()}
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{:else if activeTab === 'results' && !currentBible}
			<div class="bg-white rounded-lg shadow p-8 text-center">
				<p class="text-gray-500">No bible loaded. Select a completed session from the Sessions tab.</p>
			</div>
		{/if}
	</div>

	<!-- Modals -->
	{#if showCharacterModal && selectedCharacter}
		<!-- Character Detail Modal -->
		<!-- Implementation would go here -->
	{/if}

	{#if showSceneModal && selectedScene}
		<!-- Scene Detail Modal -->
		<!-- Implementation would go here -->
	{/if}

	{#if showStoryCircleModal}
		<!-- Story Circle Visualization Modal -->
		<!-- Implementation would go here -->
	{/if}

	{#if showExportModal}
		<!-- Export Modal -->
		<!-- Implementation would go here -->
	{/if}
</div>

<style>
	.table-read-view {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}
</style>