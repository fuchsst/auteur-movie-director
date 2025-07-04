

# **The Generative Filmmaking Pipeline: A Methodological Breakdown from Concept to Command**

## **Introduction**

The central challenge of modern generative filmmaking lies in the translation of abstract, nuanced human creative intent into the precise, structured, and logical language required by sophisticated artificial intelligence models. This is a complex problem of both artistic interpretation and technical orchestration. A director's vision, a writer's prose, or an emotional beat must be deconstructed and reassembled into a series of commands that a machine can execute. Failure to manage this complexity results in a chaotic and unpredictable creative process, yielding inconsistent outputs that fail to form a cohesive narrative. The solution is not to simplify the creative vision, but to adopt a systematic framework capable of managing its inherent intricacy.

This report details such a framework, built upon the foundational hierarchy of traditional filmmaking: Project \-\> Chapter \-\> Scene \-\> Shot \-\> Take. This structure serves as a systematic funnel, guiding the creative process through progressive stages of refinement. It allows a high-level narrative concept, initially captured in a screenplay or a simple prompt, to be methodically broken down into atomic, executable instructions for the generative engine. This document provides the definitive, step-by-step methodology for this translation process. It will detail the flow of work, the digital artifacts created and utilized at each stage, and the key user interactions required to navigate the pipeline. By blending creative strategy with technical implementation, this report serves as a comprehensive manual for the filmmaker or creative technologist operating within an advanced generative media studio, transforming the potential of AI from a novelty into a controllable, professional-grade production tool.

## **Section 1: From Idea to Narrative Framework: Structuring the Core Story**

Before a single line of a screenplay is written or parsed, the generative process begins with the most fundamental element: the core idea. This initial input is often unstructured—a simple text prompt, a logline, a one-page synopsis, or a collection of contextual documents uploaded by the user. The first critical step in the pipeline is to transform this raw creative spark into a structured narrative blueprint. This is achieved by applying established principles of dramatic structure, providing a scaffold that gives the story shape, momentum, and emotional resonance.

### **Choosing a Narrative Archetype**

The system facilitates this transformation by presenting the user with a selection of proven narrative structures, or "dramatic arcs." Each structure offers a different model for organizing plot points and character development, allowing the user to select the framework that best aligns with their story's intent. The choice of structure is a foundational decision that will guide the subsequent development of the plot, characters, and emotional beats. The following table outlines several common structures available as templates within the system.

#### **Table 1: Comparative Dramatic Structures**

| Structure | Key Stages | Best For | Core Principle |
| :---- | :---- | :---- | :---- |
| **Three-Act Structure** | Act I: Setup, Inciting Incident Act II: Rising Action, Midpoint, Confrontation Act III: Climax, Resolution | General storytelling; provides a clear beginning, middle, and end for most genres. | A logical, causal progression of events that builds tension toward a satisfying resolution. |
| **The Hero's Journey** | Ordinary World, Call to Adventure, Meeting the Mentor, Crossing the Threshold, Ordeal, Reward, The Road Back, Resurrection, Return with the Elixir | Epic adventures, fantasy, myths, and character-focused tales of profound transformation. | A character ventures from their known world into the unknown, overcomes a decisive crisis, and returns transformed. |
| **Blake Snyder Beat Sheet** | 15 specific beats including: Opening Image, Theme Stated, Catalyst, Fun & Games, Midpoint, All Is Lost, Dark Night of the Soul, Finale, Final Image 1 | Commercial screenplays requiring tight pacing and specific emotional and plot checkpoints. | A granular, beat-by-beat formula that maps out the story's emotional highs and lows against page counts. |
| **Dan Harmon's Story Circle** | 1\. You (Comfort Zone) 2\. Need (Want something) 3\. Go (Unfamiliar Situation) 4\. Search (Adapt) 5\. Find (Get what you want) 6\. Take (Pay a heavy price) 7\. Return 8\. Change | Character-driven stories, episodic content, and narratives focused on a cyclical journey of change. | A character leaves their zone of comfort to pursue a need, faces chaos, and returns home having been fundamentally changed. |

### **Developing the Story Blueprint**

Once a narrative structure is selected, the user is guided through the process of populating its key stages. For instance, if the Three-Act Structure is chosen, the user would define the inciting incident that kicks off the conflict, the obstacles that create the rising action, the climactic confrontation, and the final resolution. This interactive process encourages the writer to think through the essential story elements: the protagonist's goal, the central conflict, the primary setting, and the character's emotional arc.

The output of this crucial pre-production phase is a structured document, such as a **treatment** or a detailed **outline**. This artifact serves as the definitive blueprint for the story, bridging the gap between a high-level idea and a fully realized narrative. This structured outline then becomes the direct source material for writing the screenplay in a parsable format like Fountain, ensuring that the subsequent technical stages of the pipeline are built upon a solid and coherent narrative foundation.

## **Section 2: The Agentic Production Crew: From Concept to Executable Plan**

With a structured story blueprint in hand, the pipeline transitions from high-level ideation to detailed pre-production. This is accomplished not by a single monolithic process, but by a collaborative, multi-agent system. This approach is inspired by frameworks like the Breakthrough Method of Agile Agentic-Driven Development (BMAD-METHOD), which advocates for using a team of specialized AI agents to enhance project planning and execution.2 The implementation leverages a powerful multi-agent automation framework, CrewAI, to orchestrate this team of digital "creatives." 4

### **The CrewAI Implementation: A Team of Specialists**

The system assembles a Crew of role-based AI agents, each with a specific goal, backstory, and set of tools tailored to a distinct function within the filmmaking process.4 This mirrors a real-world production team, where specialists collaborate to break down a complex creative vision into manageable, executable parts.7 The user acts as the Executive Producer, providing the initial creative direction and offering feedback at key stages, ensuring the final output remains true to their vision in a "human-in-the-loop" workflow.2

#### **Table 2: The Agentic Production Crew Roster**

| Agent Role | Goal | Key Task & Tools |  |
| :---- | :---- | :---- | :---- |
| **Producer** | To oversee the entire creative breakdown from the initial concept to a shoot-ready plan. | Manages the Crew process, defines and assigns Tasks to other agents, and ensures the final output aligns with the user's initial input and the chosen dramatic structure.4 |  |
| **Screenwriter** | To transform the structured story outline into a complete, engaging screenplay with compelling scenes, action, and dialogue. | **Task:** write\_screenplay. Receives the outline from the Producer and generates the full script. The output is a structured text document that forms the basis for all subsequent work.9 |  |
| **Art Director** | To analyze the screenplay and define the project's overall visual aesthetic, mood, and color palette. | **Task:** define\_visual\_style. Analyzes the script for thematic and emotional cues. Creates Style assets by defining descriptive keywords for lighting, color, and composition that will be injected into image generation prompts.6 |  |
| **Casting Director** | To analyze the screenplay to identify, describe, and conceptualize all characters. | **Task:** define\_characters. Scans the script for every character. Creates Character assets, including detailed physical and personality descriptions, which are used to generate reference imagery and form the basis for training character-specific LoRA models.10 |  |
| **Location Scout** | To analyze the screenplay to identify and visualize all required settings and locations. | **Task:** define\_locations. Identifies every unique location from the scene headings. Creates Location assets with rich descriptions and reference image prompts to ensure environmental consistency.6 |  |
| **First AD** | To perform the final, granular breakdown of the script into a list of executable shots with detailed generative instructions. | **Task:** create\_shot\_list. Takes the final script and all defined Style, Character, and Location assets as its context.9 It then generates the comprehensive | Generative Shot List for each scene. |

### **The Collaborative Workflow: A Step-by-Step Breakdown**

The Producer agent orchestrates the crew through a series of sequential and parallel tasks, transforming the initial idea into a set of precise instructions for the generative engine.4

1. **Initiation and Scriptwriting:** The user provides the initial concept and the structured outline (from Section 1\) to the Producer agent.11 The  
   Producer assigns the write\_screenplay task to the Screenwriter agent. The user then reviews, edits, and approves the generated script, providing critical human feedback to guide the creative process.2  
2. **Parallel Asset Definition:** Once the script is approved, the Producer passes it as context to the Art Director, Casting Director, and Location Scout agents. These agents work in parallel, each executing their respective define\_visual\_style, define\_characters, and define\_locations tasks simultaneously.11 This parallel processing dramatically accelerates the pre-production phase. The user reviews the generated  
   Style, Character, and Location assets, making refinements as needed.  
3. **Final Shot Breakdown:** With the script and all creative assets finalized, the Producer assigns the final task, create\_shot\_list, to the First AD agent. This agent receives the script and the complete collection of assets as its context, ensuring it has all the necessary information.9 It then meticulously breaks down each scene into individual shots, generating the final, crucial artifact: The  
   Generative Shot List. This document contains the specific, multi-modal prompts required to generate every visual and auditory element of the film.

This agentic, step-by-step process, guided by human oversight, ensures that the initial abstract idea is methodically and efficiently translated into a detailed, technically grounded, and executable production plan.

## **Section 3: The Atomic Unit of Creation: Prompting the Shot**

This section details the most granular and creatively vital stage of the pipeline: the definition of a single shot. This is the nexus where all high-level planning, narrative deconstruction, and asset creation—now orchestrated by the Agentic Production Crew—converge into a specific, multi-modal, and executable set of instructions for the AI. It is here that the filmmaker's vision is translated into the literal commands that will generate the final pixels and sounds.

### **The Generative Shot List: The Director's Blueprint**

In traditional production, a shot list is the director's and cinematographer's primary blueprint for a day's shoot. It breaks a scene down into its constituent camera setups, specifying crucial details like shot size (e.g., Close-Up, Wide Shot), camera angle, camera movement, lens choice, and a brief description of the action or subject.13

The Generative Shot List is the digital evolution of this essential artifact, now produced as the final output of the First AD agent. It is the primary user interface—a form or a set of fields within the Properties Inspector—that the user fills out for each Shot node on the Production Canvas. However, its function is expanded. Instead of merely describing the shot for a human crew, it directly translates these cinematic concepts into the parameters and prompt components required by the generative models. A "Medium Shot" is no longer just a description; it becomes a specific keyword or set of keywords like (medium shot:1.2) that the AI can interpret. A "Dolly In" is not an instruction for a grip; it is a parameter like motion\_strength or direction for a Generate Video from Image node. This interface acts as a translator between the established language of filmmaking and the new language of generative AI.

### **The Composite Prompt: A Multi-Modal Instruction Set**

A fundamental aspect of this system's power is its sophisticated understanding of what constitutes a "prompt." The Text-to-Image node, for example, has input sockets not only for a text string but also for Character and Style AssetReferences. Other nodes are designed to accept audio files, video clips, or specialized ControlMap images. This architecture reveals that a prompt is not a monolithic string of text entered into a single box. It is a composite data object, a packet of instructions assembled dynamically from multiple sources.

This assembly of pointers is the core mechanism for achieving fine-grained, modular control over the generative process. When a user configures a Shot, they are not just writing a sentence; they are constructing a complete instruction set for the backend. This set is composed of several distinct types of instructions:

1. **Direct Instructions (Text):** This is the user-written text prompt that describes the action, composition, and specific visual details of the shot (e.g., "standing by the window, looking out at the pouring rain"). This text is combined with generation parameters like CFG Scale, Steps, and Seed, which are tuned based on the chosen generative model, such as FLUX.16  
2. **Identity Instructions (AssetReference):** This is a pointer to a Character asset, such as Character: John. When the generation task is initiated, the backend system resolves this UUID, locates the associated LoRA model file (e.g., john\_v2.safetensors), and programmatically injects its unique trigger word and weight (e.g., \<lora:john\_v2:0.7\>) into the final prompt string that is sent to the AI model.17 This ensures that the character's specific, trained appearance is rendered.  
3. **Aesthetic Instructions (AssetReference):** This is a pointer to a Style asset, such as Style: Noir. The backend resolves this reference and appends its associated collection of keywords (e.g., film noir, high contrast, dramatic shadows, gritty, desaturated color palette) to the prompt. This enforces a consistent visual and tonal language across different shots.  
4. **Auditory Instructions (File Path):** This is a pointer to a specific audio file, such as a line of dialogue (scene15\_john\_line1.wav) intended for a LipSync node, or a musical cue (Tense\_Underscore\_V2.mp3) for a Combine Audio node.

This composite, pointer-based approach to prompting is the system's strategic advantage. It allows for a powerful separation of concerns: the shot's specific action is defined in the text prompt, the character's identity is encapsulated within the LoRA, the overall aesthetic is governed by the Style asset, and the sound is managed by separate audio files. This makes the entire creative workflow modular, reusable, and vastly more controllable than simplistic text-only prompting.

The following table represents the ultimate artifact of the entire breakdown process. It is the direct, practical answer to the challenge of translating a movie idea into machine instructions. By methodically completing this "Generative Shot List" for each shot in a scene, the user constructs the exact set of commands the generative engine requires for execution.

#### **Table 3: The Comprehensive Generative Shot List**

| Scene: 15 | Shot \#: 15A | Description: John looks out the window at the rain, feeling the weight of his decision. |
| :---- | :---- | :---- |
| **Element Type** | **Traditional Concept** | **Generative Parameter / Prompt Component** |
| **Visuals** | Shot Size / Angle | (medium shot:1.2), (from a low angle:1.1) |
|  | Image Prompt (Text) | a man stands by a large, grimy warehouse window, looking out at the pouring rain, contemplative expression, cinematic lighting |
|  | Negative Prompt | cartoon, drawing, anime, blurry, watermark, text, signature |
|  | Generation Params | CFG Scale: 3.5, Steps: 30, Dimensions: 1920x1080 |
| **Identity** | Character | **AssetReference:** Character: John (UUID: char-john-v2) |
| **Aesthetic** | Style / Mood | **AssetReference:** Style: Project\_Odyssey\_Noir (UUID: style-noir-v1) |
| **Audio** | Dialogue | **Audio File:** dialogue/S15\_John\_L1.wav ("It's all over now.") |
|  | Music | **Audio File:** music/Tense\_Underscore\_V2.mp3 |
| **Animation** | Camera Movement | Slow Push-in |

## **Section 4: The Creative Loop: Iteration, Takes, and Emotional Pacing**

The act of generation in a creative context is rarely a linear, one-shot process. It is an inherently iterative loop of creation, evaluation, and refinement. This section explores the system's mechanisms for supporting this dynamic workflow and introduces a higher-level creative artifact—the Emotional Beat Sheet—that serves to guide the tonal and emotional trajectory of the prompting process itself.

### **Non-Destructive Iteration: The "Takes" System**

A core principle of any professional creative software is the provision of a non-destructive workflow. Artists must be free to experiment, explore variations, and make changes without the fear of permanently losing previous work. The generative studio implements this principle through its "Takes" system.

Every time a user clicks the "Generate" button on a node, the system's backend does not overwrite the previous output. Instead, it creates a new, uniquely versioned file, saved to a predictable location within the project's directory structure (e.g., 03\_Renders/SCENE\_01/SHOT-015/SHOT-015\_v01\_take04.png). These generated variations, or "Takes," are then presented to the user within the UI as a "Takes Gallery"—a scrollable grid of thumbnails located in the Properties Inspector for the selected node.

This simple yet powerful mechanism is the engine of creative iteration. The user can subtly tweak a word in a prompt, change the random seed, adjust the CFG scale, or even swap out an entire Style asset and generate a new Take to see the result. They can then instantly compare Take 04 with Take 03, switching between them to evaluate which version is more effective. The user selects an "active" take, which is then used as the input for any downstream nodes in the graph, but all other takes are preserved indefinitely. This workflow, deeply integrated with the Project-as-Repository model where every asset is version-controlled, encourages fearless experimentation and is fundamental to refining the AI's output to meet a specific artistic standard.

### **Guiding the Mood: The Emotional Beat Sheet**

While the screenplay provides the literal content of the film—the "what" of the action and dialogue—it does not always explicitly convey the intended emotional subtext or the desired feeling of a scene. To bridge this gap, filmmakers often use a beat sheet, a document that breaks the story down not by action, but by its key emotional moments and turning points.1 This high-level creative document, likely stored as a text file in the project's

02\_Source\_Creative/Scripts/ directory, becomes an essential guide for the director or creative lead during the prompting process.

The Emotional Beat Sheet acts as a crucial translation layer between narrative theory and practical prompt engineering. It provides the "how it should feel" that informs the "what to type." For example, if a sequence of shots falls under the "All is Lost" beat from a structure like Blake Snyder's Beat Sheet, the prompter has a clear directive.1 They know to move beyond literal descriptions of the action and incorporate keywords and parameters that evoke the desired mood of despair and hopelessness. This might involve adding terms like

rainy, dark, cold blue tones, and dramatic shadows to the Style prompts, or instructing the music generation node to create a slow, melancholic, minor-key piano piece. This ensures that every generated element—visuals, music, and even the pacing of animation—is working in concert to serve the intended emotional impact of that specific story moment. This practice elevates prompting from a simple act of description to a nuanced art of tonal direction, ensuring the final film possesses a cohesive and powerful emotional arc.

The following table provides a practical guide for this translation process. It connects the high-level goals of storytelling to the concrete, low-level components of an AI prompt, creating a systematic approach to infusing the generated content with the correct mood and feeling.

#### **Table 4: Emotional Beat to Prompt Keyword Translation Guide**

| Narrative Beat (Blake Snyder) | Emotional Goal | Image/Style Keywords | Music/Audio Cues | Example Character Expression Prompt |
| :---- | :---- | :---- | :---- | :---- |
| **Catalyst** | Intrigue, Disruption, Action | dynamic angle, dutch angle, motion blur, dramatic lighting, vibrant colors, lens flare | Sudden musical sting, uptempo rhythm, sharp sound effect: crash, bang, shatter | (surprised expression:1.3), shocked, eyes wide open, jaw slightly dropped |
| **Fun and Games** | Rising Action, Joy, Success | bright sunlight, warm golden hour light, playful composition, saturated colors, clean focus | Upbeat, major-key theme, energetic rhythm, playful sound design | (wide smile:1.2), laughing, confident posture, gleam in the eye |
| **Midpoint** | Point of No Return, False Victory/Defeat | epic wide shot, high contrast, overly bright (false victory) or deep shadows (false defeat) | Triumphant or ominous swell in the musical score, a moment of silence before a loud sound | determined expression, a look of grim realization, overwhelmed |
| **All Is Lost** | Despair, Defeat, Hopelessness | pouring rain, dark, night, long shadows, desaturated, cold blue tones, film noir aesthetic | Slow, melancholic, minor-key piano, ambient silence with distant thunder, somber strings | (sad expression:1.4), crying, slumped shoulders, empty stare, face hidden in shadow |
| **Finale** | Climax, Resolution, Synthesis | heroic low-angle shot, strong backlighting, cinematic slow motion, richly saturated colors | Full orchestral score, triumphant reprise of the main theme, explosive sound design | determined face, a look of relief, powerful stance, a single tear of victory |

## **Conclusion and Expert Recommendations**

The generative filmmaking pipeline detailed in this report represents a systematic and powerful methodology for translating creative vision into machine-executable reality. The workflow is a structured funnel of progressive refinement, moving from a high-level concept, which is then elaborated by an Agentic Production Crew into a detailed screenplay and a Generative Shot List. This entire process is guided by the high-level tonal direction of an Emotional Beat Sheet and supported by the iterative freedom of the Takes system. The result is a production process that is not only capable of generating high-quality media but is also predictable, controllable, and scalable.

The strategic value of this system is rooted in its sophisticated separation of concerns. It treats the core components of a film—character identity (via Character LoRAs), aesthetic language (via Style assets), narrative action (via Shot prompts), and emotional tone (via Beat Sheet guidance)—as independent, modular, and combinable elements. This modularity, managed by a crew of specialized AI agents, allows for immense flexibility and reusability, enabling a creative workflow that is both efficient and deeply expressive. It empowers the filmmaker to exert precise control over the final output while abstracting away the immense complexity of the underlying AI models.

To maximize the potential of this powerful platform, the following expert recommendations for best practice should be adopted:

1. **Invest in Asset Libraries:** The single greatest accelerator for this workflow is the development of a rich, well-curated, and comprehensive library of Character, Style, and Location assets. A robust library of reusable components dramatically speeds up the production of new scenes and ensures consistency across the entire project. Time spent building high-quality assets is an investment that pays significant dividends throughout the production lifecycle.  
2. **Embrace Iteration:** The Takes system is a core feature designed to be used liberally. The first generated output is rarely the best. Filmmakers should embrace an iterative mindset, constantly tweaking prompts, adjusting parameters, and generating new variations to explore the creative possibility space. This process of experimentation and refinement is essential for honing the AI's output to meet a specific artistic vision.  
3. **Prompt with Emotion, Not Just Description:** A successful generative film requires more than just visually accurate shots; it requires an emotional arc. The Emotional Beat Sheet is a critical tool for achieving this. Prompts should be guided by the emotional goals of the scene, using keywords for lighting, color, composition, and music that evoke the intended feeling. This ensures the final product is not just a sequence of images, but a cohesive and impactful story.  
4. **Structure Before You Generate:** The rigor of the initial story structuring and the agentic breakdown process is not administrative overhead; it is the necessary preparation that enables efficient, predictable, and high-quality generative production at scale. A well-structured plan, with clearly defined assets and detailed shot instructions, minimizes ambiguity and provides the AI with the clear, logical commands it needs to perform optimally. In generative filmmaking, disciplined planning is the bedrock of creative freedom.

#### **Works cited**

1. Blake Snyder's Beat Sheet \- Tim Stout, accessed July 3, 2025, [https://timstout.wordpress.com/story-structure/blake-snyders-beat-sheet/](https://timstout.wordpress.com/story-structure/blake-snyders-beat-sheet/)  
2. bmadcode/BMAD-METHOD: Breakthrough Method for ... \- GitHub, accessed July 4, 2025, [https://github.com/bmadcode/BMAD-METHOD](https://github.com/bmadcode/BMAD-METHOD)  
3. bmadcode/BMAD-METHOD: Breakthrough Method for Agile Ai Driven Development, accessed July 4, 2025, [https://app.daily.dev/posts/bmadcode-bmad-method-breakthrough-method-for-agile-ai-driven-development-nv25ulv9j](https://app.daily.dev/posts/bmadcode-bmad-method-breakthrough-method-for-agile-ai-driven-development-nv25ulv9j)  
4. Introduction \- CrewAI, accessed July 4, 2025, [https://docs.crewai.com/introduction](https://docs.crewai.com/introduction)  
5. Framework for orchestrating role-playing, autonomous AI agents. By fostering collaborative intelligence, CrewAI empowers agents to work together seamlessly, tackling complex tasks. \- GitHub, accessed July 4, 2025, [https://github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)  
6. Agents \- CrewAI, accessed July 4, 2025, [https://docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents)  
7. 10 Best CrewAI Projects You Must Build in 2025 \- ProjectPro, accessed July 4, 2025, [https://www.projectpro.io/article/crew-ai-projects-ideas-and-examples/1117](https://www.projectpro.io/article/crew-ai-projects-ideas-and-examples/1117)  
8. Multi AI Agent Systems with crewAI \- DeepLearning.AI, accessed July 4, 2025, [https://learn.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai/lesson/wwou5/introduction](https://learn.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai/lesson/wwou5/introduction)  
9. Tasks \- CrewAI, accessed July 4, 2025, [https://docs.crewai.com/en/concepts/tasks](https://docs.crewai.com/en/concepts/tasks)  
10. Create Consistent Original Character LoRAs in Stable Diffusion | Everly Heights, accessed July 3, 2025, [https://everlyheights.tv/blog/create-consistent-original-character-loras-in-stable-diffusion/](https://everlyheights.tv/blog/create-consistent-original-character-loras-in-stable-diffusion/)  
11. Crew AI Crash Course (Step by Step) \- Alejandro AO, accessed July 4, 2025, [https://alejandro-ao.com/crew-ai-crash-course-step-by-step/](https://alejandro-ao.com/crew-ai-crash-course-step-by-step/)  
12. Tutorial: Building AI agents with CrewAI | Generative-AI – Weights & Biases \- Wandb, accessed July 4, 2025, [https://wandb.ai/byyoung3/Generative-AI/reports/Tutorial-Building-AI-agents-with-CrewAI--VmlldzoxMTUwNTA4Ng](https://wandb.ai/byyoung3/Generative-AI/reports/Tutorial-Building-AI-agents-with-CrewAI--VmlldzoxMTUwNTA4Ng)  
13. Shot List Template — Free Download and Ultimate Guide (2024) \- StudioBinder, accessed July 3, 2025, [https://www.studiobinder.com/blog/shot-list-template-free-download/](https://www.studiobinder.com/blog/shot-list-template-free-download/)  
14. Save Time & Money with a Shot List (Free Template Included) \- Wrapbook, accessed July 3, 2025, [https://www.wrapbook.com/blog/shot-list](https://www.wrapbook.com/blog/shot-list)  
15. How to Write A Shot List That Will Transform Your Video \- TechSmith, accessed July 3, 2025, [https://www.techsmith.com/blog/shot-list/](https://www.techsmith.com/blog/shot-list/)  
16. Recommended Parameters for Image Generation Models \- GPUStack, accessed July 3, 2025, [https://docs.gpustack.ai/0.4/tutorials/recommended-parameters-for-image-generation-models/](https://docs.gpustack.ai/0.4/tutorials/recommended-parameters-for-image-generation-models/)  
17. How to create new unique and consistent characters with Loras : r/StableDiffusion \- Reddit, accessed July 3, 2025, [https://www.reddit.com/r/StableDiffusion/comments/142bou7/how\_to\_create\_new\_unique\_and\_consistent/](https://www.reddit.com/r/StableDiffusion/comments/142bou7/how_to_create_new_unique_and_consistent/)  
18. Flux AI Image Generator: A Guide With Examples \- DataCamp, accessed July 3, 2025, [https://www.datacamp.com/tutorial/flux-ai](https://www.datacamp.com/tutorial/flux-ai)  
19. Beat Sheets Help Plan a Scene's Actions & Emotions \- Darcy Pattison, accessed July 3, 2025, [https://www.darcypattison.com/writing/scenes/scene-5-beat-sheets/](https://www.darcypattison.com/writing/scenes/scene-5-beat-sheets/)