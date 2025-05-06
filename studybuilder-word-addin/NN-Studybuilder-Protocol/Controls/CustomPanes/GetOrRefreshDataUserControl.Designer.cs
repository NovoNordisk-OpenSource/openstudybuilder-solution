namespace NN_Studybuilder_Protocol.Controls.CustomPanes
{
    partial class GetOrRefreshDataUserControl
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
            this.BtnUpdate = new System.Windows.Forms.Button();
            this.BtnClose = new System.Windows.Forms.Button();
            this.ListViewContentControls = new System.Windows.Forms.ListView();
            this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
            this.label1 = new System.Windows.Forms.Label();
            this.lblExistingStudyID = new System.Windows.Forms.Label();
            this.progressBar = new NN_Studybuilder_Protocol.Controls.CustomProgressBar();
            this.tableLayoutPanel1.SuspendLayout();
            this.SuspendLayout();
            // 
            // BtnUpdate
            // 
            this.BtnUpdate.BackColor = System.Drawing.SystemColors.Window;
            this.BtnUpdate.ForeColor = System.Drawing.Color.Black;
            this.BtnUpdate.Location = new System.Drawing.Point(22, 493);
            this.BtnUpdate.Margin = new System.Windows.Forms.Padding(2);
            this.BtnUpdate.Name = "BtnUpdate";
            this.BtnUpdate.Size = new System.Drawing.Size(87, 28);
            this.BtnUpdate.TabIndex = 1;
            this.BtnUpdate.Text = "Update";
            this.BtnUpdate.UseVisualStyleBackColor = false;
            this.BtnUpdate.Click += new System.EventHandler(this.BtnUpdate_Click);
            // 
            // BtnClose
            // 
            this.BtnClose.BackColor = System.Drawing.SystemColors.Window;
            this.BtnClose.ForeColor = System.Drawing.Color.Black;
            this.BtnClose.Location = new System.Drawing.Point(162, 493);
            this.BtnClose.Margin = new System.Windows.Forms.Padding(2);
            this.BtnClose.Name = "BtnClose";
            this.BtnClose.Size = new System.Drawing.Size(87, 28);
            this.BtnClose.TabIndex = 2;
            this.BtnClose.Text = "Close";
            this.BtnClose.UseVisualStyleBackColor = false;
            this.BtnClose.Click += new System.EventHandler(this.BtnClose_Click);
            // 
            // ListViewContentControls
            // 
            this.ListViewContentControls.CheckBoxes = true;
            this.ListViewContentControls.FullRowSelect = true;
            this.ListViewContentControls.HideSelection = false;
            this.ListViewContentControls.Location = new System.Drawing.Point(22, 100);
            this.ListViewContentControls.Margin = new System.Windows.Forms.Padding(2);
            this.ListViewContentControls.Name = "ListViewContentControls";
            this.ListViewContentControls.Size = new System.Drawing.Size(228, 366);
            this.ListViewContentControls.TabIndex = 3;
            this.ListViewContentControls.UseCompatibleStateImageBehavior = false;
            this.ListViewContentControls.View = System.Windows.Forms.View.Details;
            // 
            // tableLayoutPanel1
            // 
            this.tableLayoutPanel1.BackColor = System.Drawing.SystemColors.Window;
            this.tableLayoutPanel1.ColumnCount = 2;
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 44.73684F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 55.26316F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
            this.tableLayoutPanel1.Controls.Add(this.label1, 0, 0);
            this.tableLayoutPanel1.Controls.Add(this.lblExistingStudyID, 1, 0);
            this.tableLayoutPanel1.Location = new System.Drawing.Point(22, 26);
            this.tableLayoutPanel1.Name = "tableLayoutPanel1";
            this.tableLayoutPanel1.RowCount = 1;
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLayoutPanel1.Size = new System.Drawing.Size(228, 46);
            this.tableLayoutPanel1.TabIndex = 12;
            // 
            // label1
            // 
            this.label1.Anchor = System.Windows.Forms.AnchorStyles.Left;
            this.label1.AutoSize = true;
            this.label1.ForeColor = System.Drawing.SystemColors.WindowText;
            this.label1.Location = new System.Drawing.Point(3, 16);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(83, 13);
            this.label1.TabIndex = 5;
            this.label1.Text = "Currently saved:";
            // 
            // lblExistingStudyID
            // 
            this.lblExistingStudyID.Anchor = System.Windows.Forms.AnchorStyles.Right;
            this.lblExistingStudyID.AutoSize = true;
            this.lblExistingStudyID.ForeColor = System.Drawing.SystemColors.WindowText;
            this.lblExistingStudyID.Location = new System.Drawing.Point(192, 16);
            this.lblExistingStudyID.Name = "lblExistingStudyID";
            this.lblExistingStudyID.Size = new System.Drawing.Size(33, 13);
            this.lblExistingStudyID.TabIndex = 6;
            this.lblExistingStudyID.Text = "None";
            // 
            // progressBar
            // 
            this.progressBar.BackColor = System.Drawing.Color.White;
            this.progressBar.ForeColor = System.Drawing.Color.Gray;
            this.progressBar.Location = new System.Drawing.Point(22, 548);
            this.progressBar.Name = "progressBar";
            this.progressBar.Size = new System.Drawing.Size(228, 23);
            this.progressBar.TabIndex = 13;
            this.progressBar.Visible = false;
            // 
            // GetOrRefreshDataUserControl
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.AutoScroll = true;
            this.Controls.Add(this.progressBar);
            this.Controls.Add(this.tableLayoutPanel1);
            this.Controls.Add(this.ListViewContentControls);
            this.Controls.Add(this.BtnClose);
            this.Controls.Add(this.BtnUpdate);
            this.Margin = new System.Windows.Forms.Padding(2);
            this.Name = "GetOrRefreshDataUserControl";
            this.Size = new System.Drawing.Size(286, 593);
            this.tableLayoutPanel1.ResumeLayout(false);
            this.tableLayoutPanel1.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion
        private System.Windows.Forms.Button BtnUpdate;
        private System.Windows.Forms.Button BtnClose;
        private System.Windows.Forms.ListView ListViewContentControls;
        private System.Windows.Forms.TableLayoutPanel tableLayoutPanel1;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label lblExistingStudyID;
        private CustomProgressBar progressBar;
    }
}
