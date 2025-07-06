<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import FileUpload from './FileUpload.svelte';

  const dispatch = createEventDispatcher();

  let step = 1;
  let characterName = '';
  let description = '';
  let baseFaceFile: File | null = null;
  let loraFiles: File[] = [];
  let voiceFile: File | null = null;

  // Handle base face selection
  function handleBaseFaceSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      baseFaceFile = input.files[0];
    }
  }

  // Handle voice file selection
  function handleVoiceSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      voiceFile = input.files[0];
    }
  }

  // Handle next step
  function nextStep() {
    if (step === 1 && characterName.trim()) {
      step = 2;
    }
  }

  // Handle upload
  function handleUpload() {
    if (!characterName.trim() || !baseFaceFile) return;

    dispatch('upload', {
      characterName: characterName.trim(),
      description: description.trim(),
      baseFace: baseFaceFile,
      loras: loraFiles,
      voice: voiceFile
    });
  }

  function handleCancel() {
    dispatch('close');
  }
</script>

<div class="dialog-backdrop" on:click={handleCancel}>
  <div class="dialog" on:click|stopPropagation>
    <div class="dialog-header">
      <h2>Add Character</h2>
      <button class="close-btn" on:click={handleCancel} aria-label="Close"> × </button>
    </div>

    <div class="dialog-content">
      {#if step === 1}
        <div class="step-content">
          <h3>Character Details</h3>

          <div class="form-group">
            <label for="name">Character Name *</label>
            <input
              id="name"
              type="text"
              bind:value={characterName}
              placeholder="e.g., Sarah Connor"
              autofocus
            />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              bind:value={description}
              placeholder="Brief description of the character"
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="baseFace">Base Face Image *</label>
            <input
              id="baseFace"
              type="file"
              accept=".png,.jpg,.jpeg"
              on:change={handleBaseFaceSelect}
            />
            {#if baseFaceFile}
              <p class="file-selected">Selected: {baseFaceFile.name}</p>
            {/if}
            <p class="help-text">Upload a clear, front-facing photo of the character</p>
          </div>
        </div>
      {:else}
        <div class="step-content">
          <h3>Optional Assets for {characterName}</h3>

          <div class="asset-section">
            <h4>LoRA Models</h4>
            <p class="section-desc">Upload LoRA models for different character variations</p>
            <FileUpload
              category="character"
              acceptedTypes={['.safetensors', '.pt', '.pth']}
              multiple={true}
              metadata={{
                character_name: characterName,
                is_lora: true
              }}
              on:uploaded={(e) => (loraFiles = e.detail.files)}
            />
          </div>

          <div class="asset-section">
            <h4>Voice Model</h4>
            <p class="section-desc">Upload RVC voice model for character dialogue</p>
            <input type="file" accept=".pth,.pt" on:change={handleVoiceSelect} />
            {#if voiceFile}
              <p class="file-selected">Selected: {voiceFile.name}</p>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <div class="dialog-footer">
      {#if step === 1}
        <button class="btn" on:click={handleCancel}> Cancel </button>
        <button
          class="btn btn-primary"
          on:click={nextStep}
          disabled={!characterName.trim() || !baseFaceFile}
        >
          Next
        </button>
      {:else}
        <button class="btn" on:click={() => (step = 1)}> Back </button>
        <button class="btn btn-primary" on:click={handleUpload}> Create Character </button>
      {/if}
    </div>
  </div>
</div>

<style>
  .dialog-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .dialog {
    background: var(--surface);
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .dialog-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: var(--text-secondary);
    cursor: pointer;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: var(--border-color);
    color: var(--text-primary);
  }

  .dialog-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
  }

  .step-content h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.125rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  input[type='text'],
  input[type='file'],
  textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: var(--background);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    transition: border-color 0.2s;
  }

  input:focus,
  textarea:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  textarea {
    resize: vertical;
    min-height: 60px;
  }

  .help-text {
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .file-selected {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--success-color);
  }

  .asset-section {
    margin-bottom: 2rem;
    padding: 1rem;
    background: var(--background);
    border-radius: 0.5rem;
  }

  .asset-section h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
  }

  .section-desc {
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
    background: var(--background);
  }
</style>
