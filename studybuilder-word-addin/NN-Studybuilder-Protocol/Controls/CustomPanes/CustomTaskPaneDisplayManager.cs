using System;

namespace NN_Studybuilder_Protocol.Controls.CustomPanes
{
    public class CustomTaskPaneDisplayManager
    {
        private readonly ConfigManager configManager;

        public CustomTaskPaneDisplayManager(ConfigManager configManager)
        {
            this.configManager = configManager;
        }

        public bool IsSupportedTemplate => configManager.IsSupportedTemplate;

        /// <summary>
        /// Checks if the current document template is supported and shows an info box if it is not.
        /// </summary>
        /// <param name="action"></param>
        public virtual void ShowTaskPane(Action action)
        {
            Globals.ThisAddIn.InitTaskPanes();
            action();
        }
    }
}
