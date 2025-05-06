namespace NN_Studybuilder_Protocol.Controls.CustomPanes
{
    partial class StudyBuilderNavigatorUserControl
    {
        /// <summary> 
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary> 
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle1 = new System.Windows.Forms.DataGridViewCellStyle();
            System.Windows.Forms.DataGridViewCellStyle dataGridViewCellStyle2 = new System.Windows.Forms.DataGridViewCellStyle();
            this.LblTemplateType = new System.Windows.Forms.Label();
            this.LblTemplateTypeHeader = new System.Windows.Forms.Label();
            this.BtnClose = new System.Windows.Forms.Button();
            this.BtnOpenDataPane = new System.Windows.Forms.Button();
            this.lblExistingStudyID = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.lblHeader = new System.Windows.Forms.Label();
            this.TxtSearch = new System.Windows.Forms.TextBox();
            this.BtnSave = new System.Windows.Forms.Button();
            this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
            this.GvStudyVersions = new System.Windows.Forms.DataGridView();
            this.BtnRefreshStudies = new System.Windows.Forms.Button();
            this.toolTip1 = new System.Windows.Forms.ToolTip(this.components);
            this.GvStudies = new NN_Studybuilder_Protocol.Controls.NNDataGridView();
            this.ProjectNumber = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.StudyID = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Status = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.StudyAcronym = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.StudyNumber = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tableLayoutPanel1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.GvStudyVersions)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.GvStudies)).BeginInit();
            this.SuspendLayout();
            // 
            // LblTemplateType
            // 
            this.LblTemplateType.Anchor = System.Windows.Forms.AnchorStyles.Left;
            this.LblTemplateType.AutoSize = true;
            this.LblTemplateType.ForeColor = System.Drawing.SystemColors.WindowText;
            this.LblTemplateType.Location = new System.Drawing.Point(85, 16);
            this.LblTemplateType.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.LblTemplateType.Name = "LblTemplateType";
            this.LblTemplateType.Size = new System.Drawing.Size(51, 13);
            this.LblTemplateType.TabIndex = 0;
            this.LblTemplateType.Text = "unknown";
            // 
            // LblTemplateTypeHeader
            // 
            this.LblTemplateTypeHeader.Anchor = System.Windows.Forms.AnchorStyles.Left;
            this.LblTemplateTypeHeader.AutoSize = true;
            this.LblTemplateTypeHeader.ForeColor = System.Drawing.SystemColors.WindowText;
            this.LblTemplateTypeHeader.Location = new System.Drawing.Point(2, 16);
            this.LblTemplateTypeHeader.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.LblTemplateTypeHeader.Name = "LblTemplateTypeHeader";
            this.LblTemplateTypeHeader.Size = new System.Drawing.Size(77, 13);
            this.LblTemplateTypeHeader.TabIndex = 1;
            this.LblTemplateTypeHeader.Text = "Template type:";
            // 
            // BtnClose
            // 
            this.BtnClose.ForeColor = System.Drawing.Color.Black;
            this.BtnClose.Location = new System.Drawing.Point(108, 625);
            this.BtnClose.Margin = new System.Windows.Forms.Padding(2);
            this.BtnClose.Name = "BtnClose";
            this.BtnClose.Size = new System.Drawing.Size(80, 25);
            this.BtnClose.TabIndex = 4;
            this.BtnClose.Text = "Close";
            this.BtnClose.UseVisualStyleBackColor = true;
            this.BtnClose.Click += new System.EventHandler(this.BtnClose_Click);
            // 
            // BtnOpenDataPane
            // 
            this.BtnOpenDataPane.ForeColor = System.Drawing.Color.Black;
            this.BtnOpenDataPane.Location = new System.Drawing.Point(449, 625);
            this.BtnOpenDataPane.Margin = new System.Windows.Forms.Padding(2);
            this.BtnOpenDataPane.Name = "BtnOpenDataPane";
            this.BtnOpenDataPane.Size = new System.Drawing.Size(80, 25);
            this.BtnOpenDataPane.TabIndex = 6;
            this.BtnOpenDataPane.Text = "Get Data";
            this.BtnOpenDataPane.UseVisualStyleBackColor = true;
            this.BtnOpenDataPane.Click += new System.EventHandler(this.BtnOpenDataPane_Click);
            // 
            // lblExistingStudyID
            // 
            this.lblExistingStudyID.Anchor = System.Windows.Forms.AnchorStyles.Right;
            this.lblExistingStudyID.AutoSize = true;
            this.lblExistingStudyID.ForeColor = System.Drawing.SystemColors.WindowText;
            this.lblExistingStudyID.Location = new System.Drawing.Point(475, 16);
            this.lblExistingStudyID.Name = "lblExistingStudyID";
            this.lblExistingStudyID.Size = new System.Drawing.Size(33, 13);
            this.lblExistingStudyID.TabIndex = 6;
            this.lblExistingStudyID.Text = "None";
            // 
            // label1
            // 
            this.label1.Anchor = System.Windows.Forms.AnchorStyles.Right;
            this.label1.AutoSize = true;
            this.label1.ForeColor = System.Drawing.SystemColors.WindowText;
            this.label1.Location = new System.Drawing.Point(309, 16);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(41, 13);
            this.label1.TabIndex = 5;
            this.label1.Text = "Saved:";
            // 
            // lblHeader
            // 
            this.lblHeader.AutoSize = true;
            this.lblHeader.BackColor = System.Drawing.SystemColors.Window;
            this.lblHeader.ForeColor = System.Drawing.SystemColors.WindowText;
            this.lblHeader.Location = new System.Drawing.Point(19, 98);
            this.lblHeader.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.lblHeader.Name = "lblHeader";
            this.lblHeader.Size = new System.Drawing.Size(330, 13);
            this.lblHeader.TabIndex = 0;
            this.lblHeader.Text = "Type Project number, Study ID, or Study acronym (min 3 characters):";
            // 
            // TxtSearch
            // 
            this.TxtSearch.Location = new System.Drawing.Point(17, 116);
            this.TxtSearch.Name = "TxtSearch";
            this.TxtSearch.Size = new System.Drawing.Size(512, 20);
            this.TxtSearch.TabIndex = 1;
            this.TxtSearch.KeyUp += new System.Windows.Forms.KeyEventHandler(this.TxtSearch_KeyUp);
            // 
            // BtnSave
            // 
            this.BtnSave.BackColor = System.Drawing.SystemColors.Control;
            this.BtnSave.ForeColor = System.Drawing.Color.Black;
            this.BtnSave.Location = new System.Drawing.Point(18, 625);
            this.BtnSave.Name = "BtnSave";
            this.BtnSave.Size = new System.Drawing.Size(80, 25);
            this.BtnSave.TabIndex = 4;
            this.BtnSave.Text = "Save";
            this.BtnSave.UseVisualStyleBackColor = true;
            this.BtnSave.Click += new System.EventHandler(this.BtnSave_Click);
            // 
            // tableLayoutPanel1
            // 
            this.tableLayoutPanel1.BackColor = System.Drawing.SystemColors.Window;
            this.tableLayoutPanel1.ColumnCount = 5;
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 16.43836F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33.85519F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 2.152642F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 17.61252F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 30.72407F));
            this.tableLayoutPanel1.Controls.Add(this.label1, 3, 0);
            this.tableLayoutPanel1.Controls.Add(this.lblExistingStudyID, 4, 0);
            this.tableLayoutPanel1.Controls.Add(this.LblTemplateTypeHeader, 0, 0);
            this.tableLayoutPanel1.Controls.Add(this.LblTemplateType, 1, 0);
            this.tableLayoutPanel1.Location = new System.Drawing.Point(18, 19);
            this.tableLayoutPanel1.Name = "tableLayoutPanel1";
            this.tableLayoutPanel1.RowCount = 1;
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Size = new System.Drawing.Size(511, 46);
            this.tableLayoutPanel1.TabIndex = 11;
            // 
            // GvStudyVersions
            // 
            this.GvStudyVersions.AllowUserToAddRows = false;
            this.GvStudyVersions.AllowUserToDeleteRows = false;
            this.GvStudyVersions.AutoSizeColumnsMode = System.Windows.Forms.DataGridViewAutoSizeColumnsMode.Fill;
            this.GvStudyVersions.BackgroundColor = System.Drawing.SystemColors.Window;
            this.GvStudyVersions.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            dataGridViewCellStyle1.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle1.BackColor = System.Drawing.SystemColors.Window;
            dataGridViewCellStyle1.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle1.ForeColor = System.Drawing.SystemColors.WindowText;
            dataGridViewCellStyle1.SelectionBackColor = System.Drawing.SystemColors.Highlight;
            dataGridViewCellStyle1.SelectionForeColor = System.Drawing.SystemColors.HighlightText;
            dataGridViewCellStyle1.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.GvStudyVersions.DefaultCellStyle = dataGridViewCellStyle1;
            this.GvStudyVersions.Location = new System.Drawing.Point(19, 429);
            this.GvStudyVersions.Margin = new System.Windows.Forms.Padding(2);
            this.GvStudyVersions.MultiSelect = false;
            this.GvStudyVersions.Name = "GvStudyVersions";
            this.GvStudyVersions.ReadOnly = true;
            this.GvStudyVersions.RowHeadersVisible = false;
            this.GvStudyVersions.RowTemplate.Height = 24;
            this.GvStudyVersions.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.GvStudyVersions.Size = new System.Drawing.Size(510, 122);
            this.GvStudyVersions.TabIndex = 3;
            this.GvStudyVersions.SelectionChanged += new System.EventHandler(this.GvStudyVersions_SelectionChanged);
            // 
            // BtnRefreshStudies
            // 
            this.BtnRefreshStudies.Location = new System.Drawing.Point(454, 339);
            this.BtnRefreshStudies.Name = "BtnRefreshStudies";
            this.BtnRefreshStudies.Size = new System.Drawing.Size(75, 23);
            this.BtnRefreshStudies.TabIndex = 7;
            this.BtnRefreshStudies.Text = "Refresh";
            this.toolTip1.SetToolTip(this.BtnRefreshStudies, "Refresh the list of Studies and versions");
            this.BtnRefreshStudies.UseVisualStyleBackColor = true;
            this.BtnRefreshStudies.Click += new System.EventHandler(this.BtnRefreshStudies_Click);
            // 
            // GvStudies
            // 
            this.GvStudies.AllowUserToAddRows = false;
            this.GvStudies.AllowUserToDeleteRows = false;
            this.GvStudies.AutoSizeColumnsMode = System.Windows.Forms.DataGridViewAutoSizeColumnsMode.Fill;
            this.GvStudies.BackgroundColor = System.Drawing.SystemColors.Window;
            this.GvStudies.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.GvStudies.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.ProjectNumber,
            this.StudyID,
            this.Status,
            this.StudyAcronym,
            this.StudyNumber});
            dataGridViewCellStyle2.Alignment = System.Windows.Forms.DataGridViewContentAlignment.MiddleLeft;
            dataGridViewCellStyle2.BackColor = System.Drawing.SystemColors.Window;
            dataGridViewCellStyle2.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            dataGridViewCellStyle2.ForeColor = System.Drawing.SystemColors.WindowText;
            dataGridViewCellStyle2.SelectionBackColor = System.Drawing.SystemColors.Highlight;
            dataGridViewCellStyle2.SelectionForeColor = System.Drawing.SystemColors.HighlightText;
            dataGridViewCellStyle2.WrapMode = System.Windows.Forms.DataGridViewTriState.False;
            this.GvStudies.DefaultCellStyle = dataGridViewCellStyle2;
            this.GvStudies.EmptyResultText = "Search not performed";
            this.GvStudies.Location = new System.Drawing.Point(17, 155);
            this.GvStudies.Name = "GvStudies";
            this.GvStudies.ReadOnly = true;
            this.GvStudies.RowHeadersVisible = false;
            this.GvStudies.RowHeadersWidth = 51;
            this.GvStudies.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.GvStudies.Size = new System.Drawing.Size(511, 167);
            this.GvStudies.TabIndex = 2;
            // 
            // ProjectNumber
            // 
            this.ProjectNumber.HeaderText = "Project Number";
            this.ProjectNumber.MinimumWidth = 6;
            this.ProjectNumber.Name = "ProjectNumber";
            this.ProjectNumber.ReadOnly = true;
            // 
            // StudyID
            // 
            this.StudyID.HeaderText = "Study ID";
            this.StudyID.MinimumWidth = 6;
            this.StudyID.Name = "StudyID";
            this.StudyID.ReadOnly = true;
            // 
            // Status
            // 
            this.Status.HeaderText = "Status";
            this.Status.MinimumWidth = 6;
            this.Status.Name = "Status";
            this.Status.ReadOnly = true;
            // 
            // StudyAcronym
            // 
            this.StudyAcronym.HeaderText = "Study Acronym";
            this.StudyAcronym.MinimumWidth = 6;
            this.StudyAcronym.Name = "StudyAcronym";
            this.StudyAcronym.ReadOnly = true;
            // 
            // StudyNumber
            // 
            this.StudyNumber.HeaderText = "Study Number";
            this.StudyNumber.MinimumWidth = 6;
            this.StudyNumber.Name = "StudyNumber";
            this.StudyNumber.ReadOnly = true;
            // 
            // StudyBuilderNavigatorUserControl
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.Controls.Add(this.BtnRefreshStudies);
            this.Controls.Add(this.GvStudyVersions);
            this.Controls.Add(this.tableLayoutPanel1);
            this.Controls.Add(this.BtnSave);
            this.Controls.Add(this.GvStudies);
            this.Controls.Add(this.TxtSearch);
            this.Controls.Add(this.lblHeader);
            this.Controls.Add(this.BtnOpenDataPane);
            this.Controls.Add(this.BtnClose);
            this.Margin = new System.Windows.Forms.Padding(2);
            this.Name = "StudyBuilderNavigatorUserControl";
            this.Size = new System.Drawing.Size(561, 673);
            this.tableLayoutPanel1.ResumeLayout(false);
            this.tableLayoutPanel1.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.GvStudyVersions)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.GvStudies)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label LblTemplateType;
        private System.Windows.Forms.Label LblTemplateTypeHeader;
        private System.Windows.Forms.Button BtnClose;
        private System.Windows.Forms.Button BtnOpenDataPane;
        private System.Windows.Forms.Label lblExistingStudyID;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label lblHeader;
        private System.Windows.Forms.TextBox TxtSearch;
        private NNDataGridView GvStudies;
        private System.Windows.Forms.DataGridViewTextBoxColumn ProjectNumber;
        private System.Windows.Forms.DataGridViewTextBoxColumn StudyID;
        private System.Windows.Forms.DataGridViewTextBoxColumn Status;
        private System.Windows.Forms.DataGridViewTextBoxColumn StudyAcronym;
        private System.Windows.Forms.DataGridViewTextBoxColumn StudyNumber;
        private System.Windows.Forms.Button BtnSave;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel1;
        private System.Windows.Forms.DataGridView GvStudyVersions;
        private System.Windows.Forms.Button BtnRefreshStudies;
        private System.Windows.Forms.ToolTip toolTip1;
    }
}
