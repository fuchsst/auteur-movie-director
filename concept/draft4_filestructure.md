

# **An Architectural Blueprint for a Scalable, File-Based Project Structure for a Generative Media Application**

## **Section 1: Foundational Principles of Data-Intensive Project Organization**

The design of a file and directory structure for any data-intensive application is a foundational architectural decision. For a generative media tool, where projects involve a heterogeneous mix of source code, configuration data, small text-based assets, and large binary media, this structure is paramount. It dictates not only the application's maintainability and scalability but also its usability for both human artists and automated processes. A successful file structure is not merely a collection of folders; it is a physical manifestation of a project's conceptual model, engineered to be legible, predictable, and robust. This section establishes the core philosophies that underpin the proposed architecture, drawing from best practices in software engineering, data science, and professional film production to create a durable foundation.

### **1.1 The Workspace vs. Project Dichotomy: Centralized Libraries and Self-Contained Projects**

Professional creative workflows operate on a two-tiered model: the individual project and the broader studio environment that supports it. This architecture adopts the same powerful paradigm by establishing a clear distinction between the **Workspace** and the **Project**.1

The **Workspace** is the highest-level container for the entire application environment. It is the digital equivalent of the studio itself. The Workspace is responsible for housing resources that are shared and reused across multiple, distinct creative endeavors. This includes global asset libraries such as licensed stock music, branding elements like logos and fonts, and reusable technical assets like color grading Look-Up Tables (LUTs) or effect presets.2 For a generative application, this global library also serves as the ideal location for

Pipeline\_Templates—reusable ComfyUI workflow files or Python script configurations that represent common generative techniques, as described in the application's "Production Canvas" concept.\[1, 1\]

In contrast, the **Project** is a discrete, self-contained, and portable unit of work. Each project folder represents a single film or creative piece. It is designed to be its own universe, containing all the specific assets, creative source files, configurations, and generated outputs required for that one production.1 A project should be able to be moved, archived, or shared as a single entity without breaking its internal dependencies.

This fundamental separation provides several critical advantages. It promotes asset reusability, preventing the duplication of common files across dozens of projects. It keeps individual project repositories lean and focused, as they do not need to contain the entire studio's library. Finally, it establishes a clean, logical boundary that is intuitive for users and simplifies programmatic tasks like project creation, loading, and archiving.

### **1.2 The Principle of Separation of Concerns**

A cornerstone of any maintainable system is the principle of Separation of Concerns, which dictates that different categories of data should be isolated based on their origin, mutability, and purpose.3 Applying this principle to the file system hierarchy prevents a host of common problems, including repository bloat, accidental deletion of source files, and confusion between raw materials and final products. The proposed architecture enforces this separation through a clear directory structure organized around the following distinctions:

* **Source vs. Derivative:** It is critical to physically separate human-created or ingested "source" files from machine-generated "derivative" files. Source files—such as node graph definitions, text prompts, raw camera footage, and character reference images—are the irreplaceable creative input. Derivative files—such as rendered video clips, transcoded media, or cached thumbnail images—can, in principle, be regenerated from the source files and the application's logic. Storing them in separate top-level directories (e.g., 01\_Assets and 02\_Source\_Creative vs. 03\_Renders and 05\_Cache) makes it clear what is precious and what is disposable. This simplifies backup strategies and prevents generated files from cluttering the primary creative workspace.3  
* **Data vs. Code vs. Configuration:** The application's own source code must be entirely distinct from the user's project data. Likewise, project-level configuration should be managed explicitly. The proposed structure places all user-generated project data within a Projects folder, which is separate from the application's installation directory. Within each project, a central project.json file acts as the primary configuration manifest, defining the project's identity and core parameters.  
* **Transient vs. Persistent:** Temporary, non-essential data used to improve performance (e.g., caches) or for diagnostics (e.g., logs) must be isolated from the persistent, essential project data. A dedicated 05\_Cache directory, which can be safely deleted and is explicitly excluded from version control, serves this purpose. This prevents transient files from being accidentally committed to version control, which would permanently bloat the project's history.4

### **1.3 Immutability and Atomic Versioning**

To ensure a reliable and auditable production history, the system must treat all generated outputs as immutable artifacts. When a new version of a shot is rendered, it must not overwrite the previous version. Instead, it must be saved as a new, uniquely named file.6 This practice eliminates the ambiguity of file names like

Shot\_01\_Final.mp4 or Shot\_01\_Final\_v2\_USE\_THIS\_ONE.mp4, which are a common source of error in manual workflows.

The architecture enforces this through a strict, programmatic file naming convention for all versioned outputs. For example, a rendered take for a specific shot would be named SHOT-010\_v01\_take01.mp4. This name is atomic and contains all necessary metadata: the shot identifier, the major version of the creative setup, and the specific take number. This system maps directly to the "Intermediate Result Versioning ('Takes')" feature specified in the application's UI design, where a user can generate multiple attempts for a single shot and select the active one.\[1, 1\] By making the file system the unambiguous source of truth for the project's history, we create a non-destructive workflow where artists can iterate freely without fear of losing previous work.

### **1.4 Human-Readable vs. Machine-Parsable Naming**

A well-designed structure must be legible to both its human users and the software that operates on it. This requires a hybrid approach to naming conventions that balances discoverability with the need for precise, unique identifiers.3

For high-level organization, the system will use descriptive, human-readable folder names (e.g., /Projects/Client\_X\_Commercial/). This allows users to easily navigate and understand the project hierarchy in a standard file browser.6

However, for programmatic access, relying on mutable, human-readable names is brittle. Therefore, at the root of each project lies a critical machine-readable manifest: the project.json file. This file contains essential metadata, including a universally unique identifier (UUID) for the project, its title, a detailed description, and pointers to key files like the main "Production Canvas" graph. When the application's backend needs to perform an operation, it references the project by its immutable UUID. The project.json file then acts as the authoritative index, providing the agentic framework with the stable, machine-parsable information it needs to locate assets and execute tasks reliably.

The rigor of this overall structure serves a purpose beyond simple organization; it establishes a physical API contract for the application's automated backend. The "Producer" agent, as described in the application's architecture, is responsible for orchestrating complex generative tasks.\[1, 1\] An agent tasked with training a character model or rendering a shot does not need to query a database or parse complex configuration to find its inputs. It can programmatically construct the exact path to a character's reference images or the output directory for a specific shot's renders based on a set of simple inputs (e.g., project root path, character name, shot number). This convention-over-configuration approach dramatically simplifies the agentic logic, making the backend more robust, predictable, and easier to maintain. The file system itself becomes a form of API, where the "endpoints" are the well-defined directory paths, and the "contract" is the consistent structure enforced across all projects.

## **Section 2: The Unified Project Workspace: A Concrete Directory Structure**

This section provides the central deliverable of this report: a detailed, prescriptive blueprint for the file and folder hierarchy. This structure translates the foundational principles into an actionable plan. It is a synthesis of best practices from traditional film production 1, which prioritize workflow logic, and modern data science project management 3, which emphasizes the separation of data, code, and outputs. This hybrid model is specifically adapted to the unique needs of a generative AI workflow.

### **2.1 The Workspace Root (/Generative\_Studio\_Workspace/)**

The Workspace is the single, top-level directory on the user's machine or a shared network drive. It serves as the master container for the application's global resources and all individual user projects.

* Library/: This directory is a global, cross-project repository for reusable assets and templates. Its contents are intended to be read-only from within a project context to prevent accidental modification.  
  * Branding/: Contains globally applicable branding assets like logos, standard fonts, and corporate style guides.2  
  * LUTs\_and\_Presets/: Houses reusable color lookup tables (LUTs), visual effect presets, and other configuration files that can be applied across different projects.2  
  * Stock\_Media/: A library for licensed assets, including stock music, sound effects (SFX), and stock video footage.2  
  * Pipeline\_Templates/: A critical directory for a generative workflow. It stores reusable backend templates, such as ComfyUI API-formatted .json files or Python script wrappers, that correspond to the Pipeline Node concept in the application's UI. This allows users to define and reuse complex generative processes across projects.\[1, 1\]  
* Projects/: This directory is the container for all individual, self-contained projects. Each subdirectory within Projects/ is a complete, isolated production environment.

### **2.2 Anatomy of a Single Project (/Projects/PROJECT\_NAME/)**

Every new project created by the application will be generated from a standard template, ensuring absolute consistency across the user's work. The use of numeric prefixes for the main subdirectories is a deliberate choice borrowed from post-production workflows; it enforces a logical, chronological sort order that mirrors the typical flow of work from asset ingestion to final delivery.2

* project.json: This is the most critical file in the project directory. It is a machine-readable manifest that serves as the project's official identity card. It contains essential metadata such as a unique project UUID, a human-readable title, a detailed description, default settings like aspect ratio, creation and modification timestamps, and a relative path to the main "Production Canvas" file (e.g., 02\_Source\_Creative/Canvases/main\_canvas.json). This file is the primary entry point for the application when loading or interacting with the project programmatically.  
* 01\_Assets/: This directory is the designated location for all raw, source materials that are ingested into the project. It is for inputs, not outputs.  
  * Source\_Media/: Contains all raw media captured for the project, such as video footage, still images, and field audio recordings. It is best practice to organize this further into subdirectories by shoot date, camera type, or scene number for easy navigation.1  
  * AI\_Models/: For foundational AI models that are specific to this project and not part of the global Library/. This could include a particular checkpoint file (.ckpt or .safetensors) or a specialized video model that is being used exclusively for this production.  
  * Generative\_Assets/: This directory is the physical file system representation of the abstract "Generative Asset" concept from the application's design.\[1, 1\] Each subdirectory here is a self-contained, reusable creative element.  
    * Characters/CHARACTER\_NAME/: A folder for each character, containing reference\_images/ for visual identity, a description.txt for personality traits, and the trained model file (e.g., a character LoRA or other identity model like model.safetensors).  
    * Styles/STYLE\_NAME/: A folder for each visual style, containing a collection of reference\_images/ and a keywords.txt file with descriptive terms.  
    * Locations/LOCATION\_NAME/: A folder for each location, containing reference imagery, 3D scene files (.blend, .fbx), or environment maps.  
* 02\_Source\_Creative/: This directory holds the "source code" of the creative work. These are the primary, human-edited files that define the project's structure and content. They are typically small, text-based, and ideal for granular version control.  
  * Canvases/: Contains the .json files for the "Production Canvas" node graphs. The primary graph for the project would be main\_canvas.json, but other graphs for asset generation or experiments could also reside here.\[1, 1\]  
  * Scripts/: For all narrative documents, including screenplays, outlines, interview transcripts, and production notes.1  
  * Prompts/: A location for storing complex or frequently reused text prompts in .txt files, which can then be referenced from the Production Canvas.  
* 03\_Renders/: The primary output directory for all machine-generated media from the generative pipeline. This directory and its contents should be treated as immutable. To prevent conflicts and maintain a clean history, files are never overwritten; new versions are created instead.  
  * The structure is hierarchical: SCENE\_NAME/SHOT\_NAME/.  
  * Files are named using the strict convention defined earlier: SHOT-010\_v01\_take01.mp4, SHOT-010\_v01\_take02.png, etc. This provides a direct link between the file on disk and the "Take" versioning system in the UI.\[1, 1\]  
* 04\_Project\_Files/: A directory for application-specific files required to manage the project, distinct from the creative source files.  
  * Auto\_Saves/: Contains automatic backups of the Production Canvas .json files, providing a safety net against data loss.2  
  * EDLs/: For exported Edit Decision Lists (.edl, .xml), ensuring interoperability with other professional video editing software.1  
* 05\_Cache/: A dedicated space for transient, non-essential data that can be regenerated at any time. This directory's contents are not vital to the project's integrity and should be explicitly excluded from version control and backups.  
  * Examples include UI thumbnails, pre-processed control maps for generative models (e.g., Canny edge maps, depth maps), and other temporary files.  
* 06\_Exports/: The destination for final, delivered outputs of the project. This is where the user would save the final, high-quality rendered movie file (e.g., My\_Awesome\_Film\_H264.mp4) or a sequence of frames for delivery to a client.9  
* .gitignore: A pre-configured text file that instructs Git to ignore specific files and directories. This is crucial for keeping the repository clean and efficient. The template will, at a minimum, ignore the entire 05\_Cache/ and 06\_Exports/ directories, as well as common OS-specific files (e.g., .DS\_Store, Thumbs.db).  
* .gitattributes: A pre-configured text file that defines the rules for Git LFS (Large File Storage). This critical file dictates which file types are handled by LFS and which are stored in the standard Git repository. Its configuration is detailed in the next section.

The following table provides a comprehensive, at-a-glance reference for the proposed project structure, detailing the purpose and versioning strategy for each key component.

| Path | Purpose | Example Contents | Version Control Strategy | Rationale |
| :---- | :---- | :---- | :---- | :---- |
| project.json | Project Manifest | { "uuid": "...", "title": "..." } | Standard Git | The core, text-based definition of the project. Essential for versioning creative intent and metadata. |
| 01\_Assets/ | Raw Source Materials | Subdirectories for media, models | \- | Top-level container for all project inputs. |
| .../Source\_Media/ | Raw camera/audio files | A001C002\_240101.mxf | Git LFS | Large binary files that are the ultimate source of truth for captured media. |
| .../AI\_Models/ | Project-specific models | sdxl\_base\_1.0.safetensors | Git LFS | Large binary model files that are foundational to the project's generative process. |
| .../Generative\_Assets/ | Reusable creative entities | Subdirectories for characters, styles | \- | Organizes the physical files that constitute the abstract "Generative Assets".\[1, 1\] |
| 02\_Source\_Creative/ | Human-edited creative files | Subdirectories for canvases, scripts | \- | The "source code" of the film. These files define what will be generated. |
| .../Canvases/ | Production Canvas graphs | main\_canvas.json | Standard Git | Small, text-based JSON files that define the entire generative workflow. Diffable and perfect for Git. |
| .../Scripts/ | Narrative documents | screenplay\_v3.txt | Standard Git | Text-based documents that track the narrative development of the project. |
| 03\_Renders/ | Generated Media ("Takes") | SCENE\_01/SHOT\_010/SHOT-010\_v01\_take01.mp4 | Git LFS | Immutable, large binary outputs of the generative process. Versioned by filename. |
| 04\_Project\_Files/ | NLE/App-specific files | Auto\_Saves/, EDLs/ | Standard Git | Small, project-related metadata and interoperability files. |
| 05\_Cache/ | Transient/Temporary Data | thumbnails/, control\_maps/ | Ignore (in .gitignore) | Disposable data that can be regenerated. Excluding it prevents repository bloat. |
| 06\_Exports/ | Final Deliverables | Final\_Movie\_H264.mp4 | Ignore (in .gitignore) | Final outputs not considered part of the iterative creative process. |
| .gitignore | Git Ignore Rules | 05\_Cache/, 06\_Exports/, \*.DS\_Store | Standard Git | Defines what Git should not track, essential for repository health. |
| .gitattributes | Git LFS Rules | \*.png filter=lfs diff=lfs merge=lfs \-text | Standard Git | Defines the versioning strategy for binaries vs. text, critical for performance.10 |

## **Section 3: A Hybrid Versioning Strategy for Code and Large-Scale Media**

The user query explicitly requires a solution to "easily version intermediate states" using Git \[User Query\]. This presents a significant architectural challenge, as Git was fundamentally designed for text-based source code, not the multi-gigabyte binary files common in media production. A naive attempt to commit large media files directly to a Git repository results in catastrophic performance degradation and repository bloat.5 This section details a robust, hybrid versioning strategy that leverages the strengths of both standard Git and Git Large File Storage (LFS) to create an efficient and powerful workflow.

### **3.1 The Project-as-Repository Model**

To achieve maximum isolation, portability, and scalability, the architecture formally proposes a **Project-as-Repository** model. Under this model, every individual project directory created under /Projects/PROJECT\_NAME/ is initialized as its own independent Git repository.

This approach offers several distinct advantages over a single, monolithic repository for the entire workspace:

* **Performance:** It prevents the entire application history from becoming slow and unmanageable as more projects are added. Git operations like clone, fetch, and log operate only on the scope of a single project, ensuring they remain fast and responsive.12  
* **Isolation:** Each project's version history is completely self-contained. This prevents unrelated changes in one project from affecting another and simplifies the process of tracking a specific project's evolution.  
* **Portability and Archiving:** A self-contained project repository can be easily bundled, moved to a different storage location, or archived for long-term preservation. The entire history and all its associated assets are contained within that single project folder.  
* **Scalability to Multi-Tenancy:** This model provides a natural and elegant pathway to the user's future goal of a multi-tenant system. As specified in the query, "different tenants are different git repos" becomes a straightforward implementation, where each tenant's collection of projects can be managed as a distinct set of repositories \[User Query\].

### **3.2 Mandatory Implementation of Git Large File Storage (LFS)**

Git LFS is not an optional enhancement for this workflow; it is a mandatory component. Git LFS is a Git extension designed specifically to handle large files by changing how they are stored.14 Instead of storing the large binary file directly in the Git repository's history, LFS stores a small text-based

**pointer file**. This pointer contains a unique identifier and the size of the actual file. The large file itself, known as an "LFS object," is stored in a separate, dedicated storage location, which can be a local cache or a remote server.10

When a user clones or pulls from the repository, Git downloads the small pointer files first, making the initial operation extremely fast. Then, during the checkout process, the Git LFS client reads the pointer files and downloads the required large files from the LFS store. This approach directly solves the core problem of repository bloat and directly supports the user's requirement to store projects on cloud services like Amazon S3, as the LFS remote store can be configured to be an S3 bucket.5

### **3.3 Configuring .gitattributes: The LFS Rulebook**

The heart of the LFS strategy is the .gitattributes file. This simple text file, located in the root of the project repository, acts as a rulebook, telling Git which files to handle with LFS and which to handle normally.10 By creating a standardized

.gitattributes template for every new project, the application can enforce a consistent and intelligent versioning policy.

The core principle of this policy is to separate diffable, text-based "source code" from non-diffable, opaque binary assets.

* **Tracked by Standard Git:** Files that are text-based and for which line-by-line change tracking is valuable. This includes \*.json (for Production Canvases), \*.py (for custom scripts), \*.txt (for prompts and notes), and \*.md (for documentation).  
* **Tracked by Git LFS:** Large binary files that are treated as atomic units. This includes all media and model files: \*.png, \*.jpg, \*.mp4, \*.mov, \*.wav, \*.mp3, \*.safetensors, \*.pth, and project files from other creative applications like \*.psd or \*.aep.

This separation is more than a mere technical optimization for storage; it fundamentally defines the collaborative workflow. When a developer or artist makes a change to a canvas.json file, a standard git diff provides a clear, human-readable summary of the exact change—for example, a parameter on a Shot Node was changed from 1.0 to 1.5. This enables powerful code review and auditing of the creative process itself. Conversely, a diff on a rendered .png file is meaningless. By delegating these files to LFS, we acknowledge them as immutable, versioned artifacts. We don't track their internal byte changes; we track their existence as a specific version pointed to by a specific commit. This hybrid approach provides the best of both worlds: efficient storage for large assets and meaningful, granular version history for the creative logic.

The following table provides a template .gitattributes file that should be included in every new project.

| File Pattern | Git Attributes | Rationale |
| :---- | :---- | :---- |
| \*.json | text | Ensures JSON files are treated as text, normalizing line endings. |
| \*.py | text | Ensures Python files are treated as text. |
| \*.js | text | Ensures JavaScript files are treated as text. |
| \*.txt | text | Ensures text files are treated as text. |
| \*.md | text | Ensures Markdown files are treated as text. |
| \*.png | filter=lfs diff=lfs merge=lfs \-text | Tracks all PNG images with Git LFS. |
| \*.jpg | filter=lfs diff=lfs merge=lfs \-text | Tracks all JPEG images with Git LFS. |
| \*.jpeg | filter=lfs diff=lfs merge=lfs \-text | Tracks all JPEG images with Git LFS. |
| \*.gif | filter=lfs diff=lfs merge=lfs \-text | Tracks all GIF images with Git LFS. |
| \*.mp4 | filter=lfs diff=lfs merge=lfs \-text | Tracks all MP4 videos with Git LFS. |
| \*.mov | filter=lfs diff=lfs merge=lfs \-text | Tracks all MOV videos with Git LFS. |
| \*.wav | filter=lfs diff=lfs merge=lfs \-text | Tracks all WAV audio files with Git LFS. |
| \*.mp3 | filter=lfs diff=lfs merge=lfs \-text | Tracks all MP3 audio files with Git LFS. |
| \*.safetensors | filter=lfs diff=lfs merge=lfs \-text | Tracks all SafeTensors model files with Git LFS. |
| \*.pth | filter=lfs diff=lfs merge=lfs \-text | Tracks all PyTorch model files with Git LFS. |
| \*.ckpt | filter=lfs diff=lfs merge=lfs \-text | Tracks all checkpoint model files with Git LFS. |
| \*.psd | filter=lfs diff=lfs merge=lfs \-text | Tracks all Photoshop files with Git LFS. |

### **3.4 LFS Workflow and Best Practices**

Successful implementation of Git LFS in a team environment requires adherence to several best practices:

* **Universal Installation:** It is absolutely critical that every user and every automated system interacting with the repository has Git LFS installed (git lfs install). If a user without LFS installed commits a file that should be tracked by LFS, they will commit the actual large file to the repository instead of a pointer. This corrupts the repository history, is difficult to fix, and defeats the entire purpose of using LFS.5 The application should perform a check for the LFS client upon startup.  
* **Regular Pruning:** The local LFS cache, where downloaded objects are stored, does not clean itself up automatically. Over time, it can consume significant disk space with outdated versions of files. Users must be encouraged or the application must provide a mechanism to periodically run git lfs prune. This command safely deletes old LFS files that are no longer referenced by any recent commit, freeing up local storage.5  
* **Selective Fetching:** In a collaborative cloud environment, a project may contain terabytes of assets. A user may only need a small subset of those assets to work on a single scene. Git LFS supports selectively downloading files. Using filters like git lfs pull \--include="01\_Assets/Source\_Media/Scene\_05/\*\*" allows a user to fetch only the assets for Scene 5, saving immense amounts of time, bandwidth, and local disk space.11

## **Section 4: Implementation and Programmatic Path Management**

Transitioning from architectural design to functional code requires a robust and maintainable strategy for handling file paths. Hard-coding paths as strings throughout an application is a well-known anti-pattern that leads to brittle, difficult-to-maintain code. This section provides concrete implementation guidance for managing the project file structure programmatically, ensuring the application is portable, readable, and resilient to future changes.

### **4.1 The Case for pathlib: A Modern Approach to Path Handling**

For any Python-based application, the pathlib module, introduced in Python 3.4, should be considered the standard for all file system path manipulations. It is strongly recommended over older methods like the os.path module or manual string concatenation.15

The advantages of pathlib are numerous and directly address the challenges of building a cross-platform creative application:

* **Object-Oriented Interface:** With pathlib, file paths are no longer simple strings but are instead powerful objects. A Path object has a rich set of methods and properties for querying and manipulating the path, such as .exists(), .is\_dir(), .is\_file(), .resolve() to get an absolute path, and .name or .suffix to extract parts of the filename. This object-oriented approach leads to more expressive and less error-prone code compared to the functional style of os.path.15  
* **Platform Independence:** pathlib automatically handles the critical difference between Windows path separators (\\) and Unix-based (macOS, Linux) separators (/). Code written with pathlib will run correctly on any operating system without modification, which is essential for a tool intended for a diverse user base.15  
* **Enhanced Readability:** The module overloads the forward slash (/) operator for joining path components. An operation that would be os.path.join(base\_dir, 'data', 'file.txt') with os.path becomes the far more intuitive and readable base\_dir / 'data' / 'file.txt' with pathlib. This small syntactic improvement significantly enhances code clarity, especially when constructing complex paths.15

### **4.2 A Centralized Path Management Module**

To adhere to the "Don't Repeat Yourself" (DRY) principle and create a maintainable codebase, all logic for constructing paths within the project structure should be centralized in a single, dedicated Python module (e.g., project\_paths.py). This module acts as an abstraction layer, decoupling the physical file layout from the rest of the application's business logic.18

Instead of different parts of the code independently constructing paths to assets or renders, they would call functions from this central module. For example, the module would contain functions like:

* get\_project\_root(project\_name: str) \-\> Path  
* get\_renders\_dir(project\_root: Path) \-\> Path  
* get\_character\_asset\_path(project\_root: Path, character\_name: str) \-\> Path  
* get\_shot\_take\_path(project\_root: Path, scene: str, shot: str, version: int, take: int) \-\> Path

The primary benefit of this pattern is resilience to change. If, in the future, the development team decides to rename the 03\_Renders directory to 03\_Generated\_Media, the change only needs to be made in one place: the get\_renders\_dir function within the project\_paths.py module. The hundreds of other places in the codebase that call this function would continue to work without modification. This design pattern is a crucial investment in the long-term health and maintainability of the software.

### **4.3 Automating Consistency with Project Templates**

The complexity and rigor of the proposed project structure are its greatest strengths, but they should be entirely invisible to the end-user. An artist should never be required to manually create this intricate hierarchy of folders and configuration files. Manual creation is tedious, error-prone, and would inevitably lead to inconsistencies.9

Therefore, the "New Project" function within the application's UI must be responsible for programmatically scaffolding the entire project structure. This automated process should perform the following sequence of operations:

1. Create the main project directory (e.g., /Projects/PROJECT\_NAME/).  
2. Create all the numbered subdirectories (01\_Assets, 02\_Source\_Creative, etc.) and their nested folders.  
3. Generate the project.json manifest file, populating it with a new UUID and user-provided metadata (title, description).  
4. Copy the standard .gitignore and .gitattributes template files into the project root.  
5. Initialize a new Git repository in the project root (git init).  
6. Perform an initial commit to save the foundational structure and configuration files.

By automating this setup, the application guarantees that every single project starts from a known, consistent, and correct state, which is essential for the reliability of all downstream automated processes.

## **Section 5: Architecting for the Cloud and Multi-Tenancy**

A key requirement of the user query is that the file-based architecture must be designed to easily accommodate future extension into a multi-user or multi-tenant system, with a specific mention of cloud storage like Amazon S3 \[User Query\]. The "Project-as-Repository" model, combined with Git LFS, provides a remarkably elegant and scalable foundation for this transition from a local-first application to a cloud-native service.

### **5.1 Mapping the Workspace to Cloud Object Storage**

The entire /Generative\_Studio\_Workspace/ directory structure can be mapped directly to a cloud object storage service. Using Amazon S3 as the reference example, the mapping would be as follows:

* The S3 bucket (e.g., s3://generative-studio-data/) becomes the canonical home for the entire workspace.  
* The Git LFS backend is configured to use this S3 bucket as its remote store. When a user pushes an LFS object, the file is uploaded to a specific path within the bucket (e.g., s3://generative-studio-data/lfs-objects/). This makes the cloud the single source of truth for all large binary assets.  
* The Git repositories themselves (which contain the small pointer files and text-based creative source) can also be hosted remotely. This can be done by storing bare Git repositories directly in S3 or, more commonly, by using a dedicated managed Git service like AWS CodeCommit, GitHub, or GitLab, which provides a full-featured interface for repository management.

### **5.2 Strategies for Multi-Tenancy**

The self-contained nature of the "Project-as-Repository" model enables a clean separation of tenant data in a shared cloud environment. There are two primary architectural patterns for achieving this isolation:

* **Strategy A: Bucket-per-Tenant:** In this model, each tenant (or user) is assigned their own dedicated S3 bucket (e.g., s3://tenant-a-workspace/, s3://tenant-b-workspace/). This provides the strongest possible isolation. Security policies (IAM) and cost allocation are straightforward, as they can be applied at the bucket level. However, managing thousands of individual buckets, each with its own policies and lifecycle rules, can introduce significant operational complexity and may run into service limits.  
* **Strategy B: Prefix-per-Tenant (Recommended):** In this model, all tenants share a single S3 bucket, but their data is logically isolated under a unique, tenant-specific prefix (e.g., s3://main-workspace/tenant-a/, s3://main-workspace/tenant-b/). This is the standard approach for most modern SaaS applications due to its management simplicity. A single set of lifecycle rules and bucket policies can apply to all tenants. Security is enforced using more granular IAM policies that restrict access to specific prefixes based on the authenticated user's identity.

While Strategy A offers simpler accounting, **Strategy B is the recommended approach** for its superior scalability and reduced management overhead. The choice, however, is not merely technical but also involves business and operational considerations. The Prefix-per-Tenant model simplifies infrastructure management but requires more sophisticated tooling for fine-grained cost allocation, typically relying on S3 inventory reports and object tagging. Furthermore, it demands a higher degree of security diligence, as a single misconfigured IAM policy could theoretically have a wider blast radius than in a bucket-isolated model. The recommendation for this strategy assumes a commitment to robust, automated IAM policy generation and testing as the service scales. For an early-stage product, the simplicity of managing a single bucket often outweighs the initial complexity of per-prefix cost tracking.

### **5.3 Data Synchronization and Caching**

In a cloud-native deployment, the workflow for interacting with a project changes. The compute instances that run the generative models or the application backend should be treated as stateless. When a user initiates an action on a project, the backend service would perform the following steps:

1. Authenticate the user and identify the target project repository and its associated LFS store in the cloud.  
2. Clone the project's Git repository to a temporary, local cache on the compute instance.  
3. Execute a git lfs pull command, potentially with include/exclude filters, to download only the necessary LFS objects (assets) required for the specific task.  
4. Perform the generative work (e.g., render a shot).  
5. Commit any changes to the creative source files (e.g., updating the canvas JSON) and push them back to the remote Git repository.  
6. Push any new LFS objects (the rendered output) to the S3 LFS store.  
7. Once the task is complete, the local cache on the compute node can be discarded.

This stateless, just-in-time data fetching model is a core principle of scalable cloud architecture. It ensures that compute resources are not tied to specific data, allowing the system to scale horizontally by adding more generic compute nodes as demand increases.

## **Section 6: Conclusion and Strategic Recommendations**

This report has outlined a comprehensive architectural blueprint for a file-based project structure designed specifically for a generative media application. The proposed design is grounded in established principles from software engineering and professional production workflows, providing a solution that is both immediately practical for a single-user application and strategically positioned for future evolution into a cloud-native, multi-tenant service.

### **6.1 Summary of the Architectural Blueprint**

The core of the architecture rests on a set of synergistic principles. The **Workspace/Project dichotomy** separates shared resources from self-contained creative work, promoting reuse and manageability. The rigorous **Separation of Concerns** isolates source files from derivatives and transient data from persistent assets, ensuring a clean and predictable environment. The **Project-as-Repository** model, coupled with the mandatory implementation of **Git Large File Storage (LFS)**, provides a powerful hybrid versioning system that efficiently handles both granular, text-based creative code and large-scale binary media. Finally, the entire structure is designed to be programmatically managed, with consistent naming conventions and a centralized path management module making the file system a reliable and legible API for the application's automated backend. This blueprint directly addresses the user's core requirements, providing a smart, scalable, and robust foundation.

### **6.2 Strategic Recommendations**

To ensure the long-term success and integrity of this architecture, the following strategic recommendations should guide its implementation and deployment:

* **Enforce Consistency Programmatically:** The strength of this system is derived from its consistency. This consistency must not be left to chance or user discipline. The application's code should be the sole authority for creating and managing the project structure. The "New Project" function must programmatically generate the entire directory tree and its configuration files, ensuring every project adheres to the blueprint from its inception.9  
* **Educate and Guide the User:** While much of the structure can be hidden behind a polished UI, there will be moments where users interact with the file system (e.g., via a "Save As" or "Import Asset" dialog). The application should guide these interactions. For instance, a custom file dialog could default to the correct subdirectory (e.g., 01\_Assets/Source\_Media/) based on the context of the operation, gently enforcing the organizational logic without being restrictive.  
* **Plan for Archiving as a Feature:** The self-contained nature of each project repository makes archiving an exceptionally clean process. A "closed" or "completed" project can be easily archived by bundling its entire Git repository and its associated LFS objects into a single compressed archive file (e.g., a .tar.gz). This archive can then be moved to cheaper, long-term cloud storage, such as Amazon S3 Glacier. This archival and retrieval process should not be an afterthought but should be planned as a core feature of the application's project management lifecycle.

## **Section 7: The Runtime Environment: From Code to Containerized Execution**

While the file structure provides a stable, organized foundation for project data, the runtime environment defines how that data is activated and processed. This section details the architecture of the execution layer, focusing on how the "Function Runner" concept is realized through a containerized Celery and Docker backend. It outlines the development environment, the strategy for dynamic pipeline selection based on quality settings, and the critical role of hardware-aware orchestration for managing VRAM.

### **7.1 The Containerized "Function Runner": A Celery and Docker Deep Dive**

The "Function Runner" is not a single application but an architectural pattern that treats each generative model or complex workflow as a discrete, containerized microservice. Celery acts as the high-level orchestrator, while Docker provides the necessary isolation to manage the heterogeneous and often conflicting dependencies of different AI models.\[1, 1\]

The workflow is as follows:

1. **Task Dispatch:** The FastAPI server receives a request from the user (e.g., "Generate Shot 12"). It packages the necessary data (the project.json, the main\_canvas.json, and the ID of the specific ShotNode) and dispatches a task to a Celery queue.19  
2. **Celery Worker Receives Task:** A Celery worker picks up the task. The task payload doesn't contain the generative logic itself, but rather a pipeline\_id that points to a specific implementation (e.g., t2i-flux-schnell).  
3. **Container Invocation:** The Celery worker uses the pipeline\_id to look up the corresponding Docker image and execution command. It then uses Python's subprocess module or the Docker SDK to run the specific container, for example: docker run \--gpus all \--rm \-v /path/to/models:/models \-v /path/to/project:/project t2i-flux-schnell:latest python /app/run.py \--project\_path /project \--node\_id 12\.  
4. **Isolated Execution:** The generative task runs entirely within its isolated Docker container. The container has access to the shared model library and the specific project directory via volume mounts, but its Python environment and dependencies are completely self-contained.  
5. **Result Reporting:** Upon completion, the container writes its output (e.g., SHOT-012\_v01\_take01.mp4) to the project's 03\_Renders directory and exits. The Celery worker detects the successful completion and reports the result back to the FastAPI server, which then notifies the user via WebSocket.

This pattern provides maximum flexibility and future-proofs the system. Adding a new generative model like FlexiAct or LoRAEdit doesn't require modifying the core backend; it simply involves creating a new Docker image for that model and adding its pipeline\_id to the system's registry.\[1, 1\]

### **7.2 Development and Deployment: A Monorepo and Docker Compose Strategy**

To manage the complexity of the frontend, backend API, and multiple pipeline containers, a monorepo structure is recommended for development. This keeps all related code in a single repository, simplifying dependency management and cross-service development. The entire stack can be orchestrated locally using a docker-compose.yml file.

**Recommended Project Directory Structure:**

generative-studio/  
├── docker-compose.yml  
├── frontend/  
│   ├── src/  
│   └── package.json  
├── backend/  
│   ├── api/  
│   │   └── main.py  
│   ├── workers/  
│   │   └── tasks.py  
│   └── Dockerfile  
├── pipelines/  
│   ├── t2i-sdxl/  
│   │   ├── run.py  
│   │   ├── requirements.txt  
│   │   └── Dockerfile  
│   └── t2v-flexiact/  
│       ├── run.py  
│       ├── requirements.txt  
│       └── Dockerfile  
└── workspace/  
    ├── Library/  
    │   ├── AI\_Models/  
    │   └── Pipeline\_Templates/  
    └── Projects/  
        └── My\_First\_Film/

The docker-compose.yml file would define services for each component, with crucial volume mounts to enable live-reloading for development and to provide data access to the containers:

* **frontend service:** Mounts ./frontend:/app to allow the SvelteKit development server to hot-reload code changes.  
* **api service (FastAPI):** Mounts ./backend:/app for backend code changes and ./workspace/Projects:/projects to allow the API to read project files.  
* **worker service (Celery):** Also mounts ./backend:/app and ./workspace/Projects:/projects.  
* **Pipeline services (e.g., t2i-sdxl):** Each pipeline runs as its own service. They mount the shared model library (./workspace/Library/AI\_Models:/models) and the entire projects directory (./workspace/Projects:/projects) to read inputs and write outputs.

This setup allows a developer to bring up the entire distributed system with a single docker-compose up command, providing a powerful and consistent development environment.

### **7.3 Dynamic Pipeline Selection: Managing Quality and Speed**

To give users control over the trade-off between generation speed and output quality, the system will implement a project-level "quality" setting. This setting, stored in the project.json file, allows the backend to dynamically select different pipeline implementations for the same conceptual task.

The project.json would contain a key like:  
"quality": "standard" (options: low, standard, high)  
When the "Producer" agent processes a ShotNode, it reads both the pipeline\_id from the connected PipelineNode (e.g., generate-image) and the quality setting from the project. It then combines these to select the specific, versioned pipeline to execute.

**Example Pipeline Mapping:**

| Task (from PipelineNode) | Quality (from project.json) | Selected Pipeline Container | Description |
| :---- | :---- | :---- | :---- |
| generate-image | low | t2i-sd1.5:latest | Uses Stable Diffusion 1.5 at 512x512 resolution for rapid drafts. |
| generate-image | standard | t2i-flux-schnell:latest | Uses FLUX.Schnell at 768x768 for a good balance of quality and speed. |
| generate-image | high | t2i-flux-dev-fp16:latest | Uses the full FLUX.dev FP16 model at 2048x2048 for maximum fidelity. |

This abstraction allows the user to change the entire quality profile of their project with a single setting, without having to manually re-link every PipelineNode on their canvas.

### **7.4 Hardware-Aware Orchestration: VRAM Tiers and Resource Management**

A critical responsibility of the backend is to manage hardware resources intelligently. Generative models have steep and highly variable VRAM requirements, and attempting to run a high-end workflow on low-end hardware will result in out-of-memory (OOM) errors and failed tasks. The system must be aware of the capabilities of its worker nodes.

The "Producer" agent, before dispatching a task to a Celery worker queue, must consider the VRAM requirements of the selected pipeline and the VRAM tier of the available workers.

**VRAM Tier Capabilities:**

* **12 GB VRAM (Lower Practical Limit):** This tier can run SDXL/Flux models only with aggressive optimizations. The SDXL base model (1024px) requires \--medvram-sdxl modes or FP8 quantized weights to fit. Adding even one heavy ControlNet or two IP-Adapters will likely cause an OOM error. For Flux models, the full Flux.Dev model is only possible with its 8-bit quantized version and CPU offloading; the smaller Flux.Schnell model is recommended. To make complex setups work, resolution must often be reduced (e.g., to 768px).  
* **16 GB VRAM (Comfortable Mid-Range):** This tier provides more headroom. It can comfortably run the SDXL base model and even the refiner ("Turbo") stage. It can typically handle one or two ControlNets or IP-Adapters alongside SDXL at 1024px. For Flux, the FP8-quantized Flux.Dev model fits easily, and Flux.Schnell is no problem. While full FP16 models are risky, this tier handles standard production workloads with a few extra modules well, though care is still needed with very complex stacks.  
* **24 GB VRAM ("All Features On"):** This tier lifts most practical limits for 1024px generation. It can run the full SDXL base and refiner stack with multiple ControlNets and IP-Adapters simultaneously. For Flux, it comfortably runs the full FP16 Flux.Dev model, even with multiple LoRAs and IP-Adapters, and enables experimentation with higher resolutions (e.g., 2K).

**Orchestration Logic:**

The system will maintain a profile for each pipeline that includes its estimated VRAM usage for each quality level. When a user requests a "high" quality render, the Producer agent will check if a worker with sufficient VRAM (e.g., 24 GB) is available. If only a 16 GB worker is free, the agent can be configured to either queue the task until a high-end worker is available, or automatically fall back to the "standard" quality pipeline and notify the user (e.g., "High quality not available on current hardware. Fell back to standard 1024px generation."). This intelligent, hardware-aware orchestration is critical for creating a robust and user-friendly system that avoids frustrating and difficult-to-diagnose hardware failures.

#### **Works cited**

1. The Art Of Organization: Download The Perfect Folder Structure For Filmmakers Here\!, accessed June 29, 2025, [https://noamkroll.com/the-art-of-organization-download-the-perfect-folder-structure-for-filmmakers-here/](https://noamkroll.com/the-art-of-organization-download-the-perfect-folder-structure-for-filmmakers-here/)  
2. Mastering Video File Organization And Folder Structure \- MASV, accessed June 29, 2025, [https://massive.io/file-transfer/mastering-video-file-organization/](https://massive.io/file-transfer/mastering-video-file-organization/)  
3. Data Organization \- Data Cooperative \- The University of Arizona, accessed June 29, 2025, [https://data.library.arizona.edu/data-management/best-practices/data-project-organization](https://data.library.arizona.edu/data-management/best-practices/data-project-organization)  
4. Reproducible Research: Best Practices for Data and Code Management \- Innovations for Poverty Action, accessed June 29, 2025, [https://poverty-action.org/sites/default/files/publications/IPA-Best-Practices-for-Data-and-Code-Management-Nov-2015.pdf](https://poverty-action.org/sites/default/files/publications/IPA-Best-Practices-for-Data-and-Code-Management-Nov-2015.pdf)  
5. Best Practices for Storing Large Files and Binaries \- Oracle Help Center, accessed June 29, 2025, [https://docs.oracle.com/en/cloud/paas/visual-builder/visualbuilder-manage-development-process/best-practices-storing-large-files-and-binaries.html](https://docs.oracle.com/en/cloud/paas/visual-builder/visualbuilder-manage-development-process/best-practices-storing-large-files-and-binaries.html)  
6. File and Folder Organization \- long draft \- | UC Merced Library, accessed June 29, 2025, [https://library.ucmerced.edu/node/66751](https://library.ucmerced.edu/node/66751)  
7. Navigating Data Intensive Projects | by Adam DeJans Jr. | Medium, accessed June 29, 2025, [https://medium.com/@adam.dejans/navigating-data-intensive-projects-787214a97ada](https://medium.com/@adam.dejans/navigating-data-intensive-projects-787214a97ada)  
8. How To Set Up A Folder Structure – Stillmotion Blog, accessed June 29, 2025, [https://www.stillmotionblog.com/folder-structure/](https://www.stillmotionblog.com/folder-structure/)  
9. Why You Should Have a Template Folder Structure For Video Projects \- Chris Olson Films, accessed June 29, 2025, [http://chrisolsonfilms.com/blog/2018/9/10/why-you-should-have-a-template-folder-for-video-production](http://chrisolsonfilms.com/blog/2018/9/10/why-you-should-have-a-template-folder-for-video-production)  
10. How can I handle large binary files (efficiently) with Git LFS? | Learn Version Control with Git, accessed June 29, 2025, [https://www.git-tower.com/learn/git/faq/handling-large-files-with-lfs](https://www.git-tower.com/learn/git/faq/handling-large-files-with-lfs)  
11. Best Practices for Securing Git LFS on GitHub, GitLab, Bitbucket, and Azure DevOps \- Blog, accessed June 29, 2025, [https://gitprotect.io/blog/best-practices-for-securing-git-lfs-on-github-gitlab-bitbucket-and-azure-devops/](https://gitprotect.io/blog/best-practices-for-securing-git-lfs-on-github-gitlab-bitbucket-and-azure-devops/)  
12. Git Large File Storage (LFS) Overview \- DataCamp, accessed June 29, 2025, [https://www.datacamp.com/tutorial/git-large-file-storage-lfs](https://www.datacamp.com/tutorial/git-large-file-storage-lfs)  
13. Managing large binary files with Git \- Stack Overflow, accessed June 29, 2025, [https://stackoverflow.com/questions/540535/managing-large-binary-files-with-git](https://stackoverflow.com/questions/540535/managing-large-binary-files-with-git)  
14. Managing large files \- GitHub Docs, accessed June 29, 2025, [https://docs.github.com/en/repositories/working-with-files/managing-large-files](https://docs.github.com/en/repositories/working-with-files/managing-large-files)  
15. Handling file and directory Paths \- Python Cheatsheet, accessed June 29, 2025, [https://www.pythoncheatsheet.org/cheatsheet/file-directory-path](https://www.pythoncheatsheet.org/cheatsheet/file-directory-path)  
16. Managing file paths \- Automating GIS Processes \- Read the Docs, accessed June 29, 2025, [https://autogis-site.readthedocs.io/en/latest/lessons/lesson-2/managing-file-paths.html](https://autogis-site.readthedocs.io/en/latest/lessons/lesson-2/managing-file-paths.html)  
17. What are best practices for file paths and unicode escapes? Iterating over CSV files. \- Reddit, accessed June 29, 2025, [https://www.reddit.com/r/learnpython/comments/16jo8g7/what\_are\_best\_practices\_for\_file\_paths\_and/](https://www.reddit.com/r/learnpython/comments/16jo8g7/what_are_best_practices_for_file_paths_and/)  
18. How to handle file paths when running or importing a Python program \- LabEx, accessed June 29, 2025, [https://labex.io/tutorials/python-how-to-handle-file-paths-when-running-or-importing-a-python-program-398005](https://labex.io/tutorials/python-how-to-handle-file-paths-when-running-or-importing-a-python-program-398005)  
19. Celery and Background Tasks. Using FastAPI with long running tasks | by Hitoruna | Medium, accessed June 29, 2025, [https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d](https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d)