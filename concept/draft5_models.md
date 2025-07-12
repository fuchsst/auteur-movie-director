

# **The Production Canvas, Unbound: An Architectural Blueprint for a Web-Based Generative Film Studio**

## **Section 1: A Decoupled Architectural Vision**

This document outlines a comprehensive architectural blueprint for a web-based generative film studio. It serves as an alternative vision to the monolithic, Blender-native system previously conceptualized, re-architecting it as a modern, decoupled client-server application. The primary technological pillars of this new architecture are a Svelte-based frontend and a full Python backend. This section establishes the strategic rationale for this shift, introduces the high-level system design, and justifies the core technology stack, setting the stage for the detailed component breakdowns that follow.

### **1.1 From Monolith to Microservices: The Strategic Imperative**

The original design for the generative film studio, while powerful in its conception, is inherently constrained by its tight coupling with the Blender desktop environment. This monolithic architecture limits its accessibility to users with specific hardware and software configurations, curtails its scalability, and complicates its maintenance lifecycle. The migration to a decoupled, web-native architecture is not merely a technological substitution but a strategic imperative designed to unlock the platform's full potential.

The new paradigm is a client-server model where concerns are cleanly separated. The frontend, built with SvelteKit, serves as the user's universally accessible, interactive "Production Canvas." The backend, a distributed system orchestrated by Python, acts as the powerful, scalable "Generative Engine." This separation addresses the core limitations of the original design. Accessibility is dramatically enhanced, as the studio can be accessed from any modern web browser on any operating system, removing the dependency on a local Blender installation. Scalability becomes a core feature; the generative workers, which are the most computationally expensive part of the system, can be scaled horizontally and independently of the user-facing application. This means that as the demands of a project grow, more computational resources can be allocated to the backend without any change to the client experience. Maintainability is also improved, as frontend and backend teams can develop, test, and deploy their respective components independently.

This architectural shift transforms the tool from a single-user, single-machine utility into a potential collaborative, enterprise-grade studio platform. The system's capacity is no longer bound by the user's local hardware but by the cloud or on-premise infrastructure it is deployed upon. This fundamental change is a direct and powerful consequence of re-envisioning the application with a modern web stack.

### **1.2 The Core Technology Stack: Justification and Synergy**

The selection of each technology in the stack is deliberate, chosen for its individual strengths and its synergistic fit within the overall architecture.

* **Frontend (SvelteKit):** SvelteKit is selected as the frontend framework due to its exceptional performance, concise syntax, and comprehensive feature set. 1 As a compiler, Svelte shifts work from the browser to the build step, resulting in highly optimized, minimal JavaScript bundles and a faster user experience. 3 SvelteKit extends Svelte into a full-fledged application framework, providing filesystem-based routing, server-side rendering (SSR), and API endpoint generation out of the box. 3 This makes it the ideal choice for building a sophisticated, single-page application like the Production Canvas.  
* **Backend API (FastAPI):** FastAPI is the choice for the backend API gateway due to its high performance, which is comparable to Node.js and Go, and its native support for asynchronous operations. 6 Built on ASGI, it provides first-class, clean support for WebSockets, which is a critical requirement for the real-time, interactive nature of the Production Canvas. 6  
* **Asynchronous Task Queue (Celery & Redis):** The generative processes central to the film studio are long-running and computationally expensive. Attempting to run these tasks within an API request would lead to timeouts and a poor user experience. Celery is the industry-standard solution in the Python ecosystem for offloading such tasks to background workers. 11 Paired with Redis as a fast and reliable message broker, Celery allows the FastAPI server to remain responsive by immediately returning a task ID to the client while the heavy lifting is performed asynchronously by a scalable pool of workers. 11  
* **Node-Based UI Library (Svelte Flow):** The core user interface is the "Production Canvas," a node-based editor. Svelte Flow (commercially known as @xyflow/svelte) is the premier open-source library for building such interfaces in the Svelte ecosystem. 14 Its feature set aligns perfectly with the project's requirements, offering robust support for custom nodes, custom edges, and, crucially, nested graphs or "subflows," which directly enables the implementation of hierarchical project views. 15  
* **Programmatic Video Assembly (MoviePy & EDL):** To replace Blender's Video Sequence Editor (VSE), MoviePy is selected as the primary tool for programmatic video editing. 23 It provides a flexible Python API for concatenating clips, overlaying text, and applying effects. 24 To decouple the node graph from the rendering process, an Edit Decision List (EDL)—a standard, text-based representation of an edit sequence—will be used as an intermediate format. 28 Libraries like  
  pycmx or python-edl can be used for this purpose. 29

## **Section 2: The Generative Core: Models, Quality, and Execution**

The heart of the application is its generative capability. This section details the specific models that will form the core of the creative toolkit, introduces a tiered "Quality" setting to manage resource consumption, and refines the "Function Runner" concept to show how these elements are orchestrated by the Celery-based backend.

### **2.1 The Focused Model Stack**

To ensure a high-quality and cohesive user experience, the application will focus on a curated set of powerful, open-source models for its primary generative tasks.

* Image Generation: FLUX by Black Forest Labs  
  For all text-to-image and image-to-image tasks, the application will exclusively use the FLUX model family. 33 FLUX models are state-of-the-art transformers that offer exceptional prompt adherence and image quality. 34 The different variants (  
  Schnell, Dev) provide a natural mapping to different quality and performance tiers. 35  
* Video Generation: Wan2GP Model Suite  
  Video generation tasks, including text-to-video and image-to-video, will be handled by the models integrated within the Wan2GP project. 39 Wan2GP is particularly well-suited for this application as it is optimized for users with lower-configuration GPUs and integrates a variety of models (like FusionX, LTX, and Vace ControlNet) into a cohesive system. 39  
* **Audio Generation: A Curated Suite**  
  * **Text-to-Speech (TTS):** For dialogue and narration, the application will integrate a high-quality, open-source TTS model. Leading candidates include **MeloTTS** for its multilingual support and real-time performance, and **XTTS-v2** for its excellent voice cloning capabilities from short audio clips. 44  
  * **Music & Sound Effects:** For background scores and sound design, the system will leverage models like **Stable Audio Open** for generating high-quality audio loops from text prompts, or **MusicGen** for creating longer musical pieces. 45

### **2.2 Quality Tiers and VRAM Management**

To provide users with control over generation speed and resource usage, the application will feature a global "Quality" setting with three levels: Low, Standard, and High. These settings directly map to different model configurations and target specific VRAM tiers, ensuring the application can run effectively on a range of hardware.

| Quality Setting | Target VRAM | Image Generation (FLUX) | Video Generation (Wan2GP) | Key Optimizations |
| :---- | :---- | :---- | :---- | :---- |
| **Low** | **\~12 GB** | **FLUX.1-schnell** or **FLUX.1-dev (FP8 quantized)** at lower resolutions (e.g., 768x768). | Utilizes Wan2GP's low-VRAM models and settings. | Enables ComfyUI's \--lowvram mode. Model CPU offloading is active. Limited to one simple ControlNet or IP-Adapter. |
| **Standard** | **\~16 GB** | **FLUX.1-dev (FP8 quantized)** at standard resolutions (e.g., 1024x1024). | Standard Wan2GP models. | Enables ComfyUI's \--medvram-sdxl mode. Allows for moderate workflows, such as one ControlNet and one IP-Adapter. |
| **High** | **24 GB+** | **FLUX.1-dev (full FP16)** at high resolutions (e.g., 2048x2048). | High-fidelity Wan2GP models. | All features enabled. Supports complex workflows with multiple ControlNets and IP-Adapters simultaneously. |

When a user initiates a generation task, the backend will receive the desired quality setting. If the requested quality exceeds the capabilities of the available hardware (e.g., a "High" quality request on a 16GB VRAM worker), the system will intelligently fall back to a lower setting (e.g., "Standard") and notify the user, ensuring a successful generation rather than an out-of-memory error.

### **2.3 The "Function Runner" Revisited: A Containerized, Queued Approach**

The "Function Runner" concept is realized through a combination of **ComfyUI, Celery, and Docker**. Each generative model or workflow is not run directly by the Celery worker. Instead, the worker's job is to act as a controller, preparing and dispatching a job to a dedicated, containerized ComfyUI instance.

Here's the refined workflow:

1. A user clicks "Generate" on a node in the SvelteKit frontend. The request, including the node's data and the project's "Quality" setting, is sent to the FastAPI backend.  
2. The FastAPI endpoint validates the request and creates a Celery task. It determines the appropriate Celery queue based on the quality setting (e.g., gpu\_16gb\_queue for "Standard", gpu\_24gb\_queue for "High").  
3. A Celery worker on a machine with the corresponding hardware picks up the task.  
4. The worker's Python script dynamically constructs a ComfyUI API-formatted JSON payload. 47 It populates the JSON with the prompt, seed, and other parameters from the node data. Crucially, it selects the correct models and sets the right parameters (e.g., resolution, sampler) based on the quality tier. 47  
5. The worker then makes an API call to a local, containerized ComfyUI service, submitting the JSON workflow. 47 This ComfyUI instance is pre-configured with all necessary models and custom nodes for that specific task.  
6. The worker monitors the ComfyUI job via its WebSocket API, relaying progress back to the frontend. 47  
7. Upon completion, the worker retrieves the output file path from ComfyUI and reports the final result.

This containerized approach isolates dependencies, ensures reproducibility, and allows the system to manage a heterogeneous collection of models without conflict.

## **Section 3: FLUX-Powered Image Generation Workflows**

This section details how the application will leverage the FLUX model family to power its core image creation and editing capabilities, translating abstract nodes on the canvas into concrete, high-quality visual outputs.

### **3.1 Core Image Generation Node (GenerateImage)**

The primary workhorse for creating new images is the GenerateImage node. In the Svelte Flow UI, this node will feature input fields for a positive prompt, a negative prompt, and a seed value.

When a user triggers this node, the backend maps the project's "Quality" setting to a specific FLUX model and configuration:

* **Low Quality:** The system uses the **FLUX.1-schnell** model. 35 This model is the fastest variant, optimized for speed, making it ideal for quick drafts and iterations on hardware with \~12GB of VRAM. The resolution will be capped at a 768px equivalent.  
* **Standard Quality:** The system uses the **FLUX.1-dev** model with **FP8 quantization**. 34 This provides a significant quality improvement over  
  schnell while remaining manageable on mid-range hardware (\~16GB VRAM). The resolution will be set to a 1024px equivalent.  
* **High Quality:** The system uses the full **FLUX.1-dev** model with **FP16 precision**. 34 This delivers the highest possible quality and is intended for final renders on high-end hardware (24GB+ VRAM). The resolution can be pushed to 2048px or higher.

The backend worker constructs the ComfyUI workflow JSON, loading the appropriate model file and setting the resolution and step count according to the selected quality tier.

### **3.2 Image Editing and Inpainting (EditImage)**

For image editing tasks, the application will leverage the powerful capabilities of FLUX models when combined with control inputs. A dedicated EditImage node will allow for more sophisticated operations.

* **Inputs:** This node will accept a source Image, a Mask image (where white areas indicate regions to be changed), and a Prompt describing the desired modification.  
* **Workflow:** The backend will use a ComfyUI workflow that combines the FLUX model with an inpainting preprocessor. The source image and mask are fed into the workflow, and the FLUX model regenerates only the masked area based on the new prompt.  
* **Model Selection:** The same quality tier logic applies. For a quick edit, "Low" quality will use FLUX.1-schnell. For a high-fidelity final edit, "High" quality will use the full FLUX.1-dev model to ensure the inpainted region seamlessly blends with the original image.

### **3.3 Contextual Editing (KontextNode)**

To leverage the most advanced features, a specialized KontextNode will be available, designed to use the **FLUX.1 Kontext** capabilities for instruction-based image editing. 33

* **Inputs:** This node will take a source Image and a Prompt that is a direct instruction, such as "replace the logo on the t-shirt with the text 'BFL'" or "make the sky look like a sunset". 36  
* **Workflow:** The backend will use a dedicated ComfyUI workflow specifically designed for FLUX Kontext. This workflow can parse the instructional prompt and apply the changes without needing an explicit mask, offering a more intuitive and powerful editing experience.  
* **Model Selection:** Due to its complexity, the Kontext workflow will likely be restricted to "Standard" and "High" quality settings to ensure sufficient VRAM for the model and the editing process.

By offering this tiered set of nodes, the application provides a flexible workflow, allowing users to move from rapid ideation with GenerateImage to precise modifications with EditImage and powerful, AI-driven changes with KontextNode.

## **Section 4: Development and Deployment Structure**

To support this modular and scalable architecture, the project will be organized into a clear directory structure, managed by docker-compose for a streamlined local development experience. This setup ensures that the frontend, backend, and various generative workers can be developed and run independently while communicating seamlessly.

### **4.1 Monorepo Project Structure**

A monorepo structure is recommended to keep all related code in a single repository, simplifying dependency management and cross-service development.

Plaintext

/generative-studio/  
├── frontend/                  \# SvelteKit Application  
│   ├── src/  
│   │   ├── routes/  
│   │   │   └── project/  
│   │   │       └── \[id\]/  
│   │   │           ├── \+page.svelte      \# The Production Canvas UI  
│   │   │           └── \+page.server.js   \# Data loading logic  
│   │   └── lib/  
│   │       ├── components/  
│   │       │   ├── nodes/              \# Custom Svelte Flow nodes (GenerateImage, EditImage, etc.)  
│   │       │   └── Canvas.svelte  
│   │       └── stores/                 \# Svelte stores for state management  
│   ├── static/  
│   └── svelte.config.js  
│  
├── backend/                  \# FastAPI & Celery Application  
│   ├── app/  
│   │   ├── api/                    \# FastAPI endpoints  
│   │   ├── core/                   \# Core logic, config  
│   │   └── workers/                \# Celery task definitions  
│   │       ├── \_\_init\_\_.py  
│   │       ├── image\_tasks.py      \# Tasks for FLUX generation  
│   │       └── video\_tasks.py      \# Tasks for wan2gp generation  
│   ├── Dockerfile  
│   └── requirements.txt  
│  
├── comfyui\_workflows/        \# API-formatted JSON workflows  
│   ├── flux\_generate\_image.json  
│   └── flux\_edit\_image.json  
│  
├── models/                     \# Shared directory for all AI model weights  
│   ├── flux/  
│   │   ├── FLUX.1-schnell.safetensors  
│   │   └── FLUX.1-dev.safetensors  
│   ├── wan2gp/  
│   └── tts/  
│  
└── docker-compose.yml        \# Main Docker Compose file for orchestration

### **4.2 Docker Compose Orchestration**

The docker-compose.yml file is the key to orchestrating the various services. It defines how each container is built and how they are networked together, including the crucial volume mounts for code and models.

YAML

version: '3.8'

services:  
  \# SvelteKit Frontend Service  
  frontend:  
    build:  
      context:./frontend  
    ports:  
      \- "5173:5173" \# Expose Vite dev server port  
    volumes:  
      \-./frontend:/app \# Mount frontend code for hot-reloading  
    command: npm run dev

  \# FastAPI Backend API Service  
  backend:  
    build:  
      context:./backend  
    ports:  
      \- "8000:8000"  
    volumes:  
      \-./backend/app:/app/app \# Mount backend code for hot-reloading  
    depends\_on:  
      \- redis  
    environment:  
      \- CELERY\_BROKER\_URL=redis://redis:6379/0  
      \- CELERY\_RESULT\_BACKEND=redis://redis:6379/0

  \# Redis Message Broker  
  redis:  
    image: "redis:alpine"

  \# Celery Worker for Standard Quality (16GB VRAM)  
  celery-worker-standard:  
    build:  
      context:./backend \# Uses the same Dockerfile as the backend  
    command: celery \-A app.workers.image\_tasks worker \-l info \-Q gpu\_16gb\_queue \--concurrency=1  
    volumes:  
      \-./backend/app:/app/app  
      \-./models:/app/models \# Mount shared models directory  
      \-./comfyui\_workflows:/app/workflows \# Mount workflow definitions  
    deploy:  
      resources:  
        reservations:  
          devices:  
            \- driver: nvidia  
              count: 1  
              capabilities: \[gpu\]  
    depends\_on:  
      \- redis

  \# Celery Worker for High Quality (24GB VRAM)  
  celery-worker-high:  
    build:  
      context:./backend  
    command: celery \-A app.workers.image\_tasks worker \-l info \-Q gpu\_24gb\_queue \--concurrency=1  
    volumes:  
      \-./backend/app:/app/app  
      \-./models:/app/models  
      \-./comfyui\_workflows:/app/workflows  
    deploy:  
      resources:  
        reservations:  
          devices:  
            \- driver: nvidia  
              count: 1  
              capabilities: \[gpu\]  
    depends\_on:  
      \- redis

  \# A separate container for ComfyUI, managed by the workers  
  \# This would be started/stopped by the Celery tasks themselves,  
  \# or could be a long-running service per worker type.  
  \# For simplicity, its management is abstracted into the worker logic.

This setup provides a complete, isolated, and reproducible development environment. A developer can clone the repository, run docker-compose up, and have the entire application stack—frontend, backend, and multiple GPU-enabled workers—running and ready for development. The volume mounts ensure that code changes are reflected instantly without needing to rebuild containers, creating a highly efficient workflow.

#### **Works cited**

1. SvelteKit, an innovative front-end framework \- Lemon Hive, accessed June 29, 2025, [https://www.lemonhive.com/technologies/svelte-kit](https://www.lemonhive.com/technologies/svelte-kit)  
2. Svelte • Web development for the rest of us, accessed June 29, 2025, [https://svelte.dev/](https://svelte.dev/)  
3. Svelte & SvelteKit Tutorial: How to Build a Website From Scratch \- Prismic, accessed June 29, 2025, [https://prismic.io/blog/svelte-sveltekit-tutorial](https://prismic.io/blog/svelte-sveltekit-tutorial)  
4. What is SvelteKit? Overview of the Fastest Web Development Framework | Sanity, accessed June 29, 2025, [https://www.sanity.io/glossary/sveltekit](https://www.sanity.io/glossary/sveltekit)  
5. Building your app • Docs • Svelte, accessed June 29, 2025, [https://svelte.dev/docs/kit/building-your-app](https://svelte.dev/docs/kit/building-your-app)  
6. Unlock the Power of WebSockets with FastAPI: Real-Time Apps \- Seenode, accessed June 29, 2025, [https://seenode.com/blog/websockets-with-fastapi-real-time-apps-tutorial/](https://seenode.com/blog/websockets-with-fastapi-real-time-apps-tutorial/)  
7. Asynchronous Image Processing: A Deep Dive into FastAPI and WebSockets \- Medium, accessed June 29, 2025, [https://medium.com/@riddhimansherlekar/asynchronous-image-processing-a-deep-dive-into-fastapi-and-websockets-1facf13f776b](https://medium.com/@riddhimansherlekar/asynchronous-image-processing-a-deep-dive-into-fastapi-and-websockets-1facf13f776b)  
8. Getting Started with WebSockets in FastAPI | by Hex Shift | Jun, 2025 | Medium, accessed June 29, 2025, [https://medium.com/@hexshift/getting-started-with-websockets-in-fastapi-df54d06bc0ea](https://medium.com/@hexshift/getting-started-with-websockets-in-fastapi-df54d06bc0ea)  
9. WebSockets \- FastAPI, accessed June 29, 2025, [https://fastapi.tiangolo.com/advanced/websockets/](https://fastapi.tiangolo.com/advanced/websockets/)  
10. FastAPI and WebSockets: A Comprehensive Guide \- Orchestra, accessed June 29, 2025, [https://www.getorchestra.io/guides/fastapi-and-websockets-a-comprehensive-guide](https://www.getorchestra.io/guides/fastapi-and-websockets-a-comprehensive-guide)  
11. Integrating FastAPI with Celery for Background Task Processing | by ..., accessed June 29, 2025, [https://medium.com/@tomtalksit/integrating-fastapi-with-celery-for-background-task-processing-27a81ecffffc](https://medium.com/@tomtalksit/integrating-fastapi-with-celery-for-background-task-processing-27a81ecffffc)  
12. Celery and Background Tasks. Using FastAPI with long running tasks | by Hitoruna | Medium, accessed June 29, 2025, [https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d](https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d)  
13. FastAPI \+ Celery \= \- DEV Community, accessed June 29, 2025, [https://dev.to/derlin/fastapi-celery--33mh](https://dev.to/derlin/fastapi-celery--33mh)  
14. Packages \- Svelte Society, accessed June 29, 2025, [https://www.sveltesociety.dev/packages](https://www.sveltesociety.dev/packages)  
15. Svelte Flow: The Node-Based UI for Svelte, accessed June 29, 2025, [https://svelteflow.dev/](https://svelteflow.dev/)  
16. A curated list of awesome Svelte resources \- GitHub, accessed June 29, 2025, [https://github.com/TheComputerM/awesome-svelte](https://github.com/TheComputerM/awesome-svelte)  
17. Quickstart \- Svelte Flow, accessed June 29, 2025, [https://svelteflow.dev/learn](https://svelteflow.dev/learn)  
18. xyflow/awesome-node-based-uis \- GitHub, accessed June 29, 2025, [https://github.com/xyflow/awesome-node-based-uis](https://github.com/xyflow/awesome-node-based-uis)  
19. Examples \- Svelte Flow, accessed June 29, 2025, [https://svelteflow.dev/examples](https://svelteflow.dev/examples)  
20. Examples \- React Flow, accessed June 29, 2025, [https://reactflow.dev/examples](https://reactflow.dev/examples)  
21. Subflows \- Svelte Flow, accessed June 29, 2025, [https://svelteflow.dev/examples/layout/subflows](https://svelteflow.dev/examples/layout/subflows)  
22. Sub Flows \- Svelte Flow, accessed June 29, 2025, [https://svelteflow.dev/learn/layouting/sub-flows](https://svelteflow.dev/learn/layouting/sub-flows)  
23. Easy way to do basic editing with MoviePy \- Medium, accessed June 29, 2025, [https://medium.com/@oleksandrpypenko/video-editing-with-moviepy-3cc7a862fa52](https://medium.com/@oleksandrpypenko/video-editing-with-moviepy-3cc7a862fa52)  
24. Introduction to MoviePy \- GeeksforGeeks, accessed June 29, 2025, [https://www.geeksforgeeks.org/python/introduction-to-moviepy/](https://www.geeksforgeeks.org/python/introduction-to-moviepy/)  
25. Exploring MoviePy 2: A Modern Approach to Video Editing in Python, accessed June 29, 2025, [https://bastakiss.com/blog/python-5/exploring-moviepy-2-a-modern-approach-to-video-editing-in-python-618](https://bastakiss.com/blog/python-5/exploring-moviepy-2-a-modern-approach-to-video-editing-in-python-618)  
26. MoviePy documentation — MoviePy documentation, accessed June 29, 2025, [https://zulko.github.io/moviepy/](https://zulko.github.io/moviepy/)  
27. Use moviepy for video editing : r/learnpython \- Reddit, accessed June 29, 2025, [https://www.reddit.com/r/learnpython/comments/1isacp0/use\_moviepy\_for\_video\_editing/](https://www.reddit.com/r/learnpython/comments/1isacp0/use_moviepy_for_video_editing/)  
28. Edit decision list \- Wikipedia, accessed June 29, 2025, [https://en.wikipedia.org/wiki/Edit\_decision\_list](https://en.wikipedia.org/wiki/Edit_decision_list)  
29. simonh10/python-edl: A python EDL parsing library \- GitHub, accessed June 29, 2025, [https://github.com/simonh10/python-edl](https://github.com/simonh10/python-edl)  
30. iluvcapra/pycmx: Python CMX 3600 Edit Decision List Parser \- GitHub, accessed June 29, 2025, [https://github.com/iluvcapra/pycmx](https://github.com/iluvcapra/pycmx)  
31. EDL to CDL conversion tool \- ACES Resources & Education \- Community \- ACESCentral, accessed June 29, 2025, [https://community.acescentral.com/t/edl-to-cdl-conversion-tool/731](https://community.acescentral.com/t/edl-to-cdl-conversion-tool/731)  
32. Examples — EDL 0.2 documentation \- Read the Docs, accessed June 29, 2025, [https://edl.readthedocs.io/latest/examples.html](https://edl.readthedocs.io/latest/examples.html)  
33. How do I run the 'Black Forest Labs \- Flux 1 Kontext in my PC : r/FluxAI \- Reddit, accessed July 1, 2025, [https://www.reddit.com/r/FluxAI/comments/1lm56mu/how\_do\_i\_run\_the\_black\_forest\_labs\_flux\_1\_kontext/](https://www.reddit.com/r/FluxAI/comments/1lm56mu/how_do_i_run_the_black_forest_labs_flux_1_kontext/)  
34. black-forest-labs/FLUX.1-dev \- Hugging Face, accessed July 1, 2025, [https://huggingface.co/black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev)  
35. black-forest-labs/FLUX.1-schnell \- Hugging Face, accessed July 1, 2025, [https://huggingface.co/black-forest-labs/FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)  
36. black-forest-labs/flux: Official inference repo for FLUX.1 models \- GitHub, accessed July 1, 2025, [https://github.com/black-forest-labs/flux](https://github.com/black-forest-labs/flux)  
37. stackhpc/flux-image-model-inference: Official inference repo for FLUX.1 models \- GitHub, accessed July 1, 2025, [https://github.com/stackhpc/flux-image-model-inference](https://github.com/stackhpc/flux-image-model-inference)  
38. How to Run FLUX1 for Free: A Step-by-Step Guide \- DEV Community, accessed July 1, 2025, [https://dev.to/allmightenglishtech/how-to-run-flux1-for-free-a-step-by-step-guide-3h51](https://dev.to/allmightenglishtech/how-to-run-flux1-for-free-a-step-by-step-guide-3h51)  
39. Wan2GP- is an optimized open-source video generation model designed for low-configuration GPU users, supporting multiple video generation tasks. \- AIbase, accessed July 1, 2025, [https://www.aibase.com/tool/36446](https://www.aibase.com/tool/36446)  
40. Wan2GP FusionX (Text to Video) Showcase \- Nvidia 4090\. 832x480, 81 frames, 8 steps, TeaCache 2.5x : r/StableDiffusion \- Reddit, accessed July 1, 2025, [https://www.reddit.com/r/StableDiffusion/comments/1lolwki/wan2gp\_fusionx\_text\_to\_video\_showcase\_nvidia\_4090/](https://www.reddit.com/r/StableDiffusion/comments/1lolwki/wan2gp_fusionx_text_to_video_showcase_nvidia_4090/)  
41. How to Run Advanced AI Models on Old GPU | Wan2GP Video Generator Guide \- YouTube, accessed July 1, 2025, [https://www.youtube.com/watch?v=DQ92CmedQz0\&vl=de](https://www.youtube.com/watch?v=DQ92CmedQz0&vl=de)  
42. Generate High Quality Video Using 6 Steps With Wan2.1 FusionX Model (worked with RTX 3060 6GB) \- Reddit, accessed July 1, 2025, [https://www.reddit.com/r/comfyui/comments/1liuyao/generate\_high\_quality\_video\_using\_6\_steps\_with/](https://www.reddit.com/r/comfyui/comments/1liuyao/generate_high_quality_video_using_6_steps_with/)  
43. Looking for an easy to use AI video generator. : r/StableDiffusion \- Reddit, accessed July 1, 2025, [https://www.reddit.com/r/StableDiffusion/comments/1lmyp64/looking\_for\_an\_easy\_to\_use\_ai\_video\_generator/](https://www.reddit.com/r/StableDiffusion/comments/1lmyp64/looking_for_an_easy_to_use_ai_video_generator/)  
44. Exploring the World of Open-Source Text-to-Speech Models \- BentoML, accessed July 1, 2025, [https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)  
45. \[Open Source\] DJ-IA VST \- AI Music Generation Plugin (Looking for Collaborators\!) \- Instruments Forum \- KVR Audio, accessed July 1, 2025, [https://www.kvraudio.com/forum/viewtopic.php?t=621098](https://www.kvraudio.com/forum/viewtopic.php?t=621098)  
46. 5 Open Source Generative Music Models You Can't Miss \- YouTube, accessed July 1, 2025, [https://www.youtube.com/watch?v=GQfKoIMpea8](https://www.youtube.com/watch?v=GQfKoIMpea8)  
47. Hosting a ComfyUI Workflow via API \- 9elements, accessed June 29, 2025, [https://9elements.com/blog/hosting-a-comfyui-workflow-via-api/](https://9elements.com/blog/hosting-a-comfyui-workflow-via-api/)  
48. fofr/any-comfyui-workflow | Readme and Docs \- Replicate, accessed June 29, 2025, [https://replicate.com/fofr/any-comfyui-workflow/readme](https://replicate.com/fofr/any-comfyui-workflow/readme)  
49. SaladTechnologies/comfyui-api: A simple wrapper API server that facilitates using ComfyUI as a stateless API, either by receiving outputs in the response, or by sending completed outputs to a webhook \- GitHub, accessed June 29, 2025, [https://github.com/SaladTechnologies/comfyui-api](https://github.com/SaladTechnologies/comfyui-api)