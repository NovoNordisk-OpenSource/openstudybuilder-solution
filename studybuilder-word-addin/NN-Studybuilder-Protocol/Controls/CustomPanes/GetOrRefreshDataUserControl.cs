using Microsoft.Office.Interop.Word;
using NN_Studybuilder_Protocol.Data.Services;
using NN_Studybuilder_Protocol.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using System.Windows.Forms.VisualStyles;

namespace NN_Studybuilder_Protocol.Controls.CustomPanes
{
    public partial class GetOrRefreshDataUserControl : UserControl
    {
        private readonly TemplateUpdateService templateUpdateService;

        public GetOrRefreshDataUserControl(TemplateUpdateService templateUpdateService)
        {
            this.templateUpdateService = templateUpdateService;
            InitializeComponent();
        }

        protected override void OnLoad(EventArgs e)
        {
            //progressBar.Hide();
            InitializeControls();
            base.OnLoad(e);
        }

        private void InitializeControls()
        {
            progressBar.Hide();

            InitializeListviewContentControls();
        }

        public void SetStudyId()
        {
            lblExistingStudyID.Text = ConfigManager.Instance.GetFullVersionLabel();
        }

        private void InitializeListviewContentControls()
        {
            ListViewContentControls.Columns.Add("Select all");

            // Add a 'Select All' checkbox in the header column
            InitSelectAllCheckbox();

            ListViewContentControls.FullRowSelect = true;
            ListViewContentControls.View = System.Windows.Forms.View.Details;

            var notSupported = new[] { ContentControlTagNames.DevelopmentStage };

            foreach (ContentControl cc in Globals.ThisAddIn.Application.ActiveDocument.ContentControls)
            {
                if (cc.Tag == null || !cc.Tag.StartsWith(StudyBuilderConstants.ContentControlPrefix)) continue;

                if (notSupported.FirstOrDefault(i => string.Equals(i, cc.Tag, StringComparison.OrdinalIgnoreCase)) != null) continue; // Skip until ready in API

                ListViewContentControls.Items.Add(new ListViewItem(cc.Title) { Tag = cc.Tag, Name = cc.Title });
            }

            ListViewContentControls.AutoResizeColumns(ColumnHeaderAutoResizeStyle.ColumnContent);
            // Avoid horizontal scroll bar
            ListViewContentControls.Columns[0].Width = ListViewContentControls.Width - 4;
        }

        #region Select All checkbox
        bool clicked = false;
        System.Windows.Forms.VisualStyles.CheckBoxState state;

        protected void InitSelectAllCheckbox()
        {
            ListViewContentControls.HeaderStyle = ColumnHeaderStyle.Clickable;
            ListViewContentControls.CheckBoxes = true;
            ListViewContentControls.OwnerDraw = true;
            ListViewContentControls.ColumnClick += ListViewContentControls_ColumnClick;
            ListViewContentControls.DrawColumnHeader += ListViewContentControls_DrawColumnHeader;
            ListViewContentControls.DrawItem += ListViewContentControls_DrawItem;
            ListViewContentControls.DrawSubItem += ListViewContentControls_DrawSubItem;
        }

        private void ListViewContentControls_DrawSubItem(object sender, DrawListViewSubItemEventArgs e)
        {
            e.DrawDefault = true;
        }

        private void ListViewContentControls_DrawItem(object sender, DrawListViewItemEventArgs e)
        {
            e.DrawDefault = true;
        }

        private void ListViewContentControls_DrawColumnHeader(object sender, DrawListViewColumnHeaderEventArgs e)
        {
            TextFormatFlags flags = TextFormatFlags.LeftAndRightPadding;
            e.DrawBackground();
            CheckBoxRenderer.DrawCheckBox(e.Graphics, ClientRectangle.Location, state);
            e.DrawText(flags);
        }

        private void ListViewContentControls_ColumnClick(object sender, ColumnClickEventArgs e)
        {
            if (e.Column != 0) return;

            if (!clicked)
            {
                clicked = true;
                state = CheckBoxState.CheckedPressed;

                foreach (ListViewItem item in ListViewContentControls.Items)
                {
                    item.Checked = true;
                }

                Invalidate();
            }
            else
            {
                clicked = false;
                state = CheckBoxState.UncheckedNormal;
                Invalidate();

                foreach (ListViewItem item in ListViewContentControls.Items)
                {
                    item.Checked = false;
                }
            }
        }

        #endregion

        private void BtnUpdate_Click(object sender, EventArgs e)
        {
            try
            {
                progressBar.Show();
                templateUpdateService.StepExecuted += (sndr, args) => 
                {
                    progressBar.PerformStep();
                };

                ToggleUiControls(false);                           
                Globals.ThisAddIn.Application.ScreenUpdating = false;

                var tags = new List<string>();
                foreach (ListViewItem item in ListViewContentControls.CheckedItems)
                {
                    tags.Add((string)item.Tag);
                }

                progressBar.Value = 0;
                progressBar.Step = 100 / (tags.Count + 2); // extra steps to show progress immediately and not stay at 100% before actually finished
                progressBar.Show();
                progressBar.PerformStep();

                templateUpdateService.UpdateData(tags);

                Globals.ThisAddIn.Application.ScreenUpdating = true;
                ToggleUiControls(true);
                progressBar.Hide();
            }
            catch (Exception ex)
            {
                Globals.ThisAddIn.Application.ScreenUpdating = true;
                ToggleUiControls(true);
                progressBar.Hide();

                MessageBox.Show(ex.GetBaseException().Message, "Error updating data", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnClose_Click(object sender, EventArgs e)
        {
            Globals.ThisAddIn.GetOrRefreshDataPane.Visible = false;
        }

        private void ToggleUiControls(bool enabled)
        {
            ListViewContentControls.Enabled = enabled;
            BtnUpdate.Enabled = enabled;
            BtnClose.Enabled = enabled;
        }
    }
}
