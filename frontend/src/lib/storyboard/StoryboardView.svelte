<script lang="ts">
	import { onMount } from 'svelte';
	import type { StoryboardSequence, StoryboardShot, StoryboardFrame } from '$lib/types/storyboard';
	import { storyboardStore } from '$lib/stores/storyboardStore';

	export let projectId: string;
	export let sceneId: string;

	let sequence: StoryboardSequence | null = null;
	let loading = true;
	let error: string | null = null;
	let selectedShot: StoryboardShot | null = null;
	let selectedFrame: StoryboardFrame | null = null;

	// UI state
	let showFrameEditor = false;
	let showShotEditor = false;
	let showPrevisGenerator = false;
	let generationProgress = 0;

	// Form data for new frame
	let newFrameData = {
		description: '',
		camera_angle: 'eye_level',
		camera_movement: 'static',
		composition: 'medium',
		focal_length: 35
	};

	// Form data for new shot
	let newShotData = {
		shot_type: '',
		duration: 3.0,
		camera_setup: {},
		lighting_setup: {}
	};

	onMount(async () => {
		await loadSequence();
	});

	async function loadSequence() {
		try {
			loading = true;
			sequence = await storyboardStore.getSequence(projectId, sceneId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load sequence';
		} finally {
			loading = false;
		}
	}

	async function createSequence() {
		try {
			loading = true;
			sequence = await storyboardStore.createSequence(projectId, sceneId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create sequence';
		} finally {
			loading = false;
		}
	}

	async function addShot() {
		if (!sequence) return;
		
		try {
			await storyboardStore.addShot(sequence.sequence_id, newShotData);
			await loadSequence();
			showShotEditor = false;
			newShotData = { shot_type: '', duration: 3.0, camera_setup: {}, lighting_setup: {} };
		} catch (err) {
			console.error('Failed to add shot:', err);
		}
	}

	async function addFrame(shot: StoryboardShot) {
		try {
			await storyboardStore.addFrame(sequence!.sequence_id, shot.shot_id, newFrameData);
			await loadSequence();
			showFrameEditor = false;
			newFrameData = {
				description: '',
				camera_angle: 'eye_level',
				camera_movement: 'static',
				composition: 'medium',
				focal_length: 35
			};
		} catch (err) {
			console.error('Failed to add frame:', err);
		}
	}

	async function updateFrame(frame: StoryboardFrame) {
		if (!selectedShot) return;
		
		try {
			await storyboardStore.updateFrame(
				sequence!.sequence_id,
				selectedShot.shot_id,
				frame.frame_id,
				frame
			);
			await loadSequence();
		} catch (err) {
			console.error('Failed to update frame:', err);
		}
	}

	async function generatePrevis() {
		if (!sequence) return;
		
		showPrevisGenerator = true;
		generationProgress = 0;
		
		try {
			const result = await storyboardStore.generatePrevis(sequence.sequence_id);
			
			// Simulate progress updates
			const interval = setInterval(() => {
				generationProgress = Math.min(generationProgress + 10, 100);
				if (generationProgress >= 100) {
					clearInterval(interval);
					showPrevisGenerator = false;
				}
			}, 500);
			
		} catch (err) {
			console.error('Failed to generate pre-vis:', err);
			showPrevisGenerator = false;
		}
	}

	function selectShot(shot: StoryboardShot) {
		selectedShot = shot;
		selectedFrame = null;
	}

	function selectFrame(frame: StoryboardFrame, shot: StoryboardShot) {
		selectedFrame = frame;
		selectedShot = shot;
	}

	function formatDuration(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	function getStatusColor(status: string): string {
		const colors = {
			'concept': 'bg-gray-500',
			'sketch': 'bg-blue-500',
			'draft': 'bg-yellow-500',
			'finalized': 'bg-green-500',
			'approved': 'bg-purple-500',
			'generated': 'bg-indigo-500'
		};
		return colors[status] || 'bg-gray-500';
	}
</script>

<div class="storyboard-view bg-gray-50 min-h-screen p-6">
	{#if loading}
		<div class="flex justify-center items-center h-64">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-gray-600">Loading storyboard...</span>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
			<h3 class="font-semibold mb-2">Error</h3>
			<p>{error}</p>
			<button 
				class="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
				on:click={loadSequence}
			>
				Retry
			</button>
		</div>
	{:else if !sequence}
		<div class="bg-white rounded-lg shadow p-8 text-center">
			<h2 class="text-2xl font-bold text-gray-900 mb-4">No Storyboard Found</h2>
			<p class="text-gray-600 mb-6">Create a storyboard sequence for this scene</p>
			<button
				class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
				on:click={createSequence}
			>
				Create Storyboard
			</button>
		</div>
	{:else}
		<!-- Storyboard Header -->
		<div class="bg-white rounded-lg shadow mb-6 p-6">
			<div class="flex justify-between items-center mb-4">
				<div>
					<h1 class="text-2xl font-bold text-gray-900">{sequence.sequence_name}</h1>
					<p class="text-gray-600">Scene {sequence.scene_breakdown?.scene_number || sceneId} - {sequence.scene_breakdown?.scene_heading || ''}</p>
				</div>
				<div class="flex space-x-2">
					<button
						class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
						on:click={() => showShotEditor = true}
					>
						Add Shot
					</button>
					<button
						class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
						on:click={generatePrevis}
					>
						Generate Pre-vis
					</button>
				</div>
			</div>
			
			<div class="grid grid-cols-4 gap-4 text-sm">
				<div class="bg-gray-100 p-3 rounded">
					<span class="font-semibold">Shots:</span> {sequence.get_shot_count()}
				</div>
				<div class="bg-gray-100 p-3 rounded">
					<span class="font-semibold">Frames:</span> {sequence.get_frame_count()}
				</div>
				<div class="bg-gray-100 p-3 rounded">
					<span class="font-semibold">Duration:</span> {formatDuration(sequence.total_duration)}
				</div>
				<div class="bg-gray-100 p-3 rounded">
					<span class="font-semibold">Aspect Ratio:</span> {sequence.aspect_ratio}
				</div>
			</div>
		</div>

		<!-- Storyboard Timeline -->
		<div class="bg-white rounded-lg shadow mb-6 p-6">
			<h2 class="text-xl font-semibold mb-4">Storyboard Timeline</h2>
			
			<div class="space-y-4">
				{#each sequence.shots as shot, index}
					<div 
						class="border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md {selectedShot === shot ? 'ring-2 ring-blue-500' : ''}"
						on:click={() => selectShot(shot)}
					>
						<div class="flex justify-between items-start mb-2">
							<div>
								<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
									Shot {shot.shot_number}
								</span>
								<span class="ml-2 text-sm text-gray-600">{shot.shot_type || 'Standard'}</span>
							</div>
							<span class="text-sm text-gray-500">{formatDuration(shot.duration)}</span>
						</div>
						
						<div class="grid grid-cols-4 gap-2 mt-3">
							{#each shot.frames as frame}
								<div
									class="border rounded aspect-video bg-gray-100 flex items-center justify-center text-xs text-gray-500 cursor-pointer transition-all hover:ring-2 hover:ring-blue-300 {selectedFrame === frame ? 'ring-2 ring-blue-500' : ''}"
									on:click={() => selectFrame(frame, shot)}
								>
									<div class="text-center">
										<div>Frame {frame.frame_number}</div>
										<div class="text-xs text-gray-400 mt-1">{frame.description || 'Untitled'}</div>
									</div>
								</div>
							{/each}
							
							<button
								class="border-2 border-dashed border-gray-300 rounded aspect-video flex items-center justify-center text-gray-400 hover:border-gray-400 transition-colors"
								on:click={() => { selectedShot = shot; showFrameEditor = true; }}
							>
								<div class="text-center">
									<div class="text-2xl">+</div>
									<div class="text-xs">Add Frame</div>
								</div>
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Selected Frame Details -->
		{#if selectedFrame && selectedShot}
			<div class="bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold mb-4">Frame Details</h2>
				
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
						<textarea
							bind:value={selectedFrame.description}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							rows={3}
							on:blur={() => updateFrame(selectedFrame)}
						></textarea>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Camera Angle</label>
						<select
							bind:value={selectedFrame.camera_angle}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							on:change={() => updateFrame(selectedFrame)}
						>
							<option value="eye_level">Eye Level</option>
							<option value="high_angle">High Angle</option>
							<option value="low_angle">Low Angle</option>
							<option value="dutch_angle">Dutch Angle</option>
							<option value="overhead">Overhead</option>
						</select>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Camera Movement</label>
						<select
							bind:value={selectedFrame.camera_movement}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							on:change={() => updateFrame(selectedFrame)}
						>
							<option value="static">Static</option>
							<option value="pan">Pan</option>
							<option value="tilt">Tilt</option>
							<option value="track">Track</option>
							<option value="dolly">Dolly</option>
							<option value="crane">Crane</option>
						</select>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Composition</label>
						<select
							bind:value={selectedFrame.composition}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							on:change={() => updateFrame(selectedFrame)}
						>
							<option value="wide">Wide</option>
							<option value="medium">Medium</option>
							<option value="closeup">Close-up</option>
							<option value="two_shot">Two-shot</option>
							<option value="over_shoulder">Over-shoulder</option>
						</select>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Focal Length (mm)</label>
						<input
							type="number"
							bind:value={selectedFrame.focal_length}
							min="14"
							max="200"
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							on:change={() => updateFrame(selectedFrame)}
						/>
					</div>
				</div>
			</div>
		{/if}
	{/if}

	<!-- Frame Editor Modal -->
	{#if showFrameEditor && selectedShot}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
			on:click={() => showFrameEditor = false}
		>
			<div class="bg-white rounded-lg p-6 w-full max-w-md" on:click|stopPropagation>
				<h3 class="text-lg font-semibold mb-4">Add New Frame</h3>
				
				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium text-gray-700">Description</label>
						<textarea
							bind:value={newFrameData.description}
							class="w-full px-3 py-2 border border-gray-300 rounded-md"
							rows={3}
						></textarea>
					</div>
					
					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700">Camera Angle</label>
							<select bind:value={newFrameData.camera_angle} class="w-full px-3 py-2 border border-gray-300 rounded-md">
								<option value="eye_level">Eye Level</option>
								<option value="high_angle">High Angle</option>
								<option value="low_angle">Low Angle</option>
							</select>
						</div>
						
						<div>
							<label class="block text-sm font-medium text-gray-700">Composition</label>
							<select bind:value={newFrameData.composition} class="w-full px-3 py-2 border border-gray-300 rounded-md">
								<option value="wide">Wide</option>
								<option value="medium">Medium</option>
								<option value="closeup">Close-up</option>
							</select>
						</div>
					</div>
				</div>
				
				<div class="flex space-x-3 mt-6">
					<button
						class="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
						on:click={() => { addFrame(selectedShot); showFrameEditor = false; }}
					>
						Add Frame
					</button>
					<button
						class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
						on:click={() => showFrameEditor = false}
					>
						Cancel
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Pre-vis Generation Modal -->
	{#if showPrevisGenerator}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white rounded-lg p-6 w-full max-w-md">
				<h3 class="text-lg font-semibold mb-4">Generating Pre-visualization</h3>
				
				<div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
					<div 
						class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
						style="width: {generationProgress}%"
					></div>
				</div>
				
				<p class="text-center text-gray-600">{generationProgress}% Complete</p>
			</div>
		</div>
	{/if}
</div>

<style>
	.storyboard-view {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}
</style>