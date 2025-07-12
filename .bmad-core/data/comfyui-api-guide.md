# **How to Use ComfyUI API with Python: A Complete Guide**

ComfyUI is an open source node-based application for creating images, videos, and audio with GenAI. While the graphical interface is user-friendly, programmatic access via API can enable automation and integration into your applications. This guide will walk you through two approaches to interact with ComfyUI API using Python.

# **Prerequisites**

* Python 3.x  
* websocket-client library (`pip install websocket-client`)  
* A running ComfyUI instance（For local deployment: use `127.0.0.1:8188`, for remote deployment: use your server’s IP address, e.g. `192.168.1.100:8188`）

# **Method 1: Basic API with Image Saving**

This method is used when your ComfyUI workflow contains `SaveImage` nodes, which save generated images to the local disk. The API will then retrieve these saved images through HTTP endpoints.

## **Key Steps**

## **1\. Prepare the Workflow Prompt**

The workflow prompt is a JSON structure that defines your entire generation pipeline. You can export this from the ComfyUI interface after creating your desired workflow. It includes all nodes (like model loading, sampling, encoding) and their connections.

![][image1]  
prompt\_text \= """  
{  
   "3": {  
       "class\_type": "KSampler",  
       "inputs": {  
           "cfg": 8,  
           "denoise": 1,  
           "seed": 8566257,  
           "steps": 20,  
           "sampler\_name": "euler",  
           "scheduler": "normal",  
           "latent\_image": \["5", 0\],  
           "model": \["4", 0\],  
           "positive": \["6", 0\],  
           "negative": \["7", 0\]  
       }  
   },  
   "4": {  
       "class\_type": "CheckpointLoaderSimple",  
       "inputs": {  
           "ckpt\_name": "v1-5-pruned-emaonly.safetensors"  
       }  
   },  
   \# ... other nodes configuration  
}  
"""  
prompt \= json.loads(prompt\_text)

## **2\. Customize the Prompt**

Before execution, you can modify various parameters in the prompt to customize the generation. Common modifications include changing the text prompt, seed, or sampling parameters.

\# Modify the text prompt for the positive CLIPTextEncode node  
prompt\["6"\]\["inputs"\]\["text"\] \= "masterpiece best quality man"

\# Change the seed for different results  
prompt\["3"\]\["inputs"\]\["seed"\] \= 5

## **3\. Set Up WebSocket Connection**

ComfyUI uses WebSocket to provide real-time updates about the generation process. This connection allows you to monitor the execution status and receive preview images during generation.

client\_id \= str(uuid.uuid4())  \# Generate a unique client ID  
ws \= websocket.WebSocket()  
ws.connect(f"ws://{server\_address}/ws?clientId={client\_id}")

## **4\. Queue the Prompt**

Submit the generation request to ComfyUI’s queue. Each request receives a unique prompt id that we’ll use to track its execution and retrieve results.

def queue\_prompt(prompt):  
   p \= {"prompt": prompt, "client\_id": client\_id}  
   data \= json.dumps(p).encode('utf-8')  
   req \= urllib.request.Request(f"http://{server\_address}/prompt", data=data)  
   return json.loads(urllib.request.urlopen(req).read())

\# Get prompt\_id for tracking the execution  
prompt\_id \= queue\_prompt(prompt)\['prompt\_id'\]

## **5\. Monitor Execution Status**

Listen to WebSocket messages to track the generation progress. The server sends updates about which node is currently executing and when the entire process is complete. You can also receive preview images during generation.

while True:  
   out \= ws.recv()  
   if isinstance(out, str):  
       message \= json.loads(out)  
       if message\['type'\] \== 'executing':  
           data \= message\['data'\]  
           if data\['node'\] is None and data\['prompt\_id'\] \== prompt\_id:  
               break  \# Execution complete  
   else:  
       \# Binary data (preview images)  
       continue

## **6\. Get History and Retrieve Images**

Once execution is complete, we need to:

1. Fetch the execution history to get information about generated images  
2. Use that information to retrieve the actual image data through the view endpoint

def get\_history(prompt\_id):  
   with urllib.request.urlopen(f"http://{server\_address}/history/{prompt\_id}") as response:  
       return json.loads(response.read())

def get\_image(filename, subfolder, folder\_type):  
   data \= {"filename": filename, "subfolder": subfolder, "type": folder\_type}  
   url\_values \= urllib.parse.urlencode(data)  
   with urllib.request.urlopen(f"http://{server\_address}/view?{url\_values}") as response:  
       return response.read()

\# Get history for the executed prompt  
history \= get\_history(prompt\_id)\[prompt\_id\]

\# Since a ComfyUI workflow may contain multiple SaveImage nodes,  
\# and each SaveImage node might save multiple images,  
\# we need to iterate through all outputs to collect all generated images  
output\_images \= {}  
for node\_id in history\['outputs'\]:  
   node\_output \= history\['outputs'\]\[node\_id\]  
   images\_output \= \[\]  
   if 'images' in node\_output:  
       for image in node\_output\['images'\]:  
           image\_data \= get\_image(image\['filename'\], image\['subfolder'\], image\['type'\])  
           images\_output.append(image\_data)  
   output\_images\[node\_id\] \= images\_output

## **7\. Process Images and Clean Up**

Finally, process the retrieved images as needed (save to disk, display, or further processing) and clean up resources by closing the WebSocket connection.

\# Process the generated images  
for node\_id in output\_images:  
   for image\_data in output\_images\[node\_id\]:  
       \# Convert bytes to PIL Image  
       image \= Image.open(io.BytesIO(image\_data))  
       \# Process image as needed  
       \# image.save(f"output\_{node\_id}.png")

\# Always close the WebSocket connection  
ws.close()

# **Method 2: WebSocket-Based Image Transfer**

This method is used when your ComfyUI workflow contains `SaveImageWebsocket` nodes, which stream generated images directly through the WebSocket connection without saving to disk. This is more efficient for real-time applications.

# **Key Steps**

## **1\. Prepare and Customize Prompt**

Similar to Method 1, but using SaveImageWebsocket node:

prompt\_text \= """  
{  
   "3": {  
       "class\_type": "KSampler",  
       "inputs": {  
           "cfg": 8,  
           "denoise": 1,  
           "seed": 8566257,  
           "steps": 20,  
           "sampler\_name": "euler",  
           "scheduler": "normal",  
           "latent\_image": \["5", 0\],  
           "model": \["4", 0\],  
           "positive": \["6", 0\],  
           "negative": \["7", 0\]  
       }  
   },  
   \# ... other nodes remain the same ...  
   "save\_image\_websocket\_node": {  
       "class\_type": "SaveImageWebsocket",  
       "inputs": {  
           "images": \["8", 0\]  
       }  
   }  
}  
"""  
prompt \= json.loads(prompt\_text)

\# Customize the prompt  
prompt\["6"\]\["inputs"\]\["text"\] \= "masterpiece best quality man"  
prompt\["3"\]\["inputs"\]\["seed"\] \= 5

## **2\. Set Up WebSocket Connection**

client\_id \= str(uuid.uuid4())  
ws \= websocket.WebSocket()  
ws.connect(f"ws://{server\_address}/ws?clientId={client\_id}")

## **3\. Queue the Prompt**

def queue\_prompt(prompt):  
   p \= {"prompt": prompt, "client\_id": client\_id}  
   data \= json.dumps(p).encode('utf-8')  
   req \= urllib.request.Request(f"http://{server\_address}/prompt", data=data)  
   return json.loads(urllib.request.urlopen(req).read())

\# Get prompt\_id for tracking the execution  
prompt\_id \= queue\_prompt(prompt)\['prompt\_id'\]

## **4\. Monitor Execution Status**

Similar to Method 1, we monitor the WebSocket messages to track execution progress, but we also need to track which node is currently executing to properly collect image data. When we detect that the `save_image_websocket_node` is executing, any subsequent binary data received will be the image data, which we collect directly from the WebSocket stream.

current\_node \= ""  
output\_images \= {}

while True:  
   out \= ws.recv()  
   if isinstance(out, str):  
       message \= json.loads(out)  
       if message\['type'\] \== 'executing':  
           data \= message\['data'\]  
           if data\['prompt\_id'\] \== prompt\_id:  
               if data\['node'\] is None:  
                   break  \# Execution complete  
               else:  
                   current\_node \= data\['node'\]  
   else:  
       \# Handle binary image data from SaveImageWebsocket node  
       if current\_node \== 'save\_image\_websocket\_node':  
           images\_output \= output\_images.get(current\_node, \[\])  
           images\_output.append(out\[8:\])  \# Skip first 8 bytes of binary header  
           output\_images\[current\_node\] \= images\_output

## **5\. Process Images and Clean Up**

Once all images are collected, we can process them as needed:

\# Process the images  
for node\_id in output\_images:  
   for image\_data in output\_images\[node\_id\]:  
       \# Convert binary data to PIL Image  
       image \= Image.open(io.BytesIO(image\_data))  
       \# Process image as needed  
       \# image.show()

\# Clean up  
ws.close()

# **Complete Example Code**

For complete working examples of both methods, please refer to the official ComfyUI repository:

* Method 1 (Basic API): [websockets\_api\_example.py](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py)  
* Method 2 (WebSocket): [websockets\_api\_example\_ws\_images.py](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example_ws_images.py)

💡 Looking for AI Image Inspiration?

Explore [VisionGeni AI](https://www.visiongeni.com): a completely free, no-signup gallery of Stable Diffusion 3.5 & Flux images with prompts. Try our Flux prompt generator instantly to spark your creativity.

# **Choosing Between Methods**

Use Method 1 (Basic API) when:

You need to persist images to disk

You want simpler error recovery

Network stability is a concern

Use Method 2 (WebSocket) when:

You need real-time image processing

You want to avoid disk I/O

You’re building an interactive application
Performance is critical


