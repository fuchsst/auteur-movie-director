

# **Refined Product Requirements: A Unified Specification for the Generative Media Studio**

## **Section 1: Product Vision and Strategic Foundation**

This document provides the definitive Product Requirements Document (PRD) for the Generative Media Studio. It synthesizes architectural blueprints with an analysis of the generative AI technology landscape to establish a comprehensive set of functional and non-functional requirements. This PRD will serve as the master specification for all product development and engineering efforts.

### **1.1 The Strategic Imperative: From Monolith to Scalable Web Service**

The foundational strategic decision for the product is a departure from traditional, monolithic creative software paradigms. The original concept, tied to a local desktop environment like Blender, presented inherent limitations in accessibility, scalability, and maintainability.1 To overcome these constraints and unlock the platform's full potential, the product's architecture is mandated to be a decoupled client-server application.

**Requirement:** The product shall be architected as a decoupled client-server application, cleanly separating the user-facing interface (the "Client") from the backend generative engine (the "Server").

The rationale for this architectural mandate is multi-faceted and forms the cornerstone of the product's competitive advantage. It directly addresses the primary weaknesses of desktop-bound creative tools. By separating the client from the server, the system is transformed from a single-user, single-machine utility into a potential collaborative, enterprise-grade platform. This fundamental shift is not merely a technical choice but a strategic one, designed to maximize the product's reach, power, and long-term viability.1 The client, a web application built with SvelteKit, becomes a universally accessible "Production Canvas," while the backend, a distributed Python system, functions as a powerful, scalable "Generative Engine."

### **1.2 Core Value Propositions**

This strategic architecture directly enables the product's core value propositions:

* **Accessibility:** The product must be accessible via any modern web browser on any operating system. This requirement eliminates the need for users to install specific, high-end desktop software such as Blender, dramatically lowering the barrier to entry and expanding the potential user base beyond specialized professionals to a wider creative audience.1  
* **Scalability:** The product's performance and generative capacity must not be limited by the user's local hardware. The backend architecture, built upon a distributed system of Celery workers, allows for the independent, horizontal scaling of computational resources. As a project's demands increase, more generative workers can be allocated to the backend without any change to the client experience, ensuring that the platform can handle projects of any scale.1  
* **Extensibility:** The product must be designed to be future-proof. The generative AI field is characterized by rapid, continuous innovation. The architecture must be modular and extensible, capable of rapidly integrating new and diverse generative models as they emerge from the open-source community and research labs.

### **1.3 The "Function Runner" as a Strategic Moat**

The architectural pattern of a containerized "Function Runner" backend is more than a technical implementation detail; it is the product's core strategic advantage in a rapidly evolving and fragmenting AI landscape.1

An analysis of the current technology landscape reveals a vast and growing ecosystem of powerful but heterogeneous models. Tools like FlexiAct for action transfer 2, Fantasy-Talking for talking head generation 3, and LayerFlow for layer-aware video 4 each offer unique capabilities but come with their own distinct dependencies, execution environments, and command-line interfaces. A monolithic application architecture would face immense challenges in attempting to integrate this diversity, inevitably leading to "dependency hell," complex engineering efforts, and slow integration cycles for new technologies.

The proposed architecture elegantly sidesteps this entire class of problems. By treating each external generative model as a self-contained, containerized microservice, the system creates a standardized interface for what is otherwise a chaotic ecosystem. The execute\_shot\_node Celery task does not need to understand the internal workings of a model like FlexiAct; it only needs to know how to invoke the corresponding Docker container with the correct parameters.1

This creates a powerful strategic moat. The product's ability to offer cutting-edge features is no longer constrained by the complexity of its core codebase but is instead a function of its ability to "wrap" new models in a standardized container. While competitors may need to re-engineer their core products to support a new breakthrough model, this platform can integrate it by simply building a new Docker image and defining a corresponding PipelineNode in the UI. This modularity and speed of integration will be a decisive competitive advantage.

**Product Implication:** The process of integrating a new generative model shall be treated as a first-class development workflow. The product roadmap must include the development of tooling, documentation, and potentially a software development kit (SDK) to streamline the process of packaging new external models into system-compatible PipelineNode definitions and their associated containerized backends.

## **Section 2: The Project Workspace: Requirements for Data Organization and Management**

The physical organization of data on the file system is a foundational architectural decision that dictates the application's maintainability, scalability, and usability for both human artists and automated processes.1 The requirements in this section translate the detailed file-system architecture into concrete product features, defining how users and the system interact with project data.

### **2.1 The Workspace/Project Dichotomy**

Drawing inspiration from professional creative studio workflows, the application's data model must be structured on a two-tiered hierarchy that separates shared, reusable resources from discrete, individual units of work.1

**Requirement:** The application shall implement a two-tiered data model: a global Workspace for shared resources and self-contained Projects for individual creative endeavors.

* **Workspace:** The Workspace represents the highest-level container, the digital equivalent of the entire studio. It is responsible for housing resources that are shared and reused across multiple projects. This includes a global /Library/ directory containing subfolders for Branding assets (logos, fonts), Stock\_Media (licensed music, SFX), and, critically for a generative workflow, Pipeline\_Templates. These templates are reusable backend configurations, such as ComfyUI API-formatted JSON files, that correspond to PipelineNode definitions in the UI, allowing complex generative techniques to be standardized and reused.1  
* **Project:** In contrast, a Project is a discrete, self-contained, and portable unit of work. Each project folder represents a single creative piece and is designed to be its own universe, containing all specific assets, source files, configurations, and generated outputs required for that one production. A project must be able to be moved, archived, or shared as a single entity without breaking its internal dependencies.1

### **2.2 Automated Project Scaffolding**

The rigor and consistency of the project file structure are paramount to the reliability of the automated backend. This consistency cannot be left to user discipline.

**Requirement:** The "New Project" function within the user interface must programmatically generate the complete, standardized directory structure for every new project. Users shall never be required to create this structure manually.

This requirement is critical. Manual creation is not only tedious but is guaranteed to introduce errors and inconsistencies that would break the "contract" relied upon by the backend services.1 The automated scaffolding process is a core feature that ensures every project starts from a known, correct, and consistent state. This process shall perform the following sequence of operations upon project creation:

1. Create the main project directory (e.g., /Projects/PROJECT\_NAME/).  
2. Create all numbered subdirectories (01\_Assets, 02\_Source\_Creative, etc.) and their nested folders as specified in the architecture.  
3. Generate the project.json manifest file, populating it with a new UUID and user-provided metadata (title, description).  
4. Copy the standard .gitignore and .gitattributes template files into the project root.  
5. Initialize a new Git repository in the project root (git init).  
6. Perform an initial commit to save the foundational structure and configuration files to the project's version history.1

### **2.3 The Project Manifest: project.json**

At the heart of each project is a machine-readable manifest that serves as its official identity card and the primary entry point for the application's programmatic interactions.

**Requirement:** Every project shall contain a project.json file at its root.

This file acts as the authoritative index, providing the agentic framework with the stable, machine-parsable information it needs to locate assets and execute tasks reliably.1 The schema for this JSON file must contain the following keys:

* uuid: A programmatically generated, universally unique identifier for the project. This is the project's immutable primary key.  
* title: A human-readable project title provided by the user.  
* description: A detailed, user-provided description of the project.  
* canvas\_path: A relative path pointing to the main Production Canvas file for the project (e.g., 02\_Source\_Creative/Canvases/main\_canvas.json).  
* project\_settings: An object containing project-wide default parameters. This must include:  
  * aspect\_ratio: The default aspect ratio for renders (e.g., "16:9").  
  * quality: The project-wide quality setting, an enum of "low", "standard", or "high", which dictates the selection of backend pipelines.1  
* version: An integer used for optimistic locking to manage state and prevent conflicts in future collaborative workflows.1

### **Table 1: Project Directory Structure and Rationale**

The following table provides the single, authoritative reference for the physical layout of project data. This structure serves as the API contract for all backend services, ensuring that automated processes can deterministically locate inputs and outputs. It explicitly links directory paths to their purpose and versioning strategy, eliminating ambiguity for the engineering team.

| Path | Purpose | Example Contents | Version Control Strategy | Rationale |
| :---- | :---- | :---- | :---- | :---- |
| project.json | Project Manifest | { "uuid": "...", "title": "..." } | Standard Git | The core, text-based definition of the project. Essential for versioning creative intent and metadata.1 |
| 01\_Assets/ | Raw Source Materials | Subdirectories for media, models | \- | Top-level container for all project inputs.1 |
| .../Source\_Media/ | Raw camera/audio files | A001C002\_240101.mxf | Git LFS | Large binary files that are the ultimate source of truth for captured media.1 |
| .../AI\_Models/ | Project-specific models | sdxl\_base\_1.0.safetensors | Git LFS | Large binary model files that are foundational to the project's generative process.1 |
| .../Generative\_Assets/ | Reusable creative entities | Subdirectories for characters, styles | \- | Organizes the physical files that constitute the abstract "Generative Assets".1 |
| 02\_Source\_Creative/ | Human-edited creative files | Subdirectories for canvases, scripts | \- | The "source code" of the film. These files define what will be generated.1 |
| .../Canvases/ | Production Canvas graphs | main\_canvas.json | Standard Git | Small, text-based JSON files that define the entire generative workflow. Diffable and perfect for Git.1 |
| .../Scripts/ | Narrative documents | screenplay\_v3.txt | Standard Git | Text-based documents that track the narrative development of the project.1 |
| 03\_Renders/ | Generated Media ("Takes") | SCENE\_01/SHOT\_010/SHOT-010\_v01\_take01.mp4 | Git LFS | Immutable, large binary outputs of the generative process. Versioned by filename.1 |
| 04\_Project\_Files/ | NLE/App-specific files | Auto\_Saves/, EDLs/ | Standard Git | Small, project-related metadata and interoperability files.1 |
| 05\_Cache/ | Transient/Temporary Data | thumbnails/, control\_maps/ | Ignore (in .gitignore) | Disposable data that can be regenerated. Excluding it prevents repository bloat.1 |
| 06\_Exports/ | Final Deliverables | Final\_Movie\_H264.mp4 | Ignore (in .gitignore) | Final outputs not considered part of the iterative creative process.1 |
| .gitignore | Git Ignore Rules | 05\_Cache/, 06\_Exports/, \*.DS\_Store | Standard Git | Defines what Git should not track, essential for repository health.1 |
| .gitattributes | Git LFS Rules | \*.png filter=lfs diff=lfs merge=lfs \-text | Standard Git | Defines the versioning strategy for binaries vs. text, critical for performance.1 |

## **Section 3: Non-Destructive Workflow: Requirements for Versioning and Iteration**

To ensure a reliable and auditable production history, the system must enable a non-destructive workflow where artists can iterate freely without fear of losing previous work. This section defines the product requirements for achieving this through a robust versioning strategy that leverages the Project-as-Repository model and Git LFS.

### **3.1 The Project-as-Repository Model**

To achieve maximum isolation, portability, and scalability, the architecture formally adopts a Project-as-Repository model.

**Requirement:** Every individual project directory created under /Projects/PROJECT\_NAME/ shall be initialized as its own independent Git repository.

This approach offers several distinct advantages over a single, monolithic repository for the entire workspace. It prevents the entire application's version history from becoming slow and unmanageable as more projects are added; Git operations like clone and log operate only on the scope of a single project, ensuring they remain fast.1 Each project's history is completely self-contained, simplifying change tracking. Most importantly, this model provides a natural and elegant pathway to a future multi-tenant system, where each tenant's collection of projects can be managed as a distinct set of repositories, a key strategic goal.1

### **3.2 Hybrid Versioning with Git LFS**

The product must handle a heterogeneous mix of small, text-based source files and large, multi-gigabyte binary media files. Standard Git is designed for the former, and fails catastrophically with the latter.1

**Requirement:** The system must use Git Large File Storage (LFS) for versioning all large binary files, including media assets (.mp4, .wav), AI models (.safetensors), and all rendered outputs. The use of LFS is mandatory, not an optional enhancement.

Git LFS resolves the core problem of repository bloat by replacing large files in the Git history with small, text-based pointer files. The actual binary data is stored in a separate, dedicated LFS store.1 This approach keeps the core repository lean and fast while still providing robust versioning for large assets. This is also the key technical enabler for future cloud deployment, as the LFS remote store can be configured to be an object storage bucket, such as Amazon S3.1

**Requirement:** The application shall perform a check on startup to ensure the user has the Git LFS client installed and configured. If LFS is not detected, the application must display a clear, actionable message guiding the user through the installation process. This is a critical safeguard to prevent repository corruption, which can occur if a user without LFS commits a large file directly.1

### **3.3 Intermediate Result Versioning ("Takes")**

A core tenet of the creative workflow is non-destructive iteration. The UI must provide a clear and intuitive mechanism for managing multiple versions of a single creative element, such as a shot.

**Requirement:** The user interface for the ShotNode must include a feature for managing "Takes," allowing a user to generate multiple versions of a shot, browse through them, and select an "active" take for use in the final sequence.

This "Takes" feature in the UI is not an abstract concept but a direct, one-to-one mapping to the immutable, versioned files physically present in the 03\_Renders/ directory. This symbiosis between the data structure and the UI is a cornerstone of the system's robustness. The architectural principle of "Immutability and Atomic Versioning" dictates that generated media files are never overwritten. When a new version of a shot is rendered, it is saved as a new, uniquely named file (e.g., SHOT-010\_v01\_take01.mp4, SHOT-010\_v01\_take02.png).1

The application logic must connect this file system reality to the user experience. The list of available "Takes" presented in the ShotNode UI is to be populated by programmatically scanning the contents of that specific shot's render directory (e.g., /Projects/MyFilm/03\_Renders/SCENE\_01/SHOT\_010/). When a user selects a different take in the UI, the internal state of the ShotNode is updated to point to the file path of the newly selected version. This tight coupling ensures that the file system remains the unambiguous, auditable source of truth for the project's entire generative history.

**Requirement:** The "Generate" action on a ShotNode shall always create a new take file with an incremented take number in its filename. It must never overwrite an existing file. The "Takes" list or dropdown in the UI must be populated by reading the contents of the corresponding render subdirectory.

## **Section 4: The Production Canvas: User Interface and Experience Requirements**

The frontend of the generative studio is a sophisticated, stateful web application responsible for delivering the entire user experience. This section details the requirements for this client-side application, built with SvelteKit and Svelte Flow, which together form the interactive "Production Canvas."

### **4.1 Core Canvas Functionality**

**Requirement:** The primary user interface shall be a node-based "Production Canvas" built using the Svelte Flow (@xyflow/svelte) library.1

The canvas is the user's creative workspace. It must provide a fluid and intuitive experience for visual programming. Core required features include:

* Standard node-graph interactions: adding nodes from a palette, deleting nodes, and creating connections (edges) between node sockets.  
* Canvas navigation: smooth panning and zooming of the entire graph.  
* State persistence: the ability to save the current graph state (nodes and edges) and load it upon reopening a project.  
* Client-side state management: The positions, connections, and internal data of all nodes and edges on the canvas shall be managed by a global Svelte writable store, projectStore.js, which will serve as the single source of truth for the client-side application state.1

### **4.2 State Management and Communication**

To create a real-time, responsive experience, the application must employ a modern communication protocol that avoids inefficient polling.

**Requirement:** All real-time, bidirectional communication between the SvelteKit client and the FastAPI server shall be managed over a single, persistent WebSocket connection, established on a per-project basis (e.g., at the endpoint /ws/{project\_id}).1

To ensure a fluid user experience even with network latency, the client will employ an "optimistic update" strategy for low-latency interactions like moving a node on the canvas. The Svelte UI will update its local state in the projectStore immediately, providing instant visual feedback to the user, and then asynchronously send the state change to the server via a WebSocket event. The server's database remains the ultimate single source of truth.1

The WebSocket client must be resilient. It shall include logic to automatically detect network disconnections and attempt to reconnect periodically. Upon a successful reconnection, it must emit a client:sync\_request event. The server, upon receiving this event, will respond with a server:full\_sync event containing the latest complete project state, ensuring the user's view is always brought back to a consistent and authoritative state.1

### **4.3 A Spectrum of Control: Flexible Node and Socket Definitions**

The generative AI landscape is not uniform. Different models require vastly different types of inputs and produce different outputs. A simple text-prompt node is insufficient for a truly versatile studio. The Production Canvas must be designed to accommodate this spectrum of control.

For example, a basic Text-to-Video model like LTX-Video requires a simple string input for its prompt.5 In contrast, an action transfer model like FlexiAct requires a

video input for the motion source and an image input for the target character.2 A layer-aware model like LayerFlow may require multiple

string inputs for foreground and background prompts 4, while a video restoration model like SeedVR2 requires a

video input to process.6

A one-size-fits-all PipelineNode cannot serve these diverse needs. This leads to a critical requirement for the system's extensibility.

**Requirement:** The system shall provide a flexible "Node API" or schema that allows for the definition of custom node types with custom input and output sockets. This schema must support a well-defined set of data types to act as the "contract" between nodes.

Supported socket data types shall include, at a minimum:

* **Primitives:** String, Integer, Float, Boolean.  
* **Media & Assets:** Image, Video, Audio, AssetReference (a UUID pointing to a Generative Asset).  
* **Control & Structural:** ControlMap (specialized images like depth maps), Mask (grayscale images for inpainting), PipelineReference (a UUID pointing to a backend pipeline definition), EDL (a string containing Edit Decision List data).1

This requirement ensures that the canvas can evolve into a rich and truly modular creative environment, capable of representing any generative workflow, no matter how complex.

### **Table 2: Production Canvas Node Specification**

The following table serves as the definitive guide for frontend developers, detailing the required UI components and their primary interactions. It translates abstract architectural concepts into concrete, buildable Svelte components and their expected behaviors.

| Node Type | Svelte Component | Key UI Elements | Supported Input Sockets | Supported Output Sockets | Primary Backend Interaction |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Shot Node** | ShotNode.svelte | Prompt textarea, "Generate" button, "Takes" list/dropdown, Thumbnail display, Progress indicator. | Pipeline (PipelineReference), Character (AssetReference), Style (AssetReference), Prompt (String), etc. | Output (Video/Image) | Triggers client:start\_generation WebSocket event with its own node data payload.1 |
| **Asset Node** | AssetNode.svelte | Asset preview image, Asset name label. | \- | Asset (AssetReference) | None directly. Acts as a data source for connected Shot Nodes.1 |
| **Pipeline Node** | PipelineNode.svelte | Pipeline name label, Version dropdown (optional). | \- | Pipeline (PipelineReference) | None directly. Provides the pipeline\_id for a Shot Node's generation task.1 |
| **Scene Group** | SceneGroupNode.svelte | Scene name label, Expand/Collapse button, Internal node canvas. | (Varies) | (Varies) | Acts as a container for subflows (nested graphs), enabling hierarchical organization.1 |
| **Motion Source** | MotionSourceNode.svelte | Video file input/preview. | Source Video (Video) | Motion Data (ControlMap) | Triggers a backend task to process a video (e.g., for FlexiAct 2) into a control map. |
| **Audio Source** | AudioNode.svelte | Audio file input/preview, Text input for TTS. | Source Audio (Audio), Text (String) | Audio | Triggers a backend task for TTS (e.g., F5-TTS 7) or provides audio for a talking head model. |
| **Super Resolution** | SuperResolutionNode.svelte | Scale factor input. | Input (Image/Video) | Output (Image/Video) | Triggers a backend task to apply a super-resolution model like Thera.8 |
| **Video Restoration** | VideoRestorationNode.svelte | Restoration strength slider. | Input (Video) | Output (Video) | Triggers a backend task to apply a video restoration model like SeedVR2.6 |
| **VSE Assembler** | VSEAssemblerNode.svelte | "Render Final Video" button, Status display. | Sequence In (EDL) | Final Video (Video) | Triggers client:render\_final\_sequence event, initiating the EDL compilation and MoviePy rendering pipeline.1 |

## **Section 5: The Generative Engine: Functional Requirements for Core Capabilities**

This section defines the product's initial creative toolkit. It translates the "Function Runner" architecture into a concrete set of generative capabilities, drawing directly from the analysis of the current open-source technology landscape. This is the primary point of synthesis between the internal architecture and external technological possibilities.

### **5.1 The "Function Runner" Pipeline Model**

The backend must be designed for maximum flexibility and extensibility to avoid the pitfalls of a monolithic generative engine.

**Requirement:** All generative tasks shall be executed by a "Function Runner" system. In this model, a generic Celery worker receives a task, identifies the required generative pipeline, and invokes that pipeline within its own isolated, containerized (Docker) environment.1

This model is the key to the system's long-term viability. It provides complete isolation between different AI models, eliminating dependency conflicts. It allows the platform to integrate any model that can be run from a command line, ensuring the studio can rapidly adopt new, breakthrough technologies as they become available.1

### **5.2 Initial Suite of Generative Pipelines**

To provide immediate value and a versatile creative toolkit upon launch, the product must ship with a pre-configured suite of generative pipelines.

**Requirement:** The product shall launch with an initial suite of PipelineNodes, each corresponding to a specific, containerized backend model.

The selection of these initial capabilities is based on a comprehensive review of powerful, permissively licensed, and well-regarded open-source models available in the current landscape.9 This defines the "out-of-the-box" experience for the user.

### **Table 3: Initial Generative Pipeline Capabilities**

This table directly translates the abstract concept of "generative AI" into a concrete list of product features and their underlying technical implementations. It provides a clear, traceable line from market research to a specific product feature, telling the product and engineering teams precisely *what* the studio can do at launch.

| Feature Name | PipelineNode ID | Description | Underlying Model/Tech | Source Repo(s) | Key Inputs | Key Outputs |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Text-to-Video** | t2v-wan2.1 | Generates high-quality video from a text prompt. Optimized for consumer-grade GPUs (8GB+ VRAM). | Wan2.1 | 10 | Prompt (String) | Video |
| **Image-to-Video** | i2v-ltx | Animates a static source image based on a text prompt. | LTX-Video | 5 | Source Image, Prompt (String) | Video |
| **Talking Head** | a2v-fantasy-talking | Generates a realistic talking portrait from a source image and an audio file. | FantasyTalking | 3 | Source Image, Audio | Video |
| **Action Transfer** | motion-flexiact | Transfers the motion from a source video to a target character image, preserving identity. | FlexiAct | 2 | Target Image, Motion Source Video | Video |
| **Identity Preservation** | ip-dreamo | Generates an image preserving the identity of a character/object from a reference image. | DreamO | 9 | Reference Image, Prompt (String) | Image |
| **Face Swap** | faceswap-reactor | Swaps a face from a source image onto a target image. SFW-gated. | ComfyUI-ReActor | 11 | Target Image, Source Image | Image |
| **Dialogue Generation** | tts-f5 | Generates high-quality speech from text, with voice cloning from a reference audio clip. | F5-TTS | 7 | Text (String), Reference Audio | Audio |
| **Multimodal Editing** | edit-omnigen2 | Performs complex, instruction-based image modifications with high precision. | OmniGen2 | 12 | Source Image, Instruction (String) | Image |

### **5.3 The Asset Training User Interface**

The architecture specifies a backend Celery task, tasks.assets.train\_lora, for training custom character models—a critical function for achieving character consistency in generated media.1 However, the architectural documents do not specify a user interface for this powerful capability. An analysis of the tool ecosystem, specifically the existence of projects like

fluxgym which provides a "dead simple web UI for training FLUX LoRA" 13, validates that there is a clear user need for a simplified, GUI-driven training workflow. For a non-technical artist, triggering a complex training process via an API or command line is not a viable workflow. The product must therefore expose this backend capability through an intuitive user interface.

**Requirement:** The application shall include a dedicated "Asset Manager" interface, accessible from a main navigation route (e.g., /assets).

This Asset Manager UI shall provide the following functionalities:

1. Allow users to create a new "Character" asset.  
2. Provide an interface for uploading a set of reference images for that character.  
3. Include input fields for the character's name and a unique "trigger word" for use in prompts.  
4. Feature a prominent "Train Model" button. Clicking this button shall validate the inputs and dispatch the tasks.assets.train\_lora Celery task to the backend.  
5. The UI must subscribe to progress updates for the training task (via the WebSocket connection) and display the status to the user (e.g., "Queued," "Training: 25%," "Complete").  
6. Upon successful completion, the newly trained asset must be made available for use in the Production Canvas, appearing in the asset library and draggable onto the canvas as an AssetNode.

## **Section 6: The Assembly Pipeline: Requirements for Final Sequence Rendering**

A generative studio must not only create individual clips but also assemble them into a cohesive final product. This section details the requirements for the post-generation workflow, turning a collection of generated shots into a final, editable video sequence.

### **6.1 Graph-to-EDL Compilation**

The first step in the assembly process is to translate the creative intent captured in the node graph into a standardized, machine-readable format.

**Requirement:** The system shall include a service that can traverse the Production Canvas graph and compile the sequence of "active takes" from connected ShotNodes into a standard Edit Decision List (EDL) format, such as CMX3600.

This requirement is a deliberate architectural choice to decouple the graph's creative logic from the technical process of video rendering.1 Using an EDL as an intermediate format provides several profound benefits. First, the EDL itself is a human-readable, text-based artifact that can be inspected for debugging purposes. If a final video renders incorrectly, the EDL can be examined to determine if the fault lies in the graph compilation step or the final rendering step. Second, it enhances modularity; the rendering engine (MoviePy) could be swapped for a different one in the future without altering the graph compilation logic. Finally, the EDL could be exposed as a direct export option for users, allowing them to take their generative sequence into professional editing software like DaVinci Resolve or Adobe Premiere Pro—a valuable interoperability feature.1 This compilation process shall be initiated when the user interacts with the

VSEAssemblerNode on the canvas.

### **6.2 Programmatic Video Assembly**

Once the EDL is created, it serves as the blueprint for the final render.

**Requirement:** A dedicated Celery task, tasks.assembly.render\_final\_video, shall be responsible for parsing an EDL and using the MoviePy library to programmatically assemble the final video sequence.

This task acts as the system's automated "Editor" and must execute on a CPU-optimized worker. Its required capabilities include:

* Loading video and audio clips from the project's file storage based on paths specified in the EDL.  
* Creating precise subclips using the timecode information from the EDL via MoviePy's .subclip() method.  
* Stitching the ordered list of subclips together into a single timeline using concatenate\_videoclips.  
* Applying additional effects specified in the graph, such as text overlays (TextClip) or simple transitions (moviepy.video.fx).  
* Rendering the final composite video object to a standard file format (e.g., MP4) and saving it to the 06\_Exports/ directory.1

### **6.3 Post-Production as a Core Feature**

The initial architecture focuses on generation and assembly. However, an analysis of the technology landscape reveals powerful open-source post-processing tools that can be integrated to significantly enhance the product's value and address common shortcomings of generative models. Generative outputs can sometimes be noisy, artifact-prone, or of insufficient resolution for professional use. Specialized models exist to solve these exact problems.

The node-based architecture is perfectly suited to chain these post-production processes into the main workflow. A user could generate a shot, pass its output to a restoration node, then pass that result to a super-resolution node, before finally sending the enhanced clip to the assembly stage. This transforms the product from a simple "generator \+ assembler" into a complete, end-to-end production suite.

**Requirement:** The scope of the assembly pipeline shall be expanded to a full "Post-Production Suite." This requires the implementation of new PipelineNode types and their corresponding backend Celery tasks.

Initial post-production nodes shall include:

* **SuperResolutionNode:** This node will take an image or video as input. It will trigger a backend task that uses the **Thera** model to perform aliasing-free, arbitrary-scale super-resolution, increasing the media's resolution.8  
* **VideoRestorationNode:** This node will take a video as input. It will trigger a backend task that uses the **SeedVR2** model to perform one-step video restoration, cleaning up artifacts and improving overall visual quality.6

These nodes must be designed to be inserted into the graph between generative ShotNodes and the final VSEAssemblerNode, allowing users to build complex post-processing chains visually.

## **Section 7: System-Level Requirements: Quality, Performance, and Resource Management**

This section defines critical non-functional and system-level requirements that are essential for creating a robust, stable, and user-friendly experience. These requirements govern how the system manages resources and translates user intent into technical execution.

### **7.1 Dynamic Pipeline Selection via Quality Settings**

Users need a simple way to control the trade-off between generation speed and output quality without needing to understand the underlying models.

**Requirement:** The user shall be able to set a project-wide "quality" setting, selectable from low, standard, or high. This setting shall be stored in the project's project.json manifest.

The backend must translate this simple user choice into a sophisticated technical decision.

**Requirement:** The backend task dispatcher (the "Producer" agent logic within the FastAPI endpoint) must read the project's quality setting and dynamically select the appropriate containerized pipeline for a given generative task.

For example, a generate-image task requested with the low quality setting might invoke a fast SD1.5 pipeline for quick drafts. The same task requested at high quality would invoke a more computationally expensive but higher-fidelity pipeline, such as one based on the full FLUX.dev model.1 This abstraction allows the user to change the entire quality profile of their project with a single setting.

### **7.2 Hardware-Aware Orchestration and VRAM Management**

Generative models have steep and highly variable VRAM requirements. Attempting to run a high-end workflow on low-end hardware will inevitably result in out-of-memory (OOM) errors, leading to failed tasks and a frustrating user experience. The system must be architected to prevent this.

**Requirement:** The backend task dispatcher must be hardware-aware. Before dispatching a task to a Celery worker, it must consider the estimated VRAM requirements of the selected pipeline and the known VRAM capabilities of the available worker nodes.

This intelligent orchestration is critical for system stability. The system must maintain a profile for each pipeline that includes its estimated VRAM usage for each quality level. VRAM tiers for worker nodes can be broadly categorized:

* **12 GB VRAM (Lower Practical Limit):** Can run models like SDXL or FLUX only with aggressive optimizations (e.g., \--medvram-sdxl, FP8 quantization, CPU offloading). Complex workflows with multiple conditioning models are likely to fail.1  
* **16 GB VRAM (Comfortable Mid-Range):** Can comfortably run standard production workloads like SDXL with a refiner or one or two ControlNets at 1024px resolution.1  
* **24 GB VRAM ("All Features On"):** Lifts most practical limits for 1024px generation, comfortably running full FP16 models like FLUX.dev with multiple LoRAs and ControlNets simultaneously, and enabling higher-resolution experiments.1

**Requirement:** The system shall implement intelligent task handling based on hardware availability. When a user requests a high-requirement task (e.g., a "high" quality render needing 24 GB VRAM), the dispatcher must check for a suitable worker. If only a lower-capability worker (e.g., 16 GB) is free, the system shall be configured with one of two behaviors:

1. **Queueing:** The task is held until a high-end worker becomes available.  
2. **Fallback (with notification):** The system automatically falls back to a lower-quality pipeline that fits the available hardware and notifies the user via the WebSocket (e.g., "High quality not available on current hardware. Fell back to standard 1024px generation.").1

### **Table 4: Quality Level to Pipeline Mapping**

This table provides a clear contract for how user-facing quality settings translate into specific technical implementations and their associated hardware constraints. It is essential for managing user expectations and for the configuration and operation of the backend worker pools.

| Task Type | Quality Level | Selected Pipeline Container | Description | Minimum VRAM Tier |
| :---- | :---- | :---- | :---- | :---- |
| generate-image | low | t2i-sd1.5:latest | Fast 512px drafts using Stable Diffusion 1.5 for rapid iteration. | 12 GB |
| generate-image | standard | t2i-flux-schnell:latest | Good balance of quality and speed at 768px-1024px using FLUX.Schnell. | 16 GB |
| generate-image | high | t2i-flux-dev-fp16:latest | Maximum fidelity 2K generation with the full, unquantized FLUX.dev model. | 24 GB |
| generate-video | low | t2v-wan2.1-1.3b:latest | Fast video drafts using the highly optimized 1.3B parameter Wan2.1 model. | 12 GB |
| generate-video | high | t2v-ltx-13b:latest | High-quality, high-resolution video using the full LTX-Video 13B model. | 24 GB |

## **Section 8: Strategic Roadmap: Requirements for Cloud and Multi-Tenancy**

The architectural design was deliberately forward-looking, ensuring that the initial single-user application can evolve gracefully into a cloud-native, multi-tenant Software-as-a-Service (SaaS) product. This section defines the high-level requirements for that transition.

### **8.1 Cloud Storage Integration**

**Requirement:** The system's file storage layer must be abstract and configurable to use a cloud object store, specifically Amazon S3, as its backend.

This requires two key configurations:

1. The primary file storage for project assets must be pointed to an S3 bucket instead of a local file system.  
2. The Git LFS remote for each project repository must be configured to use this S3 bucket as its remote store.  
   This makes the cloud the single, canonical source of truth for all large binary assets, a prerequisite for a distributed, cloud-native application.1

### **8.2 Multi-Tenancy Strategy**

To serve multiple users or organizations from a shared infrastructure, a clean and secure data isolation strategy is required.

**Requirement:** For the multi-tenant version of the product, tenant data shall be isolated using the "Prefix-per-Tenant" strategy within a shared S3 bucket.

In this model, all tenants share a single S3 bucket (e.g., s3://main-workspace/), but their data is logically isolated under a unique, tenant-specific prefix (e.g., s3://main-workspace/tenant-a/, s3://main-workspace/tenant-b/). This is the recommended approach for modern SaaS applications due to its superior scalability and reduced management overhead compared to a "Bucket-per-Tenant" model.1 Security and access control will be enforced using granular AWS Identity and Access Management (IAM) policies that restrict access to specific prefixes based on the authenticated user's identity.

### **8.3 Stateless, Just-in-Time Data Fetching**

A core principle of scalable cloud architecture is the decoupling of compute from storage. The generative workers must not be tied to specific data.

**Requirement:** In a cloud deployment, all compute workers (Celery workers) must be treated as stateless.

The workflow for a cloud-based task execution shall be as follows:

1. A task is dispatched to a generic worker node.  
2. The worker authenticates and identifies the target project repository and its associated LFS store in the cloud.  
3. It clones the project's Git repository to a temporary, local cache on the compute instance.  
4. It executes a git lfs pull command, potentially with include/exclude filters, to download *only* the necessary LFS objects (assets) required for the specific task.  
5. It performs the generative work.  
6. It commits any changes to creative source files (e.g., updating the canvas JSON) and pushes them back to the remote Git repository.  
7. It pushes any new LFS objects (the rendered output) to the S3 LFS store.  
8. Once the task is complete, the local cache on the compute node is discarded.

This stateless, just-in-time data fetching model ensures that compute resources are generic and interchangeable, allowing the system to scale horizontally by simply adding more compute nodes as demand increases.1

## **Section 9: Consolidated Requirements and Implementation Priorities**

This final section provides a high-level summary of the core product requirements and a strategic recommendation for the implementation sequence to ensure a focused and successful development effort.

### **9.1 Summary of Core Requirements**

* The system **shall** be a decoupled web application with a SvelteKit frontend and a Python (FastAPI, Celery) backend.1  
* The system **shall** enforce a consistent, programmatically managed file structure based on the Workspace/Project model.1  
* The system **shall** use a hybrid Git/Git LFS versioning strategy, with every project being initialized as its own independent repository.1  
* The user interface **shall** be a node-based "Production Canvas" where nodes represent the creative and technical components of the filmmaking process.1  
* The backend **shall** execute all generative tasks using a containerized "Function Runner" model, allowing for the flexible integration of heterogeneous AI models.1  
* The system **shall** provide a final assembly pipeline that compiles the node graph to an Edit Decision List (EDL) and programmatically renders the final video using MoviePy.1

### **9.2 Implementation Priority: The Core End-to-End Workflow**

The highest priority for initial development must be the validation of the core, end-to-end generative workflow. All other features, while valuable, are secondary to proving that this fundamental architectural loop is sound and functional. Initial development efforts (corresponding to Sprints 1-7 in the architectural plan 1) must be laser-focused on this goal.

**Recommendation:** The Minimum Viable Product (MVP) is defined by the successful implementation of a single, unbroken generative chain.

**Success Criteria for MVP:** A user must be able to perform the following sequence of actions successfully:

1. Create a new project via the UI.  
2. Open the Production Canvas for that project.  
3. Add a ShotNode and a basic PipelineNode (e.g., a simple Text-to-Image pipeline like t2i-sd1.5).  
4. Connect the nodes and enter a text prompt.  
5. Click the "Generate" button on the ShotNode.  
6. See the UI for that node update to a "generating" state, communicated via WebSocket.  
7. Receive the final generated image back from the backend via a server:task\_success WebSocket event.  
8. See the ShotNode's thumbnail display update with the resulting image.

Successfully implementing this workflow—from the Svelte client, through the FastAPI gateway, to a Celery worker, into a Docker container, and back to the client via WebSockets—validates every core architectural assumption of the system. It de-risks the entire project and provides a stable foundation upon which all other features can be built.

## **Appendix: API and Protocol Specifications**

### **Table 5: REST API Endpoint Specification**

| Path | Method | Auth | Request Body / Query Params | Response | Description |
| :---- | :---- | :---- | :---- | :---- | :---- |
| /auth/token | POST | No | username, password | { "access\_token": "...", "token\_type": "bearer" } | Authenticates a user and returns a JWT.1 |
| /api/v1/projects | GET | Yes | \- | \[ { "id": "...", "name": "..." } \] | Lists all projects for the authenticated user.1 |
| /api/v1/projects | POST | Yes | { "name": "New Project" } | { "id": "...", "name": "..." } | Creates a new, empty project.1 |
| /api/v1/projects/{id} | GET | Yes | \- | { "id": "...", "graph": {... } } | Retrieves the full state of a project's node graph.1 |
| /api/v1/projects/{id} | PUT | Yes | { "graph": {... }, "version": 1 } | { "status": "success" } | Saves/updates the project's node graph.1 |
| /api/v1/tasks/generate\_shot | POST | Yes | { "node\_data": {... } } | { "task\_id": "..." } | Dispatches a shot generation task to Celery and returns the task ID.1 |

### **Table 6: WebSocket Event Protocol Specification**

| Event Name | Direction | Payload Schema | Description |
| :---- | :---- | :---- | :---- |
| client:update\_node\_data | C → S | { "node\_id": "...", "data": {... } } | Sent when a user modifies a node's properties in the UI.1 |
| client:start\_generation | C → S | { "node\_id": "..." } | Sent when the user clicks "Generate" on a Shot Node.1 |
| client:sync\_request | C → S | {} | Sent by the client upon reconnecting to request the latest full graph state.1 |
| server:node\_state\_updated | S → C | { "node\_id": "...", "state": "generating" } | Informs the client that a node's state has changed (e.g., to show a loading spinner).1 |
| server:task\_progress | S → C | { "task\_id": "...", "node\_id": "...", "progress": 50, "step": "Denoising..." } | Provides granular progress updates for a running task.1 |
| server:task\_success | S → C | { "task\_id": "...", "node\_id": "...", "result": { "output\_url": "..." } } | Sent when a task completes successfully, providing the URL to the generated media.1 |
| server:task\_failed | S → C | { "task\_id": "...", "node\_id": "...", "error": "..." } | Sent when a task fails, providing an error message for the UI.1 |
| server:full\_sync | S → C | { "graph": {... } } | The server's response to a client:sync\_request, containing the entire current project state.1 |

#### **Works cited**

1. The Production Canvas, Unbound: An Architectural Blueprint for a Web-Based Generative Film Studio  
2. shiyi-zh0408/FlexiAct: \[SIGGRAPH 2025\] Official code of ... \- GitHub, accessed June 30, 2025, [https://github.com/shiyi-zh0408/FlexiAct](https://github.com/shiyi-zh0408/FlexiAct)  
3. Fantasy-AMAP/fantasy-talking: FantasyTalking: Realistic ... \- GitHub, accessed June 30, 2025, [https://github.com/Fantasy-AMAP/fantasy-talking](https://github.com/Fantasy-AMAP/fantasy-talking)  
4. SihuiJi/LayerFlow: \[SIGGRAGH'25\] Official repository of ... \- GitHub, accessed June 30, 2025, [https://github.com/SihuiJi/LayerFlow](https://github.com/SihuiJi/LayerFlow)  
5. Lightricks/LTX-Video: Official repository for LTX-Video \- GitHub, accessed June 30, 2025, [https://github.com/Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video)  
6. IceClear/SeedVR2: SeedVR2: One-Step Video Restoration ... \- GitHub, accessed June 30, 2025, [https://github.com/IceClear/SeedVR2](https://github.com/IceClear/SeedVR2)  
7. SWivid/F5-TTS: Official code for "F5-TTS: A Fairytaler that ... \- GitHub, accessed June 30, 2025, [https://github.com/SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)  
8. prs-eth/thera: Thera: Aliasing-Free Arbitrary-Scale Super ... \- GitHub, accessed June 30, 2025, [https://github.com/prs-eth/thera](https://github.com/prs-eth/thera)  
9. bytedance/DreamO: DreamO: A Unified Framework for ... \- GitHub, accessed June 30, 2025, [https://github.com/bytedance/DreamO](https://github.com/bytedance/DreamO)  
10. Wan-Video/Wan2.1: Wan: Open and Advanced Large ... \- GitHub, accessed June 30, 2025, [https://github.com/Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1)  
11. Gourieff/ComfyUI-ReActor: Fast and Simple Face Swap ... \- GitHub, accessed June 30, 2025, [https://github.com/Gourieff/ComfyUI-ReActor](https://github.com/Gourieff/ComfyUI-ReActor)  
12. VectorSpaceLab/OmniGen2: OmniGen2: Exploration to ... \- GitHub, accessed June 30, 2025, [https://github.com/VectorSpaceLab/OmniGen2](https://github.com/VectorSpaceLab/OmniGen2)  
13. cocktailpeanut/fluxgym: Dead simple FLUX LoRA training ... \- GitHub, accessed June 30, 2025, [https://github.com/cocktailpeanut/fluxgym](https://github.com/cocktailpeanut/fluxgym)