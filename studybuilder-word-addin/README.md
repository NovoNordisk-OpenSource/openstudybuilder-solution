# StudyBuilder Word Add-in

This repository contains the Word add-in for the open source project of the OpenStudyBuilder. The add-in can be installed in Microsoft Word. The Add-in connects with an OpenStudyBuilder instance to receive protocol information for a protocol template.

## Build and Test

The build is created locally in Visual Studio. To install the add-in, you need to create and embed a certificate within the installation file. This certificate can either be:

- A **development certificate** (for local testing).
- A **production certificate** (for deployment).

An example installation file can be [requested](#pre-compiled-test-installation), which contains only a development certificate. If you require assistance obtaining a production certificate, please contact [info@pointwork.com](mailto:info@pointwork.com) as a separate service.

### Build and release in Visual Studio - only local installation

Please note that more build and release options exist. For details please refer to the [official Microsoft documentation](https://learn.microsoft.com/en-us/office/dev/add-ins/).

To compile and release a Word add-in in Visual Studio, including adding a certificate, follow these steps:

1. **Open the Project**: Open your Word add-in project in Visual Studio.

2. **Add a Certificate**:
   - Right-click the project in the `Solution Explorer` and select `Properties`.
   - Navigate to the `Signing` tab.
   - Check the `Sign the ClickOnce manifests` checkbox.
   - To use a temporary, self-signed certificate:
     - Click the `Create Test Certificate` button and provide a password.
   - To use an official certificate:
     - Click the `Select from Store` button to choose a certificate from the Windows Certificate Store, or click `Select from File` to use a certificate file purchased from a certified certificate vendor.

3. **Update OpenStudyBuilder Connection**:
   - Right-click the project in the `Solution Explorer` and select `Properties`.
   - Navigate to the `Properties` tab.
   - Replace the settings with your OpenStudyBuilder Entra value settings to connecto to your OpenStudyBuilder instance - per default, the sandbox environment is connected

4. **Build the Project**:
   - Go to the `Build` menu and select `Build Solution` or press `Ctrl+Shift+B`.
   - Ensure there are no build errors in the `Output` pane.

5. **Configure Publish Settings**:
   - Navigate to the `Publish` tab in the project properties.
   - Click the `Publish Wizard` button to start the Publish Wizard.

6. **Publish Wizard Steps**:
   - **Specify the publish location**: Choose a location to publish your add-in (e.g., a network share, a web server, or an Azure App Service).
   - **Configure the publish method**: Select the appropriate publish method based on your chosen location.
   - **Update settings**: Configure any additional settings as needed, such as file replacements and versioning.

7. **Test the Add-in**:
   - Install the add-in using the published files


### Build and release - corporate installation

For more detailed information, refer to the [official Microsoft documentation](https://docs.microsoft.com/en-us/office/dev/add-ins/publish/publish) on publishing add-ins.

## Pre-compiled Test Installation

If you would like to receive an example installation file to install the add-in on your private PC (considering all risks of executable files), you can reach out via email:

- **Email:** [openstudybuilder@gmail.com](mailto:openstudybuilder@gmail.com)  
- **Subject:** "Request access to Word-add-in installer"

This example installation file will only include a development certificate. For security reasons, it is generally recommended to build the installation file yourself.

## Uninstall

To uninstall the StudyBuilder Word Add-in on Windows, follow these steps:

1. Open the **Start Menu** and search for **"Add or Remove Programs"**.
2. In the **Apps & Features** window, use the search bar to look for **"StudyBuilder"**.
3. Select the **StudyBuilder Word Add-in** from the list of installed programs.
4. Click the **Uninstall** button and follow the on-screen instructions to complete the removal process.

This will remove the StudyBuilder Word Add-in from your system.

## Documentation

Refer to the following resources for installation and usage instructions:

- [Documentation](./documentation.md)
- [Protocol Template for Testing](./ProtocolTemplate_OSB_1.0.docx)

## Contributing

We currently do not support contributions to this repository. If you have suggestions or encounter issues, please report them via:

- **GitLab Issues**
- **Slack:** [OpenStudyBuilder Slack](https://join.slack.com/t/openstudybuilder/shared_invite/zt-19mtauzic-Jvrhtmy7hGstgyiIvB1Wsw)

## Naming Conventions

The repository folder names are tightly bound to the initial selected names. Due to the build and installation setup, these names **must not be changed**.




