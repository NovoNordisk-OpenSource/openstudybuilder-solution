# System Component Architecture

[![System component architecture](/images/documentation/studybuilder-system-components.svg)](/images/documentation/studybuilder-system-components.svg)

The system is composed of the following components.

| System Component <br> (License) | Technology <br> (Git repository) | Description |
| ------ | ------ | ------------------ |
| OpenStudyBuilder App <br> (GPLv3)     | Vue.js using Vuetify library <br> (OpenStudyBuilder) | JavaScript based web application with the UI for creating the study definition specification, maintaining library standards. The OpenStudyBuilder app holds two main modules: <br> - Library <br> - Studies | 
| OpenStudyBuilder Documentation Portal <br> (GPLv3) | VitePress <br> (documentation-portal) | Markdown based documentation portal with OpenStudyBuilder Introduction, User Guides, System Documentation, Data Models and more. |
| API Specification <br> (MIT) | OpenAPI Specification / Swagger <br> (clinical-mdr-api/openapi.json) | Online Open API documentation of the Clinical MDR API and Consumer API. <br> Note, an exported version of the API specification is also shared in the git repo. |
| Clinical MDR API <br> (GPLv3) | Python using FastAPI framework <br> (clinical-mdr-api) | Python based web application based on FastAPI framework supporting all CRUD actions to the database, access control, versioning, workflows and data integrity rules. |
| Consumer API <br> (GPLv3) | Python using FastAPI framework <br> (clinical-mdr-api) | Python based web application based on FastAPI framework only supporting all read (GET) to the database and access control. API endpoints are optimized for downstream consumers and running in separate service not to impact frontend application users. |
| Clinical MDR <br> (MIT) | Cypher <br> (neo4j-mdr-db) | Clinical MDR logical and physical data models, database constraint definitions, procedures and functions. |
| Graph Database <br> (Neo4j free edition or licensed enterprise edition) | Neo4j native graph database <br> (neo4j.com) | Labeled property graph database. |
| CDISC Library Standards Import <br> (GPLv3) | Python and Cypher <br> (mdr-standards-import) | Import programs connecting to CDISC Library, downloading files to cloud storage, reading these into staging database, and then inserting data into Clinical MDR database. |
| Data Import <br> (MIT) | Python and Cypher <br> (studybuilder-import) | Import programs using .csv or JSON files as input for importing various data into the Clinical MDR database. The import programs can import JSON files exported from the system, in this way data can be moved between environments. All import actions are done via calls to the Clinical MDR API, so all import actions will be audit trailed. |
| Data Export <br> (MIT) | Python and Cypher <br> (studybuilder-export) | Program that exports all defined studies from a OpenStudybuilder instance. It's possible to filter the exported study data by including and/or excluding study numbers. |
| Reports <br> (MIT) | NeoDash Reports <br> (neo4j-mdr-db) | The NeoDash report definitions are saved within the Clinical MDR database and can be opened by the NeoDash reporting engine. <br> The NeoDash reporting engine is a browser based tool (https://neo4j.com/labs/neodash/) |

> - MIT: MIT license is a permissive free software license originating at the Massachusetts Institute of Technology (MIT).<br>For more info see: https://opensource.org/licenses/MIT

> - GPLv3: GPLv3 license is a GNU General Public License. The GPL series are all copyleft licenses, which means that any derivative work must be distributed under the same or equivalent license terms.<br>For more info see: https://opensource.org/licenses/GPL-3.0 and https://www.gnu.org/licenses/quick-guide-gplv3.html

