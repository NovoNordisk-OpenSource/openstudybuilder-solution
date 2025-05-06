using Microsoft.Office.Interop.Word;
using NN_Studybuilder_Protocol.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class ContentControlManager
    {
        private readonly ConfigManager configManager;

        public ContentControlManager(ConfigManager configManager)
        {
            this.configManager = configManager;
        }

        /// <summary>
        /// Returns the range of the first occurence of a content control with the given tag
        /// </summary>
        /// <param name="tag"></param>
        /// <param name="range"></param>
        /// <returns></returns>
        public virtual ContentControl GetContentControlFromRangeByTag(string tag, Range range)
        {
            foreach (ContentControl cc in range.ContentControls)
            {
                if (tag.ToUpperInvariant() == cc.Tag.ToUpperInvariant())
                {
                    return cc;
                }
            }

            return null;
        }

        /// <summary>
        /// Returns the range of the first occurence of a content control with the given title
        /// </summary>
        /// <param name="tag">The title of the content control</param>
        /// <returns></returns>
        public virtual ContentControl GetContentControlByTag(string tag)
        {
            if (string.IsNullOrWhiteSpace(tag)) throw new ArgumentNullException(nameof(tag));

            ContentControls contentControls = Globals.ThisAddIn.Application.ActiveDocument.SelectContentControlsByTag(tag);
            if (contentControls != null && contentControls.Count > 0)
            {
                // Content Controls collection is 1-indexed (not zero-indexed as regular .net collections)
                return contentControls[1];
            }

            return null;
        }

        /// <summary>
        /// Update the document header with the selected study uid
        /// </summary>
        /// <param name="uid">The guid of the selected study</param>
        public virtual void UpdateDateStudyId(string uid)
        {
            var updatedText = $"Study ID: {uid}";
            var section = Globals.ThisAddIn.Application.ActiveDocument.Sections[1];
            ContentControl headerContentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
            if (headerContentControl == null)
            {
                Tables tables = section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range.Tables;
                if (tables?.Count > 0)
                {
                    Range lineTwo = tables[1].Cell(2, 1).Range;
                    if (lineTwo != null)
                    {
                        lineTwo.Text = updatedText;
                    }
                }
            }
            // Pre doc template v14.0 there was a surrounding content control in the header section
            else if (headerContentControl.Range.Tables.Count > 0)
            {
                ContentControl lineTwo = GetContentControlFromRangeByTag("ccDocInfoLine2", headerContentControl.Range.Tables[1].Cell(2, 1).Range);
                if (lineTwo != null)
                {
                    lineTwo.Range.Text = updatedText;
                }
            }
        }

        public ContentControl AddWithRange(string title, string tag, Range range, bool temporary = false)
        {
            var cc = Globals.ThisAddIn.Application.ActiveDocument.ContentControls.Add(WdContentControlType.wdContentControlRichText, range);
            cc.Title = title;
            cc.Tag = tag;
            if (temporary)
            {
                cc.Temporary = temporary;
            }

            return cc;
        }

        public bool ToggleContentControlStartEndTagsVisible(bool showTags)
        {
            if (showTags == configManager.ShowContentControlStartEndTags)
            {
                return false;
            }

            configManager.ShowContentControlStartEndTags = showTags;
            var hasChanged = false;

            var undoRecord = Globals.ThisAddIn.Application.UndoRecord;
            undoRecord.StartCustomRecord("Start/End tags " + (showTags ? "visible" : "hidden"));

            try
            {
                foreach (ContentControl cc in Globals.ThisAddIn.Application.ActiveDocument.ContentControls)
                {
                    if (!cc.Tag.StartsWith(StudyBuilderConstants.ContentControlPrefix, StringComparison.OrdinalIgnoreCase)) continue;
                    if (showTags)
                    {
                        // Only change appearance if it has acutally changed - to avoid that end users get a "Save document" prompt if they have not made any changes
                        if (cc.Appearance != WdContentControlAppearance.wdContentControlTags)
                        {
                            cc.Appearance = WdContentControlAppearance.wdContentControlTags;
                            hasChanged = true;
                        }
                    }
                    else
                    {
                        if (cc.Appearance != WdContentControlAppearance.wdContentControlBoundingBox)
                        {
                            cc.Appearance = WdContentControlAppearance.wdContentControlBoundingBox;
                            hasChanged = true;
                        }
                    }
                }

                undoRecord.EndCustomRecord();
            }
            catch
            {
                Globals.ThisAddIn.Application.ActiveDocument.Undo();
                throw;
            }

            return hasChanged;
        }

        public bool GetStartEndTagState()
        {
            var showTagsFromConfig = GetStartEndTagStateFromConfig();
            var showTagsFromContentControls = GetStartEndTagStateFromContentControls();

            // State in Content Controls take priority
            if (showTagsFromConfig != showTagsFromContentControls)
            {
                configManager.ShowContentControlStartEndTags = showTagsFromContentControls;
                return showTagsFromContentControls;
            }

            return showTagsFromContentControls;
        }

        protected bool GetStartEndTagStateFromContentControls()
        {
            foreach (ContentControl cc in Globals.ThisAddIn.Application.ActiveDocument.ContentControls)
            {
                if (!cc.Tag.StartsWith(StudyBuilderConstants.ContentControlPrefix, StringComparison.OrdinalIgnoreCase)) continue;

                // Return true with the first occurence of any of the specified content controls
                return cc.Appearance == WdContentControlAppearance.wdContentControlTags;
            }

            return false;
        }

        protected bool GetStartEndTagStateFromConfig()
        {
            return configManager.ShowContentControlStartEndTags;
        }

        public void ClearContentFromAllStudyBuilderContentControls()
        {
            foreach (ContentControl cc in Globals.ThisAddIn.Application.ActiveDocument.ContentControls)
            {
                try
                {
                    if (cc.Tag is null || !cc.Tag.StartsWith(StudyBuilderConstants.ContentControlPrefix, StringComparison.OrdinalIgnoreCase)) continue;
                    if (cc.ShowingPlaceholderText) continue;

                    var lockContentsOriginal = cc.LockContents;
                    var lockContentControlOriginal = cc.LockContentControl;

                    cc.LockContentControl = false;
                    cc.LockContents = false;

                    // Must delete tables before resetting content control
                    if (cc.Range.Tables.Count > 1)
                    {
                        // Must delete tables in reverse order
                        for (int i = cc.Range.Tables.Count; i > 0; i--)
                        {
                            cc.Range.Tables[i].Delete();
                        }
                    }

                    cc.Range.Text = null;

                    cc.LockContents = lockContentsOriginal;
                    cc.LockContentControl = lockContentControlOriginal;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Could not clear text in content control with tag name {cc.Tag}{Environment.NewLine}{Environment.NewLine}{ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        public IEnumerable<ContentControl> GetAllStudyBuilderContentControls()
        {
            var result = new List<ContentControl>();
            foreach (ContentControl cc in Globals.ThisAddIn.Application.ActiveDocument.ContentControls)
            {
                if (cc.Tag is null || !cc.Tag.StartsWith(StudyBuilderConstants.ContentControlPrefix, StringComparison.OrdinalIgnoreCase)) continue;
                result.Add(cc);
            }

            return result;
        }

        public void DeleteAllStudyBuilderContentControls(bool deleteContents = true)
        {
            var ccs = GetAllStudyBuilderContentControls().OrderByDescending(c => c.Range?.Start).ToList();
            for (int i = ccs.Count() - 1; i >= 0; i--)
            {
                ccs[i]?.Delete(deleteContents);
            }
        }
    }
}
