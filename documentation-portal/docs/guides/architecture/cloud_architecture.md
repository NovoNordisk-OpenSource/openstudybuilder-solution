# Cloud Architecture

<!--
### Highlevel Design using Web App Containers

[![System Integrations](~@source/images/documentation/Clinical-MDR-Highlevel.png)](../../images/documentation/Clinical-MDR-Highlevel.png)

The deployment is based on Azure Wep App Containers. Only the Python API container will have write access to the Neo4j database.
-->
### Highlevel Azure Solution Design

[![System Integrations](~@source/images/documentation/Clinical-MDR-Azure-Highlevel.png)](../../images/documentation/Clinical-MDR-Azure-Highlevel.png)

All communication is facilitated via azure private links, which ensures private and secure connection internally in the virtual private network in which the system is hosted.

Code is published through Azure DevOps git repositories to the hosted cloud environment by utilising a self-hosted ubuntu agent. Code will be pushed in the form of docker images that will be stored in an azure container registry. Ahead of deployment, the images will automatically be scanned using Prisma CloudScan.

As the images are added to Azure Container Registry, they will be scanned utilising Azure Defender.
The Azure Container Registry will push new images to Azure App Services, where these will be hosted as individual docker containers. End users will access the system components through a single source, the Azure Application Gateway, which will pass incoming and eligible requests to the correct individual component for further processing and request fulfilment based on url paths.

As the system is hosted in a private virtual network, all incoming communication must come from NN CORP connected machines.

Monitoring and logging has been established using Azure Log Analytics Workspace and Application Insights. Authentication is facilitated through Azure Enterprise Applications, Azure App Registrations and groups.

A total of four virtual machines are created to enable a neo4j DB cluster of three VMs plus a single VM to monitor the functionality of the cluster VMs and the health of the cluster. The cluster VMs are created in separate availability zones, so they are located in different physical locations.


### Azure Resources Design
Resource groups in Azure are logical containers for cloud-based resources that enables grouping of resources as per the team's needs. They allow for resource group-specific management of resources and tracking costs from specific resource groups (and by extension, specific logical areas/functions of a system).
Three main resource groups have been created in the project: 
- The **Application** resource group, containing all resources related to running the system in practice
- The **Configuration** resource group, containing all resources related to configuring, managing and monitoring the system
- The **Deployment** resource group, containing resources that support in deployment of the system.

Additionally, two resource groups exist for handling DNS and networking of the system

[![System Integrations](~@source/images/documentation/Clinical-MDR-Azure-Resources.png)](../../images/documentation/Clinical-MDR-Azure-Resources.png)



