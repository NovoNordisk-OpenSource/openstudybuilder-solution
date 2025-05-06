using Microsoft.Office.Core;
using Microsoft.Office.Interop.Word;
using System;

namespace NN_Studybuilder_Protocol.DomainServices
{
    /// <summary>
    /// Migrated from the old VBA module 'modHeader'
    /// </summary>
    public class SectionManager
    {
        public enum TableNodeName { PortraitTable, LandscapeTable };
        CustomXMLPart optPart;

        /// <summary>
        /// Changes the orientation of the current section. If Portrait, change to Landscape and vice-versa.
        /// </summary>
        public virtual void ToggleOrientation(Selection selection)
        {
            var sectionNumber = selection.Information[WdInformation.wdActiveEndSectionNumber];
            Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionNumber];
            if (section.PageSetup.Orientation == WdOrientation.wdOrientPortrait)
            {
                SectionchangeTolandscape(section);
            }
            else
            {
                SectionchangeToPortrait(section);
            }
        }

        protected virtual void SectionchangeTolandscape(Section section)
        {
            Globals.ThisAddIn.Application.ScreenUpdating = false;

            FormatLandscapeSection(section);

            var contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
            if (contentControl == null) return;

            OPT_GetTable(TableNodeName.LandscapeTable, contentControl, section.Index, true);

            Globals.ThisAddIn.Application.ScreenUpdating = true;
        }

        protected virtual void SectionchangeToPortrait(Section section)
        {
            Globals.ThisAddIn.Application.ScreenUpdating = false;

            FormatPortaitSection(section);

            var contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
            if (contentControl == null) return;

            OPT_GetTable(TableNodeName.PortraitTable, contentControl, section.Index);

            Globals.ThisAddIn.Application.ScreenUpdating = true;
        }

        protected void OnErrorResumeNext(Action action)
        {
            try
            {
                action();
            }
            catch
            {
                // do nothing
            }
        }

        protected virtual void OPT_GetTable(TableNodeName tableNodeName, ContentControl cc, int sectionCount, bool fitToWindow = false)
        {
            // this block mimics the original VBA code, which swallowed a lot of exceptions
            //OnErrorResumeNext(() => cc.Range.Delete());
            OnErrorResumeNext(() => cc.Range.Tables[1].Delete());
            OnErrorResumeNext(() => cc.Range.Paragraphs.First.Range.Font.Size = 1);
            OnErrorResumeNext(() => cc.Range.Paragraphs.First.Range.ParagraphFormat.SpaceAfter = 0);

            var nodeValue = GetNodeValue(tableNodeName.ToString());
            OnErrorResumeNext(() => cc.Range.InsertXML(nodeValue));
            OnErrorResumeNext(() => cc.Range.Paragraphs.Last.Range.Delete());

            Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionCount].Footers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range.Font.Size = 1;

            Utility.FormatHeaderTableMargins(cc, fitToWindow);
        }

        public virtual void UpdateDateColumnTextPotraitSection(string txt, int sectionIndex, string date)
        {
            Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionIndex];
            UpdateDateColumnTextPotraitSection(txt, section, date);
        }

        public void UpdateDateColumnTextLandScapeSection(string txt, int sectionCount, string date)
        {
            Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionCount];
            UpdateDateColumnTextPotraitSection(txt, section, date);
        }

        public virtual void UpdateDateColumnTextPotraitSection(string txt, Section section, string date)
        {
            ContentControl contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
            if (contentControl.Range.Tables.Count > 0)
            {
                contentControl.Range.Tables[1].Cell(1, 3).Range.Text = txt;
                ContentControl ccDate = GetContentControlFromRangeByTag("ccDate", contentControl.Range.Tables[1].Cell(1, 4).Range);
                if (ccDate != null)
                {
                    ccDate.SetPlaceholderText(Text: date);
                }
            }
        }

        /// <summary>
        /// Helper function to retrieve the value of a specific node from custom XML.
        /// </summary>
        /// <param name="sNodeName"></param>
        /// <returns></returns>
        public virtual string GetNodeValue(string sNodeName)
        {
            if (CheckVariables())
            {
                CustomXMLNodes oNodes = optPart.SelectNodes("//" + sNodeName);

                if (oNodes.Count > 0)
                {
                    return oNodes[1].Text;
                }
            }

            return string.Empty;
        }


        /// <summary>
        /// Checks and declares the module-level variables if an XML-part with the "optNS" namespace exists.
        /// </summary>
        protected virtual bool CheckVariables()
        {
            try
            {
                CustomXMLParts xmlTable = Globals.ThisAddIn.Application.ActiveDocument.CustomXMLParts.SelectByNamespace("optNS");
                if (xmlTable != null && xmlTable.Count > 0)
                {
                    optPart = xmlTable[1];
                    return true;
                }
            }
            catch
            {
                return false;
            }

            return false;
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
        /// Adds a new page with landscape orientation
        /// </summary>
        /// <param name="selection"></param>
        //internal void LandscapeSection(Selection selection)
        //{
        //    // Store the section index of current section.
        //    var sectionIndex = selection.Information[WdInformation.wdActiveEndSectionNumber];
        //    //Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionIndex];

        //    // Adds a bookmark at the end of selection and inserts a section page break
        //    Globals.ThisAddIn.Application.ScreenUpdating = false;
        //    selection.TypeParagraph();
        //    selection.TypeParagraph();
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Add("Her", selection.Range);
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.DefaultSorting = WdBookmarkSortBy.wdSortByName;
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.ShowHidden = false;

        //    selection.MoveUp(WdUnits.wdLine, 1);
        //    selection.InsertBreak(WdBreakType.wdSectionBreakNextPage);

        //    //Set the section variable equal to the section on the newly created page
        //    var newSectionIndex = sectionIndex + 1;
        //    Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[newSectionIndex];

        //    //Format the new section
        //    FormatLandscapeSection(section);

        //    // Set header to match the orientation
        //    var contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
        //    if (contentControl == null) return;

        //    //OPT_GetLandscapeTable(contentControl, newSectionIndex);
        //    OPT_GetTable(TableNodeName.LandscapeTable, contentControl, newSectionIndex, true);

        //    // Move selection to the new section
        //    selection.GoTo(What: WdGoToItem.wdGoToBookmark, Name: "Her");
        //    selection.MoveUp(WdUnits.wdLine, 1);

        //    Globals.ThisAddIn.Application.ScreenUpdating = true;
        //}

        /// <summary>
        /// Adds a new page with portrait orientation
        /// </summary>
        /// <param name="selection"></param>
        //internal void PortaitSection(Selection selection)
        //{
        //    // Store the section index of current section.
        //    var sectionIndex = selection.Information[WdInformation.wdActiveEndSectionNumber];

        //    // Adds a bookmark at the end of selection and inserts a section page break
        //    Globals.ThisAddIn.Application.ScreenUpdating = false;
        //    selection.TypeParagraph();
        //    selection.TypeParagraph();
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Add("Her", selection.Range);
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.DefaultSorting = WdBookmarkSortBy.wdSortByName;
        //    Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.ShowHidden = false;

        //    selection.MoveUp(WdUnits.wdLine, 1);
        //    selection.InsertBreak(WdBreakType.wdSectionBreakNextPage);

        //    //Set the section variable equal to the section on the newly created page
        //    var newSectionIndex = sectionIndex + 1;
        //    Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[newSectionIndex];

        //    Globals.ThisAddIn.Application.ScreenUpdating = false;

        //    //Format the new section
        //    FormatPortaitSection(section);

        //    // Set header to match the orientation
        //    var contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
        //    if (contentControl == null) return;

        //    //OPT_GetPortraitTable(contentControl, newSectionIndex);
        //    OPT_GetTable(TableNodeName.PortraitTable, contentControl, newSectionIndex);

        //    // Move selection to the new section
        //    selection.GoTo(What: WdGoToItem.wdGoToBookmark, Name: "Her");
        //    selection.MoveUp(WdUnits.wdLine, 1);

        //    section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].LinkToPrevious = false;

        //    Globals.ThisAddIn.Application.ScreenUpdating = true;
        //}

        /// <summary>
        /// Adds a new page with the specified orientation
        /// </summary>
        /// <param name="selection">The selection to insert after</param>
        /// <param name="isPortaitOrientation">Whether orientation is portrait (true) or landscape (false)</param>
        internal Section InsertSection(Selection selection, bool isPortaitOrientation)
        {
            Globals.ThisAddIn.Application.ScreenUpdating = false;

            var sectionIndex = selection.Information[WdInformation.wdActiveEndSectionNumber];

            // Adds a bookmark at the end of selection and inserts a section page break
            selection.TypeParagraph();
            selection.TypeParagraph();
            Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Add("Her", selection.Range);
            Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.DefaultSorting = WdBookmarkSortBy.wdSortByName;
            Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.ShowHidden = false;

            selection.MoveUp(WdUnits.wdLine, 1);
            selection.InsertBreak(WdBreakType.wdSectionBreakNextPage);

            //Set the section variable equal to the section on the newly created page
            var newSectionIndex = sectionIndex + 1;
            Section section = Globals.ThisAddIn.Application.ActiveDocument.Sections[newSectionIndex];
            // Remove link to the previous section to avoid collateral updates
            section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].LinkToPrevious = false;

            //Format the new section
            if (isPortaitOrientation)
            {
                FormatPortaitSection(section);
            }
            else
            {
                FormatLandscapeSection(section);
            }

            // Set header to match the orientation
            var contentControl = GetContentControlFromRangeByTag("rtf", section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range);
            if (contentControl == null)
            {
                throw new Exception("No content control found in primary document header");
            }

            if (isPortaitOrientation)
            {
                OPT_GetTable(TableNodeName.PortraitTable, contentControl, newSectionIndex);
            }
            else
            {
                OPT_GetTable(TableNodeName.LandscapeTable, contentControl, newSectionIndex, true);
            }

            // Move selection to the new section
            selection.GoTo(What: WdGoToItem.wdGoToBookmark, Name: "Her");
            selection.MoveUp(WdUnits.wdLine, 1);

            Globals.ThisAddIn.Application.ScreenUpdating = true;

            return section;
        }

        public void FormatLandscapeSection(Section section, bool linkToPrevious = false)
        {
            section.PageSetup.Orientation = WdOrientation.wdOrientLandscape;
            section.PageSetup.TopMargin = Globals.ThisAddIn.Application.CentimetersToPoints(3.5f);
            section.PageSetup.BottomMargin = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.LeftMargin = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.RightMargin = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.Gutter = Globals.ThisAddIn.Application.CentimetersToPoints(0);
            section.PageSetup.HeaderDistance = Globals.ThisAddIn.Application.CentimetersToPoints(2.5f);
            section.PageSetup.FooterDistance = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.SectionStart = WdSectionStart.wdSectionNewPage;
            section.PageSetup.GutterPos = WdGutterStyle.wdGutterPosLeft;
        }

        public void FormatPortaitSection(Section section, bool linkToPrevious = false)
        {
            section.PageSetup.Orientation = WdOrientation.wdOrientPortrait;
            section.PageSetup.TopMargin = Globals.ThisAddIn.Application.CentimetersToPoints(3.5f);
            section.PageSetup.BottomMargin = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.LeftMargin = Globals.ThisAddIn.Application.CentimetersToPoints(2.5f);
            section.PageSetup.RightMargin = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.Gutter = Globals.ThisAddIn.Application.CentimetersToPoints(0);
            section.PageSetup.HeaderDistance = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.FooterDistance = Globals.ThisAddIn.Application.CentimetersToPoints(1.5f);
            section.PageSetup.SectionStart = WdSectionStart.wdSectionNewPage;
            section.PageSetup.GutterPos = WdGutterStyle.wdGutterPosLeft;
        }

        public void UpdateLastSection()
        {
            var sectionCount = Globals.ThisAddIn.Application.ActiveDocument.Sections.Count;
            var section = Globals.ThisAddIn.Application.ActiveDocument.Sections[sectionCount];
            section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].LinkToPrevious = false;
            section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range.Delete();
            section.Range.Select();

            var objCC = section.Headers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range.ContentControls.Add(WdContentControlType.wdContentControlRichText);
            objCC.Tag = "rtf";
            objCC.Title = "rtf";
            objCC.Range.Paragraphs.First.Range.Font.Size = 1;
            objCC.Range.Paragraphs.First.Range.ParagraphFormat.SpaceAfter = 0;

            if (section.PageSetup.Orientation == WdOrientation.wdOrientLandscape)
            {
                var nodeValue = GetNodeValue(TableNodeName.LandscapeTable.ToString());
                objCC.Range.InsertXML(nodeValue);
                Utility.FormatHeaderTableMargins(objCC, true);
            }
            else
            {
                var nodeValue = GetNodeValue(TableNodeName.PortraitTable.ToString());
                objCC.Range.InsertXML(nodeValue);
                Utility.FormatHeaderTableMargins(objCC);
            }

            //if (!customPropertyManager.DateAllowed)
            //{
            //    UpdateDateColumnTextPotraitSection(string.Empty, sectionCount, string.Empty);
            //}

            objCC.Range.Paragraphs.Last.Range.Delete();
            section.Footers[WdHeaderFooterIndex.wdHeaderFooterPrimary].Range.Font.Size = 1;
        }
    }
}
