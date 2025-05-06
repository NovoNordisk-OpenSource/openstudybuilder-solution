using Microsoft.Office.Interop.Word;
using NN_Studybuilder_Protocol.Model;
using NN_Studybuilder_Protocol.StudybuildApi;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.RegularExpressions;

namespace NN_Studybuilder_Protocol.Data.Services
{
    /// <summary>
    /// Maps content control tags to api endpoints to provide automatically updated Word document sections
    /// </summary>
    public class TemplateUpdateService
    {
        private readonly StudyService studyService;
        private readonly FileHandler fileHandler;
        private readonly ContentControlManager contentControlManager;
        protected const string No_Data_In_StudyBuilder = "No data in StudyBuilder";
        public event EventHandler<DoWorkEventArgs> StepExecuted;

        public TemplateUpdateService(StudyService studyService, FileHandler fileHandler, ContentControlManager contentControlManager)
        {
            this.studyService = studyService;
            this.fileHandler = fileHandler;
            this.contentControlManager = contentControlManager;
        }

        public void UpdateData(IEnumerable<string> contenControlTags)
        {
            var studyUid = ConfigManager.Instance.StudyUid;
            var version = string.IsNullOrWhiteSpace(ConfigManager.Instance.StudyVersion) ? null : ConfigManager.Instance.StudyVersion;

            ProtocolTitleDto protocolTitleDto = null;
            Clinical_mdr_api__models__study_selections__study__Study study = null;

            var lookup = contentControlManager.GetAllStudyBuilderContentControls().ToDictionary(c => c.Tag);

            foreach (var tag in contenControlTags)
            {
                if (!lookup.TryGetValue(tag, out var contentControl)) throw new Exception($"Content control with tag {tag} not found");
                
                var original = contentControl.LockContents;
                contentControl.LockContents = false;

                switch (contentControl.Tag.Trim())
                {
                    case ContentControlTagNames.ProtocolTitle:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.StudyTitle);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.Acronym:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Study_acronym);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }

                    case ContentControlTagNames.StudyTitleShort:
                    case ContentControlTagNames.ProtocolTitleShort:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.StudyShortTitle);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.Substance:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.SubstanceName);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    // Protocol Number / StudyID
                    case ContentControlTagNames.ProtocolNumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Study_id);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }

                    case ContentControlTagNames.UniversalTrialNumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Universal_trial_number_utn);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.EudraCTNumber:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.EudractId);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.EUTrialNumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Eu_trial_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.INDNumber:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.IndNumber);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.SB_CIVID_SIN:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Civ_id_sin_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.NCTnumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.National_clinical_trial_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.jRCTnumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Japanese_trial_registry_number_jrct);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.NMPAnumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.National_medical_products_administration_nmpa_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.EUDAMED:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Eudamed_srn_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.IDEnumber:
                        {
                            if (study == null)
                                study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.Investigational_device_exemption_ide_number);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.StudyPhase:
                        {
                            if (protocolTitleDto == null)
                                protocolTitleDto = studyService.GetProtocolTitleDto(studyUid, version).GetAwaiter().GetResult();

                            SetText(contentControl.Range, protocolTitleDto.TrialPhaseCode.Name);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.DevelopmentStage:
                        {
                            // 2024-02-02: awaiting API implementation

                            //if (study == null)
                            //    study = studyService.GetStudy(studyUid, version).GetAwaiter().GetResult();

                            //SetText(contentControl.Range, study?.Current_metadata?.Identification_metadata?.Registry_identifiers?.);
                            break;
                        }
                    case ContentControlTagNames.ObjectivesEndpoints:
                        {
                            var docxBytes = studyService.GetObjectivesEndpoints(studyUid, version).GetAwaiter().GetResult();
                            if (docxBytes == null)
                            {
                                SetText(contentControl.Range);
                                break;
                            }

                            fileHandler.InsertFile(docxBytes, contentControl.Range, "Objectives-and-endpoints.docx");
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.StudydesignGraphic:
                        {
                            var image = studyService.GetStudyDesign(studyUid, version).GetAwaiter().GetResult();
                            if (image == null)
                            {
                                SetText(contentControl.Range);
                                break;
                            }

                            fileHandler.InsertImage(image, contentControl.Range, "StudyDesign.svg");
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.Flowchart:
                    case ContentControlTagNames.SoA:
                        {
                            var docxBytes = studyService.GetFlowchart(studyUid).GetAwaiter().GetResult();
                            if (docxBytes == null)
                            {
                                SetText(contentControl.Range);
                                break;
                            }

                            fileHandler.InsertFile(docxBytes, contentControl.Range, "flowchart-temp.docx");
                            fileHandler.SetTableStyle(contentControl.Range);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.InclusionCriteria:
                        {
                            var ic = studyService.GetInclusionCriteria(studyUid, version).GetAwaiter().GetResult();
                            if (ic is null || !ic.Any())
                            {
                                SetText(contentControl.Range);
                                break;
                            }
                            UpdateCriteria(contentControl, ic);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }
                    case ContentControlTagNames.ExclusionCriteria:
                        {
                            var ec = studyService.GetExclusionCriteria(studyUid, version).GetAwaiter().GetResult();
                            if (ec is null || !ec.Any())
                            {
                                SetText(contentControl.Range);
                                break;
                            }
                            UpdateCriteria(contentControl, ec);
                            StepExecuted?.Invoke(this, null);
                            break;
                        }

                    default:
                        throw new Exception($"Content control with tag {contentControl.Tag} not mapped");
                }

                contentControl.LockContents = original;
            }
        }

        /// <summary>
        /// Set the Content Control text. If no text provided a default data not found text will be set
        /// </summary>
        /// <param name="range">The Range of the Content Control</param>
        /// <param name="text">The text to set. Null if using the default data not found text</param>
        protected void SetText(Microsoft.Office.Interop.Word.Range range, string text = null)
        {
            range.Text = string.IsNullOrWhiteSpace(text) ?
                No_Data_In_StudyBuilder :
                text;
        }

        protected void UpdateCriteria(ContentControl contentControl, IEnumerable<StudySelectionCriteria> items)
        {
            // Constants
            const string customListStyle = "Bullet List Numbered";
            contentControl.Range.Text = "";

            var bulletItems = new List<string>();

            foreach (var item in items)
            {
                var content = item.Criteria?.Name_plain?.Trim() ?? item.Latest_criteria?.Name_plain?.Trim();
                if (!string.IsNullOrWhiteSpace(content))
                {
                    bulletItems.Add(content);
                }
            }

            contentControl.Range.Text = string.Join(Environment.NewLine, bulletItems);

            dynamic ccStyle = contentControl.Range.get_Style();
            if (!string.Equals(ccStyle.NameLocal, customListStyle, StringComparison.OrdinalIgnoreCase))
            {
                contentControl.Range.set_Style(customListStyle);
            }
        }
    }
}
