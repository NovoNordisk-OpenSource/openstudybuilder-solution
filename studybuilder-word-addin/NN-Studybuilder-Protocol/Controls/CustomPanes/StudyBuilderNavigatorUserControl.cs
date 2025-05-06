using NN_Studybuilder_Protocol.Data;
using NN_Studybuilder_Protocol.Data.Services;
using NN_Studybuilder_Protocol.Exceptions;
using NN_Studybuilder_Protocol.StudybuildApi;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol.Controls.CustomPanes
{
    public partial class StudyBuilderNavigatorUserControl : UserControl
    {
        readonly StudyService studyService;
        readonly ContentControlManager contentControlManager;

        public StudyBuilderNavigatorUserControl(StudyService studyService, ContentControlManager contentControlManager, NetworkService networkService)
        {
            this.studyService = studyService;
            this.contentControlManager = contentControlManager;

            InitializeComponent();
        }       

        protected override void OnLoad(EventArgs e)
        {
            InitializeControls();
            base.OnLoad(e);
        }

        public void OnVisibleChanged(bool visible)
        {
            if (visible)
            {
                BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = IsSelectedVersion();
            }
        }

        public void InitializeControls()
        {
            TxtSearch.Text = null;
            if (GvStudies.Rows.Count > 0)
            {
                GvStudies.Rows.Clear();
            }
            GvStudies.TabStop = false;
            GvStudies.AutoGenerateColumns = false;
            GvStudies.EmptyResultText = "No results";
            SetSelectedStudyId();
            LblTemplateType.Text = ConfigManager.Instance.TemplateType;
            TxtSearch.Focus();
            BtnSave.Enabled = false;
            BtnRefreshStudies.Enabled = false;

            GvStudyVersions.Columns.AddRange(
                new DataGridViewTextBoxColumn
                {
                    Name = nameof(StudyVersionDto.Version)
                },
                new DataGridViewTextBoxColumn
                {
                    Name = nameof(StudyVersionDto.Status)
                },
                new DataGridViewTextBoxColumn
                {
                    Name = nameof(StudyVersionDto.VersionDate)
                });
        }

        private void GvStudies_SelectionChanged(object sender, EventArgs e)
        {
            if (GvStudies.SelectedRows.Count == 0) return;
            var dto = GvStudies.SelectedRows[0].Tag as StudyDto;
            if (dto != null)
            {
                GvStudyVersions.SelectionChanged -= GvStudyVersions_SelectionChanged;
                GvStudyVersions_Databind(dto.Uid);

                GvStudyVersions.SelectionChanged += GvStudyVersions_SelectionChanged;
            }

            BtnSave.Enabled = SelectedStudyChanged() || SelectedStudyVersionChanged() || SelectedStudyVersionStatusChanged();
            BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = IsSelectedVersion();
        }

        void GvStudyVersions_Databind(string studyUid)
        {
            GvStudyVersions.Rows.Clear();
            var versions = studyService.GetStudyVersions(studyUid).GetAwaiter().GetResult();
            foreach (var version in versions)
            {
                var i = GvStudyVersions.Rows.Add();
                GvStudyVersions.Rows[i].Cells[nameof(StudyVersionDto.Version)].Value = version.Version;
                GvStudyVersions.Rows[i].Cells[nameof(StudyVersionDto.Status)].Value = version.Status;
                GvStudyVersions.Rows[i].Cells[nameof(StudyVersionDto.VersionDate)].Value = version.VersionDate;
                GvStudyVersions.Rows[i].Tag = version;
            }
        }

        protected void SetSelectedStudyId()
        {
            lblExistingStudyID.Text = ConfigManager.Instance.GetFullVersionLabel();
        }

        private void Close()
        {
            BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = false;
            Globals.ThisAddIn.StudyBuilderNavigator.Visible = false;
        }

        private void BtnClose_Click(object sender, EventArgs e)
        {
            Close();
        }

        private void BtnOpenDataPane_Click(object sender, EventArgs e)
        {
            Save();
            Close();
            Globals.ThisAddIn.GetOrRefreshDataPane.Visible = true;
        }

        public IEnumerable<StudyDto> Search(string q)
        {
            try
            {
                return studyService.Search(q).GetAwaiter().GetResult();
            }
            catch (StudyBuilderNotAvailableException)
            {
                MessageBox.Show("Studybuilder is currently not available. Please try again later.");
                GvStudies.EmptyResultText = "Studybuilder not available";
                return new StudyDto[0];
            }
            catch (Exception ex)
            {
                if (ex.InnerException != null && ex.InnerException is ApiException apiEx)
                {
                    if (apiEx.StatusCode == 404)
                    {
                        GvStudies.EmptyResultText = "Not found";
                        return new StudyDto[0];
                    }
                }

                MessageBox.Show(ex.GetBaseException().Message);
                return new StudyDto[0];
            }
        }

        private void TxtSearch_KeyUp(object sender, KeyEventArgs e)
        {
            if (TxtSearch.TextLength > 2)
            {
                var datasource = Search(TxtSearch.Text.Trim());
                if (datasource.Count() > 0)
                {
                    GvStudies.SelectionChanged -= GvStudies_SelectionChanged;

                    GvStudies.DataSource = null;
                    GvStudies.Rows.Clear();
                    GvStudies_DataBind(datasource);
                    GvStudies.ClearSelection();
                    //BtnSave.Enabled = SelectedStudyChanged();
                    GvStudies.SelectionChanged += GvStudies_SelectionChanged;

                    return;
                }
            }

            GvStudies.DataSource = null;
            GvStudies.Rows.Clear();
            GvStudies.DataSource = new StudyDto[0];
            BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = BtnSave.Enabled = false;
        }

        private void GvStudies_DataBind(IEnumerable<StudyDto> datasource)
        {
            foreach (var item in datasource)
            {
                var i = GvStudies.Rows.Add();
                GvStudies.Rows[i].Cells[nameof(item.ProjectNumber)].Value = item.ProjectNumber;
                GvStudies.Rows[i].Cells[nameof(item.Status)].Value = item.Status;
                GvStudies.Rows[i].Cells[nameof(item.StudyAcronym)].Value = item.StudyAcronym;
                GvStudies.Rows[i].Cells[nameof(item.StudyId)].Value = item.StudyId;
                GvStudies.Rows[i].Cells[nameof(item.StudyNumber)].Value = item.StudyNumber;
                GvStudies.Rows[i].Tag = item;
            }
        }

        private void Save()
        {
            // save selected row, uid, to user specific settings store
            var studyDto = (StudyDto)GvStudies.SelectedRows[0].Tag;
            var status = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Status)].Value as string;
            var version = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Version)].Value as string;
            ConfigManager.Instance.StudyUid = studyDto.Uid;
            ConfigManager.Instance.StudyId = studyDto.StudyId;
            ConfigManager.Instance.StudyVersion = version;
            ConfigManager.Instance.StudyVersionStatus = status;
            Properties.Settings.Default.Save();

            SetSelectedStudyId();

            contentControlManager.UpdateDateStudyId(studyDto.StudyId);
            contentControlManager.ClearContentFromAllStudyBuilderContentControls();
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (ConfigManager.Instance.HasStudyUid && (SelectedStudyChanged() || SelectedStudyVersionChanged() || SelectedStudyVersionStatusChanged()))
            {
                var proceed = MessageBox.Show($"Please notice that changing Environment, Study selection, or Study version will clear existing StudyBuilder information{Environment.NewLine}{Environment.NewLine}Click Cancel to maintain current selection or 'OK' to continue", "Warning: This will reset StudyBuilder content", MessageBoxButtons.OKCancel, MessageBoxIcon.Question);
                if (proceed != DialogResult.OK)
                {
                    return;
                }
            }

            Save();
            BtnSave.Enabled = false;
            BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = true;
        }

        private bool SelectedStudyChanged()
        {
            if (GvStudies.SelectedRows.Count == 0) return false;
            if (!(GvStudies.SelectedRows[0].Tag is StudyDto studyDto)) return false;

            // User has not selected a Study yet
            if (!ConfigManager.Instance.HasStudyUid)
            {
                return true;
            }

            return ConfigManager.Instance.StudyUid != studyDto.Uid;
        }

        private bool SelectedStudyVersionChanged()
        {
            if (GvStudyVersions.SelectedRows.Count == 0) return false;
            var selectedVersion = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Version)].Value as string;
            //if (string.IsNullOrWhiteSpace(selectedVersion)) return false;

            //// User has not selected a Study yet
            //if (string.IsNullOrWhiteSpace(ConfigManager.Instance.StudyVersion))
            //{
            //    return true;
            //}

            if (string.IsNullOrWhiteSpace(selectedVersion) && selectedVersion == null) return false;

            return ConfigManager.Instance.StudyVersion != selectedVersion;
        }

        private bool SelectedStudyVersionStatusChanged()
        {
            if (GvStudyVersions.SelectedRows.Count == 0) return false;
            var selectedVersionStatus = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Status)].Value as string;
            if (string.IsNullOrWhiteSpace(selectedVersionStatus)) return false;

            // User has not selected a Study yet
            if (string.IsNullOrWhiteSpace(ConfigManager.Instance.StudyVersionStatus))
            {
                return true;
            }

            return ConfigManager.Instance.StudyVersionStatus != selectedVersionStatus;
        }

        private void GvStudyVersions_SelectionChanged(object sender, EventArgs e)
        {
            if (GvStudyVersions.SelectedRows.Count == 0) return;
            BtnSave.Enabled = SelectedStudyChanged() || SelectedStudyVersionChanged() || SelectedStudyVersionStatusChanged();
            BtnOpenDataPane.Enabled = BtnRefreshStudies.Enabled = IsSelectedVersion();
        }

        private bool IsSelectedVersion()
        {
            if (GvStudies.SelectedRows.Count == 0) return false;
            if (GvStudyVersions.SelectedRows.Count == 0) return false;

            var studyDto = (StudyDto)GvStudies.SelectedRows[0].Tag;
            var selectedVersion = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Version)].Value as string;
            var selectedVersionStatus = GvStudyVersions.SelectedRows[0].Cells[nameof(StudyVersionDto.Status)].Value as string;

            return ConfigManager.Instance.StudyUid == studyDto?.Uid && ConfigManager.Instance.StudyVersion == selectedVersion && ConfigManager.Instance.StudyVersionStatus == selectedVersionStatus;
        }

        private void BtnRefreshStudies_Click(object sender, EventArgs e)
        {
            try
            {
                var selectedStudy = GvStudies.SelectedRows[0].Tag as StudyDto;
                var selectedVersion = GvStudyVersions.SelectedRows[0].Tag as StudyVersionDto;

                var datasource = Search(TxtSearch.Text.Trim());
                if (datasource.Count() > 0)
                {
                    // Sometimes loading is so fast that end user might not perceive the update. This makes a short UI flicker by disabling and enabling the user control.
                    Enabled = false;
                    GvStudyVersions.ClearSelection();

                    GvStudies.DataSource = null;
                    GvStudies.Rows.Clear();
                    GvStudies_DataBind(datasource);

                    // Set selected Study and Version
                    for (int i = 0; i < GvStudies.RowCount; i++)
                    {
                        if (((StudyDto)GvStudies.Rows[i].Tag).Uid == selectedStudy.Uid)
                        {
                            GvStudies.Rows[i].Selected = true;
                            break;
                        }
                    }

                    for (int i = 0; i < GvStudyVersions.RowCount; i++)
                    {
                        var dto = (StudyVersionDto)GvStudyVersions.Rows[i].Tag;
                        if (selectedVersion.Version == dto.Version && selectedVersion.Status == dto.Status && selectedVersion.VersionDate == dto.VersionDate)
                        {
                            GvStudyVersions.Rows[i].Selected = true;
                            break;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error", ex.Message, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Enabled = true;
            }
        }
    }
}
