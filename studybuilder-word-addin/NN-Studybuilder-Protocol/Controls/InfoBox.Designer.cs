
namespace NN_Studybuilder_Protocol.Controls
{
    partial class InfoBox
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

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(InfoBox));
            this.LblMessage = new System.Windows.Forms.Label();
            this.LinkLblSupport = new System.Windows.Forms.LinkLabel();
            this.panel1 = new System.Windows.Forms.Panel();
            this.BtnCancel = new System.Windows.Forms.Button();
            this.BtnSave = new System.Windows.Forms.Button();
            this.LblApiUrl = new System.Windows.Forms.Label();
            this.CBEnvironments = new System.Windows.Forms.ComboBox();
            this.panel1.SuspendLayout();
            this.SuspendLayout();
            // 
            // LblMessage
            // 
            this.LblMessage.AutoSize = true;
            this.LblMessage.Location = new System.Drawing.Point(53, 57);
            this.LblMessage.Margin = new System.Windows.Forms.Padding(8, 0, 8, 0);
            this.LblMessage.Name = "LblMessage";
            this.LblMessage.Size = new System.Drawing.Size(175, 31);
            this.LblMessage.TabIndex = 2;
            this.LblMessage.Text = "message text";
            // 
            // LinkLblSupport
            // 
            this.LinkLblSupport.AutoSize = true;
            this.LinkLblSupport.Location = new System.Drawing.Point(851, 60);
            this.LinkLblSupport.Margin = new System.Windows.Forms.Padding(8, 0, 8, 0);
            this.LinkLblSupport.Name = "LinkLblSupport";
            this.LinkLblSupport.Size = new System.Drawing.Size(226, 31);
            this.LinkLblSupport.TabIndex = 3;
            this.LinkLblSupport.TabStop = true;
            this.LinkLblSupport.Text = "Open support link";
            this.LinkLblSupport.LinkClicked += new System.Windows.Forms.LinkLabelLinkClickedEventHandler(this.LinkLblSupport_LinkClicked);
            // 
            // panel1
            // 
            this.panel1.Anchor = System.Windows.Forms.AnchorStyles.Bottom;
            this.panel1.BackColor = System.Drawing.SystemColors.ControlLight;
            this.panel1.Controls.Add(this.BtnCancel);
            this.panel1.Controls.Add(this.BtnSave);
            this.panel1.Controls.Add(this.LinkLblSupport);
            this.panel1.Location = new System.Drawing.Point(0, 398);
            this.panel1.Margin = new System.Windows.Forms.Padding(8, 7, 8, 7);
            this.panel1.Name = "panel1";
            this.panel1.Size = new System.Drawing.Size(1165, 150);
            this.panel1.TabIndex = 4;
            // 
            // BtnCancel
            // 
            this.BtnCancel.BackColor = System.Drawing.SystemColors.Control;
            this.BtnCancel.DialogResult = System.Windows.Forms.DialogResult.Cancel;
            this.BtnCancel.Location = new System.Drawing.Point(331, 45);
            this.BtnCancel.Margin = new System.Windows.Forms.Padding(5, 5, 5, 5);
            this.BtnCancel.Name = "BtnCancel";
            this.BtnCancel.Size = new System.Drawing.Size(227, 57);
            this.BtnCancel.TabIndex = 8;
            this.BtnCancel.Text = "Cancel";
            this.BtnCancel.UseVisualStyleBackColor = false;
            this.BtnCancel.Click += new System.EventHandler(this.BtnCancel_Click);
            // 
            // BtnSave
            // 
            this.BtnSave.BackColor = System.Drawing.SystemColors.Control;
            this.BtnSave.Location = new System.Drawing.Point(61, 43);
            this.BtnSave.Margin = new System.Windows.Forms.Padding(5, 5, 5, 5);
            this.BtnSave.Name = "BtnSave";
            this.BtnSave.Size = new System.Drawing.Size(227, 57);
            this.BtnSave.TabIndex = 7;
            this.BtnSave.Text = "Save";
            this.BtnSave.UseVisualStyleBackColor = false;
            this.BtnSave.Click += new System.EventHandler(this.BtnSave_Click);
            // 
            // LblApiUrl
            // 
            this.LblApiUrl.AutoSize = true;
            this.LblApiUrl.Location = new System.Drawing.Point(53, 298);
            this.LblApiUrl.Margin = new System.Windows.Forms.Padding(8, 0, 8, 0);
            this.LblApiUrl.Name = "LblApiUrl";
            this.LblApiUrl.Size = new System.Drawing.Size(105, 31);
            this.LblApiUrl.TabIndex = 5;
            this.LblApiUrl.Text = "Api url: ";
            // 
            // CBEnvironments
            // 
            this.CBEnvironments.FormattingEnabled = true;
            this.CBEnvironments.Location = new System.Drawing.Point(181, 291);
            this.CBEnvironments.Margin = new System.Windows.Forms.Padding(8, 7, 8, 7);
            this.CBEnvironments.Name = "CBEnvironments";
            this.CBEnvironments.Size = new System.Drawing.Size(369, 39);
            this.CBEnvironments.TabIndex = 6;
            this.CBEnvironments.SelectedValueChanged += new System.EventHandler(this.CBEnvironments_SelectedValueChanged);
            // 
            // InfoBox
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(16F, 31F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.CancelButton = this.BtnCancel;
            this.CausesValidation = false;
            this.ClientSize = new System.Drawing.Size(1163, 537);
            this.Controls.Add(this.CBEnvironments);
            this.Controls.Add(this.LblApiUrl);
            this.Controls.Add(this.LblMessage);
            this.Controls.Add(this.panel1);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Margin = new System.Windows.Forms.Padding(8, 7, 8, 7);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "InfoBox";
            this.Text = "About this add-in";
            this.panel1.ResumeLayout(false);
            this.panel1.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion
        private System.Windows.Forms.Label LblMessage;
        private System.Windows.Forms.LinkLabel LinkLblSupport;
        private System.Windows.Forms.Panel panel1;
        private System.Windows.Forms.Label LblApiUrl;
        private System.Windows.Forms.ComboBox CBEnvironments;
        private System.Windows.Forms.Button BtnSave;
        private System.Windows.Forms.Button BtnCancel;
    }
}