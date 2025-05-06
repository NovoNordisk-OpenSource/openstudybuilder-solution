using Microsoft.Office.Core;
using Newtonsoft.Json;
using NN_Studybuilder_Protocol.Exceptions;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace NN_Studybuilder_Protocol
{
    /// <summary>
    /// Access application settings
    /// </summary>
    public class ConfigManager
    {
        private static ConfigManager instance = new ConfigManager();
        public static ConfigManager Instance => instance;
        protected T Get<T>(string key)
        {
            return (T)Properties.Settings.Default[key];
        }

        protected void Set(string key, object value)
        {
            Properties.Settings.Default[key] = value;
        }

        internal void SaveSettings()
        {
            Properties.Settings.Default.Save();
        }

        /// <summary>
        /// Get a value from the custom document properties
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="key"></param>
        /// <returns></returns>
        protected T GetDocumentProperty<T>(string key, bool throwIfNotFound = true)
        {
            var p = FindDocumentProperty(key);
            if (p != null)
            {
                return (T)p.Value;
            }

            if (throwIfNotFound)
                throw new DocumentPropertyException() { Key = key };

            return default;
        }

        /// <summary>
        /// Set a value in the custom document properties
        /// </summary>
        /// <param name="key">The name of the custom property</param>
        /// <param name="value">The value of the custom property</param>
        /// <param name="msoPropertyType">The type of property as used by Word custom properties</param>
        protected void SetDocumentProperty(string key, object value, MsoDocProperties msoPropertyType = MsoDocProperties.msoPropertyTypeString)
        {
            var p = FindDocumentProperty(key);
            if (p != null)
            {
                p.Value = value;
            }
            else
            {
                DocumentProperties properties = (DocumentProperties)Globals.ThisAddIn.Application.ActiveDocument.CustomDocumentProperties;
                properties.Add(key, false, msoPropertyType, value);
            }
        }

        private DocumentProperty FindDocumentProperty(string key)
        {
            DocumentProperties properties = (DocumentProperties)Globals.ThisAddIn.Application.ActiveDocument.CustomDocumentProperties;

            foreach (DocumentProperty p in properties)
            {
                if (string.Equals(p.Name, key, StringComparison.Ordinal))
                {
                    return p;
                }
            }

            return null;
        }

        protected string GetAppSetting(string key)
        {
            return System.Configuration.ConfigurationManager.AppSettings[key];
        }

        protected void SetAppSetting(string key, string value)
        {
            System.Configuration.ConfigurationManager.AppSettings[key] = value;
        }

        public string StudyUid
        {
            get { return GetDocumentProperty<string>("StudyUID", false); }
            set { SetDocumentProperty("StudyUID", value); }
        }

        public bool HasStudyUid
        {
            get { return !string.IsNullOrEmpty(GetDocumentProperty<string>("StudyUID", false)); }
        }

        public string StudyId
        {
            get { return GetDocumentProperty<string>("StudyId", false); }
            set { SetDocumentProperty("StudyId", value); }
        }

        /// <summary>
        /// Stores the last update DateTime of each individual, updatable part of the Study
        /// <para>Key: tag of the Content Control</para>
        /// /// <para>Value: last update DateTime from StudyBuilder</para>
        /// </summary>
        public Dictionary<string, DateTime> StudyVersions
        {
            get
            {
                var json = Get<string>("StudyVersions");
                if (string.IsNullOrWhiteSpace(json)) return null;

                return JsonConvert.DeserializeObject<Dictionary<string, DateTime>>(json);
            }

            set
            {
                var serialized = JsonConvert.SerializeObject(value);
                Set("StudyVersions", serialized);
            }
        }

        public string TemplateType
        {
            get { return GetDocumentProperty<string>("StudyBuilderDocType", false); }
        }

        public string StudyBuilder_TenantId
        {
            get { return Get<string>("Studybuilder_TenantId"); }
            set { Set("Studybuilder_TenantId", value); }
        }

        public string StudyBuilder_ClientId
        {
            get { return Get<string>("Studybuilder_ClientId"); }
            set { Set("Studybuilder_ClientId", value); }
        }

        public string StudyBuilder_Scopes
        {
            get { return Get<string>("Studybuilder_Scopes"); }
            set { Set("Studybuilder_Scopes", value); }
        }

        public string StudyBuilder_ApiUrl
        {
            get { return Get<string>("ApiUrl"); }
            set { Set("ApiUrl", value); }
        }

        public string StudyBuilder_Authority => $"https://login.microsoftonline.com/{StudyBuilder_TenantId}/";

        /// <summary>
        /// Check if this add-in can run in the selected document template
        /// </summary>
        public bool IsSupportedTemplate
        {
            get
            {
                try
                {
                    var supportedDocTypes = SupportedDocTypes;
                    if (supportedDocTypes.Length == 0) return false;

                    return supportedDocTypes.FirstOrDefault(d => d == TemplateType) != null;

                }
                catch (DocumentPropertyException)
                {
                    return false;
                }
            }
        }

        /// <summary>
        /// Comma separated string of template names
        /// </summary>
        public string[] SupportedDocTypes
        {
            get
            {
                return new string[] { "CSR", "InterventionalStudyProtocol" };
            }
        }

        public bool ShowContentControlStartEndTags
        {
            get { return GetDocumentProperty<bool>("ShowContentControlStartEndTags", throwIfNotFound: false); }
            set { SetDocumentProperty("ShowContentControlStartEndTags", value, MsoDocProperties.msoPropertyTypeBoolean); }
        }

        public string StudyVersion
        {
            get { return GetDocumentProperty<string>("StudyVersion", false); }
            set { SetDocumentProperty("StudyVersion", value); }
        }

        public string StudyVersionStatus
        {
            get { return GetDocumentProperty<string>("StudyVersionStatus", false); }
            set { SetDocumentProperty("StudyVersionStatus", value); }
        }

        public string GetFullVersionLabel()
        {
            var sb = new StringBuilder();
            if (!string.IsNullOrWhiteSpace(StudyVersion))
            {
                sb.Append($"(v{StudyVersion}");
            }
            if (!string.IsNullOrWhiteSpace(StudyVersionStatus))
            {
                sb.Append($"-{ StudyVersionStatus}");
            }
            if (sb.Length > 0 && sb.ToString().Contains('('))
            {
                sb.Append(")");
            }

            return $"{StudyId} {sb}".Trim();
        }
    }
}
