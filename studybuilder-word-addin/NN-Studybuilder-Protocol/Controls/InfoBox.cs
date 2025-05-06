using NN_Studybuilder_Protocol.Data;
using NN_Studybuilder_Protocol.Data.Repositories;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol.Controls
{
    public partial class InfoBox : Form
    {
        public event EventHandler EnvironmentChanged;
        private readonly string url;
        private readonly StudyBuilderApiEnvironmentRepository studyBuilderApiEnvironmentRepository;
        readonly bool showEnvironmentPicker;

        public InfoBox(string message, string url = "", string linkText = "", string caption = "About this add-in", string buttonText = "OK", bool showEnvironmentPicker = false)
        {
            InitializeComponent();
            this.showEnvironmentPicker = showEnvironmentPicker;
            LblMessage.Text = message;
            this.url = url;
            if (string.IsNullOrWhiteSpace(linkText))
            {
                LinkLblSupport.Visible = false;
                BtnCancel.Visible = false;
            }
            else LinkLblSupport.Text = linkText;
            Text = caption;
            BtnSave.Text = buttonText;
            if (showEnvironmentPicker)
            {
                studyBuilderApiEnvironmentRepository = new StudyBuilderApiEnvironmentRepository(ConfigManager.Instance);
                ShowEnvironmentPicker();
                BtnSave.Enabled = false;
            }
            else
            {
                LblApiUrl.Visible = false;
                CBEnvironments.Visible = false;
            }
        }

        private void LinkLblSupport_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(url)) throw new ArgumentNullException("Please supply a url");

            //System.Diagnostics.Process.Start($"microsoft-edge:{url}"); // not working
            System.Diagnostics.Process.Start("msedge.exe", url);
        }

        protected virtual void ShowEnvironmentPicker()
        {
            CBEnvironments.DisplayMember = nameof(StudyBuilderApiEnvironment.DisplayName);
            CBEnvironments.ValueMember = nameof(StudyBuilderApiEnvironment.ClientId);
            CBEnvironments.DataSource = studyBuilderApiEnvironmentRepository.GetEnvironments();

            CBEnvironments.SelectedItem = (CBEnvironments.DataSource as IEnumerable<StudyBuilderApiEnvironment>).FirstOrDefault(x => x.Active);
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (showEnvironmentPicker)
            {
                var env = CBEnvironments.SelectedItem as StudyBuilderApiEnvironment;
                if (env == null) return;
                studyBuilderApiEnvironmentRepository.Save(env);
                BtnSave.Enabled = false;
                // Reset all saved info and imported data in the document
                ConfigManager.Instance.StudyId = null;
                ConfigManager.Instance.StudyUid = null;
                ConfigManager.Instance.StudyVersion = null;
                ConfigManager.Instance.SaveSettings();
                if (EnvironmentChanged != null)
                {
                    EnvironmentChanged.Invoke(this, new EventArgs());
                }
            }

            Close();
        }

        private void CBEnvironments_SelectedValueChanged(object sender, EventArgs e)
        {
            var env = CBEnvironments.SelectedItem as StudyBuilderApiEnvironment;
            if (env == null) return;
            BtnSave.Enabled = env.Url != studyBuilderApiEnvironmentRepository.GetActiveEnvironmentUrl();
        }

        private void BtnCancel_Click(object sender, EventArgs e)
        {
            Close();
        }
    }
}
