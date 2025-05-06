using Microsoft.Office.Interop.Word;
using System;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol.DomainServices
{
    public class Utility
    {
        public static void UpdateAllFieldsInTheDocument()
        {
            var Application = Globals.ThisAddIn.Application;
            //Application.ActiveDocument.Bookmarks.Add(BookmarkNames.CrossRefBookmark, Range: Globals.ThisAddIn.Application.Selection.Range);
            //Application.ActiveDocument.Bookmarks.ShowHidden = false;

            var bolOriginalAlertState = Application.DisplayAlerts;
            Application.DisplayAlerts = Microsoft.Office.Interop.Word.WdAlertLevel.wdAlertsNone;
            Application.ScreenUpdating = false;

            // Set Objects
            var Doc = Application.ActiveDocument;
            var wnd = Doc.ActiveWindow;
            //Microsoft.Office.Interop.Word.Field fld;

            // get Active Pane Number
            var lngActPane = wnd.ActivePane.Index;

            // Hold View Type of Main pane
            var lngMain = wnd.Panes[1].View.Type;

            // Hold SplitSpecial
            var lngSplit = wnd.View.SplitSpecial;

            // Get Rid of any split
            wnd.View.SplitSpecial = Microsoft.Office.Interop.Word.WdSpecialPane.wdPaneNone;

            // Set View to Normal
            wnd.View.Type = Microsoft.Office.Interop.Word.WdViewType.wdNormalView;

            // Loop through each story in doc to update
            foreach (Microsoft.Office.Interop.Word.Range range in Doc.StoryRanges)
            {
                if (range.StoryType == Microsoft.Office.Interop.Word.WdStoryType.wdCommentsStory)
                {
                    Application.DisplayAlerts = Microsoft.Office.Interop.Word.WdAlertLevel.wdAlertsNone;
                    // Update fields
                    range.Fields.Update();
                    Application.DisplayAlerts = Microsoft.Office.Interop.Word.WdAlertLevel.wdAlertsNone;
                }
                else
                {
                    range.Fields.Update();
                }
            }

            //Loop through text boxes and update
            foreach (Microsoft.Office.Interop.Word.Shape shape in Doc.Shapes)
            {
                if (shape.TextFrame.HasText == (int)Microsoft.Office.Core.MsoTriState.msoTrue)
                {
                    shape.TextFrame.TextRange.Fields.Update();
                }
            }

            // Loop through all cross-reference fields and ensures that they are blue and underlined  - code added by SLVA (11-Aug-2019)
            foreach (Microsoft.Office.Interop.Word.Field fld in Doc.Fields)
            {
                fld.Select();
                if (fld.Type == Microsoft.Office.Interop.Word.WdFieldType.wdFieldRef)
                {
                    // make hyperlink underlined and blue
                    Application.Selection.Font.Underline = Microsoft.Office.Interop.Word.WdUnderline.wdUnderlineSingle;
                    Application.Selection.Font.Color = Microsoft.Office.Interop.Word.WdColor.wdColorBlue;
                }
            }

            Globals.ThisAddIn.Application.Selection.Collapse(Microsoft.Office.Interop.Word.WdCollapseDirection.wdCollapseStart);

            // Loop through TOC and update
            foreach (TableOfContents toc in Doc.TablesOfContents)
            {
                toc.Update();
            }

            // Loop through TOA and update
            foreach (TableOfAuthorities toa in Doc.TablesOfAuthorities)
            {
                toa.Update();
            }

            // Loop through TOF and update
            for (int x = 1; x <= Doc.TablesOfFigures.Count; x++)
            {
                Doc.TablesOfFigures[x].Update();
            }

            // Loop through TOT and update (TOT is also a TOF)
            for (int x = 1; x <= Doc.TablesOfFigures.Count; x++)
            {
                Doc.TablesOfFigures[x].Update();
            }

            // Return Split to original state
            wnd.View.SplitSpecial = lngSplit;

            // Return main pane to original state
            wnd.Panes[1].View.Type = lngMain;

            // Active proper pane
            wnd.Panes[lngActPane].Activate();

            // Close and release all pointers
            Application.DisplayAlerts = WdAlertLevel.wdAlertsAll;

            Application.ScreenUpdating = true;

            //fld = null;
            wnd = null;
            Doc = null;

            // Go to the table of contents - code added by SLVA 11-Aug-2019
            // ActiveDocument.TablesOfContents(1).Range.Select
            // Selection.Collapse Direction:=wdCollapseStart
            // Selection.MoveUp Unit:=wdParagraph
            //Application.Selection.GoTo(What: Microsoft.Office.Interop.Word.WdGoToItem.wdGoToBookmark, Name: BookmarkNames.TableOfContents);
            // TODO: still delete this bookmark?
            //if (BookmarkExists(BookmarkNames.CrossRefBookmark))
            //{
            //    Application.ActiveDocument.Bookmarks[BookmarkNames.CrossRefBookmark].Delete();
            //}
        }

        private static bool FindBrokenReferences()
        {
            // Traverse all document story ranges
            foreach (Range storyRange in Globals.ThisAddIn.Application.ActiveDocument.StoryRanges)
            {
                foreach (Field field in storyRange.Fields)
                {
                    var fieldResult = field.Result;
                    if (!string.IsNullOrWhiteSpace(fieldResult.Text) && fieldResult.Text.Contains("Error!"))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        public static void BrokenReferenceLinkFunction(bool updateFields = true)
        {
            if (updateFields)
            {
                UpdateAllFieldsInTheDocument();
            }

            var errorsFound = FindBrokenReferences();
            if (errorsFound)
            {
                MessageBox.Show($"Document contains some corrupt cross-references. {Environment.NewLine}Search for Error! to find corrupt cross-references in the document.", "Cross-reference error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        public static bool BookmarkExists(string bookmarkName)
        {
            if (string.IsNullOrWhiteSpace(bookmarkName)) return false;

            foreach (Bookmark bookmark in Globals.ThisAddIn.Application.ActiveDocument.Bookmarks)
            {
                if (bookmark.Name.ToLowerInvariant() == bookmarkName.ToLowerInvariant())
                {
                    return true;
                }
            }

            return false;
        }

        /// <summary>
        /// Formats various properties on the custom xml part inserted into the given content control
        /// </summary>
        /// <param name="cc">Content control containing custom xml</param>
        /// <param name="autoFitToWindow">Determines the Word table AutoFitBehvior.AutoFitToWindow</param>
        public static void FormatHeaderTableMargins(ContentControl cc, bool autoFitToWindow = false)
        {
            // Left margins on 1st column cells
            cc.Range.Tables[1].Cell(1, 1).LeftPadding = 0;
            cc.Range.Tables[1].Cell(2, 1).LeftPadding = 0;
            cc.Range.Tables[1].Cell(3, 1).LeftPadding = 0;
            cc.Range.Tables[1].Cell(4, 1).LeftPadding = 0;

            // Little hack for landscape tables
            if (autoFitToWindow)
            {
                cc.Range.Tables[1].AutoFitBehavior(WdAutoFitBehavior.wdAutoFitWindow);
            }
            else
            {
                // Move specific text in, since printing will cut the last part off
                cc.Range.Tables[1].Cell(1, 5).LeftPadding = 2;
            }
        }

        public static string[] CaptionLabels => new string[2] { "Table", "Figure" };

        public static int NonBreakingSpaceCode => 160;

        public static string NonBreakingSpace => char.ConvertFromUtf32(NonBreakingSpaceCode);
        public static string BreakingSpace => char.ConvertFromUtf32(32);
        public static string NonBreakingHyphen => char.ConvertFromUtf32(30);
        public static string BreakingHyphen => char.ConvertFromUtf32(150);

        public static void InsertBookmarkAtCursor(string bookmarkName)
        {
            if (!Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Exists(bookmarkName))
            {
                Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Add(Name: bookmarkName, Range: Globals.ThisAddIn.Application.Selection);
            }
        }

        public static void RemoveBookmark(string bookmarkName)
        {
            if (Globals.ThisAddIn.Application.ActiveDocument.Bookmarks.Exists(bookmarkName))
            {
                Globals.ThisAddIn.Application.ActiveDocument.Bookmarks[bookmarkName].Delete();
            }
        }

        public static void SelectNext(WdGoToItem wdGoToItem = WdGoToItem.wdGoToLine)
        {
            // Hack to avoid error when cursor is placed inside the special content control currently named "Type of document" and tag "ccType"
            var parent = Globals.ThisAddIn.Application.Selection.Range.ParentContentControl;
            if (parent != null && string.Equals(parent.Tag, "ccType", StringComparison.OrdinalIgnoreCase))
            {
                Range next = parent.Range.GoToNext(wdGoToItem);
                next.Select();
            }
        }

        //public static bool IsVpnAvailable()
        //{
        //    return NetworkInterface.GetIsNetworkAvailable()
        //        && NetworkInterface.GetAllNetworkInterfaces()
        //                           .FirstOrDefault(ni => ni.Description.Contains("Cisco"))?.OperationalStatus == OperationalStatus.Up;
        //}
    }
}
