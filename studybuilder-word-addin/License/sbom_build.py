import json
import requests

# read in sbom json file
file_path =  r"C:\git\NN_Studybuilder_addin\NN_Studybuilder_addin\License\StudyBuilder Word add-in SBOM.json"
output_file_path = r"C:\git\NN_Studybuilder_addin\NN_Studybuilder_addin\sbom.md"


# read in sbom json file
with open(file_path, 'r', encoding='utf-8') as file:
    sbom_data = json.load(file)

components_summary = []

# Receive relevant information
for component in sbom_data.get("components", []):
    name = component.get("name", "Unknown")
    licenses = ", ".join([license_info.get("license", {}).get("id", "") for license_info in component.get("licenses", [])])
    license_url = next((license_info.get("license", {}).get("url", "") for license_info in component.get("licenses", [])), "")
    version = component.get("version", "Unknown")
    vcs_url = next((ref.get("url") for ref in component.get("externalReferences", []) if ref.get("type") == "vcs"), "Unknown")
    
    components_summary.append({
        "name": name,
        "version": version,
        "license": licenses,
        "license_url": license_url,
        "url": vcs_url
    })

# Print the new array object (optional)
#print(json.dumps(components_summary, indent=4))

# Print names of components without a license or license_url
for component in components_summary:
    if not component["license"] and not component["license_url"]:
        print(f"Component without license or license_url: {component['name']}")


# get plain license URLs
for component in components_summary:
    if (not component["license"]):
        # component with license_url instead of license
        if (component["license_url"] == "http://go.microsoft.com/fwlink/?LinkId=329770"):
            component["license_raw"] = "https://raw.githubusercontent.com/dotnet/core/refs/heads/main/license-information.md"
        elif (component["license_url"] == "https://github.com/dotnet/corefx/blob/master/LICENSE.TXT"):
            component["license_raw"] = "https://raw.githubusercontent.com/dotnet/corefx/refs/tags/master/LICENSE.TXT"
        else:
            print(f"Component without license: {component['name']}")
    else:
        if (component["url"] == "https://github.com/Azure/azure-sdk-for-net"):
            component["license_raw"] = "https://raw.githubusercontent.com/Azure/azure-sdk-for-net/refs/heads/main/LICENSE.txt"
        elif (component["url"] == "https://github.com/manuc66/JsonSubTypes"):
            component["license_raw"] = "https://raw.githubusercontent.com/manuc66/JsonSubTypes/refs/heads/master/LICENSE"
        elif (component["url"] == "https://github.com/dotnet/runtime"):
            component["license_raw"] = "https://raw.githubusercontent.com/dotnet/runtime/refs/heads/main/LICENSE.TXT"
        elif (component["url"] == "https://github.com/AzureAD/microsoft-authentication-library-for-dotnet"):
            component["license_raw"] = "https://raw.githubusercontent.com/AzureAD/microsoft-authentication-library-for-dotnet/refs/heads/main/LICENSE"
        elif (component["url"] == "https://github.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet"):
            component["license_raw"] = "https://raw.githubusercontent.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet/refs/heads/dev/LICENSE.txt"

        elif (component["name"] == "Microsoft.NETCore.Targets"):
            component["license_raw"] = "https://raw.githubusercontent.com/dotnet/corefx/refs/tags/v3.1.0/LICENSE.TXT"
        elif (component["url"] == "https://github.com/JamesNK/Newtonsoft.Json"):
            component["license_raw"] = "https://raw.githubusercontent.com/JamesNK/Newtonsoft.Json/refs/heads/master/LICENSE.md"
        elif (component["url"] == "https://github.com/App-vNext/Polly"):
            component["license_raw"] = "https://raw.githubusercontent.com/App-vNext/Polly/refs/heads/main/LICENSE"
        elif (component["url"] == "https://github.com/App-vNext/Polly"):
            component["license_raw"] = "https://raw.githubusercontent.com/App-vNext/Polly/refs/heads/main/LICENSE"
        elif (component["url"] == "https://github.com/restsharp/RestSharp.git"):
            component["license_raw"] = "https://raw.githubusercontent.com/restsharp/RestSharp/refs/heads/dev/LICENSE.txt"
        elif (component["name"] == "SimpleInjector"):
            component["license_raw"] = "https://raw.githubusercontent.com/simpleinjector/SimpleInjector/refs/heads/master/LICENSE"
        elif (component["url"] == "git://github.com/dotnet/runtime"):
            component["license_raw"] = "https://raw.githubusercontent.com/dotnet/runtime/refs/heads/main/LICENSE.TXT"
        else:
            print(f"Component without license: {component['name']}")



# print final SBOM file
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    md_table = "| Package | Version |\n"
    md_table += "|---|---|\n"
    for component in components_summary:
        name = component["name"]
        version = component["version"]
        md_table += f"| {name} | {version} | \n"


    output_file.write("## Installed packages\n\n")
    output_file.write(md_table)
    output_file.write("\n## Third-party package licenses\n\n")

    # Loop through all components
    for component in components_summary:
        if "license_raw" in component and component["license_raw"]:
            try:
                # Fetch the license content from the URL
                response = requests.get(component["license_raw"])
                response.raise_for_status()  # Raise an error for HTTP issues
                license_content = response.text
                # Remove any occurrences of triple backticks
                license_content = license_content.replace("```", "")
            except Exception as e:
                license_content = f"Error fetching license: {e}"

            # Print the formatted output
            output_file.write(f"### License for 3rd party library {component['name']}\n\n")
            output_file.write("```\n")
            output_file.write(license_content)
            output_file.write("\n```\n\n")