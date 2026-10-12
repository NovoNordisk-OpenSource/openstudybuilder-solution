# Downloading Codelist Data from CDISC

Before being able to load the cdisc CT in the OpenStudyBuilder application, we need to download the existing packages from the cdisc library.

## Download new cdisc data (optional)

Inside the `import_standards` directory, launch the two following scripts:

```
$ uv run poe download_ct_json_data_from_cdisc_api
$ uv run poe download_data_models_json_data_from_cdisc_api
```

---
**Note:**
You may need here an account in order to be allowed to access the cdisc information here! You can skip this step if it's ok for You to work with cdisc data which are not perfectly updated to the current version.

---

This script will put the downloads in `./cdisc_data`. The script will only download versions that are not available on file already.


---
**Note:**

To avoid high usage of the cdisc api, there is a dump available in the git repository of the project.
Just unzip the cdisc_data.zip file.

---

```
$ unzip cdisc_data.zip
```