<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { collaborationService } from '$lib/canvas/services/collaboration';
  import { canvasStore } from '$lib/canvas/core/canvas-store';

  export let projectId: string;
  export let isOpen = true;

  let newMessage = '';
  let isExpanded = true;

  $: collaborationState = $collaborationService.store;
  $: users = $collaborationState.users;
  $: messages = $collaborationState.messages;
  $: cursors = $collaborationState.cursors;
  $: isConnected = $collaborationState.isConnected;

  onMount(() => {
    collaborationService.connect(projectId);

    // Subscribe to canvas changes for collaboration
    const unsubscribe = canvasStore.subscribe(state => {
      if (state.nodes.length > 0 || state.edges.length > 0) {
        // Send canvas updates to collaboration service
        collaborationService.sendCanvasUpdate({
          action: 'update',
          nodes: state.nodes,
          edges: state.edges
        });
      }
    });

    return () => {
      unsubscribe();
      collaborationService.disconnect();
    };
  });

  function sendMessage() {
    if (newMessage.trim()) {
      collaborationService.sendChat(newMessage.trim());
      newMessage = '';
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function formatTime(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString();
  }

  function getUserColor(userId: string): string {
    const user = users.find(u => u.userId === userId);
    return user?.color || '#6b7280';
  }
</script>

<div class="collaboration-panel bg-white border-l border-gray-200 flex flex-col {isOpen ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden">
  <div class="p-4 border-b border-gray-200">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-sm font-semibold text-gray-900">Collaboration</h3>
      <button
        on:click={() => isExpanded = !isExpanded}
        class="text-gray-500 hover:text-gray-700"
      >
        <svg class="w-4 h-4 transform {isExpanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>

    <!-- Connection Status -->
    <div class="flex items-center space-x-2">
      <div class="w-2 h-2 rounded-full {isConnected ? 'bg-green-500' : 'bg-red-500'}"></div>
      <span class="text-xs text-gray-600">
        {isConnected ? `${users.length} users online` : 'Disconnected'}
      </span>
    </div>
  </div>

  {#if isExpanded}
    <!-- Users Section -->
    <div class="p-4 border-b border-gray-200">
      <h4 class="text-xs font-semibold text-gray-700 mb-2">Active Users</h4>
      <div class="space-y-1">
        {#each users as user}
          <div class="flex items-center space-x-2">
            <div
              class="w-2 h-2 rounded-full"
              style="background-color: {user.color}"
            ></div>
            <span class="text-xs text-gray-700 truncate">{user.userName}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Chat Section -->
    <div class="flex-1 flex flex-col min-h-0">
      <div class="flex-1 overflow-y-auto p-4 space-y-2">
        {#each messages as message}
          <div class="text-xs space-y-1">
            <div class="flex items-center space-x-1"
              <div
                class="w-2 h-2 rounded-full"
                style="background-color: {getUserColor(message.userId)}"
              ></div>
              <span class="font-medium text-gray-900">{message.userName}</span>
              <span class="text-gray-500">{formatTime(message.timestamp)}</span>
            </div>
            
            {#if message.type === 'chat'}
              <div class="text-gray-700 ml-3">{message.data.message}</div>
            {:else if message.type === 'canvas_update'}
              <div class="text-blue-600 ml-3">Updated canvas</div>
            {:else if message.type === 'user_joined'}
              <div class="text-green-600 ml-3">Joined the session</div>
            {:else if message.type === 'user_left'}
              <div class="text-red-600 ml-3">Left the session</div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Message Input -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex space-x-2">
          <input
            type="text"
            bind:value={newMessage}
            on:keydown={handleKeyPress}
            placeholder="Type a message..."
            class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!isConnected}
          />
          <button
            on:click={sendMessage}
            disabled={!isConnected || !newMessage.trim()}
            class="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .collaboration-panel {
    height: 100%;
  }
</style>