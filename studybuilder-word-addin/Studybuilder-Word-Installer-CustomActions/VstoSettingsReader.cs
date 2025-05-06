using System;
using System.Configuration;
using System.IO;
using System.Xml;

namespace Studybuilder_Word_Installer_CustomActions
{
    public class VstoSettingsReader : AppSettingsReader
    {
        private XmlDocument vstoSettingsDoc;
        private readonly string vstoSettingsPath;

        public VstoSettingsReader(string vstoSettingsPath)
        {
            if (string.IsNullOrWhiteSpace(vstoSettingsPath)) throw new ArgumentNullException(nameof(vstoSettingsPath));
            this.vstoSettingsPath = vstoSettingsPath;            
        }

        protected XmlDocument VstoSettingsDoc
        {
            get
            {
                if (vstoSettingsDoc == null)
                {
                    if (!File.Exists(vstoSettingsPath)) throw new FileNotFoundException($"VSTO config file {vstoSettingsPath} not found");

                    vstoSettingsDoc = new XmlDocument();
                    vstoSettingsDoc.Load(vstoSettingsPath);
                }

                return vstoSettingsDoc;
            }
        }

        public void Set(string key, string value, string xmlElementName = "NN_Studybuilder_Protocol.Properties.Settings")
        {
            if (string.IsNullOrWhiteSpace(xmlElementName)) throw new ArgumentException("Please specify the VSTO settings xml element name");

            var xpath = $"//{xmlElementName}";
            var node = VstoSettingsDoc.SelectSingleNode(xpath);
            if (node == null)
            {
                throw new InvalidOperationException($"VSTO settings xml element {xmlElementName} not found in config");
            }

            try
            {
                // Select the specific "setting" node with the given name attribute
                var settingElem = (XmlElement)node.SelectSingleNode($"setting[@name='{key}']");
                if (settingElem != null)
                {
                    // Select the "value" node within the found "setting" node
                    var valueElem = (XmlElement)settingElem.SelectSingleNode("value");
                    if (valueElem != null)
                    {
                        valueElem.InnerText = value;
                    }
                    else
                    {
                        // If the "value" node doesn't exist, create it
                        valueElem = VstoSettingsDoc.CreateElement("value");
                        valueElem.InnerText = value;
                        settingElem.AppendChild(valueElem);
                    }
                }
                else
                {
                    // If the "setting" node doesn't exist, create it along with the "value" node
                    var newSettingElem = VstoSettingsDoc.CreateElement("setting");
                    newSettingElem.SetAttribute("name", key);
                    var newValueElem = VstoSettingsDoc.CreateElement("value");
                    newValueElem.InnerText = value;
                    newSettingElem.AppendChild(newValueElem);
                    node.AppendChild(newSettingElem);
                }
            }
            catch (Exception ex)
            {
                // Handle or log the exception as needed
                Console.WriteLine(ex.Message);
                Console.WriteLine(ex.StackTrace);

                throw;
            }
        }

        public void Save()
        {
            VstoSettingsDoc.Save(vstoSettingsPath);
        }
    }
}
