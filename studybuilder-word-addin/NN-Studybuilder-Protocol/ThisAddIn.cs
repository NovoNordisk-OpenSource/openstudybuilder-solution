﻿using Microsoft.Office.Interop.Word;
using Microsoft.Office.Tools;
using NN_Studybuilder_Protocol.Controls.CustomPanes;
using NN_Studybuilder_Protocol.Data.Services;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Management;
using System.Net;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol
{
    public partial class ThisAddIn
    {
        bool initializeCustom;
        Dictionary<Document, Window> WindowManager; // keeps track of custom task panes. Aka fly-outs
        Ribbon.Ribbon ribbon;
        Lazy<DependencyInjection> serviceProvider;
        public string version;
        public System.Threading.Tasks.Task<string> VersionTask;

        private void ThisAddIn_Startup(object sender, EventArgs e)
        {
            // Safety net: ensure that InitializeCustom() has executed - i.e. it might not run if the .Designer.cs file is somehow regenerated by VS.
            Debug.Assert(initializeCustom);

            // Product name is specified in installer project
            VersionTask = System.Threading.Tasks.Task.Run(() => GetMsiInstalledVersion("StudyBuilder Word add-in"));
            VersionTask.ConfigureAwait(false); 
        }

        private static string GetMsiInstalledVersion(string productName)
        {
            try
            {
                // WMI queries can be very slow when searching Win32_Product (triggers Windows Installer validation on all installed MSI packages + the query scans all installed software).
                // But does not require elevated permissions or registry hacks
                string query = $"SELECT * FROM Win32_Product WHERE Name LIKE '%{productName}%'";
                using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(query))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        return obj["Version"]?.ToString();
                    }
                }

                return $"Product name {productName} not found";
            }
            catch
            {
                return $"Error searching product name {productName}";
            }
        }

        public DependencyInjection DependencyInjection
        {
            get 
            {
                // Since the application is starting up no document is open yet, so use Lazy here or certain objects, e.g. document properties, are not yet available.
                if (serviceProvider == null) 
                    serviceProvider = new Lazy<DependencyInjection>(ConfigureServices);

                return serviceProvider.Value; 
            }
        }

        private DependencyInjection ConfigureServices()
        {
            var sp = new DependencyInjection();
            sp.RegisterServices();
            return sp;
        }

        // This method is called from the .Designer.cs file during initialization
        // Reason: to fully support the following scenarios where not all events are fired:
        // 1. a document is opened in the Word menu.
        // 2. a document is opened by double clicking on it.
        private void InitializeCustom()
        {
            if (WindowManager == null) WindowManager = new Dictionary<Document, Window>();
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12;

            initializeCustom = true;
            Globals.ThisAddIn.Application.DocumentBeforeClose += Application_DocumentBeforeClose;
            Globals.ThisAddIn.Application.DocumentOpen += Application_DocumentOpen;
            Globals.ThisAddIn.Application.DocumentChange += Application_DocumentChange;
        }

        private void Application_DocumentChange()
        {
            InvalidateRibbon();
        }

        private void ThisAddIn_Shutdown(object sender, System.EventArgs e)
        {
        }

        protected override Microsoft.Office.Core.IRibbonExtensibility CreateRibbonExtensibilityObject()
        {
            ribbon = new Ribbon.Ribbon();
            return ribbon;
        }

        /// <summary>
        /// Invalidate all ribbon controls to trigger all the "getXyz.." events on the ribbon buttons. E.g. getEnabled so buttons are enabled/disabled based on template type and possibly other conditions
        /// </summary>
        private void InvalidateRibbon()
        {
            if (ribbon != null && ribbon.ribbon != null)
            {
                ribbon.ribbon.Invalidate();
            }
        }

        #region VSTO generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InternalStartup()
        {
            this.Startup += new System.EventHandler(ThisAddIn_Startup);
            this.Shutdown += new System.EventHandler(ThisAddIn_Shutdown);
        }

        #endregion

        #region Custom Panes
        private void Application_DocumentOpen(Document doc)
        {
            // Remove any left over custom task panes from other documents
            RemoveOrphanedTaskPanes();
            InvalidateRibbon();
        }

        private void Application_DocumentBeforeClose(Document Doc, ref bool Cancel)
        {
            if (!Cancel)
            {
                if (WindowManager.TryGetValue(Doc, out Window result))
                {
                    WindowManager.Remove(Doc);
                }

                // Try to remove left over custom task panes though they might not be fully decommissioned by Word yet
                RemoveOrphanedTaskPanes(Doc);
            }
        }

        /// <summary>
        /// Removes any custom task panes associated with the given document
        /// </summary>
        /// <param name="document">The document associated to the custom task pane(s)</param>
        private void RemoveOrphanedTaskPanes(Document document)
        {
            for (int i = Globals.ThisAddIn.CustomTaskPanes.Count; i > 0; i--)
            {
                CustomTaskPane ctp = Globals.ThisAddIn.CustomTaskPanes[i - 1];
                Window window = ctp.Window as Window;

                if (window != null && window.Document == document)
                {
                    CustomTaskPanes.Remove(ctp);
                }
            }
        }


        /// <summary>
        /// Removes any custom task panes which do not have a Window associated. I.e. closed documents where the Window is not yet disposed (latency).
        /// </summary>
        private void RemoveOrphanedTaskPanes()
        {
            for (int i = Globals.ThisAddIn.CustomTaskPanes.Count; i > 0; i--)
            {
                CustomTaskPane ctp = Globals.ThisAddIn.CustomTaskPanes[i - 1];
                if (ctp.Window == null)
                {
                    CustomTaskPanes.Remove(ctp);
                }
            }
        }

        public void InitTaskPanes()
        {
            try
            {
                // Use a lookup to ensure that each custom task pane is only added and initialized exactly once
                if (!WindowManager.TryGetValue(Globals.ThisAddIn.Application.ActiveDocument, out Window w))
                {
                    var window = Globals.ThisAddIn.Application.ActiveDocument.ActiveWindow;

                    var studyBuilderNavigatorUserControl = DependencyInjection.Resolve<StudyBuilderNavigatorUserControl>();
                    var width = studyBuilderNavigatorUserControl.Width;
                    var studyBuilderNavigatorTaskPane = CustomTaskPanes.Add(studyBuilderNavigatorUserControl, CustomTaskPaneTitles.StudyBuilderNavigator, window);
                    studyBuilderNavigatorTaskPane.Width = width;
                    studyBuilderNavigatorTaskPane.Control.AutoScroll = true;
                    studyBuilderNavigatorTaskPane.Visible = false;
                    studyBuilderNavigatorTaskPane.VisibleChanged += (sender, args) => studyBuilderNavigatorUserControl.OnVisibleChanged(studyBuilderNavigatorTaskPane.Visible);

                    var getOrRefreshDataUserControl = DependencyInjection.Resolve<GetOrRefreshDataUserControl>();
                    width = getOrRefreshDataUserControl.Width;
                    var getOrRefreshTaskPane = CustomTaskPanes.Add(getOrRefreshDataUserControl, CustomTaskPaneTitles.GetOrRefreshDataUserControl, window);
                    getOrRefreshTaskPane.Width = width;
                    getOrRefreshTaskPane.Visible = false;
                    getOrRefreshTaskPane.VisibleChanged += (sender, args) => getOrRefreshDataUserControl.SetStudyId();

                    WindowManager.Add(Globals.ThisAddIn.Application.ActiveDocument, window);
                }
            }
            catch (System.Exception ex)
            {
                MessageBox.Show("Init task panes: " + ex.GetBaseException().Message);
            }
        }

        public void ReInitializeTaskPanes()
        {
            RemoveCustomTaskPaneByTitle(CustomTaskPaneTitles.StudyBuilderNavigator);
            RemoveCustomTaskPaneByTitle(CustomTaskPaneTitles.GetOrRefreshDataUserControl);
            if (WindowManager.ContainsKey(Globals.ThisAddIn.Application.ActiveDocument))
            {
                WindowManager.Remove(Globals.ThisAddIn.Application.ActiveDocument);
                InitTaskPanes();
            }
        }

        private void GenerateSynopsisUserControl_ContentControlsStartEndTagsChanged(object sender, bool e)
        {
            // The Control ID should match the control ID in the ribbon xml
            ribbon.ribbon.InvalidateControl("BtnToggleContentControlStartEndTag");
        }

        /// <summary>
        /// Search the global CustomTaskPanes collection to find the task pane matching the current active Window and document
        /// </summary>
        /// <param name="title">The title of the task pane</param>
        /// <returns>The matching task pane, if found, else null</returns>
        private CustomTaskPane FindCustomTaskPaneByTitle(string title)
        {
            for (int i = Globals.ThisAddIn.CustomTaskPanes.Count; i > 0; i--)
            {
                CustomTaskPane ctp = Globals.ThisAddIn.CustomTaskPanes[i - 1];
                if (ctp.Title != title) continue;
                Window window = ctp.Window as Window;
                if (window == null) continue;
                if (!window.Active) continue;
                if (WindowManager.ContainsKey(window.Document))
                {
                    return ctp;
                }
            }

            return null;
        }

        private void RemoveCustomTaskPaneByTitle(string title)
        {
            for (int i = Globals.ThisAddIn.CustomTaskPanes.Count; i > 0; i--)
            {
                CustomTaskPane ctp = Globals.ThisAddIn.CustomTaskPanes[i - 1];
                if (ctp.Title != title) continue;
                Window window = ctp.Window as Window;
                if (window == null) continue;
                if (!window.Active) continue;
                if (WindowManager.ContainsKey(window.Document))
                {
                    ctp = null;
                    break;
                }
            }
        }

        public CustomTaskPane StudyBuilderNavigator
        {
            get
            {
                return FindCustomTaskPaneByTitle(CustomTaskPaneTitles.StudyBuilderNavigator);
            }
        }

        public CustomTaskPane GetOrRefreshDataPane
        {
            get
            {
                return FindCustomTaskPaneByTitle(CustomTaskPaneTitles.GetOrRefreshDataUserControl);
            }
        }

        #endregion
    }
}
