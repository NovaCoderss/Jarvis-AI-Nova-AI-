import asyncio
import random
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep 

# Function to open and display images based on a given prompt
def open_images(prompt):
    folder_path = r"Data" # Folder where the images are stored
    prompt = prompt.replace(" ", "_") # Replace spaces in prompt with underscores

    # Generate the filenames for the images
    Files = [f"{prompt}_{i}.jpg" for i in range(1, 5)]

    # This loop was outside the function in the screenshot, now correctly indented
    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            # Try to open and display the image
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1) # Pause for 1 second before showing the next image
        except IOError:
            print(f"Unable to open {image_path}")

# API details for the Hugging Face Stable Diffusion model
# --- CRITICAL FIX HERE: Changed '1-0' to '1.0' in the model ID ---
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0" 
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"} 


# Async function to send a query to the Hugging Face API
async def query(payload, headers): 
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    response.raise_for_status() 
    return response.content

# Async function to generate images based on the given prompt
async def generate_images(prompt: str):
    huggingface_api_key = get_key('.env', 'HuggingFaceAPIKey')
    if not huggingface_api_key:
        print("\n" + "="*80)
        print("ERROR: HUGGINGFACE_API_KEY NOT FOUND IN YOUR .ENV FILE.")
        print("Please ensure your .env file (in your project's ROOT directory) contains:")
        print('HUGGINGFACE_API_KEY="hf_YOUR_ACTUAL_TOKEN_HERE"')
        print("Get your token from: https://huggingface.co/settings/tokens (ensure it has 'Write' role).")
        print("="*80 + "\n")
        return False 

    tasks = []

    # Create 4 image generation tasks
    for i in range(4): 
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed = {random.randint(0, 100000)}",
        }
        # Use the explicitly checked key here
        current_headers = {"Authorization": f"Bearer {huggingface_api_key}"}
        task = asyncio.create_task(query(payload, headers=current_headers)) 
        tasks.append(task)

    # Wait for all tasks to complete
    try:
        image_bytes_list = await asyncio.gather(*tasks)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request error during image generation: {e}")
        if e.response is not None:
            print(f"API Response Content: {e.response.text}")
        return False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during image fetching: {e}")
        return False

    # Save the generated images to files
    generated_image_paths = []
    for i, image_bytes in enumerate(image_bytes_list):
        output_folder = "Data" 
        os.makedirs(output_folder, exist_ok=True) 

        cleaned_prompt = prompt.replace(" ", "_")
        file_path = os.path.join(output_folder, f"{cleaned_prompt}_generated_{i + 1}.jpg") 
        
        with open(file_path, "wb") as f: 
            f.write(image_bytes)
        print(f"Saved generated image: {file_path}")
        generated_image_paths.append(file_path)
    
    # Optionally open the generated images after saving them
    for path in generated_image_paths:
        try:
            os.startfile(path) 
            print(f"Opened generated image: {path}")
            sleep(1) 
        except Exception as e:
            print(f"ERROR: Could not open generated image {path}: {e}")

    return True 

# Main execution loop, reconstructed and corrected for syntax and logic
if __name__ == "__main__":
    # Define the path to the status file
    status_file_path = r"Frontend\Files\ImageGeneration.data"

    # Ensure the directory for the status file exists
    status_dir = os.path.dirname(status_file_path)
    if status_dir and not os.path.exists(status_dir):
        os.makedirs(status_dir, exist_ok=True)
        print(f"Created directory for status file: {status_dir}")

    # Initialize the status file if it doesn't exist
    if not os.path.exists(status_file_path):
        with open(status_file_path, "w") as f:
            f.write("None,False") 
        print(f"Created initial status file: {status_file_path}")
    
    print("\n--- Image Generation Listener Started ---")
    print(f"Monitoring: {status_file_path}")
    print("To trigger image generation, edit the file with 'YourPrompt,True' (e.g., 'A cat,True')")
    print("---------------------------------------")

    while True: 
        try:
            with open(status_file_path, "r") as f:
                content = f.read().strip()
            
            Prompt = "None"
            Status = "False"

            if content:
                parts = content.split(",")
                if len(parts) >= 2: 
                    Prompt = parts[0].strip()
                    Status = parts[1].strip()
                else:
                    print(f"WARNING: Malformed content in status file: '{content}'. Expected 'Prompt,Status'.")
                    with open(status_file_path, "w") as f:
                        f.write("None,False")
                    sleep(1) 
                    continue 

            if Status.lower() == "true": 
                print(f"\n--- Detected command: Generating Images for prompt: '{Prompt}' ---")
                
                ImageStatus = asyncio.run(generate_images(prompt=Prompt))
                
                if ImageStatus: 
                    print(f"Overall Image generation task completed for prompt: '{Prompt}'")
                else:
                    print(f"Overall Image generation task FAILED for prompt: '{Prompt}'")

                with open(status_file_path, "w") as f:
                    f.write(f"{Prompt},False") 
                print(f"Status file reset to: '{Prompt},False'.")
                
                break 

            else:
                sleep(1) 

        except FileNotFoundError:
            print(f"ERROR: Status file not found at {status_file_path}. Please ensure it exists.")
            sleep(5) 
        except Exception as e:
            print(f"AN UNEXPECTED ERROR OCCURRED IN MAIN LOOP: {e}")
            sleep(5) 
