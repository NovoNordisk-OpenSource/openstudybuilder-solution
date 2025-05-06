using NN_Studybuilder_Protocol.Controls;
using NN_Studybuilder_Protocol.Controls.CustomPanes;
using NN_Studybuilder_Protocol.Data.Services;
using NN_Studybuilder_Protocol.Model;
using System;
using System.Deployment.Application;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows;
using Office = Microsoft.Office.Core;
using System.Management;

namespace NN_Studybuilder_Protocol.Ribbon
{
    [ComVisible(true)]
    public class Ribbon : Office.IRibbonExtensibility
    {
        public Office.IRibbonUI ribbon;
        CustomTaskPaneDisplayManager customTaskPaneDisplayManager;
        ContentControlManager contentControlManager;

        /// <summary>
        /// Occurs when end user toggles the Content Control Start/End tag visibility from a ribbon button
        /// </summary>
        public event EventHandler<bool> ContentControlsStartEndTagsChanged;

        public Ribbon()
        {
            // The Ribbon is initialized before ThisAddin application, so try to keep this constructor empty in order to not slow down the general Word startup process.
        }

        protected CustomTaskPaneDisplayManager CustomTaskPaneDisplayManager
        {
            get
            {
                if (customTaskPaneDisplayManager == null)
                    customTaskPaneDisplayManager = Globals.ThisAddIn.DependencyInjection.Resolve<CustomTaskPaneDisplayManager>();
                return customTaskPaneDisplayManager;
            }
        }

        protected ContentControlManager ContentControlManager
        {
            get
            {
                return contentControlManager = contentControlManager ?? Globals.ThisAddIn.DependencyInjection.Resolve<ContentControlManager>();
            }
        }

        #region IRibbonExtensibility Members

        public string GetCustomUI(string ribbonID)
        {
            return GetResourceText("NN_Studybuilder_Protocol.Ribbon.Ribbon.xml");
        }

        #endregion

        #region Ribbon Callbacks
        //Create callback methods here. For more information about adding callback methods, visit https://go.microsoft.com/fwlink/?LinkID=271226

        public void Ribbon_Load(Office.IRibbonUI ribbonUI)
        {
            ribbon = ribbonUI;
        }

        public string GetLabel(Office.IRibbonControl Control)
        {
            return LocalizationManager.GetLabel(Control.Id);
        }

        public string GetScreentip(Office.IRibbonControl Control)
        {
            return LocalizationManager.GetScreentip(Control.Id);
        }

        public string GetSupertip(Office.IRibbonControl Control)
        {
            return LocalizationManager.GetSupertip(Control.Id);
        }

        protected virtual DeploymentInfo GetVersionInfo()
        {
            var result = new DeploymentInfo
            {
                InstallationPath = "not network deployed - no path available",
                VersionNumber = "not network deployed - no version available"
            };

            if (ApplicationDeployment.IsNetworkDeployed)
            {
                result.VersionNumber = ApplicationDeployment.CurrentDeployment.CurrentVersion.ToString();
                result.InstallationPath = ApplicationDeployment.CurrentDeployment.UpdateLocation != null ? ApplicationDeployment.CurrentDeployment.UpdateLocation.AbsolutePath : "not initialized";
                return result;
            }

            // Read from Windows registry
            var task = Globals.ThisAddIn.VersionTask;
            if (!task.IsCompleted)
            {
                task.Wait();
            }
            if (task.IsFaulted)
            {
                result.VersionNumber = "Error getting version";
                result.InstallationPath = "Error getting version";
            }
            else
            {
                result.VersionNumber = task.Result; ;
                result.InstallationPath = AppDomain.CurrentDomain.BaseDirectory;
            }            

            return result;
        }

        /// <summary>
        /// Automatically rolls back any changes performed by the func
        /// </summary>
        /// <param name="undoRecordname">The name of the action as it should display in the undo history of the end user</param>
        /// <param name="func">The func to wrap in undo</param>
        protected virtual void UndoEnabledAction(string undoRecordname, Func<bool> func)
        {
            var undoRecord = Globals.ThisAddIn.Application.UndoRecord;
            undoRecord.StartCustomRecord(undoRecordname);

            var result = func();
            undoRecord.EndCustomRecord();

            if (!result)
            {
                Globals.ThisAddIn.Application.ActiveDocument.Undo();
            }
        }

        /// <summary>
        /// Wraps the given action in a Word undo record, so end users can undo the entire action or actions in one click
        /// </summary>
        /// <param name="undoRecordname">The name of the action as it should display in the undo history of the end user</param>
        /// <param name="action">The action to wrap in undo</param>
        protected virtual void UndoEnabledAction(string undoRecordname, Action action)
        {
            var undoRecord = Globals.ThisAddIn.Application.UndoRecord;
            undoRecord.StartCustomRecord(undoRecordname);
            action();
            undoRecord.EndCustomRecord();
        }

        #endregion

        #region Helpers

        internal static string GetResourceText(string resourceName)
        {
            Assembly asm = Assembly.GetExecutingAssembly();
            string[] resourceNames = asm.GetManifestResourceNames();
            for (int i = 0; i < resourceNames.Length; ++i)
            {
                if (string.Compare(resourceName, resourceNames[i], StringComparison.OrdinalIgnoreCase) == 0)
                {
                    using (StreamReader resourceReader = new StreamReader(asm.GetManifestResourceStream(resourceNames[i])))
                    {
                        if (resourceReader != null)
                        {
                            return resourceReader.ReadToEnd();
                        }
                    }
                }
            }
            return null;
        }

        #endregion

        string templateNotSupportedMessage = "This template is not supported by the StudyBuilder ribbon";

        public void BtnUpdate_Click(Office.IRibbonControl Control)
        {
            if (string.IsNullOrWhiteSpace(ConfigManager.Instance.StudyUid))
            {
                var result = MessageBox.Show("You need to select a Study before getting data", "Study not selected", MessageBoxButton.OKCancel, MessageBoxImage.Information);
                if (result == MessageBoxResult.OK)
                {
                    ShowGetOrRefreshDataPane(false);
                    ShowStudyBuilderNavigator(true);
                }

                return;
            }

            CustomTaskPaneDisplayManager.ShowTaskPane(() => Globals.ThisAddIn.GetOrRefreshDataPane.Visible = !Globals.ThisAddIn.GetOrRefreshDataPane.Visible);
            if (Globals.ThisAddIn.GetOrRefreshDataPane != null && Globals.ThisAddIn.GetOrRefreshDataPane.Visible)
            {
                ShowStudyBuilderNavigator(false);
            }
        }

        private void ShowGetOrRefreshDataPane(bool show)
        {
            CustomTaskPaneDisplayManager.ShowTaskPane(() => Globals.ThisAddIn.GetOrRefreshDataPane.Visible = show);
        }

        private void ShowStudyBuilderNavigator(bool show)
        {
            CustomTaskPaneDisplayManager.ShowTaskPane(() => Globals.ThisAddIn.StudyBuilderNavigator.Visible = show);
        }

        public void BtnNavigator_Click(Office.IRibbonControl Control)
        {
            CustomTaskPaneDisplayManager.ShowTaskPane(() => Globals.ThisAddIn.StudyBuilderNavigator.Visible = !Globals.ThisAddIn.StudyBuilderNavigator.Visible);
            if (Globals.ThisAddIn.StudyBuilderNavigator != null && Globals.ThisAddIn.StudyBuilderNavigator.Visible)
            {
                ShowGetOrRefreshDataPane(false);
            }
        }

        public void BtnAboutStudyBuilder_Click(Office.IRibbonControl Control)
        {
            var version = GetVersionInfo();
            var text = $"Add-in version: {version.VersionNumber}{Environment.NewLine}{Environment.NewLine}Installation path:{Environment.NewLine}{Environment.NewLine}{version.InstallationPath}";
            var infoBox = new InfoBox(text, showEnvironmentPicker: false);
            infoBox.EnvironmentChanged += InfoBox_EnvironmentChanged;
            infoBox.ShowDialog();
        }

        private void InfoBox_EnvironmentChanged(object sender, EventArgs e)
        {
            Globals.ThisAddIn.Application.ActiveWindow.View.ReadingLayout = false;

            ShowGetOrRefreshDataPane(false);
            // Trigger a re-initialization of controls in the user controls
            ShowStudyBuilderNavigator(false);
            Globals.ThisAddIn.ReInitializeTaskPanes();
            ShowStudyBuilderNavigator(true);

            // Update header in the document
            ContentControlManager.UpdateDateStudyId(ConfigManager.Instance.StudyId);

            // Clear all content controls
            ContentControlManager.ClearContentFromAllStudyBuilderContentControls();

            // Reset cached IPublicClientApplication
            var clientAppFactory = Globals.ThisAddIn.DependencyInjection.Resolve<PublicClientAppFactory>();
            clientAppFactory?.ResetCachedClientApp();
        }

        public bool BtnNavigator_Enabled(Office.IRibbonControl Control)
        {
            return CustomTaskPaneDisplayManager.IsSupportedTemplate;
        }

        public string BtnNavigator_Screentip(Office.IRibbonControl Control)
        {
            if (CustomTaskPaneDisplayManager.IsSupportedTemplate)
            {
                return "Open the study search pane";
            }

            return templateNotSupportedMessage;
        }

        public bool BtnUpdate_Enabled(Office.IRibbonControl Control)
        {
            return CustomTaskPaneDisplayManager.IsSupportedTemplate;
        }

        public string BtnUpdate_Screentip(Office.IRibbonControl Control)
        {
            if (CustomTaskPaneDisplayManager.IsSupportedTemplate)
            {
                return "Get the latest data from StudyBuilder";
            }

            return templateNotSupportedMessage;
        }

        public string BtnToggleContentControlStartEndTag_Screentip(Office.IRibbonControl Control)
        {
            return "Toggle StudyBuilder Content Controls start/end tags visible";
        }

        public string BtnToggleContentControlStartEndTag_Supertip(Office.IRibbonControl Control)
        {
            return $"Use this button to toggle the visibility of the StudyBuilder Content Controls";
        }

        public void BtnToggleContentControlStartEndTag_Click(Office.IRibbonControl Control, bool pressed)
        {
            ContentControlManager.ToggleContentControlStartEndTagsVisible(pressed);
            ContentControlsStartEndTagsChanged?.Invoke(this, pressed);
        }

        public bool BtnToggleContentControlStartEndTag_GetPressed(Office.IRibbonControl control)
        {
            return ContentControlManager.GetStartEndTagState();
        }

        public string BtnRemoveContentControls_Screentip(Office.IRibbonControl Control)
        {
            return "Click to remove all Study Builder Content Controls";
        }

        public void BtnRemoveContentControls_Click(Office.IRibbonControl Control)
        {
            try
            {
                var proceed = MessageBox.Show("Deleting all Study Builder content controls cannot be undone." +
                        "\r\n\r\nAre you sure you wish to proceed?",
                        "Delete Study Builder content controls?",
                        MessageBoxButton.OKCancel,
                        MessageBoxImage.Warning);

                if (proceed != MessageBoxResult.OK) return;
                UndoEnabledAction("Delete all StudyBuilder content controls", () =>
                {
                    ContentControlManager.DeleteAllStudyBuilderContentControls();
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show("An error occured during deletion:" +
                    $"\r\n\r\n{ex.GetBaseException().Message}",
                        "Error deleting Study Builder content controls",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error);
            }
        }
    }
}
